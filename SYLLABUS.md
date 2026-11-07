# Syllabus intelligence

## 1. Existing implementation audit

The backend already had syllabus document, unit, subtopic, and mapping models, document and lecture routes, a BGE embedding service, and an audio pipeline that returned Whisper metadata. The React Router course workspace already supported lecture submission, teacher-owned courses, and manual syllabus topics. This implementation builds on those entry points and on the existing Gemini, Groq, and Ollama client.

The Docling pipeline passed raw options where a PDF format option was required and attempted to export text from page objects. The model and draft migration both referenced a vector type that SQLAlchemy's PostgreSQL dialect does not export. The inspected database had no syllabus embedding column. The earlier report's ARRAY versus vector discrepancy did not describe the checked-out migration or the inspected schema.

The existing alignment implementation had a cosine-distance SQL query, but it did not scope candidates by syllabus version. The LLM prompt also contained unescaped format braces, identified topics by title, and suppressed verifier failures. Draft uploads deactivated the prior syllabus, and parsing replaced the course's topics. The audio transcriber consumed its segment iterator twice, while the pasted-transcript route referenced an undefined segment variable. The notes-based mapper remained callable from the lecture service, and the draft migration would have deleted duplicate mappings.

## 2. Files changed

| Backend files | Purpose |
| --- | --- |
| `app/ai/syllabus/__init__.py`, `parser.py`, `structurer.py`, `cli.py` | Document validation, layout extraction and OCR, recursive hierarchy validation, and the shared CLI |
| `app/ai/syllabus/alignment.py` | Transcript chunking, scoped vector retrieval, UUID validation, quote verification, and aggregation |
| `app/ai/llm/llm_client.py` | Per-request provider timeouts for syllabus operations |
| `app/ai/speech/transcription.py` | Capture Whisper segments from the original iterator |
| `app/api/v1/syllabus/router.py`, `coverage.py`, `app/api/v1/router.py` | Document, version, progress, evidence, and retry routes |
| `app/api/v1/courses/router.py`, `app/api/v1/lectures/router.py` | Replace the draft progress handler and queue alignment after lecture data commits |
| `app/models/__init__.py`, `syllabus.py`, `syllabus_document.py`, `syllabus_unit.py`, `syllabus_mapping.py`, `lecture.py`, `transcript.py` | Register the hierarchy models and persist version links, transcript segments, and alignment details |
| `app/repositories/syllabus_mapping_repository.py` | Batch upsert verified topic UUIDs while preserving earlier versions |
| `app/services/lecture_service.py`, `syllabus_service.py` | Save segments, retire the live notes mapper path, and limit manual topic editing to legacy topics |
| `app/services/syllabus_document_service.py`, `syllabus_alignment_service.py`, `syllabus_coverage_service.py` | Manage drafts and activation, run transcript alignment in a separate transaction, and calculate reports |
| `app/schemas/syllabus_document.py`, `syllabus_coverage.py` | Validate drafts, reports, version status, and evidence payloads |
| `app/core/config.py`, `pyproject.toml`, `uv.lock` | Configurable retrieval, PDF dependencies, and locked resolution |
| `alembic/versions/add_syllabus_document_tables.py`, `syllabus_intelligence.py` | Correct the unshipped revision and add version, alignment, and hierarchy fields |
| `tests/test_syllabus_alignment.py`, `test_syllabus_parser.py`, `test_syllabus_coverage.py`, `test_syllabus_postgres.py`, `test_syllabus_mapping.py`, `test_material_permissions.py`, `test_database_workflow.py` | Parser, mocked alignment, coverage, permissions, and opt-in PostgreSQL workflows |
| `README.md`, `SYLLABUS.md` | Link to the rollout, CLI, API, and frontend integration guide |

| Frontend files | Purpose |
| --- | --- |
| `app/lib/api/syllabus.ts`, `app/lib/api/client.ts` | Typed authenticated requests and per-request timeouts |
| `app/components/workspace/course-workspace.tsx`, `teacher-tools.tsx` | Add the syllabus workspace and show alignment progress after lecture submission |
| `app/components/workspace/syllabus.tsx`, `syllabus.css` | Upload and review, unit coverage, remaining topics, and lecture evidence |

The previous draft’s standalone subtopic table is retained in the migration. Confirmed nested topics use parent UUIDs on the existing topic table.

The existing Windsurf draft already changed the course relationship and audio pipeline output. The implementation reuses those working-tree changes, along with the draft syllabus models and router package.

## 3. PDF parser and CLI

The shared parser validates PDF readability, encryption and page count with PyMuPDF. Docling extracts PDF layout and tables, exporting Markdown for each physical page. PyMuPDF supplies sorted text and table markup if Docling fails, omits native text, or merges content across pages. Native or OCR page text anchors the suggested source references. Image-heavy pages with little native text are candidates for Tesseract OCR. Reports record blank pages, OCR pages, empty units, duplicate sibling names or numbers, and ambiguous structure.

The existing LLM converts page-marked text into a Pydantic hierarchy. The tree preserves original Roman numerals and decimal numbering. Course code, references, outcomes, and assessment metadata remain separate from teachable topics. The review workflow checks page ranges, topic limits, nesting, and title presence. Ambiguous page references are adjusted or cleared with a review warning. Confirmation generates embeddings and materializes the reviewed tree with stable UUIDs.

PDF, DOCX, and UTF-8 TXT are supported. DOCX uses Docling and is treated as one logical body because Word page boundaries depend on rendering. The CLI and API use the same implementation.

```powershell
python -m app.ai.syllabus.cli --input ".\sample_syllabus.pdf" --output-dir ".\syllabus_output"
```

For a text-based PDF with verbose layout output, add the native-text option to reduce the text sent to the provider. This mode retains page boundaries and can still OCR scan pages. Review reading order and table layout.

```powershell
python -m app.ai.syllabus.cli --input ".\sample_syllabus.pdf" --output-dir ".\syllabus_output" --native-pdf
```

The output directory contains `parsed_syllabus.json`, `parsed_syllabus.md`, `parsing_report.json`, and `extracted_preview.txt`. The extracted preview may contain private document content.

## 4. Sample parsing output

A separate live CLI run used Docling and the configured LLM on the same synthetic PDF. It emitted one unit, two topics, and two subtopics, and flagged cross-page layout recovery for review. The final output located Normalization on page 1 and Concurrency and Locking on page 2.

The excerpt below comes from the generated two-page PDF fixture in `tests/test_syllabus_parser.py`. Extraction used PyMuPDF and the fixture supplied a mocked LLM response. The JSON is abbreviated.

```json
{
  "subject_name": "Database Systems",
  "units": [
    {
      "title": "Database Design",
      "number": "III",
      "pages": [1],
      "topics": [
        {
          "title": "Normalization",
          "number": "3.2",
          "pages": [1],
          "subtopics": [
            {"title": "First Normal Form", "number": "3.2.1", "pages": [1], "subtopics": []}
          ]
        }
      ]
    },
    {
      "title": "Concurrency",
      "number": null,
      "pages": [2],
      "topics": [{"title": "Locking", "pages": [2], "subtopics": []}]
    }
  ]
}
```

```markdown
# Database Systems

## III Database Design (pp. 1)

- 3.2 Normalization (pp. 1)
  - 3.2.1 First Normal Form (pp. 1)

## Concurrency (pp. 2)

- Locking (pp. 2)

## Parsing report

2 pages, 2 units, 2 topics, 1 subtopic.
Review required: yes

- Docling was unavailable or failed. Fallback layout may need review.
```

## 5. Semantic retrieval

The existing `BAAI/bge-small-en-v1.5` model produces normalized 384-dimensional vectors. A confirmed topic's embedding includes its unit and ancestor titles, description, and immediate subtopics. Manual topics receive embeddings on the first alignment that needs them. The exact cosine-distance query restricts candidates to the course and chosen version, sorts by distance and UUID, and returns up to `SYLLABUS_TOP_K` candidates per chunk. An approximate index is omitted for the per-version corpus of at most 2,000 topics.

## 6. Alignment engine

Audio and pasted-transcript routes commit the transcript and notes before queueing work in FastAPI. The alignment job chunks the saved transcript at sentence or word boundaries where possible. It sends only retrieved candidates and the current chunk to the verifier. Pydantic validates UUIDs, allowed statuses, and confidence. Each excerpt must match the original text. Start and end times come from corresponding Whisper segments and are null when unavailable or ambiguous.

Aggregation ranks covered, partially covered, mentioned, and not covered in that order. Confidence breaks ties within the strongest status. Evidence is deduplicated by transcript offset and excerpt. Unsupported positive verdicts are flagged for review, and every applicable topic receives a row. A failure rolls back alignment writes within a savepoint and records a retryable error. A lecture row lock serializes concurrent alignment attempts. Upserts preserve topic IDs and older version mappings.

## 7. Coverage logic

Weighted coverage is `100 × (covered + 0.5 × partially_covered) / total_topics`. Mentions and uncovered topics earn zero. Every topic and nested subtopic is included once in its version's denominator. A course topic takes its strongest supported status across visible lectures. A lecture that did not map a topic contributes zero for it. Topic history includes evidence and review flags. Legacy mappings that lack verified transcript excerpts remain stored and require re-alignment to earn credit.

## 8. API endpoints

All paths below are under `/api/v1`. Supply the existing Bearer access token.

| Method and path | Purpose |
| --- | --- |
| `POST /courses/{course_id}/syllabus/upload` | Multipart `file` upload, creates an inactive draft and returns 201 |
| `POST /syllabus/upload` | Existing upload path, accepts multipart `course_id` and `file` |
| `GET /courses/{course_id}/syllabus/versions` | List course versions |
| `GET /syllabus/{document_id}` | Read metadata, extraction stage, and quality report |
| `POST /syllabus/{document_id}/parse` | Extract and validate a draft |
| `GET /syllabus/{document_id}/preview` | Fetch the nested draft or confirmed snapshot |
| `PUT /syllabus/{document_id}/preview` | Replace the editable draft hierarchy with a validated body |
| `POST /syllabus/{document_id}/confirm` | Generate topic embeddings and atomically activate the reviewed version |
| `GET /syllabus/{document_id}/units` | List confirmed unit rows with source numbering and pages |
| `GET /syllabus/units/{unit_id}/topics` | List confirmed topic rows with parent UUIDs |
| `GET /courses/{course_id}/syllabus/progress` | Get overall, unit, topic, and lecture progress |
| `GET /courses/{course_id}/syllabus/remaining` | Get uncompleted topics ordered by teaching priority |
| `GET /lectures/{lecture_id}/syllabus-mapping` | Get mappings, evidence, alignment state, and available versions |
| `GET /lectures/{lecture_id}/syllabus-summary` | Get lecture totals and alignment state |
| `POST /lectures/{lecture_id}/syllabus-mapping/retry` | Queue alignment against the current syllabus and return 202 |

Course reports accept `?version_id=<uuid>` for a confirmed version or `?legacy=true` for manual topics. Lecture reads also accept these parameters and default to the latest mapped version if the active version has no mappings for that lecture. Version lists, remaining topics, and lecture mappings accept optional offset and limit parameters. Only course owners can change documents or run alignment. Enrolled students can read confirmed versions, and lecture evidence follows existing approved-note permissions.

```powershell
$Api = "http://127.0.0.1:8000/api/v1"
$Headers = @{ Authorization = "Bearer $AccessToken" }
$Upload = Invoke-RestMethod -Method Post -Headers $Headers -Uri "$Api/courses/$CourseId/syllabus/upload" -Form @{ file = Get-Item ".\sample_syllabus.pdf" }
$Draft = Invoke-RestMethod -Method Post -Headers $Headers -Uri "$Api/syllabus/$($Upload.id)/parse"
$Draft.hierarchy | ConvertTo-Json -Depth 50
# Review the hierarchy, then optionally send edited JSON to PUT .../preview.
Invoke-RestMethod -Method Post -Headers $Headers -Uri "$Api/syllabus/$($Upload.id)/confirm"
Invoke-RestMethod -Headers $Headers -Uri "$Api/courses/$CourseId/syllabus/progress"
```

## 9. Frontend

Open the **Syllabus** tab on a course. Teachers can upload a file, see extraction and validation stages, edit the expandable unit and subtopic tree, and confirm a version. The course view has unit progress, a prioritized remaining list, historical version selection, and lecture evidence with timestamps. Teacher lecture submission shows background alignment state and offers retry. The existing manual-topic editor remains available in teacher tools.

## 10. Database migrations

The inspected local database is at `c4a8e7d2f091`, with vector extension 0.8.7, eight manual topics, 11 mapping rows, and zero duplicate lecture-topic pairs. It has no syllabus document tables or syllabus topic embedding column.

- `add_syllabus_document_tables` creates the document and hierarchy tables, adds `vector(384)`, and enforces a unique lecture/topic pair. The revision aborts on existing duplicates instead of selecting and deleting a row.
- `syllabus_intelligence` adds editable snapshots, confirmation metadata, version and hierarchy foreign keys, parsing status support, transcript segments, and alignment state. Unique constraints enforce one version number per course and one active version per course.
- Existing topics and mappings keep their UUIDs. Existing manual topics have no document UUID. Downgrades guard against discarding uploaded versions, saved transcript segments, or alignment state.

Generate SQL for review from the inspected revision without connecting to PostgreSQL.

```powershell
python -m alembic heads
python -m alembic upgrade c4a8e7d2f091:head --sql | Out-File -Encoding utf8 .\syllabus-upgrade.sql
python -m alembic downgrade syllabus_intelligence:c4a8e7d2f091 --sql | Out-File -Encoding utf8 .\syllabus-downgrade.sql
```

After approval, apply to an appropriate configured database with `python -m alembic upgrade head`. Take a backup before applying to a database that holds course records. The migration expects the database to follow the repository's Alembic history. A separately hand-modified embedding column or previously shipped copy of the draft revision needs schema inspection first.

## 11. Tests

The verified run with real Docling and Tesseract enabled reported **41 passed and two skipped**. The skipped tests are the opt-in PostgreSQL workflows. The frontend type check and production build passed. Alembic generated both SQL directions offline.

```powershell
python -m pytest -q
$env:TESSDATA_PREFIX = "C:\path\to\tessdata"
python -m pytest -q tests/test_syllabus_parser.py -k scanned
$env:AUDAXITY_DOCLING_INTEGRATION = "1"
python -m pytest -q tests/test_syllabus_parser.py -k docling
```

The PostgreSQL integration tests require an already migrated disposable database. The application and tests do not apply the migration automatically.

```powershell
$env:DATABASE_URL = "<disposable PostgreSQL connection URL>"
$env:AUDAXITY_DATABASE_INTEGRATION = "1"
python -m pytest -q tests/test_database_workflow.py tests/test_syllabus_postgres.py
```

## 12. Run on Windows

In PowerShell, from the backend project, use Python 3.12 and the repository's lockfile. If `uv` is already available, the installation line can be skipped.

```powershell
Set-Location M:\Audaxity_backend\academic-ai-backend
# For a fresh checkout, run: py -3.12 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install uv
uv sync --locked --inexact
python -m pip install pytest httpx
python -m app.ai.syllabus.cli --input ".\sample_syllabus.pdf" --output-dir ".\syllabus_output"
# Start after the approved database migration is applied.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Syllabus calls make one attempt per configured provider with a 60-second request timeout for hierarchy extraction and 30 seconds for verification. Use the project's existing `.env` with `GEMINI_API_KEY` or `GROQ_API_KEY` and optional provider model settings. A local Ollama installation is another existing provider. The CLI uses no database. Docling and BGE may download model files on first use.

| Setting | Default and purpose |
| --- | --- |
| `DATABASE_URL` | Existing PostgreSQL connection configuration, required for the API and Alembic |
| `SYLLABUS_TOP_K` | 10, bounded from 1 to 40 |
| `SYLLABUS_CHUNK_SIZE` | 1,800 transcript characters, bounded from 200 to 6,000 |
| `TESSDATA_PREFIX` | Optional path to a folder containing `eng.traineddata` |

For OCR, obtain the official Tesseract language file and point PyMuPDF's integrated Tesseract to its folder. The OCR path uses English language data. [Tesseract language data](https://github.com/tesseract-ocr/tessdata_fast), [PyMuPDF OCR setup](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html).

```powershell
$Tessdata = Join-Path $env:LOCALAPPDATA "Audaxity\tessdata"
New-Item -ItemType Directory -Force $Tessdata | Out-Null
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata" -OutFile (Join-Path $Tessdata "eng.traineddata")
$env:TESSDATA_PREFIX = $Tessdata
python -m app.ai.syllabus.cli --input ".\scanned_syllabus.pdf"
```

In a second PowerShell window, run the frontend.

```powershell
Set-Location M:\Audaxity_backend\audaxity_frontend
npm ci
npm run dev
```

## 13. Limits and rollout gaps

- PDF limits are 50 MiB, 250 pages, and 100,000 extracted characters per course document. The system asks for a smaller course-specific document when those limits are exceeded. Reviewed topic trees are limited to 2,000 nodes below units.
- Dense tables, mixed layouts, and low-quality scans still need review. DOCX layout has no reliable physical pagination. The parser records missing text and flags missing or suspicious hierarchy.
- Alignment runs in the API process after response completion. A process restart can leave a lecture pending. A teacher can requeue it. Confirming a new version does not silently realign old lectures.
- Keep uploaded syllabus files on storage shared by API instances if the deployment has more than one instance.
- The local database is now at the migration head. Both PostgreSQL integration workflows passed using rollback transactions and mocked AI calls. Browser testing against a real course remains a separate check.

## 14. Next action

The local API is ready for a representative course syllabus. Review the migration SQL before enabling the feature on another database.

