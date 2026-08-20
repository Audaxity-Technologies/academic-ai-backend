from app.ai.speech.transcription import transcribe_audio
from app.ai.llm.notes import generate_notes


def process_lecture(file_path: str) -> dict:
    transcript = transcribe_audio(file_path)

    notes = generate_notes(transcript)

    return {
        "transcript": transcript,
        "notes": notes,
    }