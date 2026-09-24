from pathlib import Path
from pydantic import BaseModel

from fastapi import APIRouter, File, UploadFile

from app.ai.pipeline.lecture_pipeline import process_lecture
from app.ai.llm.notes import generate_notes_from_transcript
from app.ai.pipeline.chunking import chunk_transcript
from app.ai.export.pdf_generator import generate_pdf
from app.ai.export.html_renderer import render_html
import json
from datetime import datetime

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
    transcript: str
    filename: str = "transcript"


@router.post("/upload")
async def upload_lecture(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    result = process_lecture(str(file_path))

    return {
    "filename": file.filename,
    **result,
    }


@router.post("/transcript")
async def process_transcript(request: TranscriptRequest):
    """Process a transcript directly without transcription step."""
    # Create timestamped debug folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = DEBUG_DIR / f"{request.filename}_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"[DEBUG] Session folder: {session_dir}")
    
    transcript = request.transcript
    
    # Save transcript
    transcript_path = session_dir / "01_full_transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"[DEBUG] Saved transcript to {transcript_path}")

    chunks = chunk_transcript(transcript)
    
    # Save chunks
    chunks_path = session_dir / "02_chunks.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DEBUG] Saved {len(chunks)} chunks to {chunks_path}")

    # Generate notes
    final_notes = generate_notes_from_transcript(transcript, chunks)
    
    # Save final notes
    final_notes_path = session_dir / "04_final_notes.json"
    final_notes_path.write_text(json.dumps(final_notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DEBUG] Saved final notes to {final_notes_path}")

    # Generate PDF
    pdf_name = f"{request.filename}_notes.pdf"
    pdf_path = OUTPUT_DIR / pdf_name

    generate_pdf(
        final_notes,
        str(pdf_path)
    )

    print(f"PDF generated: {pdf_path}")

    # Generate HTML
    html_name = f"{request.filename}_notes.html"
    html_path = OUTPUT_DIR / html_name

    render_html(
        final_notes,
        str(html_path)
    )

    print(f"HTML generated: {html_path}")

    return {
        "transcript_length": len(transcript),
        "chunks": len(chunks),
        "notes": final_notes,
        "pdf": str(pdf_path),
        "html": str(html_path),
        "debug_folder": str(session_dir),
    }