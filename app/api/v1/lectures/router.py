from fastapi import APIRouter

router = APIRouter(
    prefix="/lectures",
    tags=["Lectures"],
)


@router.post("/start")
async def start_lecture():
    return {
        "message": "Lecture started"
    }


@router.post("/{lecture_id}/stop")
async def stop_lecture(lecture_id: int):
    return {
        "message": "Lecture stopped",
        "lecture_id": lecture_id,
    }


@router.get("/")
async def get_lectures():
    return {
        "message": "Get lectures"
    }


@router.get("/{lecture_id}")
async def get_lecture(lecture_id: int):
    return {
        "message": "Get lecture",
        "lecture_id": lecture_id,
    }


@router.delete("/{lecture_id}")
async def delete_lecture(lecture_id: int):
    return {
        "message": "Delete lecture",
        "lecture_id": lecture_id,
    }