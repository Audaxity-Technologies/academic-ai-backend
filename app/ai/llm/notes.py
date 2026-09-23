from app.ai.llm.prompts import LECTURE_NOTES_PROMPT
from app.ai.llm.llm_client import llm_client


def generate_notes(transcript: str) -> dict:
    prompt = LECTURE_NOTES_PROMPT.replace("<<<TRANSCRIPT>>>", transcript)

    notes = llm_client.generate_content(
        prompt=prompt,
        response_mime_type="application/json",
        max_retries=3,
        base_delay=2.0
    )

    return notes