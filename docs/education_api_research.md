# Education API Research Document

**Generated:** November 8, 2026  
**Purpose:** Research free education APIs for Student Intelligence Suite integration

---

## Executive Summary

This document researches free and conditionally-free education APIs suitable for integration into the Minutes Student Intelligence Suite. Each provider is evaluated for:

- Free tier availability and conditions
- Rate limits and quotas
- Commercial-use restrictions
- Authentication requirements
- Data availability (metadata vs full text)
- Integration priority
- Risks and limitations

**Key Findings:**
- **OpenAlex** and **Crossref** are the most suitable for research paper discovery with generous free tiers
- **arXiv** has strict rate limits (1 request per 3 seconds) but is free for commercial use with attribution
- **Semantic Scholar** requires API key approval and has low introductory limits (1 RPS)
- **Google Books** and **YouTube Data API** have low default quotas that may require quota increase requests
- **Open Library** explicitly states APIs are not for high-traffic commercial backends
- **NCBI/PubMed** is suitable for biomedical research with optional API key for higher limits

---

## Provider 1: OpenAlex

### Official Documentation
https://docs.openalex.org/  
https://help.openalex.org/api/authentication/  
https://openalex.mintlify.app/api-reference/authentication

### Use Case
- Research paper discovery
- Author discovery
- Institution discovery
- Open-access research discovery
- Citation and scholarly relationship exploration

### Authentication
- **No key required:** $0.10/day budget, 10 requests per second
- **Free API key:** $1/day budget, 30 requests per second, cursor paging
- **Paid plans:** MemberPlus ($10,000/year) for $100/day budget

### Rate Limits

| Access Level | Daily Budget | Requests/Second | Notes |
|-------------|--------------|------------------|-------|
| No API key | $0.10 | 10 | Basic use only |
| Free API key | $1.00 | 30 | Recommended for production |
| Paid plans | $20-$200/day | 50 | Annual plans |

**Special Limits:**
- Semantic search: 1 request per second (all tiers)
- Complex queries (>5 OR/AND/NOT): 1 (no key), 5 (free key), 25 (annual plan) per second
- New accounts: First $1 spent at $0.10 every 5 minutes (first 50 minutes)

### Commercial Use
✅ **ALLOWED** - All data is CC0 public-domain license  
✅ No "personal use only" restrictions  
✅ No permission required for reuse  
✅ Suitable for commercial educational products

### Data Availability
- **Metadata:** Full bibliographic metadata (title, authors, DOI, publication year, venue, concepts)
- **Open Access:** OA locations, full-text links where available
- **Citations:** Citation counts, referenced works, citing works
- **Abstracts:** Where provided by publishers
- **Full Text:** Links to OA PDFs, not stored locally

### Endpoints
- `/works` - Works (papers, books, reports)
- `/authors` - Author profiles
- `/sources` - Journals, repositories
- `/institutions` - Universities, organizations
- `/concepts` - Research topics/concepts
- `/publishers` - Publishers

### Credit Costs per Request

| Endpoint Type | Cost per 1,000 calls |
|---------------|---------------------|
| Singleton (get by ID) | Free |
| List+Filter | $0.10 |
| Search | $1.00 |
| Semantic search | $1.00 |
| Content download (PDF) | $10.00 |

### Integration Priority
**HIGH** - Generous free tier, CC0 license, comprehensive metadata

### Required Configuration
```bash
OPENALEX_API_KEY=optional_free_key
```

### Caching Policy
✅ **PERMITTED** - Cache results aggressively  
✅ Negative caching supported for not-found responses

### Risks & Limitations
- Semantic search has low rate limit (1 RPS)
- New accounts have throttled first $1
- Full-text availability depends on publisher OA status
- No bulk download without paid plan

### Test Request
```bash
# Without key
curl "https://api.openalex.org/works?search=machine+learning"

# With key
curl "https://api.openalex.org/works?search=machine+learning&api_key=YOUR_KEY"

# Check rate limit
curl "https://api.openalex.org/rate-limit?api_key=YOUR_KEY"
```

### Sample Response
```json
{
  "meta": {
    "count": 12345,
    "response_status": 200,
    "db_response_time_ms": 45,
    "page": 1
  },
  "results": [
    {
      "id": "W1234567890",
      "title": "Attention Is All You Need",
      "publication_year": 2017,
      "primary_location": {
        "source": {
          "display_name": "NeurIPS",
          "type": "conference"
        }
      },
      "open_access": {
        "is_oa": true,
        "oa_url": "https://arxiv.org/pdf/1706.03762.pdf"
      },
      "authorships": [...],
      "concepts": [...]
    }
  ]
}
```

---

## Provider 2: Crossref

### Official Documentation
https://www.crossref.org/documentation/retrieve-metadata/rest-api/  
https://api.crossref.org/swagger-ui/index.html

### Use Case
- DOI lookup
- Paper metadata
- Journal metadata
- Publication information
- Author and publisher metadata

### Authentication
- **Public:** No authentication, 5 requests/second
- **Polite:** Include `mailto` parameter, 10 requests/second
- **Metadata Plus:** API key, 150 requests/second (paid)

### Rate Limits (Updated December 1, 2025)

| Pool | Single Record | List Records | Concurrency |
|------|---------------|--------------|-------------|
| Public | 5/sec | 1/sec | 1 |
| Polite | 10/sec | 3/sec | 3 |
| Plus (paid) | 150/sec | 150/sec | None |

**Important:** Rate limits are now enforced by email address for polite pool

### Commercial Use
✅ **ALLOWED** - Most metadata is not subject to copyright  
⚠️ Some abstracts may be copyrighted by publishers  
✅ Use for any purpose permitted by data license  
⚠️ Abstract reuse requires checking publisher permissions

### Data Availability
- **Metadata:** Full bibliographic metadata (title, authors, DOI, ISSN, publisher)
- **Abstracts:** Where provided by publishers (may be copyrighted)
- **License Metadata:** Where available
- **References:** Citation links
- **Funding Data:** Where available
- **ORCID/ROR IDs:** Author and affiliation identifiers

### Endpoints
- `/works` - Works by DOI, search, filter
- `/journals` - Journal metadata
- `/members` - Publisher/member metadata
- `/funders` - Funder metadata
- `/types` - Content types
- `/licenses` - License information

### Integration Priority
**HIGH** - Free access, no registration required, comprehensive metadata

### Required Configuration
```bash
CROSSREF_MAILTO=contact@example.com
# Optional for paid tier
CROSSREF_API_KEY=your_key
```

### Caching Policy
✅ **PERMITTED** - Crossref explicitly encourages caching  
✅ Most records don't change regularly  
✅ Recommend cache duration based on data type

### Risks & Limitations
- Low rate limits for list queries (1-3/sec)
- Abstracts may be copyrighted
- No full-text access
- Rate limiting by email address (affects shared deployments)

### Test Request
```bash
# Public pool
curl "https://api.crossref.org/works/10.1128/mBio.01735-25"

# Polite pool (recommended)
curl "https://api.crossref.org/works?rows=10&mailto=contact@example.com"

# Search
curl "https://api.crossref.org/works?query.author=Smith&rows=5&mailto=contact@example.com"
```

### Sample Response
```json
{
  "status": "ok",
  "message-type": "work",
  "message": {
    "DOI": "10.1128/mBio.01735-25",
    "title": ["Paper Title"],
    "author": [...],
    "published": {
      "date-parts": [[2023, 1, 15]]
    },
    "abstract": "<jats:abstract>...</jats:abstract>",
    "license": [...]
  }
}
```

---

## Provider 3: Semantic Scholar

### Official Documentation
https://api.semanticscholar.org/  
https://www.semanticscholar.org/product/api  
https://api.semanticscholar.org/api-docs/

### Use Case
- Paper search
- Paper recommendations
- Citation information
- Related papers
- Author information

### Authentication
- **No key:** 1,000 requests/second shared among all unauthenticated users
- **API key:** 1 request/second introductory limit (requires approval)
- **Higher limits:** Available by request after review

### Rate Limits

| Access Level | Rate Limit | Notes |
|--------------|-------------|-------|
| No API key | 1,000 RPS (shared) | Contended, unpredictable |
| API key (introductory) | 1 RPS | Guaranteed, requires approval |
| API key (increased) | Variable | By request after review |

**Important:** The 1,000 RPS unauthenticated limit is a shared pool, not a per-user quota. An API key moves you to a guaranteed 1 RPS allocation.

### Commercial Use
✅ **ALLOWED** - Free API for research and educational use  
⚠️ API key approval prioritizes academic/research institutions  
⚠️ Commercial projects reviewed case-by-case  
✅ No explicit commercial-use restrictions in documentation

### Data Availability
- **Metadata:** Title, authors, year, venue, citation count
- **Abstracts:** Where available
- **Citations:** Up to 9,999 citations per request
- **References:** Cited papers
- **Related Papers:** SPECTER2 embeddings
- **Influential Citations:** Citation context

### Endpoints
- `/paper/arxiv:{arxiv_id}` - Get by arXiv ID
- `/paper/DOI:{doi}` - Get by DOI
- `/paper/{paper_id}` - Get by Semantic Scholar ID
- `/paper/search` - Search papers
- `/paper/search/bulk` - Bulk search
- `/paper/batch` - Batch get by IDs (max 500)
- `/author/{author_id}` - Author profile
- `/author/batch` - Batch author lookup (max 1,000)

### Integration Priority
**MEDIUM** - Good data quality but low introductory limits and approval requirement

### Required Configuration
```bash
SEMANTIC_SCHOLAR_API_KEY=your_key
```

### Caching Policy
✅ **PERMITTED** - Encouraged to reduce API load  
✅ Cache responses to avoid repeated requests

### Risks & Limitations
- API key approval required (no guaranteed timeline)
- Introductory limit is only 1 RPS (very low)
- Unauthenticated pool is heavily contended
- Response size capped at 10 MB
- Batch size limited to 500 papers
- Search results limited to 1,000

### Test Request
```bash
# Without key
curl "https://api.semanticscholar.org/paper/10.1145/123456"

# With key
curl -H "x-api-key: YOUR_KEY" "https://api.semanticscholar.org/paper/10.1145/123456"

# Search
curl "https://api.semanticscholar.org/graph/v1/paper/search?query=machine+learning&limit=10"
```

### Sample Response
```json
{
  "paperId": "1234567890",
  "title": "Paper Title",
  "abstract": "Abstract text...",
  "authors": [...],
  "year": 2023,
  "citationCount": 42,
  "influentialCitationCount": 15,
  "references": [...],
  "citations": [...]
}
```

---

## Provider 4: arXiv

### Official Documentation
https://info.arxiv.org/help/api/  
https://info.arxiv.org/help/api/tou.html  
https://info.arxiv.org/help/api/user-manual.html

### Use Case
- Computer science research
- AI and machine learning papers
- Mathematics and physics research
- Preprint discovery

### Authentication
- **No authentication required**
- **User-Agent and email** recommended for identification

### Rate Limits
- **Maximum:** 1 request every 3 seconds
- **Concurrency:** Single connection at a time
- **Applies to:** All machines under your control
- **Large jobs:** Limit to weekends or 9 PM - 5 AM ET weekdays

**Important:** Do not attempt to bypass limits by using multiple machines. Violations may result in IP blocking.

### Commercial Use
✅ **ALLOWED** with conditions  
✅ Commercial projects should review documentation  
✅ Consider becoming an arXiv affiliate  
✅ Independent noncommercial projects are entirely independent  
⚠️ Must acknowledge arXiv data usage  
❌ Cannot use arXiv names/logos without permission  
❌ Cannot imply arXiv endorsement

### Data Availability
- **Metadata:** Title, authors, abstract, categories, published date, arXiv ID
- **Full Text:** PDF links (not redistributable without permission)
- **Categories:** Subject classifications (cs.AI, math.OC, etc.)
- **Versions:** Version history
- **Comments:** Author comments

### Endpoints
- `/api/query` - Search and retrieve metadata
- OAI-PMH - Bulk metadata harvesting

### Integration Priority
**HIGH** - Free, comprehensive CS/AI research, but strict rate limits

### Required Configuration
```bash
ARXIV_USER_AGENT=Minutes/1.0 (contact@example.com)
```

### Caching Policy
✅ **PERMITTED** - Strongly encouraged  
✅ Results don't change until next day (24-hour submission cycle)  
✅ No need to call API more than once per day for same query

### Risks & Limitations
- Very strict rate limit (1 request per 3 seconds)
- Single connection only
- Cannot scale with multiple machines
- Preprints (not peer-reviewed)
- Full-text redistribution requires copyright holder permission
- Most papers under non-exclusive distribution license (not CC0)

### Test Request
```bash
curl "https://export.arxiv.org/api/query?search_query=all:machine+learning&start=0&max_results=10"
```

### Sample Response
```xml
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.00001</id>
    <title>Paper Title</title>
    <summary>Abstract text...</summary>
    <published>2023-01-01T00:00:00Z</published>
    <author><name>Author Name</name></author>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AI"/>
  </entry>
</feed>
```

---

## Provider 5: NCBI / PubMed

### Official Documentation
https://www.ncbi.nlm.nih.gov/home/develop/api/  
https://www.ncbi.nlm.nih.gov/books/NBK25497/

### Use Case
- Medical and life-sciences papers
- Biomedical research
- Publication metadata
- PubMed Central open-access full text

### Authentication
- **No API key:** 3 requests/second
- **API key:** 10 requests/second (default, higher by request)
- **Tool and email:** Required for >3 requests/second

### Rate Limits
- **Without API key:** Maximum 3 requests/second
- **With API key:** 10 requests/second (default)
- **Higher limits:** Available by request (eutilities@ncbi.nih.gov)
- **Large jobs:** Limit to weekends or 9 PM - 5 AM ET weekdays

**Important:** If you exceed limits without registered tool/email, your IP may be blocked. Registration required to unblock.

### Commercial Use
✅ **ALLOWED** - No explicit commercial-use restrictions  
✅ E-utilities are free public APIs  
✅ PMC full text available where license permits  
⚠️ Must include tool and email parameters  
⚠️ Must register tool/email if >3 requests/second

### Data Availability
- **Metadata:** PMID, DOI, title, authors, abstract, journal, publication date
- **Full Text:** PMC open-access articles where license permits
- **MeSH Terms:** Medical subject headings
- **References:** Citation links
- **Related Articles:** Similar articles

### Endpoints
- `esearch.fcgi` - Search for UIDs
- `esummary.fcgi` - Get document summaries
- `efetch.fcgi` - Fetch full records
- `elink.fcgi` - Link between databases
- `einfo.fcgi` - Database info

### Integration Priority
**MEDIUM** - Excellent for biomedical disciplines, optional API key

### Required Configuration
```bash
NCBI_API_KEY=optional_key
NCBI_TOOL=Minutes
NCBI_EMAIL=contact@example.com
```

### Caching Policy
✅ **PERMITTED** - Encouraged to minimize requests  
✅ Use History parameter for batch operations

### Risks & Limitations
- Rate limits apply across all machines under your control
- PMC full text only where license permits
- Must register tool/email for higher limits
- IP blocking possible for violations

### Test Request
```bash
# Without key
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=machine+learning"

# With key
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=machine+learning&api_key=YOUR_KEY"
```

### Sample Response
```xml
<eSearchResult>
  <Count>12345</Count>
  <RetMax>20</RetMax>
  <RetStart>0</RetStart>
  <IdList>
    <Id>12345678</Id>
  </IdList>
</eSearchResult>
```

---

## Provider 6: Open Library

### Official Documentation
https://openlibrary.org/developers/api  
https://openlibrary.org/dev/docs/restful_api  
https://openlibrary.org/dev/docs/api/search

### Use Case
- Book discovery
- ISBN lookup
- Book metadata
- Authors and editions
- Cover images

### Authentication
- **No authentication required**
- **User-Agent and email** recommended for identification

### Rate Limits

| Access Level | Rate Limit | Notes |
|--------------|-------------|-------|
| Default (no User-Agent) | 1 request/second | Low limit |
| Identified (User-Agent + email) | 3 requests/second | 3x higher limit |

**Important:** APIs are NOT intended as bulk data backend or high-traffic commercial infrastructure. Use data dumps for bulk access.

### Commercial Use
⚠️ **RESTRICTED** - APIs not for high-traffic commercial backends  
✅ Open-source and mission-aligned projects prioritized  
✅ Library and metadata partners prioritized  
✅ Research, learning, education tools prioritized  
❌ Not for bulk data backend  
❌ Not for high-traffic commercial services  
❌ Violations may result in blocking

### Data Availability
- **Metadata:** Title, author, edition, publication year, ISBN, cover images
- **Full Text:** Links to Internet Archive (where available)
- **Authors:** Author profiles and works
- **Editions:** Multiple editions per work
- **Subjects:** Subject classifications

### Endpoints
- `/api/books` - Get by ISBN, OCLC, LCCN
- `/search.json` - Search books (use for batch results)
- `/books/{olid}` - Get by Open Library ID
- `/authors/{olid}` - Author profile
- `/covers/{key_type}/{value}-{size}.jpg` - Cover images

### Integration Priority
**LOW** - Explicitly not for commercial backends, low rate limits

### Required Configuration
```bash
OPEN_LIBRARY_USER_AGENT=Minutes/1.0 (contact@example.com)
```

### Caching Policy
✅ **PERMITTED** - Strongly encouraged  
✅ Cache responses whenever possible  
✅ Use search.json for batch results instead of individual lookups

### Risks & Limitations
- Explicitly not for commercial backends
- Low rate limits (1-3 RPS)
- No bulk access via API (use data dumps)
- Aggressive rate limiting for violations
- May block high-traffic services
- Full-text availability depends on Internet Archive

### Test Request
```bash
# Search
curl "https://openlibrary.org/search.json?q=machine+learning&limit=5"

# Get by ISBN
curl "https://openlibrary.org/api/books?bibkeys=ISBN:9780201558025&format=json"

# With User-Agent
curl -H "User-Agent: Minutes/1.0 (contact@example.com)" "https://openlibrary.org/search.json?q=test"
```

### Sample Response
```json
{
  "docs": [
    {
      "title": "Book Title",
      "author_name": ["Author Name"],
      "first_publish_year": 2020,
      "isbn": ["9780201558025"],
      "cover_i": 12345678
    }
  ]
}
```

---

## Provider 7: Google Books API

### Official Documentation
https://developers.google.com/books/docs/v1/using

### Use Case
- Book search
- ISBN lookup
- Book metadata
- Preview availability
- Publisher and publication information

### Authentication
- **API key required** for all requests
- **OAuth 2.0** for user-scoped features (bookshelves, reading positions)

### Rate Limits
- **Default quota:** 10,000 units/day for most endpoints
- **search.list:** 100 calls/day (separate bucket)
- **videos.insert:** 100 calls/day (separate bucket)
- **Cost per call:** 1 unit for most read operations
- **Quota increase:** Currently not accepting requests (as of Feb 2026)

**Important:** Google is not currently accepting quota increase requests. Default quotas may be insufficient for production use.

### Commercial Use
✅ **ALLOWED** - No explicit commercial-use restrictions  
✅ Free API key available  
⚠️ Quota increases currently not accepted  
⚠️ Default quota may be insufficient for production

### Data Availability
- **Metadata:** Title, authors, publisher, publication date, ISBN, page count
- **Preview:** Preview availability and read links
- **Categories:** Subject classifications
- **Description:** Book descriptions
- **Full Text:** Only where publishers allow preview/embedding

### Endpoints
- `/volumes` - Search volumes
- `/volumes/{volumeId}` - Get volume by ID
- `/volumes/mylibrary` - User's library (OAuth required)

### Integration Priority
**LOW-MEDIUM** - Good data but low default quotas and no quota increases

### Required Configuration
```bash
GOOGLE_BOOKS_API_KEY=your_key
```

### Caching Policy
✅ **PERMITTED** - Encouraged to reduce quota usage  
✅ Cache results that don't change frequently

### Risks & Limitations
- Default quota may be insufficient (100 searches/day)
- Quota increase requests not currently accepted
- Keyless quota is shared and heavily rate-limited
- Full-text only where publishers allow
- Must restrict API key to Books API only

### Test Request
```bash
curl "https://www.googleapis.com/books/v1/volumes?q=machine+learning&maxResults=5&key=YOUR_KEY"
```

### Sample Response
```json
{
  "kind": "books#volumes",
  "totalItems": 100,
  "items": [
    {
      "id": "zyTCAlFPjgYC",
      "volumeInfo": {
        "title": "Book Title",
        "authors": ["Author Name"],
        "publisher": "Publisher",
        "publishedDate": "2020",
        "description": "Description...",
        "industryIdentifiers": [
          {"type": "ISBN_10", "identifier": "0201558025"}
        ],
        "accessInfo": {
          "viewability": "PARTIAL",
          "embeddable": true
        }
      }
    }
  ]
}
```

---

## Provider 8: YouTube Data API v3

### Official Documentation
https://developers.google.com/youtube/v3/docs  
https://developers.google.com/youtube/v3/determine_quota_cost

### Use Case
- Discover educational videos
- Find lectures and tutorials
- Recommend playlists
- Find topic-specific learning content

### Authentication
- **API key required** for all requests
- **OAuth 2.0** for user-scoped features (uploads, playlists)

### Rate Limits (Updated June 1, 2026)

| Bucket | Daily Allowance | Cost per Call |
|--------|-----------------|---------------|
| search.list | 100 calls | 1 call |
| videos.insert | 100 calls | 1 call |
| Everything else | 10,000 units | 1 unit (most reads), 50+ (some operations) |

**Important:** Quota resets at midnight Pacific Time. Every request costs at least 1 unit, including failed requests.

### Commercial Use
✅ **ALLOWED** - Free API with daily quota  
⚠️ Quota increase requires compliance audit  
⚠️ Audit required for additional quota  
✅ No charge per request

### Data Availability
- **Metadata:** Title, description, channel, duration, published date, view count
- **Thumbnails:** Multiple thumbnail sizes
- **Statistics:** Views, likes, comments
- **Content Details:** Duration, definition, caption availability
- **No Full Text:** No transcript access via API (would require separate scraping)

### Endpoints
- `/search` - Search videos, channels, playlists
- `/videos` - Get video details
- `/channels` - Get channel details
- `/playlists` - Get playlist details
- `/playlistItems` - Get playlist items

### Integration Priority
**MEDIUM** - Good for video discovery but low search quota (100/day)

### Required Configuration
```bash
YOUTUBE_API_KEY=your_key
```

### Caching Policy
✅ **PERMITTED** - Encouraged to reduce quota usage  
✅ Cache video metadata (title, duration rarely change)  
⚠️ Must respect YouTube's data retention policies

### Risks & Limitations
- Very low search quota (100 calls/day)
- Quota increase requires audit (no guaranteed timeline)
- No transcript access via API
- Failed requests still cost quota
- Cannot pay for more quota

### Test Request
```bash
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=machine+learning+tutorial&type=video&maxResults=5&key=YOUR_KEY"
```

### Sample Response
```json
{
  "kind": "youtube#searchListResponse",
  "items": [
    {
      "id": {"videoId": "dQw4w9WgXcQ"},
      "snippet": {
        "title": "Video Title",
        "description": "Description...",
        "channelTitle": "Channel Name",
        "publishedAt": "2023-01-01T00:00:00Z",
        "thumbnails": {
          "default": {"url": "https://..."}
        }
      }
    }
  ]
}
```

---

## Provider 9: DIKSHA

### Official Documentation
https://diksha.gov.in/  
https://api.diksha.gov.in/

### Status
❌ **NO PUBLIC API DOCUMENTATION FOUND**  
❌ Access requirements unclear  
❌ May require partner approval or credentials  
❌ Cannot implement without official access

### Use Case
- Indian educational content
- School textbooks and learning resources
- Videos and interactive content
- Multilingual educational material

### Integration Priority
**BLOCKED** - No public API documentation, requires investigation

### Required Action
- Contact DIKSHA for API access
- Determine if public access or partner approval required
- Investigate official API documentation
- Do not implement without confirmed access

---

## Provider 10: SWAYAM and NPTEL

### Official Websites
https://swayam.gov.in/  
https://nptel.ac.in/

### Status
❌ **NO PUBLIC API DOCUMENTATION FOUND**  
❌ No official APIs documented  
❌ May only provide official resource links

### Use Case
- Discover Indian online courses
- Discover engineering lectures
- Find educational course material

### Integration Strategy
- Provide curated official-resource directory with direct links
- Do not scrape websites
- Do not invent API endpoints
- Store only permitted metadata

### Integration Priority
**LOW** - No API, provide link directory only

---

## Provider 11: Project Gutenberg

### Official Information
https://www.gutenberg.org/ebooks/offline_catalogs.html

### Status
✅ **PUBLIC DOMAIN CATALOGS AVAILABLE**  
✅ No API required for catalog access  
✅ RSS feeds and static files available

### Use Case
- Public-domain book discovery
- Literature and historical books
- Metadata and catalogue search

### Data Availability
- **Catalog:** RSS feeds, static catalog files
- **Full Text:** Public-domain eBooks (legally downloadable)
- **Metadata:** Title, author, language, download counts

### Integration Strategy
- Use RSS feeds or static catalog files
- Check jurisdiction-specific public-domain status
- Preserve required attribution and notices
- Link to official book page and authorized formats

### Integration Priority
**MEDIUM** - Good for public-domain content, no API required

### Risks & Limitations
- Public-domain status varies by jurisdiction
- Not all books are public domain in all countries
- No real-time search API
- Must check copyright status per jurisdiction

---

## Provider 12: Internet Archive

### Official Documentation
https://archive.org/developers/

### Status
✅ **API DOCUMENTATION AVAILABLE**  
✅ Advanced search and metadata APIs  
✅ Wayback Machine API

### Use Case
- Book and document discovery
- Eligible full-text search
- Historical and educational resources

### Integration Strategy
- Use official advanced search API
- Retrieve metadata and permitted access links
- Check item-level access and rights
- Respect lending, access, copyright, and usage restrictions

### Integration Priority
**MEDIUM** - Good for historical content, but check rights carefully

### Risks & Limitations
- Not all books are freely downloadable
- Lending restrictions apply
- Copyright and usage restrictions vary by item
- Must respect item-level access rights

---

## Provider 13: Wikimedia APIs

### Official Documentation
https://www.mediawiki.org/wiki/Wikimedia_APIs

### Status
✅ **PUBLIC API AVAILABLE**  
✅ No authentication required for read operations  
✅ Rate limits apply but are generous

### Use Case
- General knowledge
- Wikibooks
- Wikiversity
- Wikisource
- Educational reference material

### Data Availability
- **Metadata:** Page title, extract, canonical URL
- **Content:** Page content (wikitext or HTML)
- **License:** CC BY-SA 3.0 (usually)
- **Attribution:** Required

### Integration Priority
**MEDIUM** - Good for general knowledge, requires attribution

### Risks & Limitations
- Must preserve attribution and license metadata
- Content-specific licenses may vary
- Rate limits apply
- Not all content is educational

---

## Summary Table

| Provider | Free Tier | Rate Limit | Commercial Use | Priority | API Key Required |
|----------|-----------|-------------|-----------------|----------|------------------|
| **OpenAlex** | $1/day | 30 RPS (with key) | ✅ CC0 license | HIGH | Optional |
| **Crossref** | Free | 10 RPS (polite) | ✅ Most metadata | HIGH | No (paid tier available) |
| **Semantic Scholar** | 1 RPS (introductory) | 1 RPS (with key) | ✅ With approval | MEDIUM | Yes (approval required) |
| **arXiv** | Free | 1 req/3 sec | ✅ With attribution | HIGH | No |
| **NCBI/PubMed** | Free | 10 RPS (with key) | ✅ No restrictions | MEDIUM | Optional |
| **Open Library** | Free | 3 RPS (identified) | ⚠️ Not for commercial backends | LOW | No |
| **Google Books** | 10,000 units/day | 100 searches/day | ✅ No restrictions | LOW-MEDIUM | Yes |
| **YouTube Data API** | 10,000 units/day | 100 searches/day | ✅ With audit for increase | MEDIUM | Yes |
| **DIKSHA** | Unknown | Unknown | ❌ No public API | BLOCKED | Unknown |
| **SWAYAM/NPTEL** | No API | N/A | N/A | LOW | N/A |
| **Project Gutenberg** | Free catalogs | N/A (static files) | ✅ Public domain | MEDIUM | No |
| **Internet Archive** | Free | Unknown | ✅ With rights checks | MEDIUM | No |
| **Wikimedia APIs** | Free | Generous | ✅ With attribution | MEDIUM | No |

---

## Integration Recommendations

### Phase 1 (Highest Priority)
1. **OpenAlex** - Implement first. Generous free tier, CC0 license, comprehensive metadata.
2. **Crossref** - Implement second. Free access, DOI lookup, good for paper metadata.
3. **arXiv** - Implement third. Essential for CS/AI research, but implement strict rate limiting.

### Phase 2 (Medium Priority)
4. **NCBI/PubMed** - Implement for biomedical disciplines. Optional API key for higher limits.
5. **YouTube Data API** - Implement for video discovery. Use caching aggressively due to low quota.
6. **Semantic Scholar** - Implement if API key approval is obtained. Otherwise, skip.
7. **Project Gutenberg** - Implement for public-domain book discovery via RSS/catalogs.

### Phase 3 (Lower Priority)
8. **Internet Archive** - Implement for historical content with careful rights checking.
9. **Wikimedia APIs** - Implement for general knowledge with attribution.
10. **Google Books** - Implement only if quota is sufficient. May require quota increase request.

### Not Recommended / Blocked
11. **Open Library** - Explicitly not for commercial backends. Use only for low-volume lookups.
12. **DIKSHA** - No public API. Requires investigation before implementation.
13. **SWAYAM/NPTEL** - No API. Provide link directory only.

---

## Required API Keys

| Provider | Key Required | How to Obtain | Notes |
|----------|--------------|---------------|-------|
| **OpenAlex** | Optional | https://openalex.org/register | Free account, optional key |
| **Crossref** | No (paid tier) | N/A | Polite access with mailto |
| **Semantic Scholar** | Yes | https://www.semanticscholar.org/product/api#request-a-key | Approval required |
| **arXiv** | No | N/A | User-Agent recommended |
| **NCBI/PubMed** | Optional | https://www.ncbi.nlm.nih.gov/account/ | NCBI account |
| **Open Library** | No | N/A | User-Agent recommended |
| **Google Books** | Yes | Google Cloud Console | Restrict to Books API |
| **YouTube Data API** | Yes | Google Cloud Console | Enable YouTube Data API |
| **Project Gutenberg** | No | N/A | Use RSS feeds |
| **Internet Archive** | No | N/A | No authentication |
| **Wikimedia APIs** | No | N/A | No authentication for reads |

---

## Environment Variables

```bash
# OpenAlex (optional)
OPENALEX_API_KEY=your_key

# Crossref (no key, use mailto)
CROSSREF_MAILTO=contact@example.com

# Semantic Scholar (if approved)
SEMANTIC_SCHOLAR_API_KEY=your_key

# arXiv (no key, use User-Agent)
ARXIV_USER_AGENT=Minutes/1.0 (contact@example.com)

# NCBI/PubMed (optional)
NCBI_API_KEY=your_key
NCBI_TOOL=Minutes
NCBI_EMAIL=contact@example.com

# Open Library (no key, use User-Agent)
OPEN_LIBRARY_USER_AGENT=Minutes/1.0 (contact@example.com)

# Google Books
GOOGLE_BOOKS_API_KEY=your_key

# YouTube Data API
YOUTUBE_API_KEY=your_key
```

---

## Caching Strategy

### Recommended Cache Durations

| Data Type | Cache Duration | Reason |
|-----------|----------------|--------|
| Paper metadata (OpenAlex/Crossref) | 7-30 days | Rarely changes |
| arXiv metadata | 1 day | Updates daily at midnight |
| Search results | 1-24 hours | Depends on query type |
| Video metadata (YouTube) | 7-30 days | Title/duration rarely change |
| Book metadata (Google Books) | 30-90 days | Rarely changes |
| Author profiles | 30-90 days | Rarely changes |

### Cache Invalidation
- Use `etag` or `last-modified` headers when available
- Implement negative caching for not-found responses
- Respect provider-specific cache headers
- Do not cache beyond provider data retention policies

---

## Rate Limiting Implementation

### Recommended Strategy

1. **Per-provider rate limiters** - Separate rate limiter for each provider
2. **Token bucket algorithm** - Smooth out request bursts
3. **Exponential backoff** - Retry with jitter on 429 responses
4. **Request queuing** - Queue requests when rate limit reached
5. **Circuit breaker** - Disable provider after repeated failures
6. **Monitoring** - Track rate limit usage and alert before exhaustion

### Example Rate Limit Configuration

```python
PROVIDER_RATE_LIMITS = {
    "openalex": {"requests_per_second": 30, "daily_budget_usd": 1.0},
    "crossref": {"requests_per_second": 10},
    "arxiv": {"requests_per_second": 0.33},  # 1 per 3 seconds
    "semantic_scholar": {"requests_per_second": 1},
    "ncbi": {"requests_per_second": 10},
    "open_library": {"requests_per_second": 3},
    "google_books": {"search_per_day": 100, "units_per_day": 10000},
    "youtube": {"search_per_day": 100, "units_per_day": 10000},
}
```

---

## Error Handling

### Common Error Responses

| Error Code | Meaning | Action |
|------------|---------|--------|
| 429 | Rate limit exceeded | Back off exponentially, respect Retry-After |
| 403 | Forbidden | Check authentication, permissions |
| 404 | Not found | Cache negative result |
| 500 | Server error | Retry with backoff |
| 503 | Service unavailable | Retry with backoff |

### Fallback Strategy
1. Try primary provider
2. If rate limited, try alternative provider
3. If all providers fail, return cached results if available
4. If no cache, return graceful error to user

---

## Legal and Attribution Requirements

### Required Attributions

| Provider | Attribution Requirement |
|----------|------------------------|
| **OpenAlex** | No attribution required (CC0) |
| **Crossref** | No attribution required for metadata |
| **arXiv** | "Thank you to arXiv for use of its open access interoperability" |
| **Semantic Scholar** | No explicit requirement |
| **NCBI/PubMed** | No explicit requirement |
| **Open Library** | No explicit requirement |
| **Google Books** | No explicit requirement |
| **YouTube** | No explicit requirement for public data |
| **Project Gutenberg** | Preserve license notices |
| **Internet Archive** | Respect item-specific licenses |
| **Wikimedia** | CC BY-SA 3.0 attribution |

### License Compliance
- Check each resource's specific license
- Do not assume all resources have the same license
- Respect copyright and usage restrictions
- Do not redistribute full text without permission
- Link to original source whenever possible

---

## Conclusion

**Recommended Integration Order:**
1. OpenAlex (highest priority, generous free tier)
2. Crossref (free access, DOI lookup)
3. arXiv (essential for CS/AI, strict rate limits)
4. NCBI/PubMed (biomedical disciplines)
5. YouTube Data API (video discovery, low quota)
6. Project Gutenberg (public-domain books)

**Providers to Skip/Defer:**
- Open Library (not for commercial backends)
- DIKSHA (no public API)
- SWAYAM/NPTEL (no API, use links only)
- Google Books (low quota, no increases)
- Semantic Scholar (approval required, low limits)

**Key Success Factors:**
- Implement aggressive caching
- Respect rate limits strictly
- Handle 429 responses gracefully
- Provide fallback providers
- Monitor quota usage
- Respect copyright and licenses

---

**Research Complete.** Ready for implementation planning.


## First implementation slice

Crossref public metadata search requires no key. Set CROSSREF_MAILTO to an operational contact if you want to use the polite pool. Crossref publishes separate public and polite request and concurrency limits. The integration requests titles, authors, dates, and DOIs. [Crossref REST API access and limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication)

OpenAlex search is opt-in in Minutes. Configure a server-side OPENALEX_API_KEY. OpenAlex documents anonymous access and a limited free allowance for registered accounts, with additional usage subject to its pricing and rate limits. This integration uses metadata search and can surface an OpenAlex-reported open-access link. [OpenAlex authentication](https://help.openalex.org/api/authentication/) · [OpenAlex pricing](https://help.openalex.org/access/pricing/)

Neither adapter retrieves full text. No provider keys are sent to the browser. No abstracts are cached. arXiv and the remaining discovery providers are pending.
