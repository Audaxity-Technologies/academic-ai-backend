from fastapi import APIRouter

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.get("/")
async def get_notes():
    return {
        "message": "Get notes"
    }


@router.get("/{note_id}")
async def get_note(note_id: int):
    return {
        "message": "Get note",
        "note_id": note_id,
    }


@router.get("/lecture/{lecture_id}")
async def get_lecture_notes(lecture_id: int):
    return {
        "message": "Get notes for lecture",
        "lecture_id": lecture_id,
    }


@router.post("/lecture/{lecture_id}/generate")
async def generate_notes(lecture_id: int):
    return {
        "message": "Generate notes",
        "lecture_id": lecture_id,
    }