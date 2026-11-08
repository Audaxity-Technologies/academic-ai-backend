# Student Intelligence Suite - Setup Guide

**Generated:** November 8, 2026  
**Purpose:** Setup and run instructions for the Student Intelligence Suite

---

## Prerequisites

### System Requirements
- **Operating System:** Windows, macOS, or Linux
- **Python:** 3.12 or higher
- **Node.js:** 18 or higher
- **PostgreSQL:** 14 or higher with pgvector extension
- **Redis:** 7 or higher (optional, for caching and queue)
- **Git:** For version control

### Required Accounts
- **Google Cloud Account:** For Google Books and YouTube Data API keys (optional)
- **OpenAlex Account:** For optional API key (recommended)
- **NCBI Account:** For optional PubMed API key (optional)

---

## Backend Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd academic-ai-backend
```

### 2. Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
uv sync --locked --inexact
pip install pytest httpx
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Application
APP_NAME=Academic AI API
APP_VERSION=1.0.0
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/minutes

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Syllabus
SYLLABUS_TOP_K=10
SYLLABUS_CHUNK_SIZE=1800

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM Providers (at least one required)
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
GEMINI_MODEL=gemini-3.8-flash
GROQ_MODEL=openai/gpt-oss-120b
OLLAMA_MODEL=qwen3:8b

# Education API Keys (optional)
OPENALEX_API_KEY=your-openalex-key
CROSSREF_MAILTO=contact@example.com
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key
NCBI_API_KEY=your-ncbi-key
NCBI_TOOL=Minutes
NCBI_EMAIL=contact@example.com
GOOGLE_BOOKS_API_KEY=your-google-books-key
YOUTUBE_API_KEY=your-youtube-key

# Redis (optional, for caching and queue)
REDIS_URL=redis://localhost:6379/0

# OCR (optional, for scanned syllabus documents)
TESSDATA_PREFIX=C:\path\to\tessdata
```

### 5. Set Up Database

```bash
# Create PostgreSQL database
createdb minutes

# Enable pgvector extension
psql -d minutes -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
alembic upgrade head
```

### 6. Run Backend Server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd ../audaxity_frontend
```

### 2. Install Dependencies

```bash
npm ci
```

### 3. Configure Environment Variables

Create a `.env` file in the frontend root:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 4. Run Frontend Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rag_pipeline.py

# Run with coverage
pytest --cov=app

# Run PostgreSQL integration tests (opt-in)
$env:AUDAXITY_DATABASE_INTEGRATION = "1"
$env:DATABASE_URL = "<disposable PostgreSQL connection URL>"
pytest tests/test_database_workflow.py tests/test_syllabus_postgres.py
```

### Frontend Tests

```bash
npm run typecheck
npm run build
```

---

## Database Migrations

### Create New Migration

```bash
alembic revision --autogenerate -m "Add quiz models"
```

### Apply Migration

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

### Generate SQL for Review

```bash
alembic upgrade head --sql
```

---

## Syllabus CLI Usage

### Parse Syllabus Document

```powershell
# Basic parsing
python -m app.ai.syllabus.cli --input ".\sample_syllabus.pdf" --output-dir ".\syllabus_output"

# With native PDF text
python -m app.ai.syllabus.cli --input ".\sample_syllabus.pdf" --output-dir ".\syllabus_output" --native-pdf

# With OCR (requires Tesseract)
$env:TESSDATA_PREFIX = "C:\path\to\tessdata"
python -m app.ai.syllabus.cli --input ".\scanned_syllabus.pdf" --output-dir ".\syllabus_output"
```

---

## External API Key Setup

### OpenAlex (Recommended)

1. Go to https://openalex.org/register
2. Create free account
3. Get API key from account settings
4. Add to `.env`: `OPENALEX_API_KEY=your-key`

### Crossref (No Key Required)

Add to `.env`: `CROSSREF_MAILTO=contact@example.com`

### Semantic Scholar (Optional)

1. Go to https://www.semanticscholar.org/product/api#request-a-key
2. Submit request form
3. Wait for approval (no guaranteed timeline)
4. Add to `.env`: `SEMANTIC_SCHOLAR_API_KEY=your-key`

### NCBI/PubMed (Optional)

1. Go to https://www.ncbi.nlm.nih.gov/account/
2. Create account
3. Go to Account Settings → API Key Management
4. Create API key
5. Add to `.env`: `NCBI_API_KEY=your-key`

### Google Books (Optional)

1. Go to https://console.cloud.google.com
2. Create project
3. Enable Books API
4. Create API key
5. Restrict key to Books API
6. Add to `.env`: `GOOGLE_BOOKS_API_KEY=your-key`

### YouTube Data API (Optional)

1. Go to https://console.cloud.google.com
2. Create project
3. Enable YouTube Data API v3
4. Create API key
5. Restrict key to YouTube Data API
6. Add to `.env`: `YOUTUBE_API_KEY=your-key`

---

## Docker Setup (Optional)

### Backend Dockerfile

Create `Dockerfile` in backend root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --locked --inexact

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Already exists in `audaxity_frontend/Dockerfile`

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: minutes
      POSTGRES_USER: minutes
      POSTGRES_PASSWORD: minutes
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./academic-ai-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://minutes:minutes@postgres:5432/minutes
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./academic-ai-backend:/app
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs

  frontend:
    build: ./audaxity_frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### Run with Docker Compose

```bash
docker-compose up -d
```

---

## Production Deployment Checklist

### Security
- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False`
- [ ] Restrict `CORS_ORIGINS` to production domains
- [ ] Use environment-specific database credentials
- [ ] Enable HTTPS
- [ ] Restrict API keys to specific IPs/domains
- [ ] Set up database backups
- [ ] Enable firewall rules

### Database
- [ ] Use production PostgreSQL instance
- [ ] Enable pgvector extension
- [ ] Run migrations on production database
- [ ] Set up read replicas if needed
- [ ] Configure connection pooling
- [ ] Set up automated backups

### External APIs
- [ ] Obtain production API keys
- [ ] Monitor API usage and quotas
- [ ] Set up rate limiting
- [ ] Implement caching
- [ ] Configure fallback providers

### Monitoring
- [ ] Set up logging
- [ ] Configure error tracking (Sentry)
- [ ] Set up metrics (Prometheus)
- [ ] Configure health checks
- [ ] Set up alerts

### Performance
- [ ] Enable Redis caching
- [ ] Configure CDN for static assets
- [ ] Use cloud storage (S3/GCS)
- [ ] Enable gzip compression
- [ ] Optimize database queries
- [ ] Set up load balancing

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Ensure you're in the `academic-ai-backend` directory and virtual environment is activated.

**Problem:** `psycopg2.OperationalError: connection refused`

**Solution:** Ensure PostgreSQL is running and `DATABASE_URL` is correct.

**Problem:** `pgvector extension not found`

**Solution:** Run `CREATE EXTENSION vector;` in PostgreSQL database.

**Problem Whisper transcription fails

**Solution:** Ensure `faster-whisper` is installed and model files can be downloaded.

### Frontend Issues

**Problem:** `VITE_API_BASE_URL is not defined`

**Solution:** Create `.env` file in frontend root with `VITE_API_BASE_URL`.

**Problem:** API requests failing with CORS error

**Solution:** Ensure backend `CORS_ORIGINS` includes frontend URL.

**Problem:** Build fails with TypeScript errors

**Solution:** Run `npm run typecheck` to identify and fix type errors.

### External API Issues

**Problem:** OpenAlex returning 429 errors

**Solution:** Implement rate limiting or obtain API key for higher limits.

**Problem:** YouTube API quota exceeded

**Solution:** Monitor quota usage, implement caching, or request quota increase.

**Problem:** Semantic Scholar API key not approved

**Solution:** Use unauthenticated tier (shared pool) or skip provider.

---

## Development Workflow

### Feature Development Workflow

1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement backend changes (models, services, API)
3. Create database migration: `alembic revision --autogenerate -m "Feature name"`
4. Run migration: `alembic upgrade head`
5. Implement frontend changes
6. Write tests
7. Run tests: `pytest`
8. Test manually
9. Commit changes
10. Create pull request

### Hotfix Workflow

1. Create hotfix branch: `git checkout -b hotfix/issue-description`
2. Implement fix
3. Create migration if needed
4. Run tests
5. Commit changes
6. Merge to main branch
7. Tag release: `git tag v1.0.1`

---

## API Testing

### Using cURL

```bash
# Health check
curl http://127.0.0.1:8000/

# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Get courses (with token)
curl http://127.0.0.1:8000/api/v1/courses/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search (RAG)
curl "http://127.0.0.1:8000/api/v1/search/?query=machine+learning&course_id=COURSE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Swagger UI

Navigate to `http://127.0.0.1:8000/docs` for interactive API documentation.

---

## Performance Tuning

### Database Tuning

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '16MB';

-- Increase effective cache size
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Restart PostgreSQL after changes
```

### Application Tuning

```python
# In app/core/config.py
# Increase database pool size
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_pre_ping": True,
}
```

---

## Backup and Restore

### Database Backup

```bash
pg_dump -U minutes -d minutes > backup.sql
```

### Database Restore

```bash
psql -U minutes -d minutes < backup.sql
```

### File Backup

```bash
# Backup uploads and outputs
tar -czf backup-files.tar.gz uploads outputs
```

---

## Uninstallation

### Remove Virtual Environment

```powershell
# Windows
Remove-Item -Recurse -Force .venv

# Linux/macOS
rm -rf .venv
```

### Remove Dependencies

```bash
pip freeze | xargs pip uninstall -y
```

---

## Support

### Documentation
- Repository audit: `docs/student_intelligence_audit.md`
- Implementation plan: `docs/student_intelligence_implementation_plan.md`
- Architecture: `docs/student_intelligence_architecture.md`
- Education API research: `docs/education_api_research.md`
- Syllabus guide: `SYLLABUS.md`

### Getting Help
- Check existing documentation
- Review test files for examples
- Check API documentation at `/docs`
- Review error logs

---

## Summary

This setup guide provides everything needed to:
1. Set up the development environment
2. Configure the application
3. Run the backend and frontend
4. Run tests
5. Deploy to production

**Next Steps:**
1. Complete setup
2. Run existing tests to verify installation
3. Review existing features
4. Begin Phase 1 implementation

---

**Setup Guide Complete.**


## Study Companion and Exam Preparation

Apply the additive local PostgreSQL migrations from the backend directory, then start the API.

```powershell
. .\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run npm run dev from the existing audaxity_frontend directory. Open an enrolled course and use the **Study Companion** or **Exam Preparation** tab. A teacher can prepare course search from the Companion tab after approving lecture notes. Exam generation uses selected current syllabus topics and can use indexed approved lecture passages.

The Companion uses GET/POST /api/v1/conversations, GET/DELETE /api/v1/conversations/{thread_id}, and GET/POST /api/v1/conversations/{thread_id}/messages. The student question body accepts content. The message route accepts the optional explanation_level query parameter. Message reads accept offset and limit, with the newest page returned in conversation order.

Practice endpoints are GET /api/v1/practice-exams/topics, GET/POST /api/v1/practice-exams, GET /api/v1/practice-exams/{exam_id}, and POST /api/v1/practice-exams/{exam_id}/submit. The topic and exam lists take course_id. Creation accepts course_id, topic_ids, difficulty, count, and optional duration_minutes. Submit one answer per question in order, with a zero-based choice or null and optional time in seconds. The server stores the first result and marks late submissions. Question choices and timestamps in an open attempt live in the browser until submission.

Phase 1.1 uses approved indexed lecture material. Student-uploaded document retrieval remains pending. The Phase 1.2 slice supports multiple-choice practice, scores, and feedback. Other question formats and AI-generated revision plans remain pending.


## Previous-year papers

Open **Past Papers** in a course workspace. Upload a PDF that you are permitted to use. The file and extracted questions are visible only to your account. Choose native PDF text for digital papers, or try layout extraction for complex page ordering. Scans use the same optional OCR setup as the syllabus parser.

The upload accepts PDFs up to 20 MiB and 20 pages. Questions are checked against the physical page text. Complete questions that span more than one page may be omitted. Marks are recorded only when an adjacent printed annotation can be verified. The year is optional and supplied by the uploader. Syllabus topics are pgvector suggestions from the current version, and course explanations require cited approved passages.

POST /api/v1/question-papers accepts multipart course_id, file, optional exam_year, and optional native_pdf. GET /api/v1/question-papers and GET /api/v1/question-papers/analysis accept course_id. GET /api/v1/question-papers/{paper_id} returns extracted questions. GET /api/v1/question-papers/{paper_id}/file downloads the original PDF. DELETE /api/v1/question-papers/{paper_id} removes the owner's paper. POST /api/v1/question-papers/{paper_id}/questions/{index}/explanation uses a zero-based question index.

Analysis describes the account's uploaded papers. It reports known years, recorded marks, exact repeated wording, and suggested topic counts. Practice notes are local to the current view. Model explanations do not score them.

Migration 8ac42f607d91 adds the private question paper table and duplicate-file constraint. The previous two student feature migrations remain its ancestors. Restart the API after updating the application code.


## Flashcards and spaced repetition

Open **Flashcards** in the course workspace. Create question-answer, definition, formula, concept, or cloze cards. Use three underscores for a cloze blank. Generate cards from approved lecture notes and transcripts, or from a selected syllabus topic with enough supporting text. Generation checks proposed excerpts against the supplied source and can return fewer cards than requested. Standalone PDF-to-card generation is pending.

Use **Due now** to review. The scheduler applies the SM-2 ease and interval formulas, with a first successful interval of one day, a second of six days, and later intervals rounded up. Ratings below three restart the interval sequence. This workspace schedules those cards for the next day and caps intervals at ten years. Due times are stored as UTC instants and displayed in browser time. See [Woźniak's SM-2 description](https://super-memory.org/archive/english/ol/sm2.htm).

Cards linked to topics with two or more incorrect, attempted questions across the last ten submitted practice sets are prioritised when due. You can filter by topic or source lecture, inspect actual recall ratings, and export card content and the current schedule as JSON. Review events stay in the app. Cards based on a withdrawn lecture are hidden.

GET /api/v1/flashcards takes course_id and optional due_only, topic_id, lecture_id, offset, and limit. POST /api/v1/flashcards creates a manual card. POST /api/v1/flashcards/generate creates source-backed cards. PUT and DELETE /api/v1/flashcards/{card_id} edit and remove an owned card. GET and POST /api/v1/flashcards/{card_id}/reviews read review history and schedule a due card. A review sends rating from zero to five and the card's current review_count. Replaying a successful review does not add another event.

Migration 469ad0c648b1 adds flashcards and review history. Restart the API after updating the code.


## Study Planner

Open **Study Planner** in a course. Enter an exam, assignment, or study goal, select optional current syllabus topics, and set a date range and time budget. The planner estimates workload from your minutes per topic or per goal. It fills available time up to the daily cap, accounts for time already scheduled across your courses, and prioritises topics repeatedly missed in practice. Minutes that do not fit remain visible.

Mark sessions complete when you finish them. Replanning replaces unfinished sessions while preserving completed ones. The daily and seven-day view describes scheduled work. Course lecture coverage is shown separately from your own completed sessions. Calendar dates use your browser's local date. Scheduled reminders and calendar sync remain pending. The existing notifications router does not persist or dispatch reminders.

GET /api/v1/study-planner/goals lists private goals for course_id. POST to the same path creates a goal. POST /api/v1/study-planner/goals/{goal_id}/replan accepts start_date, deadline, and daily_minutes. PATCH /api/v1/study-planner/goals/{goal_id}/sessions/{session_id} accepts completed. DELETE /api/v1/study-planner/goals/{goal_id} removes an owned goal. Migration 3c81358a47e2 adds goals and sessions.

## My Progress

Open **My Progress** in a course and choose 7, 30, or 90 days. The dashboard reads saved practice attempts, flashcard reviews, and completed study sessions. Practice accuracy divides correct answers by answered questions. Unanswered questions appear separately. Flashcard recall reports ratings of three or higher among recorded reviews. Study minutes are the planned duration of sessions marked complete. These measures describe recorded activity.

GET /api/v1/analytics/learning-progress accepts course_id, days, and timezone. Date buckets use the requested IANA time zone. The dashboard displays your private activity and uses the existing course syllabus coverage endpoint for lecture coverage. Past-paper totals describe uploaded papers and extracted questions, since that workspace does not yet score attempts.
