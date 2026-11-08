from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.study_plan import GoalCreate, GoalReplan, SessionUpdate
from app.services.study_plan_service import allocate_sessions


def test_prioritizes_repeated_misses_and_works_around_existing_bookings():
    day = date(2026, 11, 9)
    targets = [{"id": "new", "title": "New topic"}, {"id": "miss", "title": "Practice mistakes"}]
    slots, overflow = allocate_sessions(
        targets, day, day + timedelta(days=1), 30, 25,
        completed={}, booked={day: 20}, priorities={"miss"},
    )
    assert [(item["topic_id"], item["study_date"], item["minutes"]) for item in slots] == [
        ("miss", day, 10), ("miss", day + timedelta(days=1), 15),
        ("new", day + timedelta(days=1), 15),
    ]
    assert overflow == 10


def test_completed_minutes_are_never_planned_twice():
    day = date(2026, 11, 9)
    targets = [{"id": None, "title": "Assignment"}]
    slots, overflow = allocate_sessions(targets, day, day, 10, 20,
                                        completed={None: 15}, booked={}, priorities=set())
    assert len(slots) == 1 and slots[0]["minutes"] == 5
    assert overflow == 0


def test_fully_booked_deadline_can_leave_all_work_unscheduled():
    day = date.max
    slots, overflow = allocate_sessions([{"id": None, "title": "Study"}], day, day, 20, 30,
                                        completed={}, booked={day: 20}, priorities=set())
    assert slots == [] and overflow == 30


def test_schedule_validation():
    today = date(2026, 11, 9)
    with pytest.raises(ValidationError):
        GoalReplan(start_date=today, deadline=today - timedelta(days=1), daily_minutes=30)
    with pytest.raises(ValidationError):
        GoalReplan(start_date=today, deadline=today + timedelta(days=181), daily_minutes=30)
    topic = uuid4()
    with pytest.raises(ValidationError):
        GoalCreate(course_id=uuid4(), title="Exam", kind="exam", topic_ids=[topic, topic],
                   start_date=today, deadline=today, minutes_per_item=30, daily_minutes=45)
    with pytest.raises(ValidationError):
        SessionUpdate(completed="true")

