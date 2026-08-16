from fastapi import APIRouter

router = APIRouter(
    prefix="/faculty",
    tags=["Faculty"],
)


@router.get("/")
async def get_faculty():
    return {
        "message": "Get faculty"
    }


@router.get("/{faculty_id}")
async def get_faculty_member(faculty_id: int):
    return {
        "message": "Get faculty member",
        "faculty_id": faculty_id,
    }


@router.post("/")
async def create_faculty():
    return {
        "message": "Create faculty member"
    }


@router.put("/{faculty_id}")
async def update_faculty(faculty_id: int):
    return {
        "message": "Update faculty member",
        "faculty_id": faculty_id,
    }


@router.delete("/{faculty_id}")
async def delete_faculty(faculty_id: int):
    return {
        "message": "Delete faculty member",
        "faculty_id": faculty_id,
    }