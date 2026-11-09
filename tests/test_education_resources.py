import io
import json
from email.message import Message
from types import SimpleNamespace
from urllib.error import HTTPError

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.v1.health.router import router as health_router
from app.api.v1.resources import router
from app.database.dependencies.auth import get_current_user
from app.services import education_resources as resources


def crossref_payload():
    return {"message": {"items": [{
        "DOI": "10.1234/ABC", "title": ["Distributed <i>systems</i>"],
        "issued": {"date-parts": [[2024]]}, "author": [{"given": "Sam", "family": "Rao"}],
    }]}}


def test_dedup_retains_provenance_and_does_not_mutate_cache(monkeypatch):
    crossref = list(resources.crossref_hits(crossref_payload()))
    openalex = list(resources.openalex_hits({"results": [{
        "display_name": "Distributed systems", "doi": "https://doi.org/10.1234/abc",
        "open_access": {"is_oa": True, "oa_url": "https://example.com/open"},
    }, {
        "id": "https://openalex.org/W123", "display_name": "Another work",
        "open_access": {"is_oa": True, "oa_url": "javascript:alert(1)"},
    }]}))
    monkeypatch.setattr(resources, "PROVIDERS", (
        SimpleNamespace(name="crossref", search=lambda *_: (crossref, "ok")),
        SimpleNamespace(name="openalex", search=lambda *_: (openalex, "ok")),
    ))
    results = resources.search_resources("systems", None, 8)["results"]
    assert len(results) == 2
    assert results[0].providers == ["crossref", "openalex"]
    assert results[0].authors == ["Sam Rao"] and results[0].year == 2024
    assert results[0].open_access_url == "https://example.com/open"
    assert results[1].open_access_url is None
    assert crossref[0].providers == ["crossref"] and crossref[0].open_access_url is None


def test_crossref_retries_transient_failure_and_caches(monkeypatch):
    provider = resources.Provider("crossref", "https://api.crossref.org/works", resources.crossref_hits)
    calls = []

    def fetch(request, timeout):
        calls.append(request.full_url)
        assert timeout == resources.HTTP_TIMEOUT
        if len(calls) == 1:
            raise TimeoutError
        return io.BytesIO(json.dumps(crossref_payload()).encode())

    monkeypatch.setattr(resources, "open_url", fetch)
    monkeypatch.setattr(resources, "sleep", lambda _: None)
    assert provider.search("distributed systems", 8)[1] == "ok"
    assert provider.search("distributed systems", 8)[1] == "ok"
    assert len(calls) == 2


def test_provider_rate_limit_creates_cooldown(monkeypatch):
    provider = resources.Provider("crossref", "https://api.crossref.org/works", resources.crossref_hits)
    calls = []
    headers = Message()
    headers["Retry-After"] = "60"

    def fetch(request, **_):
        calls.append(request.full_url)
        raise HTTPError(request.full_url, 429, "Rate limited", headers, None)

    monkeypatch.setattr(resources, "open_url", fetch)
    assert provider.search("first search", 8) == ([], "rate_limited")
    assert provider.search("other search", 8) == ([], "rate_limited")
    assert len(calls) == 1


def test_openalex_key_stays_in_header_and_malformed_response_degrades(monkeypatch):
    provider = resources.Provider("openalex", "https://api.openalex.org/works", resources.openalex_hits)
    monkeypatch.setattr(resources.settings, "OPENALEX_API_KEY", None)
    assert provider.search("machine learning", 8) == ([], "not_configured")
    monkeypatch.setattr(resources.settings, "OPENALEX_API_KEY", SecretStr("test-key"))

    def fetch(request, **_):
        assert "test-key" not in request.full_url
        assert request.get_header("Authorization") == "Bearer test-key"
        return io.BytesIO(b'{"results":"malformed"}')

    monkeypatch.setattr(resources, "open_url", fetch)
    assert provider.search("machine learning", 8) == ([], "unavailable")


def test_search_requires_auth_and_other_routes_work_when_all_providers_fail(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    app.include_router(health_router)
    client = TestClient(app)
    assert client.get("/resources/search", params={"q": "databases"}).status_code in (401, 403)
    app.dependency_overrides[get_current_user] = lambda: object()
    monkeypatch.setattr(resources, "PROVIDERS", tuple(
        SimpleNamespace(name=name, search=lambda *_: ([], "unavailable"))
        for name in ("crossref", "openalex")
    ))
    result = client.get("/resources/search", params={"q": "databases"})
    assert result.status_code == 200
    assert result.json() == {"results": [], "providers": {"crossref": "unavailable", "openalex": "unavailable"}}
    assert client.get("/health/").json()["status"] == "healthy"

