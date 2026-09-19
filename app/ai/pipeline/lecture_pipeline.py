from pathlib import Path

from app.ai.speech.transcription import transcribe_audio
from app.ai.llm.notes import generate_notes
from app.ai.llm.merge_notes import merge_notes
from app.ai.pipeline.chunking import chunk_transcript
from app.ai.export.pdf_generator import generate_pdf


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def process_lecture(file_path: str) -> dict:
    transcription_result = transcribe_audio(file_path)

    transcript = transcription_result["transcript"]

    chunks = chunk_transcript(transcript)

    all_notes = []

    for index, chunk in enumerate(chunks):
        print(f"Processing chunk {index + 1}/{len(chunks)}")

        chunk_notes = generate_notes(chunk)

        all_notes.append(chunk_notes)

    print("Merging chunk notes...")

    final_notes = merge_notes(all_notes)

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
    }