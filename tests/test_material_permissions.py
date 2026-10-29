"""API-level permission/processing contracts without a live database or AI calls."""
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

os.environ["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost/audaxity_test_unused"
os.environ["JWT_SECRET_KEY"] = "audaxity-test-only-not-a-real-secret"

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.api.v1.notes import router as notes
from app.api.v1.lectures import router as lectures
from app.api.v1.auth import router as auth
from app.core.constants import NoteStatus, UserRole
from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.services.course_service import CourseService
from app.schemas.course import CourseCreate


@pytest.fixture
def environment(monkeypatch, tmp_path):
    app = FastAPI()
    for router in [notes.router, lectures.router, auth.router]:
        app.include_router(router, prefix="/api/v1")
    db = Mock()
    user = SimpleNamespace(id=uuid4(), role=UserRole.TEACHER)
    course = SimpleNamespace(id=uuid4(), teacher_id=user.id)
    now = datetime.now(timezone.utc)
    content = {"title": "Transactions", "summary": "A unit of work.", "learning_objectives": [], "sections": [], "questions_and_answers": [], "revision_summary": None}
    note = SimpleNamespace(id=uuid4(), lecture_id=uuid4(), title="Transactions", content=content,
                           pdf_path=None, html_path=None, status=NoteStatus.DRAFT,
                           created_at=now, updated_at=now,
                           lecture=SimpleNamespace(course_id=course.id, transcript=SimpleNamespace(content="The original lecture", language="en")))
    def course_access(self, course_id, current):
        if current.id != course.teacher_id and current.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Course access denied")
        if getattr(current, "enrolled", True) is False:
            raise HTTPException(status_code=403, detail="Course access denied")
        return course
    def teacher_access(self, course_id, current):
        if current.id != course.teacher_id or current.role != UserRole.TEACHER:
            raise HTTPException(status_code=403, detail="Course access denied")
        return course
    monkeypatch.setattr(CourseService, "get_course_for_user", course_access)
    monkeypatch.setattr(CourseService, "get_course", teacher_access)
    monkeypatch.setattr(notes.NoteService, "get_note", lambda self, id: note)
    monkeypatch.setattr(notes.NoteService, "get_lecture_note", lambda self, id: note)
    monkeypatch.setattr(notes.NoteService, "get_course_notes", lambda self, id: [note])
    monkeypatch.chdir(tmp_path)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return SimpleNamespace(app=app, client=TestClient(app), db=db, user=user, course=course, note=note, content=content)


def test_students_only_read_approved_materials(environment):
    e = environment
    e.user.role = UserRole.STUDENT
    assert e.client.get(f"/api/v1/notes/{e.note.id}").status_code == 404
    assert e.client.get(f"/api/v1/notes/course/{e.course.id}").json() == []
    e.note.status = NoteStatus.APPROVED
    assert e.client.get(f"/api/v1/notes/{e.note.id}").status_code == 200
    assert len(e.client.get(f"/api/v1/notes/course/{e.course.id}").json()) == 1
    e.user.enrolled = False
    assert e.client.get(f"/api/v1/notes/{e.note.id}").status_code == 403


def test_student_cannot_change_note_or_process_lecture(environment):
    e = environment
    e.user.role = UserRole.STUDENT
    e.note.status = NoteStatus.APPROVED
    assert e.client.put(f"/api/v1/notes/{e.note.id}", json={"status": "draft"}).status_code == 403
    assert e.client.post("/api/v1/lectures/transcript", json={"course_id": str(e.course.id), "transcript": "hello"}).status_code == 403
    assert e.client.post("/api/v1/lectures/upload", data={"course_id": str(e.course.id)}, files={"file": ("lecture.wav", b"audio")}).status_code == 403
    e.db.commit.assert_not_called()


def test_unrelated_teacher_cannot_access_material(environment):
    e = environment
    e.user.id = uuid4()
    assert e.client.get(f"/api/v1/notes/{e.note.id}").status_code == 403
    assert e.client.get(f"/api/v1/notes/{e.note.id}/download/pdf").status_code == 403
    assert e.client.get(f"/api/v1/lectures/{e.note.lecture_id}/transcript").status_code == 403


def test_all_processing_endpoints_require_authentication(environment):
    e = environment
    e.app.dependency_overrides.pop(get_current_user)
    for path, kwargs in [
        ("/api/v1/lectures/transcript", {"json": {"course_id": str(e.course.id), "transcript": "hello"}}),
        ("/api/v1/lectures/upload", {"data": {"course_id": str(e.course.id)}, "files": {"file": ("lecture.wav", b"audio")}}),
    ]:
        assert e.client.post(path, **kwargs).status_code in (401, 403)


def test_pdf_path_must_stay_in_output_directory(environment, tmp_path):
    e = environment
    external = tmp_path / "private.pdf"
    external.write_bytes(b"private")
    e.note.pdf_path = str(external)
    assert e.client.get(f"/api/v1/notes/{e.note.id}/download/pdf").status_code == 404
    folder = tmp_path / "outputs"
    folder.mkdir()
    pdf = folder / "notes.pdf"
    pdf.write_bytes(b"%PDF-test")
    e.note.pdf_path = str(pdf)
    response = e.client.get(f"/api/v1/notes/{e.note.id}/download/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-test"


def test_admin_self_registration_is_rejected(environment):
    r = environment.client.post("/api/v1/auth/register", json={"email": "test@example.com", "full_name": "Test", "password": "test-password", "role": "admin"})
    assert r.status_code == 422


def test_student_cannot_create_course():
    db = Mock()
    with pytest.raises(HTTPException) as exc:
        CourseService(db).create_course(CourseCreate(name="Test", code="CS"), SimpleNamespace(role=UserRole.STUDENT))
    assert exc.value.status_code == 403
    db.commit.assert_not_called()


def test_review_invalidates_search_index(environment, monkeypatch):
    e = environment
    def update(self, note, title, content, status):
        note.status = status
        return note
    monkeypatch.setattr(notes.NoteService, "update_note", update)
    response = e.client.put(f"/api/v1/notes/{e.note.id}", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert "DELETE FROM rag_chunks" in str(e.db.execute.call_args.args[0])
    e.db.commit.assert_called_once()


def test_transcript_processing_persists_verified_contract(environment, monkeypatch, tmp_path):
    e = environment
    debug, output = tmp_path / "debug_outputs", tmp_path / "outputs"
    debug.mkdir(); output.mkdir()
    monkeypatch.setattr(lectures, "DEBUG_DIR", debug)
    monkeypatch.setattr(lectures, "OUTPUT_DIR", output)
    monkeypatch.setattr(lectures, "generate_notes_from_transcript", lambda *args: e.content)
    monkeypatch.setattr(lectures, "generate_pdf", lambda *args: None)
    monkeypatch.setattr(lectures, "render_html", lambda *args: None)
    monkeypatch.setattr(lectures, "run_syllabus_mapping", lambda **kw: {"mappings": [], "coverage_percentage": 0})
    lecture = SimpleNamespace(id=uuid4())
    service = Mock()
    service.create_lecture.return_value = lecture
    monkeypatch.setattr(lectures, "LectureService", lambda db: service)
    response = e.client.post("/api/v1/lectures/transcript", json={"course_id": str(e.course.id), "title": "Transactions", "transcript": "A transaction is a unit of work."})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["notes"]["title"] == "Transactions"
    service.save_transcript.assert_called_once()
    service.save_note.assert_called_once()
    service.mark_completed.assert_called_once_with(lecture)
    e.db.commit.assert_called_once()


def test_processing_failure_does_not_return_success(environment, monkeypatch, tmp_path):
    e = environment
    debug = tmp_path / "debug_outputs"; debug.mkdir()
    monkeypatch.setattr(lectures, "DEBUG_DIR", debug)
    monkeypatch.setattr(lectures, "generate_notes_from_transcript", Mock(side_effect=RuntimeError("Provider unavailable")))
    client = TestClient(e.app, raise_server_exceptions=False)
    response = client.post("/api/v1/lectures/transcript", json={"course_id": str(e.course.id), "transcript": "Original lecture text."})
    assert response.status_code == 500
    e.db.rollback.assert_called_once()
    e.db.commit.assert_not_called()


def test_edit_regenerates_files_and_returns_to_draft(environment, monkeypatch, tmp_path):
    e = environment
    e.note.status = NoteStatus.APPROVED
    def update(self, note, title, content, status):
        note.title = title or note.title
        note.content = content or note.content
        note.status = status
        return note
    monkeypatch.setattr(notes.NoteService, "update_note", update)
    content = {**e.content, "title": "Edited <lecture>", "summary": "A & B <script>alert('test')</script>"}
    response = e.client.put(f"/api/v1/notes/{e.note.id}", json={"title": content["title"], "content": content, "status": "approved"})
    assert response.status_code == 200
    assert response.json()["status"] == "draft"
    from pathlib import Path
    assert Path(e.note.pdf_path).read_bytes().startswith(b"%PDF")
    rendered = Path(e.note.html_path).read_text(encoding="utf-8")
    assert "<script>alert('test')</script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "Edited &lt;lecture&gt;" in rendered


def test_audio_pipeline_saves_transcript_and_notes(environment, monkeypatch, tmp_path):
    e = environment
    folder = tmp_path / "uploads"; folder.mkdir()
    monkeypatch.setattr(lectures, "UPLOAD_DIR", folder)
    monkeypatch.setattr(lectures, "process_lecture", lambda path: {"transcript": "Original spoken lecture", "notes": e.content, "pdf": "outputs/test.pdf", "html": "outputs/test.html", "debug_folder": "debug_outputs/test"})
    monkeypatch.setattr(lectures, "run_syllabus_mapping", lambda **kwargs: {"mappings": [], "coverage_percentage": 0})
    service = Mock(); lecture = SimpleNamespace(id=uuid4()); service.create_lecture.return_value = lecture
    monkeypatch.setattr(lectures, "LectureService", lambda db: service)
    response = e.client.post("/api/v1/lectures/upload", data={"course_id": str(e.course.id), "title": "Test lecture"}, files={"file": ("lecture.wav", b"test audio", "audio/wav")})
    assert response.status_code == 200
    assert response.json()["transcript"] == "Original spoken lecture"
    service.save_note.assert_called_once()
    service.save_transcript.assert_called_once()
    service.mark_completed.assert_called_once_with(lecture)
    saved = list(folder.iterdir())
    assert len(saved) == 1 and saved[0].name != "lecture.wav"
    assert saved[0].read_bytes() == b"test audio"


def test_upload_rejects_invalid_type_and_blank_transcript(environment):
    e = environment
    assert e.client.post("/api/v1/lectures/upload", data={"course_id": str(e.course.id)}, files={"file": ("lecture.exe", b"test")}).status_code == 422
    assert e.client.post("/api/v1/lectures/transcript", json={"course_id": str(e.course.id), "transcript": "   "}).status_code == 422
    e.db.commit.assert_not_called()
