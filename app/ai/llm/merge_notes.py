
import json

from app.ai.llm.llm_client import llm_client


MERGE_NOTES_PROMPT = """
You are an expert educational editor combining notes from multiple
consecutive chunks of ONE lecture into a complete set of study notes.

Your goal is to produce accurate, detailed, well-organized notes that
allow a student who missed the lecture to learn the material.

CORE RULE: PRESERVE INFORMATION BEFORE IMPROVING PRESENTATION.

The input contains structured notes generated from different parts of
the same lecture. Treat these notes as source material, not as a summary
that should be rewritten more concisely.

INSTRUCTIONS:

1. INFORMATION PRESERVATION
- Preserve every distinct concept, explanation, definition, example,
  analogy, formula, procedure, and factual detail in the input.
- Do not shorten a detailed explanation into a brief summary.
- Do not remove technical details simply because they appear minor.
- Never invent information to fill gaps.
- If information is unclear or contradictory, do not guess or silently
  reconcile it.

2. MERGING RELATED SECTIONS
- Combine sections only when they discuss the same underlying concept.
- When combining sections, preserve all unique information from both.
- Prefer the more complete explanation, but incorporate the useful
  details from every other explanation.
- Preserve different examples separately. Do not replace them with one
  generic example.
- Keep distinct concepts in separate sections even if they are related.
- Remove only genuinely redundant repetitions.

3. ORDER AND CONTINUITY
- Preserve the chronological order of the input chunks and their
  concepts unless a clear organizational improvement is necessary.
- Use surrounding sections to understand continuity across chunk
  boundaries.
- Do not assume that a concept is duplicated merely because similar
  terminology appears in two chunks.
- Do not discard content from a chunk simply because another chunk
  discusses a related topic.

4. EXPLANATIONS
- Retain the teaching depth of the input explanations.
- Combine complementary explanations into a coherent account.
- Preserve step-by-step reasoning and the sequence of processes.
- Do not force every section to meet a fixed word count.
- Explain only what is supported by the input notes.

5. EXAMPLES AND DEFINITIONS
- Preserve every distinct example and analogy.
- Keep definitions precise and associated with the correct concept.
- Retain formulas, variables, units, and conditions exactly as supplied,
  unless an obvious formatting correction is safe.
- Never fabricate missing formulas or definitions.

6. DIAGRAMS
- Preserve useful diagrams from the input.
- Merge diagrams only when they represent the same process and can be
  combined without losing information.
- Ensure Mermaid syntax is valid.
- For flowchart branches, use:
  B{Decision text} -->|Condition A| C[Result A]
  B -->|Condition B| D[Result B]
- For mindmaps, use indentation hierarchy without arrows.
- If a diagram cannot be safely combined, retain the most appropriate
  individual diagram rather than inventing a new process.

7. INSTRUCTOR EMPHASIS AND QUESTIONS
- Preserve all distinct instructor emphasis items, especially exam
  hints and explicitly important concepts.
- Preserve every distinct question-and-answer pair.
- Do not turn an actual student question into a generic FAQ.
- Deduplicate only exact or clearly equivalent repetitions.

8. OTHER FIELDS
- Combine learning objectives without losing distinct learning goals.
- Keep the summary as a short orientation to the lecture.
- Make revision_summary concise but cover every major section.
- Preserve common misconceptions from all input sections.
- Use empty arrays when a category has no supported content.
- Use null for mermaid_code when diagram type is "none".

9. FINAL QUALITY CHECK
Before returning the result, check that:
- Every distinct input concept appears in the output.
- No unique example, definition, formula, emphasis item, or Q&A pair
  has been accidentally omitted.
- Merged explanations have not become less detailed than their inputs.
- Related sections are combined without mixing unrelated concepts.
- The output follows the required JSON schema.
- No unsupported facts have been introduced.

Return ONLY valid JSON with exactly this structure:

{
  "title": "string",
  "summary": "string",
  "learning_objectives": ["string"],
  "sections": [
    {
      "heading": "string",
      "explanation": "string",
      "examples": [
        {
          "description": "string",
          "illustration": "string"
        }
      ],
      "definitions": [
        {
          "term": "string",
          "definition": "string"
        }
      ],
      "formulas": ["string"],
      "diagram": {
        "type": "flowchart|mindmap|none",
        "mermaid_code": "string or null"
      },
      "instructor_emphasis": ["string"],
      "common_misconceptions": ["string"]
    }
  ],
  "questions_and_answers": [
    {
      "question": "string",
      "answer": "string"
    }
  ],
  "revision_summary": "string"
}

Chunk notes:

<<<CHUNK_NOTES>>>
"""


def merge_notes(chunk_notes: list[dict]) -> dict:
    if not chunk_notes:
        raise ValueError("Cannot merge notes: no chunk notes were provided.")

    invalid_chunks = [
        index
        for index, notes in enumerate(chunk_notes)
        if not isinstance(notes, dict) or not notes
    ]

    if invalid_chunks:
        raise ValueError(
            "Cannot merge notes: empty or invalid notes for chunk(s): "
            + ", ".join(str(index + 1) for index in invalid_chunks)
        )

    chunk_notes_text = json.dumps(
        chunk_notes,
        ensure_ascii=False,
        indent=2,
    )

    prompt = MERGE_NOTES_PROMPT.replace(
        "<<<CHUNK_NOTES>>>",
        chunk_notes_text,
    )

    result = llm_client.generate_content(
        prompt=prompt,
        response_mime_type="application/json",
        max_retries=3,
        base_delay=2.0,
    )

    if not isinstance(result, dict):
        raise ValueError("Merge model did not return a JSON object.")

    required_keys = {
        "title",
        "summary",
        "learning_objectives",
        "sections",
        "questions_and_answers",
        "revision_summary",
    }

    missing_keys = required_keys - result.keys()

    if missing_keys:
        raise ValueError(
            "Merged notes are missing required keys: "
            + ", ".join(sorted(missing_keys))
        )

    if not isinstance(result["sections"], list) or not result["sections"]:
        raise ValueError("Merged notes contain no sections.")

    return result
