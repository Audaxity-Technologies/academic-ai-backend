from pathlib import Path
import json
from datetime import datetime

from app.ai.speech.transcription import transcribe_audio
from app.ai.llm.notes import generate_notes_from_transcript
from app.ai.pipeline.chunking import chunk_transcript
from app.ai.export.pdf_generator import generate_pdf


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

DEBUG_DIR = Path("debug_outputs")
DEBUG_DIR.mkdir(exist_ok=True)


def process_lecture(file_path: str) -> dict:
    # Create timestamped debug folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = DEBUG_DIR / f"{Path(file_path).stem}_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"[DEBUG] Session folder: {session_dir}")
    
    transcription_result = transcribe_audio(file_path)

    transcript = transcription_result["transcript"]
    
    # Save full transcript
    transcript_path = session_dir / "01_full_transcript.txt"
    transcript_path.write_text(transcript, encoding="utf-8")
    print(f"[DEBUG] Saved transcript to {transcript_path}")

    chunks = chunk_transcript(transcript)
    
    # Save chunks
    chunks_path = session_dir / "02_chunks.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DEBUG] Saved {len(chunks)} chunks to {chunks_path}")

    # Generate notes using the new chunk-aware function
    final_notes = generate_notes_from_transcript(transcript, chunks)
    
    # Save final notes
    final_notes_path = session_dir / "04_final_notes.json"
    final_notes_path.write_text(json.dumps(final_notes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DEBUG] Saved final notes to {final_notes_path}")

    # Generate PDF
    pdf_name = f"{Path(file_path).stem}_notes.pdf"
    pdf_path = OUTPUT_DIR / pdf_name

    generate_pdf(
        final_notes,
        str(pdf_path)
    )

    print(f"PDF generated: {pdf_path}")

    return {
        "transcript": transcript,
        "language": transcription_result.get("language"),
        "chunks": len(chunks),
        "notes": final_notes,
        "pdf": str(pdf_path),
        "debug_folder": str(session_dir),
    }