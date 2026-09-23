import json

from app.ai.llm.llm_client import llm_client


MERGE_NOTES_PROMPT = """
You are an AI assistant that combines notes generated from multiple
chunks of the same lecture into ONE coherent set of study notes.

Rules:
- Combine overlapping information.
- Remove duplicate concepts and repeated explanations.
- Preserve important technical terms, definitions, examples, formulas,
  and explanations.
- Maintain the logical order of the lecture.
- Do not invent information that is not present in the chunk notes.
- Create a clear and concise overall summary.
- Extract the most important key concepts.
- Combine related sections where appropriate.

Return ONLY valid JSON in exactly this format:

{
    "title": "Lecture title",
    "summary": "Overall lecture summary",
    "key_concepts": [
        "Concept 1",
        "Concept 2"
    ],
    "notes": [
        {
            "heading": "Topic heading",
            "content": "Detailed explanation"
        }
    ]
}

Chunk notes:

<<<CHUNK_NOTES>>>
"""

def merge_notes(chunk_notes: list[dict]) -> dict:

    chunk_notes_text = json.dumps(
        chunk_notes,
        ensure_ascii=False,
        indent=2
    )

    prompt = MERGE_NOTES_PROMPT.replace("<<<CHUNK_NOTES>>>", chunk_notes_text)

    result = llm_client.generate_content(
        prompt=prompt,
        response_mime_type="application/json",
        max_retries=3,
        base_delay=2.0
    )

    return result