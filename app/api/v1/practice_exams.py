from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.practice_exam import ExamCreate, ExamDetail, ExamSubmission, ExamSummary, ExamTopic
from app.services.practice_exam_service import PracticeExamService, detail, summarize

router = APIRouter(prefix="/practice-exams", tags=["Practice exams"])


@router.get("/topics", response_model=list[ExamTopic])
def topics(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        ExamTopic(id=topic.id, title=topic.title, unit=topic.unit.title if topic.unit else None)
        for topic in PracticeExamService(db, user).topics(course_id)
    ]


@router.get("", response_model=list[ExamSummary])
def list_exams(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [summarize(exam) for exam in PracticeExamService(db, user).list_exams(course_id)]


@router.post("", response_model=ExamDetail, status_code=201)
def create_exam(body: ExamCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return detail(PracticeExamService(db, user).create(body))


@router.get("/{exam_id}", response_model=ExamDetail)
def get_exam(exam_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return detail(PracticeExamService(db, user).get_exam(exam_id))


@router.post("/{exam_id}/submit", response_model=ExamDetail)
def submit_exam(exam_id: UUID, body: ExamSubmission,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return detail(PracticeExamService(db, user).submit(exam_id, body.answers))

