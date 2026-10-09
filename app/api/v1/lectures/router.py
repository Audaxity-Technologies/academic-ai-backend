
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
from app.ai.pipeline.syllabus_mapping import process_syllabus_mapping

from app.repositories.syllabus_repository import SyllabusRepository
from app.repositories.syllabus_mapping_repository import (
    SyllabusMappingRepository,
)


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


def run_syllabus_mapping(
    db: Session,
    lecture_id: UUID,
    course_id: UUID,
    lecture_notes: dict,
) -> dict:
    """
    Fetch course syllabus topics, run AI mapping,
    and persist the results for this lecture.
    """
    syllabus_repository = SyllabusRepository(db)
    topics = syllabus_repository.get_by_course(course_id)

    if not topics:
        print(
            f"[SYLLABUS] No syllabus topics found for course {course_id}"
        )
        return {
            "mappings": [],
            "coverage_percentage": 0.0,
            "message": "No syllabus topics configured for this course.",
        }

    # Map topic titles to their database UUIDs.
    topic_records = {
        topic.title: topic.id
        for topic in topics
    }

    result = process_syllabus_mapping(
        syllabus_topics=[topic.title for topic in topics],
        lecture_notes=lecture_notes,
    )

    # Validate that each returned topic belongs to this course.
    expected_titles = set(topic_records)
    returned_titles = [
        item["syllabus_topic"]
        for item in result["mappings"]
    ]

    if (
        len(returned_titles) != len(expected_titles)
        or set(returned_titles) != expected_titles
    ):
        raise ValueError(
            "Syllabus mapper did not return exactly one result "
            "for every syllabus topic."
        )

    mapping_repository = SyllabusMappingRepository(db)

    mapping_repository.save_mappings(
        lecture_id=lecture_id,
        topic_records=topic_records,
        mappings=result["mappings"],
    )

    print(
        f"[SYLLABUS] Mapping completed for lecture {lecture_id}: "
        f"{result['coverage_percentage']}%"
    )

    return result


@router.post("/upload")
async def upload_lecture(
    course_id: UUID = Form(...),
    title: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Audio upload pipeline:
    1. Save audio
    2. Create lecture
    3. Transcribe audio and generate notes
    4. Save transcript and notes
    5. Map notes against course syllabus
    6. Save mapping results and complete lecture
    """
    safe_filename = Path(file.filename or "lecture_audio").name
    file_path = UPLOAD_DIR / safe_filename

    lecture_service = LectureService(db)
    lecture = None

    try:
        with file_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        lecture_title = title or Path(safe_filename).stem

        lecture = lecture_service.create_lecture(
            course_id=course_id,
            title=lecture_title,
            source_type=LectureSourceType.AUDIO,
            source_path=str(file_path),
        )

        result = process_lecture(str(file_path))

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

        lecture_service.save_note(
            lecture=lecture,
            title=result["notes"].get("title", lecture_title),
            content=result["notes"],
            pdf_path=result["pdf"],
            html_path=result["html"],
        )

        # Syllabus mapping happens after notes are generated.
        mapping_result = run_syllabus_mapping(
            db=db,
            lecture_id=lecture.id,
            course_id=course_id,
            lecture_notes=result["notes"],
        )

        lecture.debug_path = result["debug_folder"]
        lecture_service.mark_completed(lecture)

        db.commit()

        return {
            "lecture_id": str(lecture.id),
            "status": "completed",
            "transcript": result["transcript"],
            "notes": result["notes"],
            "pdf": result["pdf"],
            "html": result["html"],
            "syllabus_mapping": mapping_result,
        }

    except Exception:
        db.rollback()

        if lecture is not None:
            try:
                lecture_service.mark_failed(lecture)
                db.commit()
            except Exception:
                db.rollback()

        raise

    finally:
        await file.close()


@router.post("/transcript")
async def process_transcript(
    request: TranscriptRequest,
    db: Session = Depends(get_db),
):
    """
    Direct transcript pipeline:
    1. Save transcript and generate notes
    2. Generate PDF and HTML
    3. Save lecture, transcript and notes
    4. Map notes against the course syllabus
    5. Persist mapping results
    """
    safe_filename = Path(request.filename).stem or "transcript"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    session_dir = DEBUG_DIR / f"{safe_filename}_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript = request.transcript
    transcript_path = session_dir / "01_full_transcript.txt"

    lecture_service = LectureService(db)
    lecture = None

    try:
        transcript_path.write_text(
            transcript,
            encoding="utf-8",
        )

        chunks = chunk_transcript(transcript)

        (session_dir / "02_chunks.json").write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        final_notes = generate_notes_from_transcript(
            transcript,
            chunks,
        )

        (session_dir / "04_final_notes.json").write_text(
            json.dumps(final_notes, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        pdf_path = OUTPUT_DIR / f"{safe_filename}_{timestamp}_notes.pdf"
        html_path = OUTPUT_DIR / f"{safe_filename}_{timestamp}_notes.html"

        generate_pdf(final_notes, str(pdf_path))
        render_html(final_notes, str(html_path))

        lecture_title = request.title or safe_filename

        lecture = lecture_service.create_lecture(
            course_id=request.course_id,
            title=lecture_title,
            source_type=LectureSourceType.TRANSCRIPT,
        )

        lecture_service.save_transcript(
            lecture=lecture,
            content=transcript,
            language=None,
            transcript_path=str(transcript_path),
        )

        lecture_service.save_note(
            lecture=lecture,
            title=final_notes.get("title", lecture_title),
            content=final_notes,
            pdf_path=str(pdf_path),
            html_path=str(html_path),
        )

        mapping_result = run_syllabus_mapping(
            db=db,
            lecture_id=lecture.id,
            course_id=request.course_id,
            lecture_notes=final_notes,
        )

        lecture.debug_path = str(session_dir)
        lecture_service.mark_completed(lecture)

        db.commit()

        return {
            "lecture_id": str(lecture.id),
            "status": "completed",
            "transcript_length": len(transcript),
            "chunks": len(chunks),
            "notes": final_notes,
            "pdf": str(pdf_path),
            "html": str(html_path),
            "debug_folder": str(session_dir),
            "syllabus_mapping": mapping_result,
        }

    except Exception:
        db.rollback()

        if lecture is not None:
            try:
                lecture_service.mark_failed(lecture)
                db.commit()
            except Exception:
                db.rollback()

        raise
