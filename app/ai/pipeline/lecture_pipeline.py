from app.ai.speech.transcription import transcribe_audio
from app.ai.llm.notes import generate_notes
from app.ai.pipeline.chunking import chunk_transcript


def process_lecture(file_path: str) -> dict:
    transcription_result = transcribe_audio(file_path)

    transcript = transcription_result["transcript"]

    chunks = chunk_transcript(transcript)

    all_notes = []

    for index, chunk in enumerate(chunks):
        print(f"Processing chunk {index + 1}/{len(chunks)}")

        chunk_notes = generate_notes(chunk)

        all_notes.append(chunk_notes)

    return {
        "transcript": transcript,
        "language": transcription_result.get("language"),
        "chunks": len(chunks),
        "notes": all_notes,
    }