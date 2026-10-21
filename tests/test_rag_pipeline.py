import sys
from types import ModuleType, SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.constants import UserRole

llm_module = ModuleType("app.ai.llm.llm_client")
llm_module.llm_client = SimpleNamespace(generate_content=None)
sys.modules.setdefault("app.ai.llm.llm_client", llm_module)

embedding_module = ModuleType("sentence_transformers")
embedding_module.SentenceTransformer = object
embedding_module.CrossEncoder = object
sys.modules.setdefault("sentence_transformers", embedding_module)

from app.rag import service as rag_service
from app.rag.chunker import build_note_chunks, build_transcript_chunks
from app.services.course_service import CourseService


def test_note_chunks_include_sections_and_question_answers():
    note = SimpleNamespace(
        id=uuid4(),
        title="Transactions",
        content={
            "sections": [
                {
                    "heading": "Atomicity",
                    "explanation": "All operations succeed or none do.",
                    "definitions": [
                        {"term": "Atomicity", "definition": "All or nothing."}
                    ],
                    "examples": [],
                    "formulas": [],
                    "instructor_emphasis": [],
                    "common_misconceptions": [],
                }
            ],
            "questions_and_answers": [
                {"question": "What is atomicity?", "answer": "All or nothing."}
            ],
        },
    )
    lecture = SimpleNamespace(id=uuid4(), course_id=uuid4(), title="Lecture 1")

    chunks = build_note_chunks(note, lecture)

    assert len(chunks) == 2
    assert chunks[0]["source_type"] == "note_section"
    assert "Atomicity: All or nothing." in chunks[0]["content"]
    assert chunks[1]["source_type"] == "note_qa"
    assert "What is atomicity?" in chunks[1]["content"]


def test_transcript_chunks_overlap_and_preserve_course_metadata():
    transcript = SimpleNamespace(content=" ".join(f"word{i}" for i in range(12)))
    lecture = SimpleNamespace(id=uuid4(), course_id=uuid4(), title="Lecture 1")

    chunks = build_transcript_chunks(
        transcript,
        lecture,
        chunk_size=6,
        overlap=2,
    )

    assert len(chunks) == 3
    assert chunks[0]["content"].split()[-2:] == chunks[1]["content"].split()[:2]
    assert chunks[1]["course_id"] == lecture.course_id


def test_answer_question_discards_invalid_source_ids(monkeypatch):
    chunk = SimpleNamespace(
        id=uuid4(),
        title="Atomicity",
        source_type="note_section",
        lecture_id=uuid4(),
        content="All operations in a transaction succeed or none do.",
    )
    monkeypatch.setattr(rag_service, "hybrid_search", lambda **_kwargs: [chunk])
    monkeypatch.setattr(
        rag_service,
        "rerank",
        lambda **_kwargs: [{"chunk": chunk, "score": 0.8}],
    )
    monkeypatch.setattr(
        rag_service.llm_client,
        "generate_content",
        lambda **_kwargs: {
            "answer": "Atomicity is all-or-nothing.",
            "confidence": 1.4,
            "sources": [1, 999, "1", True],
        },
    )

    result = rag_service.answer_question(db=None, query="Define atomicity", course_id=uuid4())

    assert result["answer"] == "Atomicity is all-or-nothing."
    assert result["confidence"] == 1.0
    assert [source["id"] for source in result["sources"]] == [1]


def test_student_can_access_only_enrolled_courses():
    student = SimpleNamespace(id=uuid4(), role=UserRole.STUDENT)
    course = SimpleNamespace(id=uuid4())
    service = CourseService(db=None)
    service.repo = SimpleNamespace(
        get_by_id=lambda _course_id: course,
        is_student_enrolled=lambda course_id, student_id: False,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_course_for_user(course.id, student)

    assert exc_info.value.status_code == 403

    service.repo.is_student_enrolled = lambda course_id, student_id: True
    assert service.get_course_for_user(course.id, student) is course


def test_admin_role_does_not_bypass_course_access():
    admin = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN)
    course = SimpleNamespace(id=uuid4(), teacher_id=uuid4())
    service = CourseService(db=None)
    service.repo = SimpleNamespace(
        get_by_id=lambda _course_id: course,
        is_student_enrolled=lambda _course_id, _student_id: False,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_course_for_user(course.id, admin)

    assert exc_info.value.status_code == 403


def test_teacher_enrollment_by_email_is_idempotent():
    teacher = SimpleNamespace(id=uuid4(), role=UserRole.TEACHER)
    student = SimpleNamespace(
        id=uuid4(),
        role=UserRole.STUDENT,
        email="student@example.edu",
    )
    course = SimpleNamespace(
        id=uuid4(),
        teacher_id=teacher.id,
        students=[],
    )
    db = SimpleNamespace(commit=lambda: None)
    service = CourseService(db=db)
    service.repo = SimpleNamespace(get_by_id=lambda _course_id: course)
    service.user_repo = SimpleNamespace(get_by_email=lambda _email: student)

    first = service.enroll_student(course.id, student.email, teacher)
    second = service.enroll_student(course.id, student.email, teacher)

    assert first is student
    assert second is student
    assert course.students == [student]
