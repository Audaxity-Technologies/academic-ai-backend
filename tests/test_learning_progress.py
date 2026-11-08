from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.services.learning_progress_service import aggregate_activity


def test_daily_activity_uses_requested_timezone_and_excludes_unanswered_from_accuracy():
    topic = uuid4()
    instant = datetime(2026, 11, 8, 20, 0, tzinfo=UTC)
    exams = [SimpleNamespace(
        questions=[{"topic_id": str(topic)}] * 3,
        result={"submitted_at": instant.isoformat(), "feedback": [
            {"choice": 1, "correct": True}, {"choice": None, "correct": False},
            {"choice": 2, "correct": False},
        ]},
    )]
    reviews = [SimpleNamespace(rating=rating, reviewed_at=instant) for rating in (5, 0)]
    sessions = [SimpleNamespace(minutes=30, completed_at=instant)]
    summary, topics = aggregate_activity(
        exams, reviews, sessions, ZoneInfo("Asia/Kolkata"), date(2026, 11, 8), date(2026, 11, 9),
    )
    assert summary["active_days"] == summary["submitted_exams"] == 1
    assert (summary["answered"], summary["correct"], summary["unanswered"]) == (2, 1, 1)
    assert (summary["reviews"], summary["successful_recalls"]) == (2, 1)
    assert summary["days"][0]["answered"] == 0
    assert summary["days"][1]["completed_planned_minutes"] == 30
    assert topics[topic] == {"correct": 1, "incorrect": 1, "unanswered": 1}


def test_empty_window_has_real_zero_counts():
    today = date(2026, 11, 9)
    summary, topics = aggregate_activity([], [], [], ZoneInfo("UTC"), today, today)
    assert summary["active_days"] == 0
    assert summary["submitted_exams"] == 0
    assert len(summary["days"]) == 1
    assert not topics

