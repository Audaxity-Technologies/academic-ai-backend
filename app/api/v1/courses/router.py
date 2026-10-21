from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseStudentEnrollment,
    CourseUpdate,
)
from app.schemas.user import UserResponse
from app.services.course_service import CourseService

from app.schemas.syllabus import (
    SyllabusTopicCreate,
    SyllabusTopicResponse,
    SyllabusTopicUpdate,
)
from app.services.syllabus_service import SyllabusService

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(db)

    return service.create_course(
        data=data,
        teacher=current_user,
    )


@router.get(
    "/",
    response_model=list[CourseResponse],
)
def get_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(db)

    return service.list_courses(
        teacher=current_user,
    )


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(db)

    return service.get_course_for_user(course_id=course_id, user=current_user)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: UUID,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(db)

    return service.update_course(
        course_id=course_id,
        data=data,
        teacher=current_user,
    )


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CourseService(db)

    service.delete_course(
        course_id=course_id,
        teacher=current_user,
    )


@router.post(
    "/{course_id}/students",
    response_model=UserResponse,
)
def enroll_student(
    course_id: UUID,
    request: CourseStudentEnrollment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CourseService(db).enroll_student(
        course_id=course_id,
        student_email=str(request.email),
        teacher=current_user,
    )


@router.get(
    "/{course_id}/students",
    response_model=list[UserResponse],
)
def list_course_students(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CourseService(db).list_students(course_id, current_user)


@router.delete(
    "/{course_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unenroll_student(
    course_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    CourseService(db).unenroll_student(
        course_id=course_id,
        student_id=student_id,
        teacher=current_user,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post(
    "/{course_id}/syllabus",
    response_model=SyllabusTopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_syllabus_topic(
    course_id: UUID,
    data: SyllabusTopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SyllabusService(db)

    return service.create_topic(
        course_id=course_id,
        data=data,
        teacher=current_user,
    )


@router.get(
    "/{course_id}/syllabus",
    response_model=list[SyllabusTopicResponse],
)
def get_syllabus(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SyllabusService(db)

    return service.list_topics(
        course_id=course_id,
        teacher=current_user,
    )


@router.put(
    "/{course_id}/syllabus/{topic_id}",
    response_model=SyllabusTopicResponse,
)
def update_syllabus_topic(
    course_id: UUID,
    topic_id: UUID,
    data: SyllabusTopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SyllabusService(db)

    return service.update_topic(
        course_id=course_id,
        topic_id=topic_id,
        data=data,
        teacher=current_user,
    )


@router.delete(
    "/{course_id}/syllabus/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_syllabus_topic(
    course_id: UUID,
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SyllabusService(db)

    service.delete_topic(
        course_id=course_id,
        topic_id=topic_id,
        teacher=current_user,
    )
