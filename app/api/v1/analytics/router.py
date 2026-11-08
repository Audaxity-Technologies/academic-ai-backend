from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.learning_progress import LearningProgressResponse
from app.services.course_service import CourseService
from app.services.learning_progress_service import learning_progress

from fastapi import APIRouter

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/student")
async def get_student_analytics():
    return {
        "message": "Get student analytics",
        "data": {},
    }


@router.get("/faculty")
async def get_faculty_analytics():
    return {
        "message": "Get faculty analytics",
        "data": {},
    }


@router.get("/department")
async def get_department_analytics():
    return {
        "message": "Get department analytics",
        "data": {},
    }

@router.get("/learning-progress", response_model=LearningProgressResponse)
def get_learning_progress(course_id: UUID, days: Literal["7", "30", "90"] = "30",
                          timezone: str = Query("UTC", min_length=1, max_length=80),
                          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    CourseService(db).get_course_for_user(course_id, user)
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(422, "Choose a supported IANA time zone") from exc
    return learning_progress(db, user.id, course_id, zone, int(days))
