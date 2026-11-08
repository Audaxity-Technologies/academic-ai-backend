# Student Intelligence Suite - Repository Audit Report

**Generated:** November 8, 2026  
**Repository:** Minutes (Academic AI Platform)  
**Backend:** FastAPI + PostgreSQL  
**Frontend:** React Router v8 + TypeScript + TailwindCSS

---

## Executive Summary

Minutes is an AI-powered academic platform with a solid foundation for lecture management, transcription, notes generation, and syllabus alignment. The existing RAG infrastructure, multi-provider LLM integration, and syllabus intelligence features provide a strong base for building a comprehensive Student Intelligence Suite.

**Current State:**
- **Backend:** FastAPI with PostgreSQL + pgvector, multi-provider LLM (Gemini, Groq, Ollama), BGE embeddings
- **Frontend:** React Router v8 with modern UI components (shadcn/ui, motion, lucide-react)
- **Core Features:** Lecture upload, transcription, AI notes generation, PDF export, syllabus parsing, lecture-to-syllabus alignment, RAG-based search
- **Authentication:** JWT-based with role-based access (student, teacher, admin)
- **Database:** PostgreSQL with UUID primary keys, cascade deletes, timezone-aware timestamps

**Key Gaps for Student Intelligence:**
- No quiz/exam preparation features
- No flashcard system with spaced repetition
- No study planner or progress tracking
- No PYQ (Previous Year Question) analysis
- No educational resource discovery
- No research assistant
- No viva practice
- No learning analytics dashboard
- No collaborative study features

---

## 1. Architecture Overview

### 1.1 Backend Architecture

**Framework:** FastAPI 0.141.1  
**Language:** Python 3.12+  
**Database:** PostgreSQL with pgvector extension  
**ORM:** SQLAlchemy 2.1.4  
**Migrations:** Alembic  
**Authentication:** JWT (HS256)  
**File Storage:** Local filesystem (uploads/, outputs/, debug_outputs/)

**Project Structure:**
```
app/
├── ai/
│   ├── llm/              # Multi-provider LLM client
│   ├── pipeline/         # Lecture processing pipeline
│   ├── export/           # PDF/HTML generation
│   ├── speech/           # Whisper transcription
│   └── syllabus/         # Syllabus parsing & alignment
├── api/v1/               # API endpoints
├── core/                 # Config, constants, security
├── database/             # Session, dependencies
├── middleware/           # CORS, auth, rate limiting
├── models/               # SQLAlchemy models
├── rag/                  # RAG system (embeddings, retrieval)
├── repositories/         # Data access layer
├── schemas/              # Pydantic schemas
├── services/             # Business logic
├── utils/                # Utilities
└── workers/              # Background tasks (placeholder)
```

### 1.2 Frontend Architecture

**Framework:** React Router v8  
**Language:** TypeScript  
**Styling:** TailwindCSS v4  
**UI Components:** shadcn/ui, base-ui/react  
**Animations:** GSAP, motion  
**Icons:** lucide-react  
**State Management:** React hooks, Context API

**Project Structure:**
```
app/
├── components/
│   ├── landing/          # Landing page components
│   ├── workspace/        # Course workspace components
│   └── ui/               # Reusable UI components
├── context/              # Auth context
├── hooks/                # Custom hooks
├── lib/                  # API client, utilities
├── routes/               # Page routes
└── root.tsx              # App root
```

---

## 2. Database Models Audit

### 2.1 Existing Models

| Model | Purpose | Status | Notes |
|-------|---------|--------|-------|
| **User** | User accounts with roles (student, teacher, admin) | ✅ IMPLEMENTED | UUID PK, email unique, password_hash, JWT auth |
| **Course** | Course management with teacher-student enrollment | ✅ IMPLEMENTED | Many-to-many with students via course_students table |
| **Lecture** | Lecture records with audio/transcript sources | ✅ IMPLEMENTED | Links to Course, Transcript, Note, SyllabusMapping |
| **Transcript** | Full lecture transcript with segments | ✅ IMPLEMENTED | JSONB segments with timestamps |
| **Note** | AI-generated notes in structured JSONB format | ✅ IMPLEMENTED | Status: draft/approved/rejected, PDF/HTML paths |
| **SyllabusTopic** | Syllabus topics with embeddings | ✅ IMPLEMENTED | Vector(384) for semantic retrieval, hierarchy support |
| **SyllabusDocument** | Uploaded syllabus files (PDF/DOCX/TXT) | ✅ IMPLEMENTED | Version tracking, parsing status, hierarchy |
| **SyllabusUnit** | Syllabus units/modules | ✅ IMPLEMENTED | Part of hierarchy with page references |
| **SyllabusSubtopic** | Syllabus subtopics | ✅ IMPLEMENTED | Nested under units/topics |
| **SyllabusMapping** | Lecture-to-syllabus alignment with evidence | ✅ IMPLEMENTED | Status, confidence, evidence JSONB, version support |
| **RAGChunk** | Vector chunks for RAG search | ✅ IMPLEMENTED | Vector(384), links to course/lecture/note |
| **Department** | Department management | ⚠️ PLACEHOLDER | Model exists, no implementation |
| **Faculty** | Faculty management | ⚠️ PLACEHOLDER | Model exists, no implementation |
| **Institution** | Institution management | ⚠️ PLACEHOLDER | Model exists, no implementation |
| **Student** | Student-specific data | ⚠️ PLACEHOLDER | Model exists, no implementation |
| **Recording** | Recording metadata | ⚠️ PLACEHOLDER | Model exists, no implementation |

### 2.2 Missing Models for Student Intelligence

| Model | Purpose | Priority |
|-------|---------|----------|
| **StudySession** | Track study sessions by student, topic, duration | HIGH |
| **StudyPlan** | Study plans with goals, deadlines, schedules | HIGH |
| **StudyTask** | Individual study tasks with completion status | HIGH |
| **Flashcard** | Flashcard decks with question/answer pairs | HIGH |
| **FlashcardReview** | Spaced repetition reviews with FSRS/SM-2 scheduling | HIGH |
| **Quiz** | Quiz definitions with metadata | HIGH |
| **QuizQuestion** | Quiz questions (MCQ, short-answer, long-answer) | HIGH |
| **QuizAttempt** | Student quiz attempts with scores | HIGH |
| **QuizAnswer** | Individual question answers | HIGH |
| **PYQDocument** | Uploaded previous year question papers | HIGH |
| **PYQQuestion** | Extracted PYQ questions with metadata | HIGH |
| **SavedResource** | Bookmarked educational resources | MEDIUM |
| **ResourceCollection** | Organized resource collections | MEDIUM |
| **ResourceSearchHistory** | Search history for resources | LOW |
| **StudentLearningInsight** | Learning analytics snapshots | MEDIUM |
| **StudyGroup** | Collaborative study groups | LOW |
| **StudyGroupMembership** | Group membership with permissions | LOW |
| **ConversationThread** | AI chat conversation history | MEDIUM |
| **ConversationMessage** | Individual chat messages | MEDIUM |

---

## 3. API Endpoints Audit

### 3.1 Existing Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/health` | GET | Health check | ✅ IMPLEMENTED |
| `/api/v1/auth/login` | POST | User login | ✅ IMPLEMENTED |
| `/api/v1/auth/register` | POST | User registration | ✅ IMPLEMENTED |
| `/api/v1/users/me` | GET | Current user profile | ✅ IMPLEMENTED |
| `/api/v1/courses/` | GET/POST | List/create courses | ✅ IMPLEMENTED |
| `/api/v1/courses/{id}` | GET | Get course details | ✅ IMPLEMENTED |
| `/api/v1/courses/{id}/students` | GET/POST | Manage enrollments | ✅ IMPLEMENTED |
| `/api/v1/lectures/` | GET | List lectures | ✅ IMPLEMENTED |
| `/api/v1/lectures/upload` | POST | Upload audio lecture | ✅ IMPLEMENTED |
| `/api/v1/lectures/transcript` | POST | Submit transcript | ✅ IMPLEMENTED |
| `/api/v1/lectures/{id}` | GET | Get lecture details | ✅ IMPLEMENTED |
| `/api/v1/lectures/{id}/transcript` | GET | Get transcript | ✅ IMPLEMENTED |
| `/api/v1/notes/` | GET | List notes | ✅ IMPLEMENTED |
| `/api/v1/notes/course/{id}` | GET | Get course notes | ✅ IMPLEMENTED |
| `/api/v1/notes/{id}` | PUT | Update note status/content | ✅ IMPLEMENTED |
| `/api/v1/notes/{id}/download/pdf` | GET | Download PDF | ✅ IMPLEMENTED |
| `/api/v1/search/` | GET | RAG search | ✅ IMPLEMENTED |
| `/api/v1/search/index/{id}` | POST | Index course content | ✅ IMPLEMENTED |
| `/api/v1/syllabus/upload` | POST | Upload syllabus | ✅ IMPLEMENTED |
| `/api/v1/syllabus/{id}` | GET | Get syllabus document | ✅ IMPLEMENTED |
| `/api/v1/syllabus/{id}/parse` | POST | Parse syllabus | ✅ IMPLEMENTED |
| `/api/v1/syllabus/{id}/preview` | GET/PUT | Preview/edit hierarchy | ✅ IMPLEMENTED |
| `/api/v1/syllabus/{id}/confirm` | POST | Confirm syllabus version | ✅ IMPLEMENTED |
| `/api/v1/syllabus/{id}/units` | GET | Get units | ✅ IMPLEMENTED |
| `/api/v1/syllabus/units/{id}/topics` | GET | Get topics | ✅ IMPLEMENTED |
| `/api/v1/courses/{id}/syllabus/progress` | GET | Get syllabus progress | ✅ IMPLEMENTED |
| `/api/v1/courses/{id}/syllabus/remaining` | GET | Get remaining topics | ✅ IMPLEMENTED |
| `/api/v1/lectures/{id}/syllabus-mapping` | GET | Get lecture mapping | ✅ IMPLEMENTED |
| `/api/v1/lectures/{id}/syllabus-mapping/retry` | POST | Retry alignment | ✅ IMPLEMENTED |
| `/api/v1/courses/{id}/syllabus/versions` | GET | List syllabus versions | ✅ IMPLEMENTED |
| `/api/v1/analytics/student` | GET | Student analytics | ⚠️ PLACEHOLDER |
| `/api/v1/analytics/faculty` | GET | Faculty analytics | ⚠️ PLACEHOLDER |
| `/api/v1/analytics/department` | GET | Department analytics | ⚠️ PLACEHOLDER |
| `/api/v1/notifications/` | GET | Notifications | ⚠️ PLACEHOLDER |

### 3.2 Missing Endpoints for Student Intelligence

**AI Study Companion:**
- `POST /api/v1/conversations` - Start conversation
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation
- `POST /api/v1/conversations/{id}/messages` - Send message
- `GET /api/v1/conversations/{id}/messages` - Get messages

**Exam Preparation:**
- `POST /api/v1/quizzes` - Create quiz
- `GET /api/v1/quizzes` - List quizzes
- `GET /api/v1/quizzes/{id}` - Get quiz
- `POST /api/v1/quizzes/{id}/generate` - Generate questions
- `POST /api/v1/quizzes/{id}/attempts` - Start attempt
- `POST /api/v1/quizzes/{id}/attempts/{attempt_id}/submit` - Submit attempt
- `GET /api/v1/quizzes/{id}/attempts` - Get attempts
- `GET /api/v1/quizzes/{id}/attempts/{attempt_id}` - Get attempt results

**Previous Year Questions:**
- `POST /api/v1/pyq/upload` - Upload PYQ document
- `GET /api/v1/pyq/documents` - List PYQ documents
- `GET /api/v1/pyq/documents/{id}` - Get PYQ document
- `GET /api/v1/pyq/documents/{id}/questions` - Get extracted questions
- `POST /api/v1/pyq/documents/{id}/parse` - Parse PYQ
- `GET /api/v1/pyq/topics/{id}/frequency` - Get topic frequency

**Flashcards:**
- `POST /api/v1/flashcards` - Create flashcard
- `GET /api/v1/flashcards` - List flashcards
- `GET /api/v1/flashcards/{id}` - Get flashcard
- `PUT /api/v1/flashcards/{id}` - Update flashcard
- `DELETE /api/v1/flashcards/{id}` - Delete flashcard
- `POST /api/v1/flashcards/{id}/review` - Submit review
- `GET /api/v1/flashcards/due` - Get due cards
- `POST /api/v1/flashcards/generate` - Generate from content

**Study Planner:**
- `POST /api/v1/study-plans` - Create study plan
- `GET /api/v1/study-plans` - List study plans
- `GET /api/v1/study-plans/{id}` - Get study plan
- `PUT /api/v1/study-plans/{id}` - Update study plan
- `POST /api/v1/study-plans/{id}/sessions` - Log study session
- `GET /api/v1/study-plans/{id}/tasks` - Get tasks
- `PUT /api/v1/study-plans/{id}/tasks/{task_id}` - Update task

**Viva Practice:**
- `POST /api/v1/viva/start` - Start viva session
- `POST /api/v1/viva/{id}/answer` - Submit answer
- `GET /api/v1/viva/{id}/feedback` - Get feedback
- `GET /api/v1/viva/{id}/summary` - Get session summary

**Learning Analytics:**
- `GET /api/v1/analytics/student/progress` - Get progress dashboard
- `GET /api/v1/analytics/student/weak-topics` - Get weak topics
- `GET /api/v1/analytics/student/performance` - Get performance metrics
- `GET /api/v1/analytics/student/recommendations` - Get recommendations

**Resource Discovery:**
- `GET /api/v1/resources/search` - Search resources
- `POST /api/v1/resources` - Save resource
- `GET /api/v1/resources` - List saved resources
- `DELETE /api/v1/resources/{id}` - Delete saved resource
- `POST /api/v1/resources/collections` - Create collection
- `GET /api/v1/resources/collections` - List collections

**Research Assistant:**
- `GET /api/v1/research/papers` - Search papers
- `GET /api/v1/research/papers/{id}` - Get paper details
- `POST /api/v1/research/reading-list` - Add to reading list
- `GET /api/v1/research/reading-list` - Get reading list
- `DELETE /api/v1/research/reading-list/{id}` - Remove from list

---

## 4. Frontend Pages Audit

### 4.1 Existing Pages

| Route | Page | Status | Notes |
|-------|------|--------|-------|
| `/` | Landing page | ✅ IMPLEMENTED | Hero, features, how-it-works |
| `/login` | Login | ✅ IMPLEMENTED | Auth form |
| `/signup` | Signup | ✅ IMPLEMENTED | Registration form |
| `/workspace` | Course list | ✅ IMPLEMENTED | Teacher/student views |
| `/workspace/courses/{id}` | Course workspace | ✅ IMPLEMENTED | Materials, notes, RAG search, syllabus |
| `/prepare` | Prepare page | ✅ IMPLEMENTED | Placeholder |

### 4.2 Missing Pages for Student Intelligence

**Student Navigation:**
- `/workspace/dashboard` - Student dashboard with recommendations
- `/workspace/companion` - AI Study Companion chat interface
- `/workspace/exam-prep` - Exam preparation studio
- `/workspace/pyq` - Previous Year Questions
- `/workspace/flashcards` - Flashcard review interface
- `/workspace/planner` - Study planner
- `/workspace/viva` - Viva practice
- `/workspace/resources` - Resource discovery
- `/workspace/research` - Research assistant
- `/workspace/progress` - Learning analytics
- `/workspace/saved` - Saved items

---

## 5. AI/ML Infrastructure Audit

### 5.1 LLM Integration

**Provider:** Multi-provider with fallback  
**Primary:** Google Gemini (gemini-3.8-flash)  
**Fallbacks:** Groq (openai/gpt-oss-120b), Ollama (qwen3:8b)  
**Implementation:** `app/ai/llm/llm_client.py`  
**Features:**
- Exponential backoff retry (3 attempts)
- Configurable timeout per request
- JSON response format
- Lazy initialization (doesn't require credentials for non-AI routes)

**Status:** ✅ IMPLEMENTED and robust

### 5.2 Embeddings

**Model:** BAAI/bge-small-en-v1.5  
**Dimensions:** 384  
**Implementation:** `app/rag/embeddings.py`  
**Features:**
- lru_cache for model
- Batch embedding support
- Used for RAG and syllabus topic embeddings

**Status:** ✅ IMPLEMENTED

### 5.3 RAG System

**Components:**
- **Chunker:** `app/rag/chunker.py` - Text chunking
- **Embeddings:** `app/rag/embeddings.py` - Vector generation
- **Indexer:** `app/rag/indexer.py` - Course indexing
- **Retriever:** `app/rag/retriever.py` - Vector, BM25, hybrid search
- **Reranker:** `app/rag/reranker.py` - Result reranking
- **Service:** `app/rag/service.py` - Answer generation

**Features:**
- Vector search with pgvector cosine distance
- BM25 keyword search with caching
- Hybrid search with Reciprocal Rank Fusion
- Source citations
- Confidence scoring

**Status:** ✅ IMPLEMENTED and production-ready

### 5.4 Speech Recognition

**Provider:** faster-whisper  
**Implementation:** `app/ai/speech/transcription.py`  
**Features:**
- Audio file transcription
- Language detection
- Segment extraction with timestamps
- Multiple format support (wav, mp3, m4a, ogg, webm, mp4, flac)

**Status:** ✅ IMPLEMENTED

### 5.5 Document Processing

**Parser:** Docling (PDF/DOCX), PyMuPDF (fallback)  
**Implementation:** `app/ai/syllabus/parser.py`  
**Features:**
- PDF parsing with layout extraction
- OCR support via Tesseract
- Table extraction
- Page boundary preservation

**Status:** ✅ IMPLEMENTED for syllabus

---

## 6. Syllabus Intelligence Audit

### 6.1 Syllabus Parsing

**Status:** ✅ FULLY IMPLEMENTED  
**Features:**
- PDF/DOCX/TXT upload
- Docling-based parsing with PyMuPDF fallback
- OCR for scanned documents
- LLM-based hierarchy extraction
- Unit → Topic → Subtopic structure
- Page reference tracking
- Validation and review workflow
- Version management

**API Endpoints:**
- Upload, parse, preview, confirm workflow
- Draft editing before confirmation
- Version history

**Status:** ✅ PRODUCTION-READY

### 6.2 Lecture-to-Syllabus Alignment

**Status:** ✅ FULLY IMPLEMENTED  
**Features:**
- Two-stage alignment (semantic retrieval + LLM verification)
- Transcript chunking
- Evidence extraction with timestamps
- Coverage calculation
- Status tracking (covered, partially_covered, mentioned, not_covered)
- Confidence scoring
- Version-aware mapping
- Retry mechanism

**Status:** ✅ PRODUCTION-READY

### 6.3 Syllabus Coverage

**Status:** ✅ FULLY IMPLEMENTED  
**Features:**
- Weighted coverage calculation
- Unit-wise progress
- Topic-wise progress
- Lecture-wise evidence
- Remaining topics prioritization
- Historical version comparison

**Status:** ✅ PRODUCTION-READY

---

## 7. Authentication & Authorization Audit

### 7.1 Authentication

**Method:** JWT Bearer tokens  
**Implementation:** `app/core/security.py`  
**Features:**
- Password hashing with pwdlib (argon2)
- JWT token generation with expiration
- Token validation middleware
- Role-based access (student, teacher, admin)

**Status:** ✅ IMPLEMENTED

### 7.2 Authorization

**Implementation:** Service-layer ownership validation  
**Pattern:**
- `CourseService.get_course(user)` - Teacher access
- `CourseService.get_course_for_user(course_id, user)` - Student/Teacher access
- Repository-level filtering by user_id

**Status:** ✅ IMPLEMENTED for core features

**Gaps:**
- No fine-grained permissions for new features
- No permission system for collaborative features

---

## 8. File Storage Audit

**Current Implementation:** Local filesystem  
**Directories:**
- `uploads/` - Uploaded lectures and syllabus documents
- `outputs/` - Generated PDFs and HTML
- `debug_outputs/` - Debug artifacts

**Limitations:**
- No cloud storage integration (S3, GCS, Azure Blob)
- No CDN for static assets
- Single-server deployment only
- No file cleanup mechanism

**Status:** ⚠️ NEEDS IMPROVEMENT for production scaling

---

## 9. Background Jobs Audit

**Current Implementation:** FastAPI BackgroundTasks  
**Usage:**
- Lecture alignment queued after response completion

**Limitations:**
- No persistent queue (Redis, Celery)
- No job monitoring or retry
- No distributed execution
- Process restart loses pending jobs

**Status:** ⚠️ NEEDS IMPROVEMENT for production

**Placeholder Files:**
- `app/workers/lecture_worker.py` - Empty
- `app/workers/notification_worker.py` - Empty
- `app/workers/queue.py` - Empty

---

## 10. Testing Audit

### 10.1 Existing Tests

| Test File | Purpose | Status |
|-----------|---------|--------|
| `test_database_workflow.py` | Database workflow | ✅ PASSING |
| `test_material_permissions.py` | Material access permissions | ✅ PASSING |
| `test_rag_pipeline.py` | RAG pipeline | ✅ PASSING |
| `test_syllabus_alignment.py` | Syllabus alignment | ✅ PASSING |
| `test_syllabus_coverage.py` | Syllabus coverage | ✅ PASSING |
| `test_syllabus_mapping.py` | Syllabus mapping | ✅ PASSING |
| `test_syllabus_parser.py` | Syllabus parser | ✅ PASSING |
| `test_syllabus_postgres.py` | PostgreSQL integration | ✅ PASSING (opt-in) |

**Test Framework:** pytest  
**Coverage:** Core features (auth, courses, lectures, syllabus, RAG)  
**Status:** ✅ GOOD COVERAGE for existing features

### 10.2 Missing Tests

- No tests for new student intelligence features (expected, not implemented)
- No frontend tests
- No integration tests with external APIs
- No performance tests
- No load tests

---

## 11. Deployment & Configuration Audit

### 11.1 Configuration

**File:** `app/core/config.py`  
**Method:** pydantic-settings with .env  
**Current Variables:**
- `DATABASE_URL` - PostgreSQL connection
- `CORS_ORIGINS` - Allowed origins
- `SYLLABUS_TOP_K` - Retrieval limit (default: 10)
- `SYLLABUS_CHUNK_SIZE` - Chunk size (default: 1800)
- `JWT_SECRET_KEY` - JWT signing key
- `JWT_ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 60)

**LLM Provider Variables:**
- `GEMINI_API_KEY` - Google Gemini API key
- `GROQ_API_KEY` - Groq API key
- `GEMINI_MODEL` - Gemini model (default: gemini-3.8-flash)
- `GROQ_MODEL` - Groq model (default: openai/gpt-oss-120b)
- `OLLAMA_MODEL` - Ollama model (default: qwen3:8b)

**Status:** ✅ IMPLEMENTED

### 11.2 Deployment

**Current:** Local development setup  
**Missing:**
- Docker configuration (frontend has Dockerfile, backend does not)
- Docker Compose for full stack
- Environment-specific configs (dev, staging, prod)
- CI/CD pipeline
- Health checks beyond basic endpoint
- Logging configuration
- Monitoring/metrics

**Status:** ⚠️ NEEDS IMPROVEMENT for production

---

## 12. Feature Classification Matrix

### 12.1 Student Intelligence Features

| Feature | Status | Backend | Frontend | Tests | Notes |
|---------|--------|---------|----------|-------|-------|
| **A. Personal AI Study Companion** | | | | | |
| Contextual Q&A with course materials | PARTIALLY | ✅ RAG exists | ⚠️ Basic UI | ✅ | Extend existing RAG with conversation history |
| Multi-level explanations | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Follow-up questions | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Citation tracking | PARTIALLY | ✅ RAG has citations | ⚠️ Basic UI | ✅ | Improve UI |
| Conversation history | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| PDF-based Q&A | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Source vs general AI distinction | PARTIALLY | ✅ RAG is source-only | ⚠️ Needs UI | ✅ | Add general AI fallback option |
| **B. AI Exam Preparation Studio** | | | | | |
| Syllabus-aware question generation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Multiple question types | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Difficulty levels | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic-wise tests | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Full-length mock tests | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Explanations after answers | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Score tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Time tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Weak topic identification | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Personalised revision plan | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Question history to avoid duplicates | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Exam mode with timer | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **C. Previous Year Question Intelligence** | | | | | |
| PYQ upload (PDF) | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Question extraction | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Question mapping to syllabus | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Repeated question detection | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic frequency analysis | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Pattern identification | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic-wise collections | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Historical marks distribution | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (if data available) |
| Interactive practice | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Model answers | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Source preservation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **D. Smart Flashcards & Spaced Repetition** | | | | | |
| Flashcard generation from content | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Multiple card types | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Manual card creation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Organization by course/topic | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Spaced repetition (FSRS/SM-2) | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Difficulty rating | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Retention tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Due cards display | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Weak topic recommendations | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Export capability | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **E. Personalised Study Planner** | | | | | |
| Exam/deadline management | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Schedule generation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic prioritization | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Workload estimation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Daily/weekly targets | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Re-planning on missed sessions | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Session tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Syllabus progress display | PARTIALLY | ✅ Syllabus coverage exists | ⚠️ Needs UI | ✅ | Extend to planner |
| Calendar integration | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (OAuth) |
| Notifications | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **F. AI Viva and Oral Practice** | | | | | |
| Viva question generation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Sequential questioning | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Typed answer evaluation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Correctness/completeness scoring | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Missing concept identification | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Ideal answer display | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Follow-up questions | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic-wise performance | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Difficulty modes | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Voice interaction | NOT IMPLEMENTED | ❌ | ❌ | ❌ | Future enhancement |
| **G. Learning Analytics Dashboard** | | | | | |
| Quiz accuracy tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic-wise performance | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Flashcard retention | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Study session tracking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Syllabus coverage | PARTIALLY | ✅ Syllabus coverage exists | ⚠️ Needs UI | ✅ | Extend to analytics |
| PYQ performance | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Weak concept identification | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Revision recommendations | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Study consistency | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Actionable insights | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **H. Educational Resource Discovery** | | | | | |
| Research paper search | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (OpenAlex, etc.) |
| Book discovery | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (Open Library, Google Books) |
| Video lecture discovery | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (YouTube API) |
| Course discovery | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (SWAYAM, NPTEL) |
| OER discovery | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Contextual search | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Metadata display | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Bookmarking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Reading lists | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Source linking | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **I. AI Research Assistant** | | | | | |
| Paper search (external APIs) | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Filtering (year, author, OA) | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Abstract display | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| DOI/publisher links | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Citation relationships | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Reading list management | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Paper organization | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Legal summaries only | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Citation export | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **J. Academic Notes Workspace** | | | | | |
| Cross-course search | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Transcript search | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Topic/keyword search | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Organization by unit/topic | PARTIALLY | ✅ Syllabus structure exists | ⚠️ Needs UI | ✅ | Extend to notes |
| Bookmarking/pinning | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Personal annotations | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Revision notes generation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Formula sheets | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Definition sheets | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Combined unit documents | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Timestamp linking | PARTIALLY | ✅ Transcript has segments | ⚠️ Needs UI | ✅ | Extend to notes |
| **K. Learning Groups & Collaboration** | | | | | |
| Course-based study groups | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Shared study lists | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Shared flashcard decks | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Shared question collections | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Shared resource collections | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Collaborative notes | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Group quizzes | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Permission system | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| **L. Accessibility & Multilingual** | | | | | |
| Simplified explanations | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Multilingual support | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (depends on LLM) |
| Note translation | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Accessible UI | PARTIALLY | ⚠️ Basic semantic HTML | ⚠️ Needs ARIA | ❌ | Needs audit |
| Keyboard navigation | PARTIALLY | ⚠️ Basic keyboard support | ⚠️ Needs testing | ❌ | Needs audit |
| Screen reader support | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |
| Formula rendering | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature (KaTeX/MathJax) |
| Code formatting | NOT IMPLEMENTED | ❌ | ❌ | ❌ | New feature |

---

## 13. Technical Debt & Limitations

### 13.1 Backend

1. **No persistent queue system** - Background tasks use FastAPI BackgroundTasks, which don't survive process restarts
2. **Local file storage** - No cloud storage integration, single-server limitation
3. **No rate limiting implementation** - Middleware exists but is empty
4. **No logging configuration** - Basic logging only
5. **No monitoring/metrics** - No Prometheus, OpenTelemetry, etc.
6. **No caching layer** - No Redis for session caching or API response caching
7. **No API versioning strategy** - Only v1 exists
8. **No request ID tracking** - Difficult to trace requests across logs
9. **No health check depth** - Only basic endpoint, no dependency checks
10. **No graceful shutdown** - No signal handling for in-flight requests

### 13.2 Frontend

1. **No error boundary** - React error boundary not implemented
2. **No loading skeletons** - Basic loading states only
3. **No offline support** - No service worker or PWA
4. **No form validation library** - Manual validation
5. **No state persistence** - No local storage for drafts
6. **No analytics** - No usage tracking
7. **No A/B testing framework** - No experimentation support
8. **No feature flags** - All features always on
9. **No internationalization** - English only
10. **No dark mode** - Light mode only (though CSS supports it)

### 13.3 Database

1. **No read replicas** - Single database instance
2. **No connection pooling configuration** - Default SQLAlchemy pool
3. **No query logging** - No slow query tracking
4. **No backup automation** - Manual backups only
5. **No migration rollback automation** - Manual Alembic operations
6. **No data retention policy** - Data grows indefinitely
7. **No soft deletes** - Hard deletes only
8. **No audit logging** - No change tracking

---

## 14. Dependencies Audit

### 14.1 Backend Dependencies (from pyproject.toml)

| Dependency | Version | Purpose | Status |
|------------|---------|---------|--------|
| fastapi | 0.141.1 | Web framework | ✅ Current |
| sqlalchemy | 2.1.4 | ORM | ✅ Current |
| psycopg2-binary | 2.9.13 | PostgreSQL adapter | ✅ Current |
| pgvector | 0.5.1 | Vector extension | ✅ Current |
| alembic | 1.20.0 | Migrations | ✅ Current |
| pydantic | 2.13.4 | Validation | ✅ Current |
| pydantic-settings | 2.15.0 | Config | ✅ Current |
| python-jose | 2.15.1 | JWT | ✅ Current |
| pwdlib | 0.3.1 | Password hashing | ✅ Current |
| google-genai | 2.19.0 | Gemini API | ✅ Current |
| groq | 0.11.0 | Groq API | ✅ Current |
| ollama | 0.6.3 | Ollama client | ✅ Current |
| sentence-transformers | 6.1.0 | Embeddings | ✅ Current |
| faster-whisper | 1.2.1 | Speech recognition | ✅ Current |
| docling | 2.x | Document parsing | ✅ Current |
| pymupdf | 1.24.x | PDF processing | ✅ Current |
| reportlab | 5.0.1 | PDF generation | ✅ Current |
| rank-bm25 | 0.2.2 | BM25 search | ✅ Current |
| uvicorn | 0.52.3 | ASGI server | ✅ Current |
| python-dotenv | 1.2.2 | Env variables | ✅ Current |
| python-multipart | 0.0.32 | Form data | ✅ Current |

**Missing for Student Intelligence:**
- `httpx` or `aiohttp` - Async HTTP client for external APIs
- `tenacity` - Retry logic (optional, can use custom)
- `redis` - Caching and queue (optional for Phase 1)
- `celery` - Background tasks (optional for Phase 1)
- `katex` or `mathjax` - Formula rendering (frontend)
- `bibtexparser` - Citation export (optional)

### 14.2 Frontend Dependencies (from package.json)

| Dependency | Version | Purpose | Status |
|------------|---------|---------|--------|
| react | 19.3.0 | UI framework | ✅ Current |
| react-dom | 19.3.0 | React DOM | ✅ Current |
| react-router | 8.4.0 | Routing | ✅ Current |
| tailwindcss | 4 | Styling | ✅ Current |
| lucide-react | 1.61.0 | Icons | ✅ Current |
| motion | 14.5.0 | Animations | ✅ Current |
| gsap | 3.15.0 | Animations | ✅ Current |
| @base-ui/react | 1.9.0 | UI components | ✅ Current |
| shadcn | 4.22.1 | UI components | ✅ Current |
| class-variance-authority | 0.7.1 | Component variants | ✅ Current |
| lenis | 1.3.27 | Smooth scroll | ✅ Current |

**Missing for Student Intelligence:**
- `react-markdown` - Markdown rendering (for notes)
- `react-syntax-highlighter` - Code highlighting
- `katex` or `react-katex` - Formula rendering
- `date-fns` or `dayjs` - Date formatting
- `recharts` or `chart.js` - Analytics charts
- `react-beautiful-dnd` - Drag and drop (for flashcards)
- `react-hot-toast` - Toast notifications

---

## 15. Security Audit

### 15.1 Implemented Security

✅ Password hashing with argon2  
✅ JWT authentication with expiration  
✅ Role-based access control  
✅ CORS configuration  
✅ SQL injection protection (ORM)  
✅ File upload validation (size, type)  
✅ Ownership validation in services  
✅ Cascade deletes for data integrity  

### 15.2 Security Gaps

❌ No rate limiting (middleware exists but empty)  
❌ No input sanitization beyond Pydantic  
❌ No CSRF protection (not needed for API-only, but good practice)  
❌ No security headers (CSP, HSTS, etc.)  
❌ No request size limits (except file uploads)  
❌ No SQL injection protection for raw queries (if any)  
❌ No XSS protection in frontend (React handles most, but need validation)  
❌ No audit logging for sensitive actions  
❌ No API key rotation strategy  
❌ No secrets management (environment variables only)  

---

## 16. Performance Considerations

### 16.1 Current Performance

**Strengths:**
- Vector search with pgvector is efficient
- BM25 caching with lru_cache
- Async LLM calls with timeout
- Connection pooling (default SQLAlchemy)

**Weaknesses:**
- No response caching
- No database query optimization (no indexes on all foreign keys)
- No pagination on some endpoints
- No lazy loading for relationships
- No CDN for static assets
- No image optimization
- No code splitting in frontend

### 16.2 Performance Risks for New Features

1. **External API calls** - Need timeout, retry, caching
2. **Large file uploads** - Need streaming, chunking
3. **Vector operations** - Need approximate indexes for large datasets
4. **Real-time features** - Need WebSockets or polling
5. **Analytics queries** - Need materialized views or caching

---

## 17. Scalability Assessment

### 17.1 Current Scalability

**Single-server deployment:**
- ✅ Can handle moderate load
- ❌ No horizontal scaling
- ❌ No load balancing
- ❌ No auto-scaling

**Database:**
- ✅ PostgreSQL can scale vertically
- ❌ No read replicas
- ❌ No sharding strategy

**File storage:**
- ❌ Local filesystem only
- ❌ No distributed storage

### 17.2 Scalability Requirements for Student Intelligence

**High priority:**
- Cloud storage (S3/GCS) for file uploads
- Redis for caching and session storage
- Read replicas for database
- CDN for static assets

**Medium priority:**
- Message queue (Celery/RabbitMQ) for background jobs
- Load balancer
- Auto-scaling

**Low priority (Phase 3+):**
- Database sharding
- Microservices architecture

---

## 18. Summary & Recommendations

### 18.1 Strengths

1. **Solid foundation** - Lecture management, transcription, notes generation, syllabus alignment are production-ready
2. **Robust RAG system** - Vector search, BM25, hybrid search with citations
3. **Multi-provider LLM** - Gemini, Groq, Ollama with fallback and retry
4. **Modern frontend** - React Router v8, TypeScript, TailwindCSS, shadcn/ui
5. **Good test coverage** - Core features have passing tests
6. **Clean architecture** - Separation of concerns (models, repositories, services, API)
7. **Syllabus intelligence** - Advanced parsing, alignment, coverage tracking

### 18.2 Critical Gaps

1. **No student-facing features** - All features are teacher-centric
2. **No assessment/practice tools** - No quizzes, flashcards, PYQ analysis
3. **No learning analytics** - No progress tracking, weak topic identification
4. **No resource discovery** - No integration with educational APIs
5. **No collaboration** - No study groups, sharing
6. **No persistent queue** - Background tasks don't survive restarts
7. **No cloud storage** - Local filesystem only
8. **No rate limiting** - Vulnerable to abuse

### 18.3 Implementation Priority

**Phase 0 (This audit):**
- ✅ Repository audit
- ✅ Implementation plan
- ⏳ Education API research
- ⏳ Architecture document

**Phase 1 (Core Student Intelligence):**
1. Extend AI Study Companion with conversation history
2. Build Exam Preparation Studio
3. Build PYQ upload and analysis
4. Build Flashcards with spaced repetition
5. Build Study Planner
6. Build Learning Analytics dashboard
7. Add Redis for caching
8. Add persistent queue (Celery)

**Phase 2 (Educational Resource Discovery):**
1. Implement OpenAlex integration
2. Implement Crossref integration
3. Implement arXiv integration
4. Implement Semantic Scholar (if quota allows)
5. Implement Google Books
6. Implement YouTube Data API
7. Implement Open Library (with usage restrictions)
8. Build resource discovery UI

**Phase 3 (Advanced Features):**
1. AI Viva Practice
2. Advanced learning analytics
3. Research assistant
4. Multilingual support
5. Collaborative study groups
6. Google Classroom integration

**Phase 4 (Infrastructure):**
1. Cloud storage (S3/GCS)
2. CDN setup
3. Read replicas
4. Load balancing
5. Monitoring and logging
6. CI/CD pipeline

### 18.4 Risks

**Technical Risks:**
- External API rate limits may block features
- LLM costs may be high for question generation
- Vector search performance at scale
- Background job reliability without persistent queue

**Product Risks:**
- Student adoption without clear value proposition
- Feature creep - too many features at once
- Poor UX if features are not well-integrated
- Data privacy concerns with external APIs

**Mitigation:**
- Implement features incrementally with user feedback
- Add caching and rate limiting for external APIs
- Start with proven algorithms (SM-2 for spaced repetition)
- Provide clear opt-in for external integrations
- Monitor costs and add usage limits

---

## 19. Next Steps

1. **Complete education API research** - Document free APIs, rate limits, commercial use terms
2. **Create implementation plan** - Detailed phase-by-phase plan with dependencies
3. **Create architecture document** - System design for new features
4. **Set up infrastructure** - Redis, Celery, cloud storage
5. **Implement Phase 1** - Core student intelligence features
6. **Test and iterate** - User feedback and refinement

---

**Audit Complete.** Ready to proceed with implementation planning.


## Windsurf handoff verification

The handoff included the Phase 1.1 models, migration, repository, service, API routes, and a frontend client. The existing course tab still called one-shot search. Inspection found client-writable assistant messages, missing course authorization on saved threads, partial persistence on provider failures, and unbounded context sent to retrieval.

| Phase | At handoff | Current scope |
| --- | --- | --- |
| 1.1 Study Companion | Backend draft and frontend client | Course tab, persistent follow-ups, explanation styles, and citations to approved indexed material. Standalone student-uploaded document retrieval is pending. |
| 1.2 Exam Preparation | Planned | Syllabus-aware multiple-choice practice, timer, scoring, explanations, per-question time, and topics to revisit. Other question formats and generated revision plans are pending. |
| 1.3 Previous Year Questions | Planned | Private PDF library, source-page questions, suggested syllabus matches, exact repeats, recorded marks, and course-backed explanations. Cross-page question reconstruction, near-duplicate matching, and scored practice history remain pending. |
| 1.4 Flashcards | Planned | Private manual and generated cards, topic and lecture filters, due reviews with SM-2 intervals, history, recommendations based on practice misses, and JSON export. Standalone PDF-to-card generation remains pending. |
| 1.5 Study Planner | Planned | Private goals and deadlines, capacity-aware schedules, completed sessions, and replanning. Calendar sync and scheduled reminders are pending. |
| 1.6 Learning Progress | Planned | Course-scoped practice accuracy, topic results, flashcard recall, completed study sessions, and reported syllabus coverage. Past-paper activity remains an inventory until scored practice exists. |

The additive conversation and practice-exam migrations were applied to the configured localhost PostgreSQL database. Downgrade SQL was inspected offline and includes guards for saved data. The PostgreSQL workflow uses rollback transactions and mocked AI responses.
