from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.models.course import Course
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.user_repository import UserRepository
from app.schemas.course import CourseCreate, CourseUpdate


class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CourseRepository(db)
        self.user_repo = UserRepository(db)

    def create_course(
        self,
        data: CourseCreate,
        teacher: User,
    ) -> Course:
        existing_course = self.repo.get_by_code(data.code)

        if existing_course:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course code already exists",
            )

        course = Course(
            name=data.name,
            code=data.code,
            description=data.description,
            teacher_id=teacher.id,
            is_active=True,
        )

        self.repo.create(course)
        self.db.commit()
        self.db.refresh(course)

        return course

    def get_course(
        self,
        course_id: UUID,
        teacher: User,
    ) -> Course:
        course = self.repo.get_by_id(course_id)

        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        if course.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this course",
            )

        return course

    def list_courses(
        self,
        teacher: User,
    ) -> list[Course]:
        if teacher.role == UserRole.TEACHER:
            return self.repo.get_by_teacher(teacher.id)
        if teacher.role == UserRole.STUDENT:
            return self.repo.get_by_student(teacher.id)
        return []

    def get_course_for_user(self, course_id: UUID, user: User) -> Course:
        course = self.repo.get_by_id(course_id)

        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        if user.role == UserRole.TEACHER and course.teacher_id == user.id:
            return course
        if (
            user.role == UserRole.STUDENT
            and self.repo.is_student_enrolled(course_id, user.id)
        ):
            return course

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this course",
        )

    def enroll_student(
        self,
        course_id: UUID,
        student_email: str,
        teacher: User,
    ) -> User:
        if teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can manage course enrollment",
            )

        course = self.get_course(course_id, teacher)
        student = self.user_repo.get_by_email(student_email)

        if student is None or student.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        if not any(enrolled.id == student.id for enrolled in course.students):
            course.students.append(student)
            self.db.commit()

        return student

    def list_students(self, course_id: UUID, teacher: User) -> list[User]:
        if teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can view course enrollment",
            )

        course = self.get_course(course_id, teacher)
        return sorted(
            course.students,
            key=lambda student: student.full_name.lower(),
        )

    def unenroll_student(
        self,
        course_id: UUID,
        student_id: UUID,
        teacher: User,
    ) -> None:
        if teacher.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can manage course enrollment",
            )

        course = self.get_course(course_id, teacher)
        student = next(
            (item for item in course.students if item.id == student_id),
            None,
        )

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student is not enrolled in this course",
            )

        course.students.remove(student)
        self.db.commit()

    def update_course(
        self,
        course_id: UUID,
        data: CourseUpdate,
        teacher: User,
    ) -> Course:
        course = self.get_course(course_id, teacher)

        if data.code is not None and data.code != course.code:
            existing_course = self.repo.get_by_code(data.code)

            if existing_course and existing_course.id != course.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Course code already exists",
                )

        if data.name is not None:
            course.name = data.name

        if data.code is not None:
            course.code = data.code

        if data.description is not None:
            course.description = data.description

        if data.is_active is not None:
            course.is_active = data.is_active

        self.repo.update(course)
        self.db.commit()
        self.db.refresh(course)

        return course

    def delete_course(
        self,
        course_id: UUID,
        teacher: User,
    ) -> None:
        course = self.get_course(course_id, teacher)

        self.repo.delete(course)
        self.db.commit()
