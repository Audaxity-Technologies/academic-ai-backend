import json
import re
from collections import OrderedDict
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from http.client import HTTPException as HTTPClientError
from threading import Lock
from time import monotonic, sleep
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.core.config import settings
from app.schemas.education_resource import ResourceHit

CACHE_SECONDS = 900
CACHE_LIMIT = 128
HTTP_TIMEOUT = 5
MAX_RESPONSE = 512 * 1024


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


open_url = build_opener(NoRedirects()).open


def clean(value):
    return " ".join(re.sub(r"<[^>]*>", " ", unescape(value)).split())[:400] if isinstance(value, str) else ""


def doi_value(value):
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", clean(value), flags=re.I).casefold()
    return value if re.fullmatch(r"10\.\d{4,9}/\S+", value) else None


def secure_url(value):
    if not isinstance(value, str) or len(value) > 2000 or any(char.isspace() for char in value):
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme == "https" and url.hostname and url.username is None else None
    except ValueError:
        return None


def dictionaries(items):
    return (item for item in items if isinstance(item, dict)) if isinstance(items, list) else ()


def retry_delay(value):
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            seconds = 1.0
    return max(1.0, min(900.0, seconds))


def hit(provider, title, authors, year, doi, identifier=None, open_url=None):
    if not title or not (doi or identifier):
        return None
    return ResourceHit(
        id=f"doi:{doi}" if doi else identifier, title=title, authors=list(filter(None, authors))[:8],
        year=year if type(year) is int and 1000 <= year <= 2200 else None, doi=doi,
        source_url=f"https://doi.org/{quote(doi, safe='/')}" if doi else identifier,
        open_access_url=open_url, providers=[provider],
    )


def crossref_hits(payload):
    rows = payload["message"]["items"]
    if not isinstance(rows, list):
        raise ValueError("Invalid Crossref response")
    for row in dictionaries(rows):
        titles = row.get("title")
        authors = [
            clean(f"{clean(author.get('given'))} {clean(author.get('family'))}") or clean(author.get("name"))
            for author in dictionaries(row.get("author"))
        ]
        issued = row.get("issued")
        dates = issued.get("date-parts") if isinstance(issued, dict) else None
        year = dates[0][0] if isinstance(dates, list) and dates and isinstance(dates[0], list) and dates[0] else None
        result = hit("crossref", clean(titles[0]) if isinstance(titles, list) and titles else "",
                     authors, year, doi_value(row.get("DOI")))
        if result:
            yield result


def openalex_hits(payload):
    rows = payload["results"]
    if not isinstance(rows, list):
        raise ValueError("Invalid OpenAlex response")
    for row in dictionaries(rows):
        identifier = row.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"https://openalex\.org/W\d+", identifier):
            identifier = None
        access = row.get("open_access")
        open_url = secure_url(access.get("oa_url")) if isinstance(access, dict) and access.get("is_oa") is True else None
        authors = [clean(item["author"].get("display_name")) for item in dictionaries(row.get("authorships"))
                   if isinstance(item.get("author"), dict)]
        result = hit("openalex", clean(row.get("display_name")), authors, row.get("publication_year"),
                     doi_value(row.get("doi")), identifier, open_url)
        if result:
            yield result


class Provider:
    def __init__(self, name, endpoint, normalizer):
        self.name = name
        self.endpoint = endpoint
        self.normalizer = normalizer
        self.lock = Lock()
        self.cache = OrderedDict()
        self.next_request = self.cooldown_until = 0.0

    def search(self, query, limit):
        if self.name == "openalex" and (not settings.OPENALEX_API_KEY or not settings.OPENALEX_API_KEY.get_secret_value()):
            return [], "not_configured"
        if not self.lock.acquire(timeout=1):
            return [], "unavailable"
        try:
            key = (query, limit)
            now = monotonic()
            cached = self.cache.get(key)
            if cached is not None and cached[0] > now:
                self.cache.move_to_end(key)
                return cached[1], "ok"
            if self.cooldown_until > now:
                return [], "rate_limited"
            hits, status = self.fetch(query, limit)
            if status == "ok":
                self.cache[key] = (monotonic() + CACHE_SECONDS, hits)
                self.cache.move_to_end(key)
                if len(self.cache) > CACHE_LIMIT:
                    self.cache.popitem(last=False)
            return hits, status
        finally:
            self.lock.release()

    def fetch(self, query, limit):
        headers = {"Accept": "application/json", "User-Agent": "Audaxity-Metadata/1.0"}
        if self.name == "crossref":
            params = {"query.bibliographic": query, "rows": limit, "select": "DOI,title,author,issued"}
            if settings.CROSSREF_MAILTO:
                params["mailto"] = settings.CROSSREF_MAILTO
        else:
            params = {"search": query, "per_page": limit,
                      "select": "id,doi,display_name,publication_year,authorships,open_access"}
            headers["Authorization"] = f"Bearer {settings.OPENALEX_API_KEY.get_secret_value()}"
        request = Request(f"{self.endpoint}?{urlencode(params)}", headers=headers)
        for attempt in range(2):
            sleep(max(0, self.next_request - monotonic()))
            self.next_request = monotonic() + 1
            try:
                with open_url(request, timeout=HTTP_TIMEOUT) as response:
                    raw = response.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    return [], "unavailable"
                hits = list(self.normalizer(json.loads(raw)))
                self.cooldown_until = 0
                return hits, "ok"
            except HTTPError as exc:
                exc.close()
                if exc.code == 429:
                    delay = retry_delay(exc.headers.get("Retry-After") if exc.headers else None)
                    self.cooldown_until = monotonic() + delay
                    if attempt or delay > 2:
                        return [], "rate_limited"
                    self.next_request = max(self.next_request, self.cooldown_until)
                elif exc.code not in (500, 502, 503, 504) or attempt:
                    return [], "unavailable"
            except (OSError, HTTPClientError):
                if attempt:
                    return [], "unavailable"
            except (TypeError, ValueError, KeyError):
                return [], "unavailable"
        return [], "unavailable"


PROVIDERS = (
    Provider("crossref", "https://api.crossref.org/works", crossref_hits),
    Provider("openalex", "https://api.openalex.org/works", openalex_hits),
)


def search_resources(query, selected, limit):
    statuses = {}
    merged = {}
    for provider in PROVIDERS:
        if selected and provider.name != selected:
            continue
        hits, status = provider.search(query, limit)
        statuses[provider.name] = status
        for item in hits:
            existing = merged.get(item.id)
            if existing is None:
                merged[item.id] = item.model_copy(deep=True)
                continue
            existing.providers = list(dict.fromkeys([*existing.providers, *item.providers]))
            existing.open_access_url = existing.open_access_url or item.open_access_url
            existing.authors = existing.authors or item.authors
            existing.year = existing.year or item.year
    return {"results": list(merged.values()), "providers": statuses}

