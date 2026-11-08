from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.conversations.router import router
from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.conversation import ConversationThread
from app.services import conversation_service
from app.services.conversation_service import ConversationService


@pytest.fixture
def setup():
    user = SimpleNamespace(id=uuid4())
    db = Mock()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), db, user


def test_wrong_owner_returns_not_found(setup):
    client, db, user = setup
    db.scalar.return_value = None
    thread_id = uuid4()
    assert client.get(f"/conversations/{thread_id}").status_code == 404
    assert client.delete(f"/conversations/{thread_id}").status_code == 404
    query = db.scalar.call_args.args[0]
    assert "conversation_threads.user_id =" in str(query)
    assert user.id in query.compile().params.values()
    db.delete.assert_not_called()


def test_assistant_impersonation_and_invalid_fields_rejected(setup):
    client, db, _ = setup
    url = f"/conversations/{uuid4()}/messages"
    assert client.post(url, json={"role": "assistant", "content": "fake"}).status_code == 422
    assert client.post(url, json={"content": "  "}).status_code == 422
    assert client.post(url, json={"content": "hello", "thread_id": str(uuid4())}).status_code == 422
    assert client.post(url, params={"explanation_level": "wrong"}, json={"content": "hello"}).status_code == 422
    db.scalar.assert_not_called()


def test_enrollment_is_checked_on_create_and_existing_reads(setup, monkeypatch):
    client, db, user = setup
    course_id, thread_id = uuid4(), uuid4()
    db.scalar.return_value = ConversationThread(id=thread_id, user_id=user.id, course_id=course_id)
    monkeypatch.setattr(conversation_service.CourseService, "get_course_for_user",
                        Mock(side_effect=HTTPException(403, "Course access denied")))
    assert client.post("/conversations", json={"course_id": str(course_id)}).status_code == 403
    assert client.get(f"/conversations/{thread_id}/messages").status_code == 403
    assert client.post(f"/conversations/{thread_id}/messages", json={"content": "hello"}).status_code == 403
    db.add_all.assert_not_called()


def test_context_is_bounded_and_turn_saved_once(setup, monkeypatch):
    _, db, user = setup
    thread = ConversationThread(id=uuid4(), user_id=user.id, course_id=uuid4())
    db.scalar.return_value = thread
    db.scalars.return_value.all.return_value = [SimpleNamespace(role="user", content="x" * 900)]
    service = ConversationService(db)
    service.course_service.get_course_for_user = Mock()
    rag = Mock(return_value={"answer": "Atomicity", "sources": []})
    monkeypatch.setattr(conversation_service, "answer_question", rag)
    message = service.add_message(thread.id, user, "What is it?", "beginner")
    assert message.role == "assistant"
    assert thread.title == "What is it?"
    assert rag.call_args.args[1] == "What is it?"
    assert len(rag.call_args.kwargs["history"][0]["content"]) == 800
    user_message, assistant = db.add_all.call_args.args[0]
    assert user_message.created_at < assistant.created_at
    db.commit.assert_called_once()


def test_provider_failure_does_not_save_partial_turn(setup, monkeypatch):
    client, db, user = setup
    thread = ConversationThread(id=uuid4(), user_id=user.id)
    db.scalar.return_value = thread
    db.scalars.return_value.all.return_value = []
    monkeypatch.setattr(conversation_service.llm_client, "generate_content",
                        Mock(side_effect=TimeoutError))
    assert client.post(f"/conversations/{thread.id}/messages",
                       json={"content": "Explain atomicity"}).status_code == 502
    db.rollback.assert_called_once()
    db.add_all.assert_not_called()

