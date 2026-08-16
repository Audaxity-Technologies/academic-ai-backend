from fastapi import APIRouter

router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


@router.get("/")
async def get_students():
    return {
        "message": "Get students"
    }


@router.get("/{student_id}")
async def get_student(student_id: int):
    return {
        "message": "Get student",
        "student_id": student_id,
    }


@router.post("/")
async def create_student():
    return {
        "message": "Create student"
    }


@router.put("/{student_id}")
async def update_student(student_id: int):
    return {
        "message": "Update student",
        "student_id": student_id,
    }


@router.delete("/{student_id}")
async def delete_student(student_id: int):
    return {
        "message": "Delete student",
        "student_id": student_id,
    }