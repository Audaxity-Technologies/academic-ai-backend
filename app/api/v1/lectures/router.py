from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.ai.speech.transcription import transcribe_audio


router = APIRouter(
    prefix="/lectures",
    tags=["Lectures"],
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_lecture(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    result = transcribe_audio(str(file_path))

    return {
        "filename": file.filename,
        "language": result["language"],
        "transcript": result["transcript"],
    }