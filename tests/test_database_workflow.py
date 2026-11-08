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
    # The request transaction is rolled back, so its lecture is not visible to the background session.
    monkeypatch.setattr(processing, "run_lecture_alignment", lambda lecture_id: None)
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
            conversation = client.post("/api/v1/conversations", headers=student,
                                       json={"course_id": course_id})
            assert conversation.status_code == 200, conversation.text
            thread_path = f"/api/v1/conversations/{conversation.json()['id']}"
            assert client.get(thread_path, headers=teacher).status_code == 404
            reply = client.post(f"{thread_path}/messages", headers=student,
                                params={"explanation_level": "beginner"},
                                json={"content": "What is atomicity?"})
            assert reply.status_code == 200, reply.text
            assert reply.json()["citations"][0]["lecture_id"] == lecture_id
            saved = client.get(thread_path, headers=student).json()["messages"]
            assert [message["role"] for message in saved] == ["user", "assistant"]
            topic = client.post(f"/api/v1/courses/{course_id}/syllabus", headers=teacher,
                                json={"title": "Atomicity", "position": 1})
            assert topic.status_code == 201, topic.text
            topic_id = topic.json()["id"]
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {"questions": [{
                "topic_id": topic_id, "prompt": "What does atomicity guarantee?",
                "options": ["All or nothing", "No writes", "No locks", "No reads"],
                "correct_index": 0, "explanation": "The transaction commits as one unit.",
                "source_numbers": [1],
            }]})
            exam = client.post("/api/v1/practice-exams", headers=student, json={
                "course_id": course_id, "topic_ids": [topic_id], "count": 1,
            })
            assert exam.status_code == 201, exam.text
            assert "correct_index" not in exam.json()["questions"][0]
            exam_path = f"/api/v1/practice-exams/{exam.json()['id']}"
            assert client.get(exam_path, headers=teacher).status_code == 404
            scored = client.post(f"{exam_path}/submit", headers=student,
                                 json={"answers": [{"choice": 0, "seconds": 6}]})
            assert scored.status_code == 200, scored.text
            assert scored.json()["result"]["score"] == 1
            repeated = client.post(f"{exam_path}/submit", headers=student,
                                   json={"answers": [{"choice": 1}]})
            assert repeated.json()["result"] == scored.json()["result"]
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {
                "answer": "Atomicity is all or nothing. [1]", "confidence": .9, "sources": [1],
            })
            from io import BytesIO
            from reportlab.pdfgen.canvas import Canvas
            from app.services import question_paper_service as paper_service
            from app.models.syllabus import SyllabusTopic
            from uuid import UUID

            row = db.get(SyllabusTopic, UUID(topic_id))
            row.embedding = vector
            db.commit()
            monkeypatch.setattr(paper_service, "embed_documents", lambda texts: [vector for _ in texts])
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {"questions": [{
                "text": "Explain atomicity.", "number": "1", "marks_label": "[5 marks]",
            }]})
            pdf_source = BytesIO()
            canvas = Canvas(pdf_source)
            canvas.drawString(50, 740, "1. Explain atomicity. [5 marks]")
            canvas.save()
            upload_args = {"data": {"course_id": course_id, "exam_year": "2023", "native_pdf": "true"},
                           "files": {"file": ("past-paper.pdf", pdf_source.getvalue(), "application/pdf")}}
            paper_response = client.post("/api/v1/question-papers", headers=student, **upload_args)
            assert paper_response.status_code == 201, paper_response.text
            saved_paper = paper_response.json()
            assert saved_paper["questions"][0]["page"] == 1
            assert saved_paper["questions"][0]["marks"] == 5
            assert saved_paper["questions"][0]["topic_id"] == topic_id
            assert "storage_path" not in saved_paper
            paper_path = f"/api/v1/question-papers/{saved_paper['id']}"
            assert client.get(f"{paper_path}/file", headers=teacher).status_code == 404
            assert client.get(f"{paper_path}/file", headers=student).content == pdf_source.getvalue()
            assert client.post("/api/v1/question-papers", headers=student, **upload_args).status_code == 409
            stats = client.get("/api/v1/question-papers/analysis", headers=student,
                               params={"course_id": course_id}).json()
            assert stats["paper_count"] == 1 and stats["marks_distribution"] == {"5": 1}
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {
                "answer": "Atomicity is all or nothing. [1]", "confidence": .9, "sources": [1],
            })
            model_answer = client.post(f"{paper_path}/questions/0/explanation", headers=student)
            assert model_answer.status_code == 200, model_answer.text
            assert model_answer.json()["sources"][0]["lecture_id"] == lecture_id
            assert client.delete(paper_path, headers=teacher).status_code == 404
            assert client.delete(paper_path, headers=student).status_code == 204
            assert client.get(f"{paper_path}/file", headers=student).status_code == 404
            assert not list((tmp_path / "uploads/question-papers").glob("*.pdf"))
            cards_path = "/api/v1/flashcards"
            card = client.post(cards_path, headers=student, json={
                "course_id": course_id, "topic_id": topic_id, "kind": "definition",
                "front": "Define atomicity", "back": "All or nothing.",
            })
            assert card.status_code == 201, card.text
            card_id = card.json()["id"]
            due = client.get(cards_path, headers=student, params={"course_id": course_id, "due_only": True})
            assert due.status_code == 200, due.text
            assert due.json()["due_count"] == 1
            reviews_path = f"{cards_path}/{card_id}/reviews"
            assert client.get(reviews_path, headers=teacher).status_code == 404
            first_review = client.post(reviews_path, headers=student, json={"rating": 5, "review_count": 0})
            assert first_review.status_code == 200, first_review.text
            assert first_review.json()["interval_days"] == first_review.json()["review_count"] == 1
            retry = client.post(reviews_path, headers=student, json={"rating": 5, "review_count": 0})
            assert retry.json()["due_at"] == first_review.json()["due_at"]
            assert client.post(reviews_path, headers=student, json={"rating": 4, "review_count": 1}).status_code == 409
            assert len(client.get(reviews_path, headers=student).json()) == 1
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {"cards": [
                {"kind": "concept", "front": "What commits as one unit?", "back": "A transaction.",
                 "evidence": "A transaction succeeds as one unit"},
                {"kind": "concept", "front": "What is nonsense?", "back": "An invented claim.",
                 "evidence": "This fabricated excerpt never appeared."},
            ]})
            generated_cards = client.post(f"{cards_path}/generate", headers=student, json={
                "course_id": course_id, "lecture_id": lecture_id, "kind": "concept", "count": 2,
            })
            assert generated_cards.status_code == 201, generated_cards.text
            assert len(generated_cards.json()) == 1
            derived_id = generated_cards.json()[0]["id"]
            monkeypatch.setattr(rag.llm_client, "generate_content", lambda **_: {
                "answer": "Atomicity is all or nothing. [1]", "confidence": .9, "sources": [1],
            })
            from datetime import date, timedelta

            plan_path = "/api/v1/study-planner/goals"
            start = date(2026, 11, 9)
            deadline = start + timedelta(days=2)
            goal = client.post(plan_path, headers=student, json={
                "course_id": course_id, "title": "Database midterm", "kind": "exam",
                "topic_ids": [topic_id], "start_date": start.isoformat(), "deadline": deadline.isoformat(),
                "minutes_per_item": 30, "daily_minutes": 20,
            })
            assert goal.status_code == 201, goal.text
            plan = goal.json()
            assert [item["minutes"] for item in plan["sessions"]] == [20, 10]
            goal_path = f"{plan_path}/{plan['id']}"
            original_id = plan["sessions"][0]["id"]
            mark_url = f"{goal_path}/sessions/{original_id}"
            assert client.patch(mark_url, headers=teacher, json={"completed": True}).status_code == 404
            assert client.patch(mark_url, headers=student, json={"completed": True}).json()["status"] == "completed"
            blocked = client.post(plan_path, headers=student, json={
                "course_id": course_id, "title": "Short assignment", "kind": "assignment",
                "start_date": start.isoformat(), "deadline": start.isoformat(),
                "minutes_per_item": 10, "daily_minutes": 20,
            })
            assert blocked.status_code == 201, blocked.text
            assert blocked.json()["unscheduled_minutes"] == 10
            assert blocked.json()["sessions"] == []
            replan_args = {"start_date": (start + timedelta(days=1)).isoformat(),
                           "deadline": deadline.isoformat(), "daily_minutes": 5}
            replanned = client.post(f"{goal_path}/replan", headers=student, json=replan_args)
            assert replanned.status_code == 200, replanned.text
            assert [item["minutes"] for item in replanned.json()["sessions"]] == [20, 5, 5]
            assert replanned.json()["sessions"][0]["id"] == original_id
            assert replanned.json()["sessions"][0]["status"] == "completed"
            again = client.post(f"{goal_path}/replan", headers=student, json=replan_args)
            assert again.json()["sessions"] == replanned.json()["sessions"]
            assert client.delete(goal_path, headers=teacher).status_code == 404
            analytics_path = "/api/v1/analytics/learning-progress"
            report = client.get(analytics_path, headers=student, params={
                "course_id": course_id, "days": "7", "timezone": "Asia/Kolkata",
            })
            assert report.status_code == 200, report.text
            activity = report.json()
            assert (activity["answered"], activity["correct"], activity["reviews"]) == (1, 1, 1)
            assert activity["completed_sessions"] == 1
            assert activity["completed_planned_minutes"] == 20
            assert activity["topics"][0]["topic_id"] == topic_id
            assert len(activity["days"]) == 7
            teacher_report = client.get(analytics_path, headers=teacher,
                                        params={"course_id": course_id})
            assert teacher_report.status_code == 200
            assert teacher_report.json()["active_days"] == 0
            assert client.get(analytics_path, headers=student, params={
                "course_id": course_id, "timezone": "Not/AZone",
            }).status_code == 422
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
            hidden = client.get(thread_path, headers=student).json()["messages"][-1]
            assert client.get(exam_path, headers=student).status_code == 410
            assert client.get(f"{cards_path}/{derived_id}/reviews", headers=student).status_code == 404
            assert client.delete(f"{cards_path}/{derived_id}", headers=student).status_code == 204
            assert hidden["citations"] == []
            assert "no longer published" in hidden["content"]
            assert client.delete(thread_path, headers=student).status_code == 204
            after = client.get("/api/v1/search/", headers=student, params={"course_id": course_id, "query": "What is atomicity?"})
            assert after.status_code == 200 and after.json()["sources"] == []
        finally:
            app.dependency_overrides.pop(get_db, None)
            db.close()
            transaction.rollback()
    with Session(engine) as verification:
        assert verification.scalar(select(User).where(User.email == teacher_email)) is None
        assert verification.scalar(select(User).where(User.email == student_email)) is None
