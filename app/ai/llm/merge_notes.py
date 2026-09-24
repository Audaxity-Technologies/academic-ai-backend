import json

from app.ai.llm.llm_client import llm_client


MERGE_NOTES_PROMPT = """
You are an AI assistant that combines notes generated from multiple
chunks of the same lecture into ONE coherent set of study notes.

CRITICAL INSTRUCTIONS:

You are merging chunk-level notes from the SAME continuous lecture. Chunks may have overlapping content at their boundaries — merge overlapping sections into one, keeping the more detailed/complete version of any duplicated explanation, never the shorter one.

Do not summarize the merged sections down — if two chunks each explain part of the same concept, COMBINE the explanations into one complete, longer explanation. The output should be as detailed as the sum of the inputs, not a condensed version of them.

Preserve all examples, diagrams, Q&A pairs, and instructor_emphasis items from every chunk — deduplicate only exact repeats, never merge two different examples into one abstracted example.

Reconstruct a single logical ordering for the whole lecture, regardless of chunk order given.

Do not invent information that is not present in the chunk notes.

Return ONLY valid JSON in exactly this format:

{
  "title": "string",
  "summary": "string — 3-5 sentences, orientation only, not a replacement for the sections",
  "learning_objectives": ["string", ...],
  "sections": [
    {
      "heading": "string",
      "explanation": "string — full teaching-depth explanation, 150-300 words",
      "examples": [
        {"description": "string", "illustration": "string — the instructor's actual example/analogy reproduced in substance"}
      ],
      "definitions": [
        {"term": "string", "definition": "string"}
      ],
      "formulas": ["string", ...],
      "diagram": {"type": "flowchart|mindmap|none", "mermaid_code": "string or null"},
      "instructor_emphasis": ["string", ...],
      "common_misconceptions": ["string", ...]
    }
  ],
  "questions_and_answers": [
    {"question": "string", "answer": "string"}
  ],
  "revision_summary": "string — condensed, exam-oriented recap covering every section in a few sentences each"
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