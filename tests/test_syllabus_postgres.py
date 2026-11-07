"""Opt-in workflow for an already migrated disposable PostgreSQL database."""
import os
from uuid import uuid4

import pytest


@pytest.mark.skipif(os.getenv("AUDAXITY_DATABASE_INTEGRATION") != "1",
                    reason="Requires an already migrated disposable PostgreSQL database")
def test_versions_and_repeated_alignment_in_postgres(monkeypatch, tmp_path):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from app.ai.syllabus import alignment
    from app.core.constants import LectureSourceType, UserRole
    from app.database.database import engine
    from app.models.course import Course
    from app.models.lecture import Lecture
    from app.models.syllabus_mapping import SyllabusMapping
    from app.models.transcript import Transcript
    from app.models.user import User
    from app.services import syllabus_document_service as documents
    from app.services.syllabus_alignment_service import align_saved_lecture

    monkeypatch.setattr(documents, "embed_documents", lambda texts: [[1.0] + [0.0] * 383 for _ in texts])
    monkeypatch.setattr(alignment, "embed_query", lambda _: [1.0] + [0.0] * 383)
    monkeypatch.setattr(alignment.SyllabusAlignmentEngine, "verify", staticmethod(
        lambda chunk, candidates: [
            alignment.Verification(topic_id=topic.id, status="covered", confidence=.9, excerpts=[chunk])
            for topic in candidates
        ]
    ))
    path = tmp_path / "sample.txt"
    path.write_text("Unit I\nTransactions", encoding="utf-8")
    monkeypatch.setattr("app.ai.syllabus.structurer.llm_client.generate_content", lambda **_: {
        "units": [{"title": "Transactions", "number": "I", "topics": [{"title": "Atomicity"}]}],
    })
    unique = uuid4().hex
    with engine.connect() as conn, conn.begin() as outer:
        with Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
            teacher = User(email=f"syllabus-{unique}@example.com", full_name="Test teacher",
                           password_hash="unused", role=UserRole.TEACHER)
            db.add(teacher)
            db.flush()
            course = Course(name="Databases", code=unique[:10], teacher_id=teacher.id)
            db.add(course)
            db.flush()
            service = documents.SyllabusDocumentService(db)
            first = service.upload_document(course.id, path, path.name)
            service.parse(first)
            service.confirm(first)
            lecture = Lecture(course_id=course.id, title="Transactions", source_type=LectureSourceType.TRANSCRIPT)
            db.add(lecture)
            db.flush()
            db.add(Transcript(lecture_id=lecture.id, content="Transactions are atomic."))
            db.commit()
            assert align_saved_lecture(db, lecture.id)["coverage_percentage"] == 100
            second = service.upload_document(course.id, path, path.name)
            assert not second.is_active and first.is_active
            service.parse(second)
            service.confirm(second)
            assert not first.is_active and second.is_active and second.version == 2
            for _ in range(2):
                assert align_saved_lecture(db, lecture.id)["syllabus_document_id"] == second.id
            assert db.scalar(select(func.count()).select_from(SyllabusMapping).where(
                SyllabusMapping.lecture_id == lecture.id
            )) == 2
        outer.rollback()

