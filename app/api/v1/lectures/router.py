from pathlib import Path
from uuid import UUID
from datetime import datetime
import json

from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.dependencies.database import get_db
from app.services.lecture_service import LectureService
from app.core.constants import LectureSourceType, LectureStatus

from app.ai.pipeline.lecture_pipeline import process_lecture
from app.ai.llm.notes import generate_notes_from_transcript
from app.ai.pipeline.chunking import chunk_transcript
from app.ai.export.pdf_generator import generate_pdf
from app.ai.export.html_renderer import render_html


router = APIRouter(
    prefix="/lectures",
    tags=["Lectures"],
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

DEBUG_DIR = Path("debug_outputs")
DEBUG_DIR.mkdir(exist_ok=True)


class TranscriptRequest(BaseModel):
    course_id: UUID
    transcript: str
    filename: str = "transcript"
    title: str | None = None


@router.post("/upload")
async def upload_lecture(
    course_id: UUID = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an audio lecture.

    Flow:
    1. Save uploaded audio file
    2. Create Lecture row
    3. Run existing AI lecture pipeline
    4. Save Transcript row
    5. Save Note row
    6. Update Lecture paths/status
    7. Commit everything to database
    """

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    lecture_service = LectureService(db)

    lecture_title = title or Path(file.filename).stem

    lecture = lecture_service.create_lecture(
        course_id=course_id,
        title=lecture_title,
        source_type=LectureSourceType.AUDIO,
        source_path=str(file_path),
    )

    try:
        # Existing AI pipeline remains unchanged.
        result = process_lecture(str(file_path))

        # Save transcript in database.
        lecture_service.save_transcript(
            lecture=lecture,
            content=result["transcript"],
            language=result.get("language"),
            transcript_path=str(
                DEBUG_DIR
                / Path(result["debug_folder"]).name
                / "01_full_transcript.txt"
            ),
        )

        # Save generated notes in database.
        lecture_service.save_note(
            lecture=lecture,
            title=result["notes"].get(
                "title",
                lecture_title,
            ),
            content=result["notes"],
            pdf_path=result["pdf"],
            html_path=result["html"],
        )

        lecture.debug_path = result["debug_folder"]

        # Mark lecture as successfully completed.
        lecture_service.mark_completed(lecture)

        db.commit()

        return {
            "lecture": lecture,
            "transcript": result["transcript"],
            "notes": result["notes"],
            "pdf": result["pdf"],
            "html": result["html"],
        }

    except Exception:
        db.rollback()

        lecture.status = LectureStatus.FAILED

        db.add(lecture)
        db.commit()

        raise


@router.post("/transcript")
async def process_transcript(
    request: TranscriptRequest,
    db: Session = Depends(get_db),
):
    """
    Process a transcript directly without the audio transcription step.

    Flow:
    1. Create debug/session folder
    2. Save transcript
    3. Chunk transcript
    4. Generate notes
    5. Generate PDF
    6. Generate HTML
    7. Create Lecture row
    8. Create Transcript row
    9. Create Note row
    10. Mark Lecture completed
    11. Commit everything to database
    """

    # Create timestamped debug folder.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    session_dir = DEBUG_DIR / (
        f"{request.filename}_{timestamp}"
    )

    session_dir.mkdir(exist_ok=True)

    print(f"[DEBUG] Session folder: {session_dir}")

    transcript = request.transcript

    # Save full transcript.
    transcript_path = session_dir / "01_full_transcript.txt"

    transcript_path.write_text(
        transcript,
        encoding="utf-8",
    )

    print(
        f"[DEBUG] Saved transcript to {transcript_path}"
    )

    # Chunk transcript.
    chunks = chunk_transcript(transcript)

    chunks_path = session_dir / "02_chunks.json"

    chunks_path.write_text(
        json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"[DEBUG] Saved {len(chunks)} chunks to {chunks_path}"
    )

    # Generate notes.
    final_notes = generate_notes_from_transcript(
        transcript,
        chunks,
    )

    # Save final notes JSON.
    final_notes_path = session_dir / "04_final_notes.json"

    final_notes_path.write_text(
        json.dumps(
            final_notes,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"[DEBUG] Saved final notes to {final_notes_path}"
    )

    # Generate PDF.
    pdf_name = f"{request.filename}_notes.pdf"

    pdf_path = OUTPUT_DIR / pdf_name

    generate_pdf(
        final_notes,
        str(pdf_path),
    )

    print(f"PDF generated: {pdf_path}")

    # Generate HTML.
    html_name = f"{request.filename}_notes.html"

    html_path = OUTPUT_DIR / html_name

    render_html(
        final_notes,
        str(html_path),
    )

    print(f"HTML generated: {html_path}")

    # -----------------------------
    # DATABASE PERSISTENCE
    # -----------------------------

    lecture_service = LectureService(db)

    lecture_title = request.title or request.filename

    # Create lecture.
    lecture = lecture_service.create_lecture(
        course_id=request.course_id,
        title=lecture_title,
        source_type=LectureSourceType.TRANSCRIPT,
    )

    try:
        # Save transcript.
        lecture_service.save_transcript(
            lecture=lecture,
            content=transcript,
            language=None,
            transcript_path=str(transcript_path),
        )

        # Save notes.
        lecture_service.save_note(
            lecture=lecture,
            title=final_notes.get(
                "title",
                lecture_title,
            ),
            content=final_notes,
            pdf_path=str(pdf_path),
            html_path=str(html_path),
        )

        # Save debug folder path.
        lecture.debug_path = str(session_dir)

        # Mark lecture completed.
        lecture_service.mark_completed(lecture)

        # Commit lecture + transcript + note.
        db.commit()

        return {
            "lecture_id": str(lecture.id),
            "transcript_length": len(transcript),
            "chunks": len(chunks),
            "notes": final_notes,
            "pdf": str(pdf_path),
            "html": str(html_path),
            "debug_folder": str(session_dir),
        }

    except Exception:
        db.rollback()

        lecture.status = LectureStatus.FAILED

        db.add(lecture)
        db.commit()

        raise