from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.syllabus_coverage import (
    AlignmentQueued, CourseProgress, LectureCoverage, LectureSummary, TopicProgress,
)
from app.services.course_service import CourseService
from app.services.material_access import authorize_note
from app.services.note_service import NoteService
from app.services.syllabus_alignment_service import run_lecture_alignment
from app.services.syllabus_coverage_service import checked_version, course_progress, lecture_progress

router = APIRouter(tags=["Syllabus coverage"])


@router.get("/courses/{course_id}/syllabus/progress", response_model=CourseProgress)
def progress(course_id: UUID, version_id: UUID | None = None, legacy: bool = False,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    CourseService(db).get_course_for_user(course_id, user)
    version = checked_version(db, course_id, version_id, legacy)
    return course_progress(db, course_id, version, user)


@router.get("/courses/{course_id}/syllabus/remaining", response_model=list[TopicProgress])
def remaining(course_id: UUID, version_id: UUID | None = None, legacy: bool = False,
              offset: int = Query(0, ge=0), limit: int | None = Query(None, ge=1, le=200),
              db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = progress(course_id, version_id, legacy, db, user)
    priority = {"not_covered": 0, "partially_covered": 1, "mentioned": 2}
    topics = sorted((topic for unit in report["units"] for topic in unit["topics"]
                   if topic["status"] in priority), key=lambda topic: priority[topic["status"]])
    return topics[offset:offset + limit if limit is not None else None]


@router.get("/lectures/{lecture_id}/syllabus-mapping", response_model=LectureCoverage)
def mapping(lecture_id: UUID, version_id: UUID | None = None, legacy: bool = False,
            offset: int = Query(0, ge=0), limit: int | None = Query(None, ge=1, le=200),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = authorize_note(db, user, NoteService(db).get_lecture_note(lecture_id))
    result = lecture_progress(db, note.lecture, version_id, legacy)
    result["mappings"] = result["mappings"][offset:offset + limit if limit is not None else None]
    return result


@router.get("/lectures/{lecture_id}/syllabus-summary", response_model=LectureSummary)
def summary(lecture_id: UUID, version_id: UUID | None = None, legacy: bool = False,
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = authorize_note(db, user, NoteService(db).get_lecture_note(lecture_id))
    return lecture_progress(db, note.lecture, version_id, legacy)


@router.post("/lectures/{lecture_id}/syllabus-mapping/retry", status_code=202,
             response_model=AlignmentQueued)
def retry(lecture_id: UUID, tasks: BackgroundTasks,
          db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    note = authorize_note(db, user, NoteService(db).get_lecture_note(lecture_id))
    lecture = note.lecture
    CourseService(db).get_course(lecture.course_id, user)
    if not lecture.transcript:
        raise HTTPException(409, "This lecture has no saved transcript.")
    try:
        db.refresh(lecture, with_for_update={"nowait": True})
    except OperationalError as exc:
        sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
        if sqlstate != "55P03":
            raise
        db.rollback()
        raise HTTPException(409, "Alignment is already running for this lecture.") from exc
    lecture.alignment_status = "pending"
    lecture.alignment_error = None
    db.commit()
    tasks.add_task(run_lecture_alignment, lecture.id)
    return {"status": "pending"}

