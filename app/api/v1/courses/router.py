from fastapi import APIRouter

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.get("/")
async def get_courses():
    return {
        "message": "Get courses"
    }


@router.get("/{course_id}")
async def get_course(course_id: int):
    return {
        "message": "Get course",
        "course_id": course_id,
    }


@router.post("/")
async def create_course():
    return {
        "message": "Create course"
    }


@router.put("/{course_id}")
async def update_course(course_id: int):
    return {
        "message": "Update course",
        "course_id": course_id,
    }


@router.delete("/{course_id}")
async def delete_course(course_id: int):
    return {
        "message": "Delete course",
        "course_id": course_id,
    }