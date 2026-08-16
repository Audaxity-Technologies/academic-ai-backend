from fastapi import APIRouter

from app.api.v1.health.router import router as health_router
from app.api.v1.institutions.router import router as institution_router
from app.api.v1.users.router import router as users_router
from app.api.v1.courses.router import router as courses_router
from app.api.v1.departments.router import router as departments_router
from app.api.v1.faculty.router import router as faculty_router
from app.api.v1.students.router import router as students_router
from app.api.v1.lectures.router import router as lectures_router
from app.api.v1.notes.router import router as notes_router

from app.api.v1.search.router import router as search_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.notifications.router import router as notifications_router
api_router = APIRouter(
    prefix="/api/v1",
)


api_router.include_router(health_router)
api_router.include_router(institution_router)
api_router.include_router(users_router)
api_router.include_router(courses_router)
api_router.include_router(departments_router)
api_router.include_router(faculty_router)
api_router.include_router(students_router)
api_router.include_router(lectures_router)
api_router.include_router(notes_router)
api_router.include_router(search_router)
api_router.include_router(analytics_router)
api_router.include_router(notifications_router)