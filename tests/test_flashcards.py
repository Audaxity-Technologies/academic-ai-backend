from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.flashcard import CardContent, ReviewRequest
from app.services.flashcard_service import FlashcardService, priority_topics, sm2


def test_sm2_intervals_round_up_and_reset_on_failed_recall():
    first = sm2(250, 0, 0, 5)
    second = sm2(*first, 5)
    third = sm2(*second, 5)
    assert first == (260, 1, 1)
    assert second == (270, 2, 6)
    assert third == (280, 3, 17)
    assert sm2(140, 3, 17, 0) == (130, 0, 1)
    assert sm2(130, 0, 1, 3)[1:] == (1, 1)


def test_reject_invalid_rating_and_cloze():
    with pytest.raises(ValidationError):
        ReviewRequest(rating=6, review_count=0)
    with pytest.raises(ValidationError):
        ReviewRequest(rating=True, review_count=0)
    with pytest.raises(ValidationError):
        CardContent(kind="cloze", front="No blank", back="answer")


def test_review_retry_returns_existing_schedule():
    card = SimpleNamespace(id=uuid4(), review_count=1, due_at=datetime.now(UTC))
    db = Mock()
    db.scalar.return_value = SimpleNamespace(rating=4)
    service = FlashcardService(db, SimpleNamespace(id=uuid4()))
    service.get_card = Mock(return_value=card)
    assert service.review(card.id, ReviewRequest(rating=4, review_count=0)) is card
    db.add.assert_not_called()
    with pytest.raises(HTTPException) as error:
        service.review(card.id, ReviewRequest(rating=2, review_count=0))
    assert error.value.status_code == 409



def test_priority_uses_repeated_incorrect_answers_without_counting_skips():
    topic = uuid4()
    another = uuid4()
    attempt = SimpleNamespace(
        questions=[{"topic_id": str(topic)}, {"topic_id": str(topic)}, {"topic_id": str(another)}],
        result={"feedback": [{"choice": 1, "correct": False}, {"choice": 2, "correct": False},
                             {"choice": None, "correct": False}]},
    )
    assert priority_topics([attempt]) == [topic]
