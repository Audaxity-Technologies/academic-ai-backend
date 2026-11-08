# Student Intelligence Suite - Architecture Document

**Generated:** November 8, 2026  
**Based on:** Repository Audit, Education API Research, and Implementation Plan

---

## Executive Summary

This document describes the architecture for the Student Intelligence Suite, extending the existing Minutes platform with student-centric features. The architecture builds on the existing FastAPI + PostgreSQL + React Router foundation, adding new models, services, API endpoints, and frontend components while maintaining backward compatibility.

**Key Architectural Principles:**
- Extend, don't replace existing infrastructure
- Reuse existing RAG, LLM, and syllabus systems
- Provider-based architecture for external APIs
- Service layer for business logic
- Repository layer for data access
- Proper authentication and authorization
- Graceful degradation for external dependencies

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React Router)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Student UI  │  │  Teacher UI  │  │  Admin UI    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer (v1)                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │  Auth    │  │ Courses  │  │ Lectures │  ...          │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         Student Intelligence Endpoints           │    │  │
│  │  │  Conversations, Quizzes, Flashcards, Planner...  │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │  LLM     │  │  RAG     │  │ Syllabus │  ...          │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         Student Intelligence Services            │    │  │
│  │  │  QuizService, FlashcardService, PlannerService...  │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Integration Layer                          │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │         Education Provider Adapters               │    │  │
│  │  │  OpenAlex, Crossref, arXiv, Google Books, YouTube │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                Repository Layer                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │  User    │  │  Course  │  │  Quiz    │  ...          │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Database (PostgreSQL)                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │  Users   │  │ Courses  │  │  Quizzes │  ...          │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ OpenAlex │  │ Crossref │  │  arXiv   │  │  Gemini  │ ... │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### New Models

#### 1. Conversation Models

```python
# app/models/conversation.py

class ConversationThread(Base):
    __tablename__ = "conversation_threads"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", backref="conversation_threads")
    course = relationship("Course", backref="conversation_threads")
    messages = relationship("ConversationMessage", back_populates="thread", cascade="all, delete-orphan")

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversation_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    thread = relationship("ConversationThread", back_populates="messages")
```

#### 2. Quiz Models

```python
# app/models/quiz.py

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    quiz_type: Mapped[str | None] = mapped_column(String(50))  # 'topic_test', 'mock_test', 'practice'
    difficulty: Mapped[str | None] = mapped_column(String(20))  # 'easy', 'medium', 'hard', 'mixed'
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    time_limit: Mapped[int | None] = mapped_column(Integer)  # seconds
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    course = relationship("Course", backref="quizzes")
    creator = relationship("User", backref="created_quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'mcq', 'short_answer', 'long_answer', 'numerical'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # for MCQ
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str | None] = mapped_column(String(20))
    syllabus_topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("syllabus_topics.id"), index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_from: Mapped[str | None] = mapped_column(String(100))  # 'syllabus', 'manual', 'ai'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    quiz = relationship("Quiz", back_populates="questions")
    syllabus_topic = relationship("SyllabusTopic")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[Decimal | None] = mapped_column(Decimal(5, 2))
    total_questions: Mapped[int] = mapped_column(Integer)
    correct_answers: Mapped[int] = mapped_column(Integer)
    time_taken: Mapped[int | None] = mapped_column(Integer)  # seconds
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'in_progress', 'completed', 'abandoned'
    
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", backref="quiz_attempts")
    answers = relationship("QuizAnswer", back_populates="attempt", cascade="all, delete-orphan")

class QuizAnswer(Base):
    __tablename__ = "quiz_answers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    time_spent: Mapped[int | None] = mapped_column(Integer)  # seconds
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("QuizQuestion")
```

#### 3. Flashcard Models

```python
# app/models/flashcard.py

class Flashcard(Base):
    __tablename__ = "flashcards"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    syllabus_topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("syllabus_topics.id"), index=True)
    lecture_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), index=True)
    card_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'qa', 'definition', 'formula', 'concept', 'cloze'
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    cloze_answer: Mapped[str | None] = mapped_column(Text)  # for cloze deletion
    source_type: Mapped[str | None] = mapped_column(String(50))  # 'manual', 'generated', 'imported'
    source_reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", backref="flashcards")
    course = relationship("Course", backref="flashcards")
    syllabus_topic = relationship("SyllabusTopic", backref="flashcards")
    lecture = relationship("Lecture", backref="flashcards")
    reviews = relationship("FlashcardReview", back_populates="flashcard", cascade="all, delete-orphan")

class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flashcard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=again, 2=hard, 3=good, 4=easy
    review_time: Mapped[int | None] = mapped_column(Integer)  # seconds
    scheduled_interval: Mapped[int | None] = mapped_column(Integer)  # days until next review
    ease_factor: Mapped[Decimal | None] = mapped_column(Decimal(3, 2))
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    flashcard = relationship("Flashcard", back_populates="reviews")
    user = relationship("User", backref="flashcard_reviews")
```

#### 4. Study Planner Models

```python
# app/models/study_planner.py

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_type: Mapped[str | None] = mapped_column(String(50))  # 'exam', 'assignment', 'personal'
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    daily_study_hours: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", backref="study_plans")
    course = relationship("Course", backref="study_plans")
    tasks = relationship("StudyTask", back_populates="plan", cascade="all, delete-orphan")

class StudyTask(Base):
    __tablename__ = "study_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    syllabus_topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("syllabus_topics.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    estimated_hours: Mapped[Decimal | None] = mapped_column(Decimal(4, 2))
    priority: Mapped[int | None] = mapped_column(Integer)  # 1=high, 2=medium, 3=low
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # 'pending', 'in_progress', 'completed', 'skipped'
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    plan = relationship("StudyPlan", back_populates="tasks")
    syllabus_topic = relationship("SyllabusTopic", backref="study_tasks")

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("study_tasks.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    session_type: Mapped[str | None] = mapped_column(String(50))  # 'reading', 'practice', 'revision', 'quiz'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    task = relationship("StudyTask")
    user = relationship("User", backref="study_sessions")
    course = relationship("Course", backref="study_sessions")
```

#### 5. Academic Resource Models

```python
# app/models/academic_resource.py

class AcademicResource(Base):
    __tablename__ = "academic_resources"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'paper', 'book', 'video', 'course'
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'openalex', 'crossref', 'arxiv', etc.
    provider_resource_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    publisher: Mapped[str | None] = mapped_column(String(255))
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str | None] = mapped_column(String(10))
    doi: Mapped[str | None] = mapped_column(String(255), unique=True)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    landing_page_url: Mapped[str | None] = mapped_column(Text)
    full_text_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    is_open_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_type: Mapped[str | None] = mapped_column(String(50))
    license: Mapped[str | None] = mapped_column(String(100))
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", backref="saved_resources")
    course = relationship("Course", backref="academic_resources")

class ResourceCollection(Base):
    __tablename__ = "resource_collections"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user = relationship("User", backref="resource_collections")
    resources = relationship("AcademicResource", secondary="collection_resources", backref="collections")

class CollectionResource(Base):
    __tablename__ = "collection_resources"
    
    collection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resource_collections.id", ondelete="CASCADE"), primary_key=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_resources.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

---

## API Design

### API Endpoint Organization

```
/api/v1/
├── auth/                    # Existing
├── courses/                 # Existing
├── lectures/                # Existing
├── notes/                   # Existing
├── syllabus/                # Existing
├── search/                  # Existing (RAG)
├── conversations/           # NEW: AI Study Companion
│   ├── POST /               # Start conversation
│   ├── GET /                # List conversations
│   ├── GET /{id}            # Get conversation
│   ├── POST /{id}/messages  # Send message
│   └── GET /{id}/messages  # Get messages
├── quizzes/                  # NEW: Exam Preparation
│   ├── POST /               # Create quiz
│   ├── GET /                # List quizzes
│   ├── GET /{id}            # Get quiz
│   ├── POST /{id}/generate  # Generate questions
│   ├── POST /{id}/attempts  # Start attempt
│   ├── POST /{id}/attempts/{attempt_id}/submit
│   ├── GET /{id}/attempts
│   └── GET /{id}/attempts/{attempt_id}
├── flashcards/               # NEW: Flashcards
│   ├── POST /               # Create flashcard
│   ├── GET /                # List flashcards
│   ├── GET /{id}            # Get flashcard
│   ├── PUT /{id}            # Update flashcard
│   ├── DELETE /{id}         # Delete flashcard
│   ├── POST /{id}/review    # Submit review
│   ├── GET /due             # Get due cards
│   └── POST /generate       # Generate from content
├── study-plans/             # NEW: Study Planner
│   ├── POST /               # Create study plan
│   ├── GET /                # List study plans
│   ├── GET /{id}            # Get study plan
│   ├── PUT /{id}            # Update study plan
│   ├── POST /{id}/sessions  # Log study session
│   ├── GET /{id}/tasks      # Get tasks
│   └── PUT /{id}/tasks/{task_id}
├── pyq/                     # NEW: Previous Year Questions
│   ├── POST /upload         # Upload PYQ document
│   ├── GET /documents       # List PYQ documents
│   ├── GET /documents/{id}  # Get PYQ document
│   ├── POST /documents/{id}/parse
│   ├── GET /documents/{id}/questions
│   ├── GET /topics/{id}/frequency
│   └── GET /repeated-questions
├── resources/               # NEW: Resource Discovery
│   ├── GET /search          # Search resources
│   ├── POST /               # Save resource
│   ├── GET /                # List saved resources
│   ├── DELETE /{id}         # Delete saved resource
│   ├── POST /collections    # Create collection
│   └── GET /collections    # List collections
├── viva/                    # NEW: Viva Practice
│   ├── POST /start          # Start viva session
│   ├── POST /{id}/answer    # Submit answer
│   ├── GET /{id}/feedback   # Get feedback
│   └── GET /{id}/summary    # Get session summary
├── research/                # NEW: Research Assistant
│   ├── GET /papers          # Search papers
│   ├── GET /papers/{id}     # Get paper details
│   ├── POST /reading-list   # Add to reading list
│   └── GET /reading-list    # Get reading list
└── analytics/               # Enhanced: Learning Analytics
    ├── GET /student/progress
    ├── GET /student/weak-topics
    ├── GET /student/performance
    └── GET /student/recommendations
```

---

## Provider Architecture

### Base Provider Interface

```python
# app/integrations/education/base.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AcademicResource(BaseModel):
    """Normalized resource model"""
    id: str
    title: str
    description: Optional[str] = None
    resource_type: str
    provider: str
    provider_resource_id: Optional[str] = None
    authors: Optional[List[Dict[str, Any]]] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    language: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    arxiv_id: Optional[str] = None
    canonical_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    full_text_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_open_access: bool = False
    access_type: Optional[str] = None
    license: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseProvider(ABC):
    """Base class for education API providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 10
    ) -> List[AcademicResource]:
        """Search for resources"""
        pass
    
    @abstractmethod
    def get_details(self, provider_id: str) -> Optional[AcademicResource]:
        """Get details by provider-specific ID"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is accessible"""
        pass
```

### OpenAlex Provider Example

```python
# app/integrations/education/openalex.py

import httpx
from typing import Optional, List, Dict, Any
from .base import BaseProvider, AcademicResource

class OpenAlexProvider(BaseProvider):
    """OpenAlex API provider"""
    
    BASE_URL = "https://api.openalex.org"
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 10
    ) -> List[AcademicResource]:
        params = {
            "search": query,
            "per_page": min(limit, 100),
            "page": page
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        if filters:
            for key, value in filters.items():
                params[f"filter.{key}"] = value
        
        response = httpx.get(
            f"{self.BASE_URL}/works",
            params=params,
            timeout=30.0
        )
        response.raise_for_status()
        
        data = response.json()
        resources = []
        
        for item in data.get("results", []):
            resource = AcademicResource(
                id=item.get("id", ""),
                title=item.get("title", ""),
                resource_type="paper",
                provider="openalex",
                provider_resource_id=item.get("id", ""),
                authors=[{
                    "id": a.get("author", {}).get("id"),
                    "name": a.get("author", {}).get("display_name")
                } for a in item.get("authorships", [])],
                publication_date=item.get("publication_year"),
                doi=item.get("doi"),
                canonical_url=item.get("id"),
                landing_page_url=item.get("id"),
                full_text_url=item.get("open_access", {}).get("oa_url"),
                is_open_access=item.get("open_access", {}).get("is_oa", False),
                metadata=item
            )
            resources.append(resource)
        
        return resources
    
    def get_details(self, provider_id: str) -> Optional[AcademicResource]:
        response = httpx.get(
            f"{self.BASE_URL}/works/{provider_id}",
            timeout=30.0
        )
        response.raise_for_status()
        
        item = response.json()
        # Convert to AcademicResource (similar to search)
        return AcademicResource(...)
    
    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.BASE_URL}/works?per_page=1", timeout=10.0)
            return response.status_code == 200
        except Exception:
            return False
```

### Provider Registry

```python
# app/integrations/education/registry.py

from typing import Dict, Optional
from .base import BaseProvider
from .openalex import OpenAlexProvider
from .crossref import CrossrefProvider
from .arxiv import ArxivProvider

class ProviderRegistry:
    """Registry for education API providers"""
    
    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}
    
    def register(self, name: str, provider: BaseProvider):
        self._providers[name] = provider
    
    def get(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(name)
    
    def list_all(self) -> list[str]:
        return list(self._providers.keys())

# Global registry instance
registry = ProviderRegistry()

# Initialize providers with API keys from environment
import os

if os.getenv("OPENALEX_API_KEY"):
    registry.register("openalex", OpenAlexProvider(api_key=os.getenv("OPENALEX_API_KEY")))
else:
    registry.register("openalex", OpenAlexProvider())

if os.getenv("CROSSREF_MAILTO"):
    registry.register("crossref", CrossrefProvider(mailto=os.getenv("CROSSREF_MAILTO")))

# ... initialize other providers
```

---

## Service Layer Architecture

### Service Layer Pattern

```python
# app/services/quiz_service.py

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.repositories.quiz_repository import QuizRepository
from app.ai.llm.question_generator import QuestionGenerator

class QuizService:
    """Service for quiz management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = QuizRepository(db)
        self.question_generator = QuestionGenerator()
    
    def create_quiz(
        self,
        course_id: str,
        title: str,
        quiz_type: str,
        difficulty: str,
        question_count: int,
        user_id: str
    ) -> Quiz:
        """Create a new quiz"""
        quiz = Quiz(
            course_id=course_id,
            title=title,
            quiz_type=quiz_type,
            difficulty=difficulty,
            question_count=question_count,
            created_by=user_id
        )
        return self.repository.create(quiz)
    
    def generate_questions(
        self,
        quiz_id: str,
        syllabus_topic_ids: List[str],
        question_types: List[str]
    ) -> List[QuizQuestion]:
        """Generate questions from syllabus topics"""
        quiz = self.repository.get_by_id(quiz_id)
        
        questions = []
        for topic_id in syllabus_topic_ids:
            for q_type in question_types:
                generated = self.question_generator.generate(
                    syllabus_topic_id=topic_id,
                    question_type=q_type,
                    difficulty=quiz.difficulty
                )
                if generated:
                    question = QuizQuestion(
                        quiz_id=quiz_id,
                        question_type=q_type,
                        content=generated["content"],
                        options=generated.get("options"),
                        correct_answer=generated["answer"],
                        explanation=generated.get("explanation"),
                        difficulty=quiz.difficulty,
                        syllabus_topic_id=topic_id,
                        generated_from="ai"
                    )
                    questions.append(question)
        
        return self.repository.bulk_create_questions(questions)
    
    def start_attempt(self, quiz_id: str, user_id: str) -> QuizAttempt:
        """Start a quiz attempt"""
        quiz = self.repository.get_by_id(quiz_id)
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            total_questions=len(quiz.questions),
            status="in_progress"
        )
        return self.repository.create_attempt(attempt)
    
    def submit_attempt(
        self,
        attempt_id: str,
        answers: List[Dict[str, Any]]
    ) -> QuizAttempt:
        """Submit quiz attempt and calculate score"""
        attempt = self.repository.get_attempt_by_id(attempt_id)
        
        correct_count = 0
        for answer_data in answers:
            question = self.repository.get_question_by_id(answer_data["question_id"])
            is_correct = question.correct_answer == answer_data["selected_answer"]
            
            if is_correct:
                correct_count += 1
            
            answer = QuizAnswer(
                attempt_id=attempt_id,
                question_id=answer_data["question_id"],
                selected_answer=answer_data["selected_answer"],
                is_correct=is_correct,
                time_spent=answer_data.get("time_spent")
            )
            self.repository.create_answer(answer)
        
        attempt.correct_answers = correct_count
        attempt.score = (correct_count / attempt.total_questions) * 100
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)
        
        return self.repository.update_attempt(attempt)
```

---

## Frontend Architecture

### Component Structure

```
app/
├── components/
│   ├── workspace/
│   │   ├── companion/           # AI Study Companion
│   │   │   ├── ConversationList.tsx
│   │   │   ├── ConversationView.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ExplanationLevelSelector.tsx
│   │   ├── exam-prep/            # Exam Preparation
│   │   │   ├── QuizCreator.tsx
│   │   │   ├── QuestionGenerator.tsx
│   │   │   ├── QuizTaker.tsx
│   │   │   └── ResultsView.tsx
│   │   ├── flashcards/           # Flashcards
│   │   │   ├── FlashcardViewer.tsx
│   │   │   ├── ReviewButtons.tsx
│   │   │   └── DueCardsList.tsx
│   │   ├── planner/              # Study Planner
│   │   │   ├── StudyPlanCreator.tsx
│   │   │   ├── ScheduleView.tsx
│   │   │   └── TaskList.tsx
│   │   ├── pyq/                  # Previous Year Questions
│   │   │   ├── PYQUploader.tsx
│   │   │   ├── QuestionList.tsx
│   │   │   └── FrequencyChart.tsx
│   │   ├── resources/            # Resource Discovery
│   │   │   ├── ResourceSearch.tsx
│   │   │   ├── ResourceCard.tsx
│   │   │   └── ResourceFilters.tsx
│   │   ├── progress/             # Learning Analytics
│   │   │   ├── ProgressDashboard.tsx
│   │   │   ├── WeakTopicsChart.tsx
│   │   │   └── RecommendationList.tsx
│   │   └── viva/                 # Viva Practice
│   │       ├── VivaSession.tsx
│   │       ├── QuestionDisplay.tsx
│   │       └── FeedbackView.tsx
│   └── ui/                       # Reusable UI components
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Input.tsx
│       └── Modal.tsx
├── lib/
│   ├── api/
│   │   ├── academic.ts           # Existing
│   │   ├── companion.ts          # NEW: AI Study Companion
│   │   ├── quiz.ts               # NEW: Exam Preparation
│   │   ├── flashcard.ts          # NEW: Flashcards
│   │   ├── planner.ts            # NEW: Study Planner
│   │   ├── pyq.ts                # NEW: PYQ
│   │   ├── resources.ts          # NEW: Resource Discovery
│   │   └── analytics.ts          # NEW: Analytics
│   └── hooks/
│       ├── useAuth.ts            # Existing
│       ├── useResource.ts        # Existing
│       ├── useQuiz.ts            # NEW
│       └── useFlashcard.ts       # NEW
└── routes/
    ├── companion.tsx             # NEW: /workspace/companion
    ├── exam-prep.tsx            # NEW: /workspace/exam-prep
    ├── flashcards.tsx            # NEW: /workspace/flashcards
    ├── planner.tsx              # NEW: /workspace/planner
    ├── pyq.tsx                  # NEW: /workspace/pyq
    ├── resources.tsx            # NEW: /workspace/resources
    ├── progress.tsx             # NEW: /workspace/progress
    └── viva.tsx                 # NEW: /workspace/viva
```

### API Client Pattern

```typescript
// app/lib/api/companion.ts

import { apiClient } from "./client"

export interface Conversation {
  id: string
  user_id: string
  course_id: string | null
  title: string | null
  created_at: string
  updated_at: string
}

export interface ConversationMessage {
  id: string
  thread_id: string
  role: "user" | "assistant"
  content: string
  citations: any[] | null
  created_at: string
}

export const companionAPI = {
  conversations: () => apiClient.get<Conversation[]>("/api/v1/conversations"),
  
  createConversation: (data: { course_id?: string; title?: string }) =>
    apiClient.post<Conversation>("/api/v1/conversations", data),
  
  getConversation: (id: string) =>
    apiClient.get<Conversation>(`/api/v1/conversations/${id}`),
  
  getMessages: (id: string) =>
    apiClient.get<ConversationMessage[]>(`/api/v1/conversations/${id}/messages`),
  
  sendMessage: (data: { thread_id: string; content: string }) =>
    apiClient.post<ConversationMessage>("/api/v1/conversations/messages", data),
}
```

---

## Caching Strategy

### Cache Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                      │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Cache Layer (Redis)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  API Cache    │  │  Query Cache │  │  Session Cache│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Database Layer                         │
└─────────────────────────────────────────────────────────┘
```

### Cache Keys and TTL

| Cache Type | Key Pattern | TTL | Notes |
|-------------|-------------|-----|-------|
| API Response | `api:{endpoint}:{params_hash}` | 5-60 min | Depends on endpoint |
| Query Result | `query:{model}:{query_hash}` | 10-30 min | For complex queries |
| External API | `external:{provider}:{query_hash}` | 1-24 hours | Provider-specific |
| Session | `session:{user_id}` | 1 hour | User session data |
| Rate Limit | `ratelimit:{user_id}:{endpoint}` | 1 second | Per-user rate limiting |

---

## Rate Limiting Strategy

### Rate Limit Implementation

```python
# app/core/rate_limit.py

from functools import wraps
from fastapi import HTTPException, Request
from redis import Redis
import time

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """Check if request is allowed"""
        current = time.time()
        window_start = current - window
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current entries
        count = self.redis.zcard(key)
        
        if count < limit:
            self.redis.zadd(key, {str(current): current})
            self.redis.expire(key, window)
            return True
        
        return False

def rate_limit(limit: int, window: int = 60):
    """Rate limit decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_id = request.state.user.id if hasattr(request.state, 'user') else "anonymous"
            key = f"ratelimit:{user_id}:{func.__name__}"
            
            if not rate_limiter.is_allowed(key, limit, window):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Error Handling Strategy

### Error Handling Pattern

```python
# app/core/exceptions.py

from fastapi import HTTPException, status

class MinutesException(Exception):
    """Base exception for Minutes"""
    pass

class ResourceNotFoundException(MinutesException):
    """Resource not found"""
    pass

class PermissionDeniedException(MinutesException):
    """Permission denied"""
    pass

class ExternalServiceException(MinutesException):
    """External service error"""
    pass

class RateLimitExceededException(MinutesException):
    """Rate limit exceeded"""
    pass

# Exception handler
@app.exception_handler(MinutesException)
async def minutes_exception_handler(request: Request, exc: MinutesException):
    if isinstance(exc, ResourceNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)}
        )
    elif isinstance(exc, AccessDeniedException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)}
        )
    # ... other exceptions
```

---

## Security Architecture

### Authentication Flow

```
┌──────────┐
│  Client  │
└─────┬────┘
      │
      │ 1. Login (email, password)
      ▼
┌──────────┐
│   API    │
└─────┬────┘
      │
      │ 2. Validate credentials
      ▼
┌──────────┐
│  Database│
└─────┬────┘
      │
      │ 3. Return JWT token
      ▼
┌──────────┐
│  Client  │ (stores token)
└─────┬────┘
      │
      │ 4. Request with Bearer token
      ▼
┌──────────┐
│   API    │
└─────┬────┘
      │
      │ 5. Validate JWT
      ▼
┌──────────┐
│ Protected│
│  Endpoint│
└──────────┘
```

### Authorization Pattern

```python
# app/services/course_service.py

def get_course(course_id: str, user: User) -> Course:
    """Get course with ownership validation"""
    course = repository.get_by_id(course_id)
    
    if not course:
        raise ResourceNotFoundException("Course not found")
    
    if course.teacher_id != user.id:
        raise PermissionDeniedException("You don't have access to this course")
    
    return course

def get_course_for_user(course_id: str, user: User) -> Course:
    """Get course for enrolled student or teacher"""
    course = repository.get_by_id(course_id)
    
    if not course:
        raise ResourceNotFoundException("Course not found")
    
    # Check if user is teacher or enrolled student
    if course.teacher_id != user.id and user not in course.students:
        raise PermissionDeniedException("You don't have access to this course")
    
    return course
```

---

## Monitoring and Logging

### Logging Strategy

```python
# app/core/logging.py

import logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in services
logger.info("quiz_created", quiz_id=quiz.id, user_id=user.id)
logger.error("external_api_failed", provider="openalex", error=str(e))
```

### Metrics

```python
# app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# API metrics
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint'])

# Business metrics
quizzes_created = Counter('quizzes_created_total', 'Total quizzes created')
quiz_attempts = Counter('quiz_attempts_total', 'Total quiz attempts')
flashcard_reviews = Counter('flashcard_reviews_total', 'Total flashcard reviews')

# External API metrics
external_api_requests = Counter('external_api_requests_total', 'External API requests', ['provider', 'status'])
external_api_duration = Histogram('external_api_duration_seconds', 'External API duration', ['provider'])
```

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────┐
│                    Developer Machine                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Frontend    │  │   Backend    │  │  PostgreSQL  │  │
│  │  (Vite dev)  │  │  (Uvicorn)   │  │  (local)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                          │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Backend 1   │ │  Backend 2   │ │  Backend N   │
│  (FastAPI)   │ │  (FastAPI)   │ │  (FastAPI)   │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL (Primary)                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL (Replicas)                  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    Redis (Cache/Queue)                    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    S3/GCS (File Storage)                  │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Quiz Generation Flow

```
┌──────────┐
│  Teacher │
└─────┬────┘
      │ 1. Create quiz with parameters
      ▼
┌──────────┐
│   API    │
└─────┬────┘
      │ 2. Get syllabus topics
      ▼
┌──────────┐
│  Service │
└─────┬────┘
      │ 3. Call LLM for each topic
      ▼
┌──────────┐
│   LLM    │ (Gemini/Groq/Ollama)
└─────┬────┘
      │ 4. Return generated questions
      ▼
┌──────────┐
│  Service │
└─────┬────┘
      │ 5. Save to database
      ▼
┌──────────┐
│ Database │
└──────────┘
```

### Resource Search Flow

```
┌──────────┐
│  Student │
└─────┬────┘
      │ 1. Search query
      ▼
┌──────────┐
│   API    │
└─────┬────┘
      │ 2. Check cache
      ▼
┌──────────┐
│  Redis   │ (cache hit?)
└─────┬────┘
      │ No
      ▼
┌──────────┐
│  Service │
└─────┬────┘
      │ 3. Call multiple providers
      ▼
┌──────────┐
│ Providers│ (OpenAlex, Crossref, etc.)
└─────┬────┘
      │ 4. Return results
      ▼
┌──────────┐
│  Service │
└─────┬────┘
      │ 5. Normalize and deduplicate
      ▼
┌──────────┐
│  Service │
└─────┬────┘
      │ 6. Cache results
      ▼
┌──────────┐
│  Redis   │
└─────┬────┘
      │ 7. Return to API
      ▼
┌──────────┐
│   API    │
└─────┬────┘
      │ 8. Return to student
      ▼
┌──────────┐
│  Student │
└──────────┘
```

---

## Technology Stack Summary

### Backend
- **Framework:** FastAPI 0.141.1
- **Language:** Python 3.12+
- **Database:** PostgreSQL with pgvector
- **ORM:** SQLAlchemy 2.1.4
- **Migrations:** Alembic
- **Authentication:** JWT (HS256)
- **LLM:** Gemini, Groq, Ollama (multi-provider)
- **Embeddings:** BAAI/bge-small-en-v1.5
- **Async:** httpx for external API calls
- **Caching:** Redis (planned)
- **Queue:** Celery (planned)

### Frontend
- **Framework:** React Router v8
- **Language:** TypeScript
- **Styling:** TailwindCSS v4
- **UI Components:** shadcn/ui, base-ui/react
- **Icons:** lucide-react
- **Animations:** GSAP, motion
- **State:** React hooks, Context API

### External APIs
- **OpenAlex:** Research papers (priority 1)
- **Crossref:** DOI lookup (priority 1)
- **arXiv:** CS/AI papers (priority 1)
- **NCBI/PubMed:** Biomedical (priority 2)
- **YouTube:** Videos (priority 2)
- **Google Books:** Books (priority 2)
- **Project Gutenberg:** Public-domain (priority 2)

---

## Scalability Considerations

### Database Scaling
- **Read replicas:** For read-heavy operations (quiz attempts, analytics)
- **Connection pooling:** SQLAlchemy pool with appropriate size
- **Indexes:** On all foreign keys and frequently queried fields
- **Partitioning:** Consider partitioning large tables (quiz_attempts, flashcard_reviews)

### API Scaling
- **Horizontal scaling:** Multiple backend instances behind load balancer
- **Rate limiting:** Per-user rate limiting to prevent abuse
- **Caching:** Redis for API responses and query results
- **Async operations:** Background tasks for long-running operations

### File Storage Scaling
- **Cloud storage:** S3 or GCS for file uploads
- **CDN:** CloudFront or Cloud CDN for static assets
- **Lifecycle policies:** Automatic cleanup of old files

---

## Disaster Recovery

### Backup Strategy
- **Database:** Daily backups with point-in-time recovery
- **File storage:** Versioned backups with retention policy
- **Configuration:** Version-controlled in Git
- **Redis:** AOF persistence with snapshots

### Failover Strategy
- **Database:** Automatic failover to replica
- **API:** Multiple instances with health checks
- **External APIs:** Fallback to cached data or alternative providers

---

## Architecture Document Complete

This architecture document provides the foundation for implementing the Student Intelligence Suite. The architecture extends the existing Minutes platform while maintaining backward compatibility and following established patterns.

**Next Steps:**
1. Review and approve architecture
2. Begin Phase 1 implementation
3. Implement database migrations
4. Create service layer
5. Build API endpoints
6. Develop frontend components
7. Test and deploy

---

**Architecture Document Complete.** Ready for implementation.
