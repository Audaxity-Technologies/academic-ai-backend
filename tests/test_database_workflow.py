"""Opt-in real PostgreSQL workflow; all records roll back, all AI is mocked.

Run separately with AUDAXITY_DATABASE_INTEGRATION=1 and the backend's configured
database. Never run against a database where test transactions are prohibited.
"""
import os
from uuid import uuid4
import pytest


@pytest.mark.skipif(os.getenv("AUDAXITY_DATABASE_INTEGRATION") != "1", reason="Opt-in PostgreSQL integration test")
def test_teacher_to_student_workflow_in_rolled_back_transaction(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.main import app
    from app.database.database import engine
    from app.database.dependencies.database import get_db
    from app.api.v1.lectures import router as processing
    from app.rag import indexer, retriever, service as rag
    from app.models.user import User

    unique = uuid4().hex
    teacher_email = f"teacher-{unique}@example.com"
    student_email = f"student-{unique}@example.com"
    notes = {"title": "Atomicity", "summary": "A transaction succeeds as one unit.",
             "learning_objectives": ["Explain atomicity"],
             "sections": [{"heading": "All or nothing", "explanation": "If one operation fails, all operations roll back.",
                           "examples": [], "definitions": [], "formulas": [], "diagram": {"type": "none", "mermaid_code": None},
                           "instructor_emphasis": [], "common_misconceptions": []}],
             "questions_and_answers": [], "revision_summary": "All or nothing."}
    monkeypatch.chdir(tmp_path)
    output, debug = tmp_path / "outputs", tmp_path / "debug_outputs"
    output.mkdir(); debug.mkdir()
    monkeypatch.setattr(processing, "OUTPUT_DIR", output)
    monkeypatch.setattr(processing, "DEBUG_DIR", debug)
    monkeypatch.setattr(processing, "generate_notes_from_transcript", lambda *args: notes)
    # No syllabus topics are created, so no syllabus model request is needed.
    vector = [1.0] + [0.0] * 383
    monkeypatch.setattr(indexer, "embed_documents", lambda texts: [vector for _ in texts])
    monkeypatch.setattr(retriever, "embed_query", lambda text: vector)
    monkeypatch.setattr(rag, "rerank", lambda query, chunks, top_k: [{"chunk": c, "score": 1.0} for c in chunks[:top_k]])
    monkeypatch.setattr(rag.llm_client, "generate_content", lambda **kw: {"answer": "Atomicity is all or nothing. [1]", "confidence": .9, "sources": [1]})

    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
        app.dependency_overrides[get_db] = lambda: db
        try:
            client = TestClient(app)
            def register(email, role):
                r = client.post("/api/v1/auth/register", json={"email": email, "full_name": f"Integration {role}", "password": "test-integration-password", "role": role})
                assert r.status_code == 201, r.text
                login = client.post("/api/v1/auth/login", json={"email": email, "password": "test-integration-password"})
                assert login.status_code == 200, login.text
                return {"Authorization": f"Bearer {login.json()['access_token']}"}
            teacher = register(teacher_email, "teacher")
            student = register(student_email, "student")
            assert client.get("/api/v1/users/me", headers=teacher).json()["role"] == "teacher"
            created = client.post("/api/v1/courses/", headers=teacher, json={"name": "Integration course", "code": f"IT-{unique}"})
            assert created.status_code == 201, created.text
            course_id = created.json()["id"]
            assert client.get(f"/api/v1/courses/{course_id}", headers=student).status_code == 403
            assert client.post(f"/api/v1/courses/{course_id}/students", headers=teacher, json={"email": student_email}).status_code == 200
            assert client.get("/api/v1/courses/", headers=student).json()[0]["id"] == course_id
            result = client.post("/api/v1/lectures/transcript", headers=teacher, json={"course_id": course_id, "title": "Atomicity", "transcript": "A transaction succeeds as one unit or all operations roll back."})
            assert result.status_code == 200, result.text
            lecture_id = result.json()["lecture_id"]
            material = client.get(f"/api/v1/notes/course/{course_id}", headers=teacher).json()[0]
            note_id = material["id"]
            assert material["status"] == "draft"
            assert client.get(f"/api/v1/notes/course/{course_id}", headers=student).json() == []
            assert client.get(f"/api/v1/lectures/{lecture_id}/transcript", headers=student).status_code == 404
            before = client.post(f"/api/v1/search/index/{course_id}", headers=teacher)
            assert before.status_code == 200 and before.json()["chunks_indexed"] == 0
            assert client.put(f"/api/v1/notes/{note_id}", headers=student, json={"status": "approved"}).status_code in (403, 404)
            assert client.put(f"/api/v1/notes/{note_id}", headers=teacher, json={"status": "approved"}).status_code == 200
            assert client.get(f"/api/v1/notes/{note_id}", headers=student).json()["status"] == "approved"
            assert client.get(f"/api/v1/lectures/{lecture_id}/transcript", headers=student).json()["content"].startswith("A transaction")
            pdf = client.get(f"/api/v1/notes/{note_id}/download/pdf", headers=student)
            assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
            assert client.post(f"/api/v1/search/index/{course_id}", headers=student).status_code == 403
            indexed = client.post(f"/api/v1/search/index/{course_id}", headers=teacher)
            assert indexed.status_code == 200 and indexed.json()["chunks_indexed"] > 0
            answer = client.get("/api/v1/search/", headers=student, params={"course_id": course_id, "query": "What is atomicity?"})
            assert answer.status_code == 200, answer.text
            assert answer.json()["sources"] and answer.json()["answer"].startswith("Atomicity")
            # Legacy indexes must not bypass current publication rules.
            from app.models.note import Note
            from app.core.constants import NoteStatus
            from uuid import UUID
            stored_note = db.get(Note, UUID(note_id))
            stored_note.status = NoteStatus.DRAFT
            db.commit()
            legacy = client.get("/api/v1/search/", headers=student, params={"course_id": course_id, "query": "What is atomicity?"})
            assert legacy.status_code == 200 and legacy.json()["sources"] == []
            stored_note.status = NoteStatus.APPROVED
            db.commit()
            assert client.put(f"/api/v1/notes/{note_id}", headers=teacher, json={"status": "draft"}).status_code == 200
            assert client.get(f"/api/v1/notes/{note_id}/download/pdf", headers=student).status_code == 404
            after = client.get("/api/v1/search/", headers=student, params={"course_id": course_id, "query": "What is atomicity?"})
            assert after.status_code == 200 and after.json()["sources"] == []
        finally:
            app.dependency_overrides.pop(get_db, None)
            db.close()
            transaction.rollback()
    with Session(engine) as verification:
        assert verification.scalar(select(User).where(User.email == teacher_email)) is None
        assert verification.scalar(select(User).where(User.email == student_email)) is None
