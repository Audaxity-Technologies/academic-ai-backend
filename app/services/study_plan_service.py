from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.ai.syllabus.alignment import topic_scope
from app.models.study_plan import StudyGoal, StudySession
from app.models.syllabus import SyllabusTopic
from app.models.user import User
from app.services.course_service import CourseService
from app.services.flashcard_service import recent_topic_priorities
from app.services.syllabus_alignment_service import active_version

DAY = timedelta(days=1)


def allocate_sessions(targets, start, deadline, daily_minutes, minutes_per_item, completed, booked, priorities):
    """Allocate the remaining target minutes into available calendar slots."""
    slots = []
    unscheduled = 0
    day = start
    available = max(0, daily_minutes - booked.get(day, 0))
    ordered = sorted(targets, key=lambda item: (
        item["id"] not in priorities, completed.get(item["id"], 0) > 0,
    ))
    for target in ordered:
        remaining = max(0, minutes_per_item - completed.get(target["id"], 0))
        while remaining and day <= deadline:
            if available == 0:
                if day == deadline:
                    break
                day += DAY
                available = max(0, daily_minutes - booked.get(day, 0))
                continue
            amount = min(remaining, available)
            slots.append({"topic_id": target["id"], "title": target["title"],
                          "study_date": day, "minutes": amount})
            remaining -= amount
            available -= amount
        unscheduled += remaining
    return slots, unscheduled


class StudyPlanService:
    def __init__(self, db, user):
        self.db = db
        self.user = user

    def authorize(self, course_id):
        CourseService(self.db).get_course_for_user(course_id, self.user)

    def lock_calendar(self):
        # Serialize changes to the same student's time budget across courses.
        self.db.scalar(select(User.id).where(User.id == self.user.id).with_for_update())

    def active_sessions(self):
        return selectinload(StudyGoal.sessions.and_(StudySession.status != "rescheduled"))

    def list_goals(self, course_id):
        self.authorize(course_id)
        return list(self.db.scalars(select(StudyGoal).where(
            StudyGoal.user_id == self.user.id, StudyGoal.course_id == course_id,
        ).options(self.active_sessions()).order_by(StudyGoal.deadline, StudyGoal.id).limit(100)))

    def get_goal(self, goal_id, *, lock=False, check_course=True):
        query = select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == self.user.id)
        if lock:
            query = query.with_for_update()
        goal = self.db.scalar(query.options(self.active_sessions()).execution_options(populate_existing=True))
        if goal is None:
            raise HTTPException(404, "Study goal not found")
        if check_course:
            self.authorize(goal.course_id)
        return goal

    def create(self, body):
        self.authorize(body.course_id)
        self.lock_calendar()
        topic_ids = set(body.topic_ids)
        if topic_ids:
            scope = topic_scope(body.course_id, active_version(self.db, body.course_id))
            topics = list(self.db.scalars(scope.where(SyllabusTopic.id.in_(topic_ids))
                                         .order_by(SyllabusTopic.position, SyllabusTopic.id)))
            if {topic.id for topic in topics} != topic_ids:
                raise HTTPException(422, "Choose topics from this course's current syllabus")
            targets = [{"id": str(topic.id), "title": topic.title} for topic in topics]
        else:
            targets = [{"id": None, "title": body.title}]
        goal = StudyGoal(
            user_id=self.user.id, course_id=body.course_id, title=body.title, kind=body.kind,
            deadline=body.deadline, daily_minutes=body.daily_minutes,
            minutes_per_item=body.minutes_per_item, targets=targets,
        )
        self.db.add(goal)
        self.db.flush()
        return self.save_schedule(goal, body.start_date, [])

    def replan(self, goal_id, body):
        self.lock_calendar()
        goal = self.get_goal(goal_id, lock=True)
        goal.deadline = body.deadline
        goal.daily_minutes = body.daily_minutes
        return self.save_schedule(goal, body.start_date, goal.sessions)

    def save_schedule(self, goal, start, sessions):
        completed = Counter()
        planned = []
        for item in sessions:
            if item.status == "completed":
                completed[str(item.topic_id) if item.topic_id else None] += item.minutes
            else:
                planned.append(item)
        booked = dict(self.db.execute(select(
            StudySession.study_date, func.sum(StudySession.minutes)
        ).join(StudyGoal).where(
            StudyGoal.user_id == self.user.id, StudySession.study_date.between(start, goal.deadline),
            StudySession.status.in_(("planned", "completed")),
            or_(StudySession.goal_id != goal.id, StudySession.status == "completed"),
        ).group_by(StudySession.study_date)).all())
        priorities = {str(topic) for topic in recent_topic_priorities(self.db, self.user.id, goal.course_id)}
        slots, goal.unscheduled_minutes = allocate_sessions(
            goal.targets, start, goal.deadline, goal.daily_minutes,
            goal.minutes_per_item, completed, booked, priorities,
        )
        before = Counter((str(item.topic_id) if item.topic_id else None, item.title,
                          item.study_date, item.minutes) for item in planned)
        after = Counter((slot["topic_id"], slot["title"], slot["study_date"], slot["minutes"]) for slot in slots)
        if before != after:
            for item in planned:
                item.status = "rescheduled"
            self.db.add_all([
                StudySession(
                    goal_id=goal.id, **{**slot, "topic_id": UUID(slot["topic_id"]) if slot["topic_id"] else None},
                ) for slot in slots
            ])
        goal_id = goal.id
        self.db.commit()
        return self.get_goal(goal_id)

    def update_session(self, goal_id, session_id, completed):
        goal = self.get_goal(goal_id, lock=True)
        item = next((session for session in goal.sessions if session.id == session_id), None)
        if item is None:
            raise HTTPException(404, "Study session not found")
        if completed and item.status != "completed":
            item.status = "completed"
            item.completed_at = datetime.now(UTC)
        elif not completed:
            item.status = "planned"
            item.completed_at = None
        self.db.commit()
        return item

    def remove(self, goal_id):
        self.lock_calendar()
        self.db.delete(self.get_goal(goal_id, lock=True, check_course=False))
        self.db.commit()

