from app.ai.llm.prompts import LECTURE_NOTES_PROMPT
from app.ai.llm.llm_client import llm_client
from app.ai.llm.merge_notes import merge_notes
import json


def generate_notes(transcript: str) -> dict:
    """Generate notes from a transcript chunk."""
    prompt = LECTURE_NOTES_PROMPT.replace("<<<TRANSCRIPT>>>", transcript)

    try:
        notes = llm_client.generate_content(
            prompt=prompt,
            response_mime_type="application/json",
            max_retries=3,
            base_delay=2.0
        )
        return notes
    except json.JSONDecodeError as e:
        print(f"[NOTES] JSON parsing failed: {e}")
        print(f"[NOTES] This may indicate the LLM returned malformed JSON")
        raise
    except Exception as e:
        print(f"[NOTES] Error generating notes: {type(e).__name__}: {e}")
        raise


def generate_notes_from_transcript(transcript: str, chunks: list[str]) -> dict:
    """
    Generate notes from a full transcript, handling chunking logic.
    
    If chunks is a single element (below threshold), generate notes directly.
    If multiple chunks, generate per-chunk notes then merge.
    """
    if len(chunks) == 1:
        print(f"[NOTES] Single chunk detected, generating notes directly")
        return generate_notes(chunks[0])
    
    print(f"[NOTES] Multiple chunks detected ({len(chunks)}), generating per-chunk notes")
    chunk_notes = []
    
    for i, chunk in enumerate(chunks):
        print(f"[NOTES] Processing chunk {i+1}/{len(chunks)}")
        try:
            notes = generate_notes(chunk)
            chunk_notes.append(notes)
        except Exception as e:
            print(f"[NOTES] Failed to generate notes for chunk {i+1}: {e}")
            # Continue with other chunks even if one fails
            chunk_notes.append({})
    
    print(f"[NOTES] Merging {len(chunk_notes)} chunk notes")
    return merge_notes(chunk_notes)