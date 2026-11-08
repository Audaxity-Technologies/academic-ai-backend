from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ActivityDay(BaseModel):
    day: date
    answered: int
    correct: int
    reviews: int
    successful_recalls: int
    completed_sessions: int
    completed_planned_minutes: int


class TopicPerformance(BaseModel):
    topic_id: UUID
    title: str
    current_syllabus: bool
    correct: int
    incorrect: int
    unanswered: int


class LearningProgressResponse(BaseModel):
    course_id: UUID
    timezone: str
    from_date: date
    to_date: date
    active_days: int
    submitted_exams: int
    answered: int
    correct: int
    unanswered: int
    reviews: int
    successful_recalls: int
    completed_sessions: int
    completed_planned_minutes: int
    paper_count: int
    extracted_question_count: int
    days: list[ActivityDay]
    topics: list[TopicPerformance]

