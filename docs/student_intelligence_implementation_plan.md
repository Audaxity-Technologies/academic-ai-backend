# Student Intelligence Suite - Implementation Plan

**Generated:** November 8, 2026  
**Based on:** Repository Audit and Education API Research  
**Target:** Transform Minutes into a comprehensive student academic workspace

---

## Executive Summary

This implementation plan outlines a phased approach to building the Student Intelligence Suite for Minutes. The plan prioritizes features that create genuine academic value, reuses existing infrastructure, and integrates with free education APIs where appropriate.

**Implementation Phases:**
- **Phase 0:** Repository audit and planning (COMPLETED)
- **Phase 1:** Core Student Intelligence (8-12 weeks)
- **Phase 2:** Educational Resource Discovery (6-8 weeks)
- **Phase 3:** Advanced Student Learning (8-10 weeks)
- **Phase 4:** Infrastructure improvements (ongoing)

**Total Estimated Duration:** 22-30 weeks for full implementation

---

## Phase 0: Repository Audit and Planning ✅ COMPLETED

### Deliverables
- ✅ Repository audit report (`docs/student_intelligence_audit.md`)
- ✅ Education API research (`docs/education_api_research.md`)
- ⏳ Implementation plan (this document)
- ⏳ Architecture document

### Key Findings
- Existing RAG system is production-ready
- Syllabus intelligence is fully implemented
- No student-facing features exist
- No assessment/practice tools
- No external API integrations

### Next Steps
- Complete architecture document
- Begin Phase 1 implementation

---

## Phase 1: Core Student Intelligence

**Duration:** 8-12 weeks  
**Priority:** HIGH  
**Dependencies:** None (builds on existing infrastructure)

### Objectives
Transform Minutes from a teacher-centric platform to a student-centric academic workspace with:
- Enhanced AI Study Companion
- Exam Preparation Studio
- Previous Year Question analysis
- Flashcards with spaced repetition
- Study Planner
- Learning Analytics dashboard

### 1.1 Enhanced AI Study Companion

#### Current State
- ✅ RAG system exists with vector search, BM25, hybrid search
- ✅ LLM integration with multi-provider support
- ✅ Source citations and confidence scoring
- ⚠️ Basic chat UI exists in course workspace
- ❌ No conversation history
- ❌ No multi-level explanations
- ❌ No PDF-based Q&A

#### Implementation Tasks

**Backend:**
1. Create conversation models
   - `ConversationThread` - Stores conversation metadata (course, topic, title)
   - `ConversationMessage` - Stores individual messages (role, content, citations)
   - Add foreign key relationships to User and Course
   - Add indexes on user_id, course_id, created_at

2. Create conversation service
   - `ConversationService` - Manage threads and messages
   - Methods: create_thread, get_thread, add_message, get_messages
   - Include conversation context in RAG queries
   - Support conversation history window (last N messages)

3. Enhance RAG service
   - Add conversation-aware retrieval
   - Implement multi-level explanation prompts
   - Add PDF document upload for Q&A
   - Support follow-up question context

4. Create API endpoints
   - `POST /api/v1/conversations` - Start conversation
   - `GET /api/v1/conversations` - List conversations
   - `GET /api/v1/conversations/{id}` - Get conversation
   - `POST /api/v1/conversations/{id}/messages` - Send message
   - `GET /api/v1/conversations/{id}/messages` - Get messages
   - `POST /api/v1/conversations/{id}/upload-pdf` - Upload PDF for context

**Frontend:**
1. Create conversation UI components
   - `ConversationList` - List of conversations
   - `ConversationView` - Chat interface
   - `MessageBubble` - Message display with citations
   - `ExplanationLevelSelector` - Choose explanation level
   - `PDFUploader` - Upload PDF for context

2. Create route `/workspace/companion`
3. Integrate with existing course workspace
4. Add conversation history to course view

**Database Changes:**
```sql
CREATE TABLE conversation_threads (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_conversation_threads_user_id ON conversation_threads(user_id);
CREATE INDEX ix_conversation_threads_course_id ON conversation_threads(course_id);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY,
    thread_id UUID NOT NULL REFERENCES conversation_threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    citations JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_conversation_messages_thread_id ON conversation_messages(thread_id);
```

**Acceptance Criteria:**
- Students can start conversations about enrolled courses
- Answers prioritize course materials with citations
- Conversation history is maintained
- Students can choose explanation level (beginner, detailed, exam-oriented)
- PDFs can be uploaded for context
- Follow-up questions work correctly
- Source vs general AI distinction is clear

**Risks:**
- LLM costs may increase with conversation history
- PDF parsing may fail for complex documents
- Conversation storage may grow large

**Mitigation:**
- Limit conversation history window (last 10 messages)
- Implement conversation archiving
- Cache PDF embeddings
- Monitor LLM costs

---

### 1.2 Exam Preparation Studio

#### Current State
- ❌ No quiz/exam features exist
- ❌ No question generation
- ❌ No assessment tracking

#### Implementation Tasks

**Backend:**
1. Create quiz models
   - `Quiz` - Quiz metadata (course, topic, difficulty, question_count)
   - `QuizQuestion` - Individual questions (type, content, options, answer, explanation)
   - `QuizAttempt` - Student quiz attempts (score, time_taken, status)
   - `QuizAnswer` - Individual question answers (selected_option, is_correct)

2. Create question generation service
   - `QuestionGenerationService` - Generate questions from syllabus topics
   - Use existing LLM client with structured prompts
   - Support multiple question types (MCQ, short-answer, long-answer, numerical)
   - Support difficulty levels (easy, medium, hard)
   - Use syllabus topics and course materials as source
   - Implement question history to avoid duplicates

3. Create quiz service
   - `QuizService` - Manage quizzes and attempts
   - Methods: create_quiz, generate_questions, start_attempt, submit_attempt, get_results
   - Calculate scores and accuracy
   - Track time per question
   - Identify weak topics

4. Create API endpoints
   - `POST /api/v1/quizzes` - Create quiz
   - `GET /api/v1/quizzes` - List quizzes
   - `GET /api/v1/quizzes/{id}` - Get quiz
   - `POST /api/v1/quizzes/{id}/generate` - Generate questions
   - `POST /api/v1/quizzes/{id}/attempts` - Start attempt
   - `POST /api/v1/quizzes/{id}/attempts/{attempt_id}/submit` - Submit attempt
   - `GET /api/v1/quizzes/{id}/attempts` - Get attempts
   - `GET /api/v1/quizzes/{id}/attempts/{attempt_id}` - Get attempt results

**Frontend:**
1. Create quiz UI components
   - `QuizCreator` - Create quiz with parameters
   - `QuestionGenerator` - Generate questions
   - `QuizTaker` - Take quiz with timer
   - `QuestionCard` - Display question
   - `ResultsView` - Show results and explanations
   - `WeakTopicsView` - Show weak topics

2. Create route `/workspace/exam-prep`
3. Add quiz creation to teacher tools
4. Add quiz taking to student workspace

**Database Changes:**
```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    quiz_type VARCHAR(50), -- 'topic_test', 'mock_test', 'practice'
    difficulty VARCHAR(20), -- 'easy', 'medium', 'hard', 'mixed'
    question_count INTEGER NOT NULL,
    time_limit INTEGER, -- seconds
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY,
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_type VARCHAR(50) NOT NULL, -- 'mcq', 'short_answer', 'long_answer', 'numerical'
    content TEXT NOT NULL,
    options JSONB, -- for MCQ
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(20),
    syllabus_topic_id UUID REFERENCES syllabus_topics(id),
    position INTEGER NOT NULL,
    generated_from VARCHAR(100), -- 'syllabus', 'manual', 'ai'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY,
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    score DECIMAL(5,2),
    total_questions INTEGER,
    correct_answers INTEGER,
    time_taken INTEGER, -- seconds
    status VARCHAR(20) -- 'in_progress', 'completed', 'abandoned'
);

CREATE TABLE quiz_answers (
    id UUID PRIMARY KEY,
    attempt_id UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES quiz_questions(id),
    selected_answer TEXT,
    is_correct BOOLEAN,
    time_spent INTEGER, -- seconds
    answered_at TIMESTAMPTZ
);
```

**Acceptance Criteria:**
- Teachers can create quizzes with parameters
- Questions generated from syllabus topics
- Multiple question types supported
- Difficulty levels respected
- Students can take quizzes with timer
- Scores calculated accurately
- Explanations provided after answers
- Weak topics identified
- Question history prevents duplicates

**Risks:**
- LLM may generate low-quality questions
- Question generation may be slow
- Duplicate questions may still occur
- Scoring for subjective questions is difficult

**Mitigation:**
- Use structured prompts with examples
- Implement question validation
- Use semantic similarity to detect duplicates
- Focus on objective question types first
- Allow teacher review of generated questions

---

### 1.3 Previous Year Question Intelligence

#### Current State
- ❌ No PYQ features exist
- ❌ No PDF upload for question papers
- ❌ No question extraction

#### Implementation Tasks

**Backend:**
1. Create PYQ models
   - `PYQDocument` - Uploaded question papers (PDF)
   - `PYQQuestion` - Extracted questions with metadata
   - `PYQTopicMapping` - Map questions to syllabus topics
   - `PYQFrequency` - Track topic frequency across papers

2. Create PYQ parser service
   - `PYQParserService` - Parse question papers
   - Use Docling for PDF parsing
   - Extract questions, marks, sections, question numbers
   - Identify question patterns
   - Map to syllabus topics using existing alignment engine

3. Create PYQ service
   - `PYQService` - Manage PYQ documents and questions
   - Methods: upload_document, parse_document, get_questions, get_frequency
   - Calculate topic frequency
   - Identify repeated questions
   - Generate topic-wise collections

4. Create API endpoints
   - `POST /api/v1/pyq/upload` - Upload PYQ document
   - `GET /api/v1/pyq/documents` - List PYQ documents
   - `GET /api/v1/pyq/documents/{id}` - Get PYQ document
   - `POST /api/v1/pyq/documents/{id}/parse` - Parse PYQ
   - `GET /api/v1/pyq/documents/{id}/questions` - Get extracted questions
   - `GET /api/v1/pyq/topics/{id}/frequency` - Get topic frequency
   - `GET /api/v1/pyq/repeated-questions` - Get repeated questions

**Frontend:**
1. Create PYQ UI components
   - `PYQUploader` - Upload question papers
   - `PYQParser` - Parse and review extraction
   - `QuestionList` - Display extracted questions
   - `FrequencyChart` - Show topic frequency
   - `RepeatedQuestionsView` - Show repeated questions
   - `TopicWiseCollection` - Topic-wise question collections

2. Create route `/workspace/pyq`
3. Add PYQ upload to teacher tools
4. Add PYQ practice to student workspace

**Database Changes:**
```sql
CREATE TABLE pyq_documents (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    year INTEGER,
    exam_type VARCHAR(100), -- 'midsem', 'endsem', 'external'
    parsing_status VARCHAR(50) DEFAULT 'pending',
    parsing_error TEXT,
    parsed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pyq_questions (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES pyq_documents(id) ON DELETE CASCADE,
    question_number VARCHAR(50),
    section VARCHAR(100),
    content TEXT NOT NULL,
    marks INTEGER,
    page_number INTEGER,
    syllabus_topic_id UUID REFERENCES syllabus_topics(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pyq_topic_frequency (
    id UUID PRIMARY KEY,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    syllabus_topic_id UUID REFERENCES syllabus_topics(id),
    question_count INTEGER DEFAULT 0,
    total_marks INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(course_id, syllabus_topic_id)
);
```

**Acceptance Criteria:**
- Teachers can upload PYQ documents
- Questions extracted with metadata
- Questions mapped to syllabus topics
- Topic frequency calculated
- Repeated questions identified
- Original source preserved
- Page numbers preserved
- Students can practice questions

**Risks:**
- PDF parsing may fail for complex layouts
- Question extraction may be inaccurate
- Topic mapping may be incorrect
- Handwritten questions cannot be parsed

**Mitigation:**
- Use Docling with OCR fallback
- Allow manual review and correction
- Use existing alignment engine for mapping
- Focus on typed question papers
- Provide manual editing tools

---

### 1.4 Smart Flashcards and Spaced Repetition

#### Current State
- ❌ No flashcard features exist
- ❌ No spaced repetition system

#### Implementation Tasks

**Backend:**
1. Create flashcard models
   - `Flashcard` - Flashcard with question/answer
   - `FlashcardReview` - Review history with scheduling
   - `FlashcardDeck` - Organize cards into decks

2. Implement spaced repetition algorithm
   - Use FSRS (Free Spaced Repetition Scheduler) or SM-2
   - Calculate next review date based on performance
   - Support difficulty ratings (again, hard, good, easy)
   - Track retention metrics

3. Create flashcard generation service
   - `FlashcardGenerationService` - Generate from content
   - Generate from lecture notes, PDFs, transcripts, syllabus topics
   - Support multiple card types (Q&A, definition, formula, concept, cloze)
   - Use LLM with structured prompts

4. Create flashcard service
   - `FlashcardService` - Manage cards and reviews
   - Methods: create_card, generate_cards, review_card, get_due_cards
   - Calculate retention statistics
   - Recommend cards based on weak topics

5. Create API endpoints
   - `POST /api/v1/flashcards` - Create flashcard
   - `GET /api/v1/flashcards` - List flashcards
   - `GET /api/v1/flashcards/{id}` - Get flashcard
   - `PUT /api/v1/flashcards/{id}` - Update flashcard
   - `DELETE /api/v1/flashcards/{id}` - Delete flashcard
   - `POST /api/v1/flashcards/{id}/review` - Submit review
   - `GET /api/v1/flashcards/due` - Get due cards
   - `POST /api/v1/flashcards/generate` - Generate from content

**Frontend:**
1. Create flashcard UI components
   - `FlashcardViewer` - Display card with flip animation
   - `ReviewButtons` - Difficulty rating buttons
   - `DueCardsList` - List of cards due today
   - `FlashcardCreator` - Manual card creation
   - `FlashcardGenerator` - Generate from content
   - `RetentionChart` - Show retention statistics

2. Create route `/workspace/flashcards`
3. Add flashcard generation to course workspace
4. Add flashcard review to student dashboard

**Database Changes:**
```sql
CREATE TABLE flashcards (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    syllabus_topic_id UUID REFERENCES syllabus_topics(id),
    lecture_id UUID REFERENCES lectures(id) ON DELETE CASCADE,
    card_type VARCHAR(50) NOT NULL, -- 'qa', 'definition', 'formula', 'concept', 'cloze'
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    cloze_answer TEXT, -- for cloze deletion
    source_type VARCHAR(50), -- 'manual', 'generated', 'imported'
    source_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE flashcard_reviews (
    id UUID PRIMARY KEY,
    flashcard_id UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL, -- 1=again, 2=hard, 3=good, 4=easy
    review_time INTEGER, -- seconds
    scheduled_interval INTEGER, -- days until next review
    ease_factor DECIMAL(3,2),
    scheduled_date TIMESTAMPTZ NOT NULL,
    actual_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_flashcard_reviews_flashcard_id ON flashcard_reviews(flashcard_id);
CREATE INDEX ix_flashcard_reviews_scheduled_date ON flashcard_reviews(scheduled_date);
CREATE INDEX ix_flashcard_reviews_user_id ON flashcard_reviews(user_id);
```

**Acceptance Criteria:**
- Students can create manual flashcards
- Flashcards generated from course content
- Multiple card types supported
- Spaced repetition scheduling works correctly
- Due cards displayed accurately
- Retention tracking works
- Difficulty rating affects scheduling
- Export capability (Anki format)

**Risks:**
- Spaced repetition algorithm complexity
- Card generation quality
- Review scheduling accuracy
- Large number of cards may affect performance

**Mitigation:**
- Use proven algorithm (FSRS or SM-2)
- Allow manual review of generated cards
- Test scheduling thoroughly
- Implement pagination for large card sets
- Provide export to Anki for backup

---

### 1.5 Personalised Study Planner

#### Current State
- ❌ No study planner features exist
- ⚠️ Syllabus coverage tracking exists but not integrated

#### Implementation Tasks

**Backend:**
1. Create study planner models
   - `StudyPlan` - Study plans with goals
   - `StudyTask` - Individual study tasks
   - `StudySession` - Completed study sessions

2. Create study planner service
   - `StudyPlannerService` - Manage plans and schedules
   - Methods: create_plan, generate_schedule, log_session, get_progress
   - Prioritize incomplete and weak topics
   - Estimate workload using topic complexity
   - Recommend daily and weekly targets
   - Re-plan when sessions missed

3. Create API endpoints
   - `POST /api/v1/study-plans` - Create study plan
   - `GET /api/v1/study-plans` - List study plans
   - `GET /api/v1/study-plans/{id}` - Get study plan
   - `PUT /api/v1/study-plans/{id}` - Update study plan
   - `POST /api/v1/study-plans/{id}/sessions` - Log study session
   - `GET /api/v1/study-plans/{id}/tasks` - Get tasks
   - `PUT /api/v1/study-plans/{id}/tasks/{task_id}` - Update task

**Frontend:**
1. Create study planner UI components
   - `StudyPlanCreator` - Create plan with goals
   - `ScheduleView` - Display schedule
   - `TaskList` - List of tasks
   - `SessionLogger` - Log study session
   - `ProgressView` - Show progress
   - `RecommendationView` - Show recommendations

2. Create route `/workspace/planner`
3. Add study planner to student dashboard
4. Integrate with syllabus coverage

**Database Changes:**
```sql
CREATE TABLE study_plans (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    goal_type VARCHAR(50), -- 'exam', 'assignment', 'personal'
    target_date DATE,
    daily_study_hours INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE study_tasks (
    id UUID PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
    syllabus_topic_id UUID REFERENCES syllabus_topics(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    estimated_hours DECIMAL(4,2),
    priority INTEGER, -- 1=high, 2=medium, 3=low
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'skipped'
    scheduled_date DATE,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE study_sessions (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES study_tasks(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    duration_minutes INTEGER NOT NULL,
    notes TEXT,
    session_type VARCHAR(50), -- 'reading', 'practice', 'revision', 'quiz'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Acceptance Criteria:**
- Students can create study plans
- Plans generated from exam dates and syllabus
- Incomplete topics prioritized
- Daily/weekly targets recommended
- Study sessions logged
- Progress tracked
- Re-planning on missed sessions
- Syllabus completion progress shown

**Risks:**
- Workload estimation may be inaccurate
- Students may not follow plans
- Re-planning logic complexity
- Calendar integration complexity

**Mitigation:**
- Allow manual adjustment of estimates
- Use realistic default estimates
- Simple re-planning logic initially
- Defer calendar integration to Phase 3

---

### 1.6 Learning Analytics Dashboard

#### Current State
- ⚠️ Syllabus coverage tracking exists
- ⚠️ Basic analytics placeholder exists
- ❌ No student-specific analytics

#### Implementation Tasks

**Backend:**
1. Create analytics models
   - `StudentLearningInsight` - Learning analytics snapshots
   - Aggregate data from quizzes, flashcards, study sessions

2. Create analytics service
   - `AnalyticsService` - Calculate learning metrics
   - Methods: get_progress, get_weak_topics, get_recommendations
   - Track quiz accuracy, topic-wise performance
   - Track flashcard retention
   - Track study sessions and consistency
   - Generate actionable recommendations

3. Create API endpoints
   - `GET /api/v1/analytics/student/progress` - Get progress dashboard
   - `GET /api/v1/analytics/student/weak-topics` - Get weak topics
   - `GET /api/v1/analytics/student/performance` - Get performance metrics
   - `GET /api/v1/analytics/student/recommendations` - Get recommendations

**Frontend:**
1. Create analytics UI components
   - `ProgressDashboard` - Main dashboard
   - `WeakTopicsChart` - Show weak topics
   - `PerformanceMetrics` - Show performance data
   - `RecommendationList` - Show recommendations
   - `StudyConsistencyChart` - Show consistency

2. Create route `/workspace/progress`
3. Add analytics summary to student dashboard

**Database Changes:**
```sql
CREATE TABLE student_learning_insights (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    insight_date DATE NOT NULL,
    quiz_accuracy DECIMAL(5,2),
    flashcard_retention DECIMAL(5,2),
    study_session_count INTEGER,
    total_study_minutes INTEGER,
    syllabus_coverage DECIMAL(5,2),
    weak_topics JSONB,
    recommendations JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, course_id, insight_date)
);
```

**Acceptance Criteria:**
- Quiz accuracy tracked
- Topic-wise performance shown
- Flashcard retention tracked
- Study sessions tracked
- Syllabus coverage shown
- Weak topics identified
- Recommendations generated
- Actionable insights provided

**Risks:**
- Data aggregation complexity
- Recommendation quality
- Performance with large datasets

**Mitigation:**
- Use incremental aggregation
- Simple recommendation logic initially
- Implement pagination and caching
- Use database indexes

---

## Phase 2: Educational Resource Discovery

**Duration:** 6-8 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 1 completion

### Objectives
Integrate with free education APIs to help students discover learning materials:
- Research papers (OpenAlex, Crossref, arXiv)
- Books (Google Books, Project Gutenberg)
- Videos (YouTube Data API)
- Open educational resources

### 2.1 Provider Architecture

#### Implementation Tasks

**Backend:**
1. Create provider architecture
   - `app/integrations/education/` directory
   - `base.py` - Base provider interface
   - `openalex.py` - OpenAlex provider
   - `crossref.py` - Crossref provider
   - `arxiv.py` - arXiv provider
   - `google_books.py` - Google Books provider
   - `youtube.py` - YouTube provider
   - `project_gutenberg.py` - Project Gutenberg provider
   - `registry.py` - Provider registry

2. Create common models
   - `AcademicResource` - Normalized resource model
   - Fields: id, title, description, resource_type, provider, metadata
   - Use JSONB for provider-specific metadata

3. Create integration service
   - `EducationIntegrationService` - Manage provider calls
   - Implement deduplication (DOI, ISBN, arXiv ID)
   - Implement caching layer
   - Implement rate limiting per provider
   - Implement error handling and fallbacks

4. Create API endpoints
   - `GET /api/v1/resources/search` - Search resources
   - `POST /api/v1/resources` - Save resource
   - `GET /api/v1/resources` - List saved resources
   - `DELETE /api/v1/resources/{id}` - Delete saved resource
   - `POST /api/v1/resources/collections` - Create collection
   - `GET /api/v1/resources/collections` - List collections

**Frontend:**
1. Create resource discovery UI
   - `ResourceSearch` - Search interface
   - `ResourceCard` - Display resource
   - `ResourceFilters` - Filter by type, year, etc.
   - `SavedResources` - Saved resources list
   - `ResourceCollections` - Collections management

2. Create route `/workspace/resources`
3. Add resource search to course workspace

**Database Changes:**
```sql
CREATE TABLE academic_resources (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- 'paper', 'book', 'video', 'course'
    provider VARCHAR(50) NOT NULL, -- 'openalex', 'crossref', 'arxiv', etc.
    provider_resource_id VARCHAR(255),
    title TEXT NOT NULL,
    description TEXT,
    authors JSONB,
    publisher TEXT,
    publication_date DATE,
    language VARCHAR(10),
    doi VARCHAR(255),
    isbn VARCHAR(20),
    arxiv_id VARCHAR(50),
    canonical_url TEXT,
    landing_page_url TEXT,
    full_text_url TEXT,
    thumbnail_url TEXT,
    is_open_access BOOLEAN DEFAULT FALSE,
    access_type VARCHAR(50),
    license TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_academic_resources_doi ON academic_resources(doi) WHERE doi IS NOT NULL;
CREATE UNIQUE INDEX ix_academic_resources_isbn ON academic_resources(isbn) WHERE isbn IS NOT NULL;
CREATE UNIQUE INDEX ix_academic_resources_arxiv_id ON academic_resources(arxiv_id) WHERE arxiv_id IS NOT NULL;

CREATE TABLE resource_collections (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE collection_resources (
    collection_id UUID NOT NULL REFERENCES resource_collections(id) ON DELETE CASCADE,
    resource_id UUID NOT NULL REFERENCES academic_resources(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (collection_id, resource_id)
);
```

**Acceptance Criteria:**
- Search works across multiple providers
- Results normalized and deduplicated
- Rate limits respected
- Caching works correctly
- Resources can be saved
- Collections can be created
- Source links preserved
- Open-access status shown
- No fake download buttons

**Risks:**
- External API rate limits
- API key requirements
- Data quality varies by provider
- Deduplication complexity

**Mitigation:**
- Implement aggressive caching
- Respect rate limits strictly
- Use multiple providers for redundancy
- Simple deduplication initially (DOI, ISBN, arXiv ID)
- Handle provider failures gracefully

---

## Phase 3: Advanced Student Learning

**Duration:** 8-10 weeks  
**Priority:** MEDIUM  
**Dependencies:** Phase 1 and Phase 2 completion

### Objectives
Build advanced learning features:
- AI Viva Practice
- Advanced learning analytics
- Research assistant
- Multilingual learning
- Collaborative study groups

### 3.1 AI Viva Practice

#### Implementation Tasks

**Backend:**
1. Create viva models
   - `VivaSession` - Viva practice sessions
   - `VivaQuestion` - Questions asked
   - `VivaAnswer` - Student answers
   - `VivaFeedback` - Feedback and evaluation

2. Create viva service
   - `VivaService` - Manage viva sessions
   - Generate viva questions from topics
   - Evaluate answers
   - Provide feedback
   - Track performance

3. Create API endpoints
   - `POST /api/v1/viva/start` - Start viva session
   - `POST /api/v1/viva/{id}/answer` - Submit answer
   - `GET /api/v1/viva/{id}/feedback` - Get feedback
   - `GET /api/v1/{id}/summary` - Get session summary

**Frontend:**
1. Create viva UI components
   - `VivaSession` - Session interface
   - `QuestionDisplay` - Show question
   - `AnswerInput` - Input answer
   - `FeedbackView` - Show feedback
   - `SessionSummary` - Show summary

2. Create route `/workspace/viva`

**Acceptance Criteria:**
- Viva questions generated from topics
- Sequential questioning works
- Answers evaluated
- Feedback provided
- Performance tracked
- Difficulty modes supported

---

### 3.2 Research Assistant

#### Implementation Tasks

**Backend:**
1. Create research models
   - `ReadingList` - Saved papers
   - `PaperNote` - Notes on papers

2. Create research service
   - `ResearchService` - Manage research features
   - Use OpenAlex, Crossref, arXiv APIs
   - Search papers
   - Get paper details
   - Manage reading lists
   - Export citations

3. Create API endpoints
   - `GET /api/v1/research/papers` - Search papers
   - `GET /api/v1/research/papers/{id}` - Get paper details
   - `POST /api/v1/research/reading-list` - Add to reading list
   - `GET /api/v1/research/reading-list` - Get reading list

**Frontend:**
1. Create research UI components
   - `PaperSearch` - Search interface
   - `PaperDetails` - Show paper details
   - `ReadingList` - Manage reading list
   - `CitationExport` - Export citations

2. Create route `/workspace/research`

**Acceptance Criteria:**
- Paper search works
- Paper details displayed
- Reading list managed
- Citations exported
- Source links preserved

---

### 3.3 Collaborative Study Groups

#### Implementation Tasks

**Backend:**
1. Create collaboration models
   - `StudyGroup` - Study groups
   - `StudyGroupMembership` - Group membership
   - `SharedResource` - Shared resources

2. Create collaboration service
   - `CollaborationService` - Manage groups
   - Permission-based access
   - Shared resources

3. Create API endpoints
   - `POST /api/v1/study-groups` - Create group
   - `GET /api/v1/study-groups` - List groups
   - `POST /api/v1/study-groups/{id}/members` - Add member
   - `POST /api/v1/study-groups/{id}/resources` - Share resource

**Frontend:**
1. Create collaboration UI components
   - `GroupList` - List groups
   - `GroupView` - Group interface
   - `MemberManagement` - Manage members
   - `ResourceSharing` - Share resources

2. Create route `/workspace/groups`

**Acceptance Criteria:**
- Groups can be created
- Members can be added
- Resources can be shared
- Permissions enforced
- Private data not exposed

---

## Phase 4: Infrastructure Improvements

**Duration:** Ongoing  
**Priority:** MEDIUM  
**Dependencies:** All phases

### Objectives
Improve infrastructure for production readiness:
- Persistent queue system
- Cloud storage
- Redis caching
- Monitoring and logging
- CI/CD pipeline

### 4.1 Persistent Queue System

#### Implementation Tasks
- Implement Celery with Redis
- Migrate background tasks from FastAPI BackgroundTasks
- Add task monitoring
- Add retry logic
- Add task scheduling

### 4.2 Cloud Storage

#### Implementation Tasks
- Implement S3 or GCS integration
- Migrate file uploads from local storage
- Add CDN for static assets
- Implement file cleanup

### 4.3 Redis Caching

#### Implementation Tasks
- Implement Redis for session caching
- Implement Redis for API response caching
- Implement Redis for rate limiting
- Add cache invalidation

### 4.4 Monitoring and Logging

#### Implementation Tasks
- Implement structured logging
- Add performance monitoring
- Add error tracking (Sentry)
- Add metrics (Prometheus)

### 4.5 CI/CD Pipeline

#### Implementation Tasks
- Set up GitHub Actions
- Add automated tests
- Add deployment automation
- Add database migration automation

---

## Database Migration Strategy

### Migration Order
1. Phase 1 models (conversations, quizzes, flashcards, study planner, analytics)
2. Phase 2 models (academic resources, collections)
3. Phase 3 models (viva, research, collaboration)

### Migration Best Practices
- Use Alembic for all migrations
- Test migrations on staging database
- Provide downgrade paths
- Add indexes after data migration
- Use transactions for complex migrations

### Migration Commands
```bash
# Generate migration
alembic revision --autogenerate -m "Add conversation models"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# Generate SQL for review
alembic upgrade head --sql
```

---

## Testing Strategy

### Unit Tests
- Test all service methods
- Test repository methods
- Test provider adapters
- Test utility functions

### Integration Tests
- Test API endpoints
- Test database operations
- Test external API integrations (mocked)
- Test authentication/authorization

### End-to-End Tests
- Test user flows
- Test error scenarios
- Test rate limiting
- Test caching

### Test Coverage Target
- 80%+ code coverage for new features
- 100% coverage for critical paths (authentication, authorization)

---

## Deployment Strategy

### Staging Environment
- Deploy to staging first
- Run full test suite
- Manual testing
- Performance testing

### Production Deployment
- Blue-green deployment
- Database migration before code deployment
- Monitor for errors
- Rollback plan ready

### Rollback Plan
- Database rollback scripts
- Code rollback to previous version
- Data backup before migration

---

## Risk Management

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| External API rate limits | High | Medium | Aggressive caching, rate limiting |
| LLM cost overruns | Medium | High | Usage limits, monitoring |
| Database performance issues | Medium | High | Indexes, caching, pagination |
| Background job failures | Medium | Medium | Celery, retry logic, monitoring |

### Product Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low student adoption | Medium | High | User feedback, iterative improvement |
| Feature creep | High | Medium | Strict scope management |
| Poor UX | Medium | High | User testing, design review |
| Data privacy concerns | Low | High | Privacy by design, compliance review |

---

## Acceptance Criteria Summary

### Phase 1 Acceptance
- All core student features implemented
- All database migrations applied
- All API endpoints tested
- Frontend pages functional
- Existing features not broken
- Tests passing

### Phase 2 Acceptance
- All provider integrations working
- Rate limits respected
- Caching functional
- Deduplication working
- External API failures handled gracefully

### Phase 3 Acceptance
- Advanced features implemented
- Collaboration features functional
- Research assistant working
- Multilingual support where applicable

### Phase 4 Acceptance
- Infrastructure production-ready
- Monitoring functional
- CI/CD pipeline working
- Deployment automated

---

## Success Metrics

### Technical Metrics
- Test coverage > 80%
- API response time < 500ms (p95)
- Database query time < 100ms (p95)
- Uptime > 99.5%

### Product Metrics
- Student adoption rate
- Feature usage statistics
- User satisfaction scores
- Retention rates

---

## Timeline Summary

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 0 | 1 week | Week 1 | Week 1 |
| Phase 1 | 8-12 weeks | Week 2 | Week 13 |
| Phase 2 | 6-8 weeks | Week 14 | Week 21 |
| Phase 3 | 8-10 weeks | Week 22 | Week 31 |
| Phase 4 | Ongoing | Week 2 | Ongoing |

**Total:** 22-30 weeks for full implementation

---

## Next Steps

1. Review and approve this implementation plan
2. Create architecture document
3. Set up development environment for Phase 1
4. Begin Phase 1 implementation with AI Study Companion
5. Weekly progress reviews
6. Adjust timeline based on progress

---

**Implementation Plan Complete.** Ready for architecture design and Phase 1 implementation.
