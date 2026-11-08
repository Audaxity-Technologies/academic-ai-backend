from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.practice_exam import ExamAnswer, ExamCreate, GeneratedExam
from app.services import practice_exam_service as practice


def make_question(topic_id, **changes):
    return {"topic_id": str(topic_id), "prompt": "Which operation is atomic?",
            "options": ["A", "B", "C", "D"], "correct_index": 1,
            "explanation": "The operation commits as one unit.", "lecture_ids": [], **changes}


def test_public_questions_hide_answers_and_explanations():
    topic_id = uuid4()
    exam = SimpleNamespace(id=uuid4(), course_id=uuid4(), difficulty="easy", duration_minutes=None,
                           created_at=datetime.now(UTC), questions=[make_question(topic_id)], result=None)
    public = practice.detail(exam).model_dump()
    assert set(public["questions"][0]) == {"topic_id", "prompt", "options"}
    assert public["result"] is None


def test_grade_tracks_accuracy_time_and_deadline():
    now = datetime.now(UTC)
    topic_id = uuid4()
    exam = SimpleNamespace(created_at=now - timedelta(minutes=2), duration_minutes=1,
                           questions=[make_question(topic_id), make_question(topic_id)])
    result = practice.grade(exam, [ExamAnswer(choice=1, seconds=12), ExamAnswer()], now)
    assert (result.score, result.total, result.late) == (1, 2, True)
    assert result.feedback[0].seconds == 12
    assert not result.feedback[1].correct


def test_reject_malformed_question():
    with pytest.raises(ValidationError):
        GeneratedExam.model_validate({"questions": [make_question(uuid4(), options=["A", "a", "B", "C"])]})


def test_unselected_topic_rejected_without_saving(monkeypatch):
    course, topic = uuid4(), uuid4()
    db = Mock()
    db.scalar.return_value = None
    service = practice.PracticeExamService(db, SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(service, "topics", lambda *_: [
        SimpleNamespace(id=topic, title="Atomicity", description=None)
    ])
    monkeypatch.setattr(service, "list_exams", lambda *_: [])
    monkeypatch.setattr(practice.llm_client, "generate_content", lambda **_: {
        "questions": [make_question(uuid4())],
    })
    with pytest.raises(HTTPException) as exc:
        service.create(ExamCreate(course_id=course, topic_ids=[topic], count=1))
    assert exc.value.status_code == 502
    db.add.assert_not_called()
    db.rollback.assert_called_once()

