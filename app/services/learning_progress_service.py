from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import DateTime, cast, func, select

from app.ai.syllabus.alignment import topic_scope
from app.models.flashcard import Flashcard, FlashcardReview
from app.models.practice_exam import PracticeExam
from app.models.question_paper import QuestionPaper
from app.models.study_plan import StudyGoal, StudySession
from app.models.syllabus import SyllabusTopic
from app.services.syllabus_alignment_service import active_version

COUNTERS = (
    "answered", "correct", "reviews", "successful_recalls",
    "completed_sessions", "completed_planned_minutes",
)


def aggregate_activity(exams, reviews, sessions, zone, first, last):
    days = {}
    day = first
    while day <= last:
        days[day] = {"day": day, **dict.fromkeys(COUNTERS, 0)}
        day += timedelta(days=1)
    topics = defaultdict(lambda: {"correct": 0, "incorrect": 0, "unanswered": 0})
    unanswered = submitted_exams = 0
    for exam in exams:
        result = exam.result
        submitted = datetime.fromisoformat(result["submitted_at"]).astimezone(zone).date()
        if submitted not in days:
            continue
        submitted_exams += 1
        stats = days[submitted]
        for question, feedback in zip(exam.questions, result["feedback"]):
            topic = topics[UUID(question["topic_id"])]
            if feedback["choice"] is None:
                topic["unanswered"] += 1
                unanswered += 1
            else:
                stats["answered"] += 1
                if feedback["correct"]:
                    topic["correct"] += 1
                    stats["correct"] += 1
                else:
                    topic["incorrect"] += 1
    for review in reviews:
        day = review.reviewed_at.astimezone(zone).date()
        if day in days:
            days[day]["reviews"] += 1
            days[day]["successful_recalls"] += int(review.rating >= 3)
    for session in sessions:
        day = session.completed_at.astimezone(zone).date()
        if day in days:
            days[day]["completed_sessions"] += 1
            days[day]["completed_planned_minutes"] += session.minutes
    totals = {key: sum(item[key] for item in days.values()) for key in COUNTERS}
    return {
        **totals, "submitted_exams": submitted_exams, "unanswered": unanswered,
        "active_days": sum(bool(row["answered"] or row["reviews"] or row["completed_sessions"])
                           for row in days.values()),
        "days": list(days.values()),
    }, topics


def learning_progress(db, user_id, course_id, zone, period):
    now = datetime.now(UTC)
    last = now.astimezone(zone).date()
    first = last - timedelta(days=period - 1)
    start = datetime.combine(first, time.min, tzinfo=zone)
    submitted = cast(PracticeExam.result["submitted_at"].as_string(), DateTime(timezone=True))
    exams = db.scalars(select(PracticeExam).where(
        PracticeExam.user_id == user_id, PracticeExam.course_id == course_id,
        submitted >= start, submitted <= now,
    ))
    reviews = db.scalars(select(FlashcardReview).join(Flashcard).where(
        Flashcard.user_id == user_id, Flashcard.course_id == course_id,
        FlashcardReview.reviewed_at >= start, FlashcardReview.reviewed_at <= now,
    ))
    sessions = db.scalars(select(StudySession).join(StudyGoal).where(
        StudyGoal.user_id == user_id, StudyGoal.course_id == course_id,
        StudySession.status == "completed", StudySession.completed_at >= start, StudySession.completed_at <= now,
    ))
    result, topic_counts = aggregate_activity(exams, reviews, sessions, zone, first, last)
    titles = {}
    current = set()
    if topic_counts:
        titles = dict(db.execute(select(SyllabusTopic.id, SyllabusTopic.title).where(
            SyllabusTopic.course_id == course_id, SyllabusTopic.id.in_(topic_counts)
        )).all())
        current = set(db.scalars(topic_scope(course_id, active_version(db, course_id))
                                 .with_only_columns(SyllabusTopic.id).where(SyllabusTopic.id.in_(topic_counts))))
    paper_count, question_count = db.execute(select(
        func.count(QuestionPaper.id), func.coalesce(func.sum(func.jsonb_array_length(QuestionPaper.questions)), 0)
    ).where(QuestionPaper.user_id == user_id, QuestionPaper.course_id == course_id)).one()
    topics = [
        {"topic_id": topic_id, "title": titles.get(topic_id, "Archived topic"),
         "current_syllabus": topic_id in current, **counts}
        for topic_id, counts in topic_counts.items()
    ]
    topics.sort(key=lambda item: (-item["incorrect"], item["title"], str(item["topic_id"])))
    return {
        **result, "course_id": course_id, "timezone": zone.key, "from_date": first, "to_date": last,
        "paper_count": paper_count, "extracted_question_count": question_count, "topics": topics,
    }

