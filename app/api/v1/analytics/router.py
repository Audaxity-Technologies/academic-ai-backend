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