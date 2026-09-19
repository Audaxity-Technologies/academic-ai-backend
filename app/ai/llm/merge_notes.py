import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


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

{{
    "title": "Lecture title",
    "summary": "Overall lecture summary",
    "key_concepts": [
        "Concept 1",
        "Concept 2"
    ],
    "notes": [
        {{
            "heading": "Topic heading",
            "content": "Detailed explanation"
        }}
    ]
}}

Chunk notes:

{chunk_notes}
"""


def merge_notes(chunk_notes: list[dict]) -> dict:

    chunk_notes_text = json.dumps(
        chunk_notes,
        ensure_ascii=False,
        indent=2
    )

    prompt = MERGE_NOTES_PROMPT.format(
        chunk_notes=chunk_notes_text
    )

    max_retries = 3

    for attempt in range(max_retries):
        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            return json.loads(response.text)

        except Exception as e:

            print(
                f"Gemini merge attempt {attempt + 1} failed: {e}"
            )

            if attempt == max_retries - 1:
                raise

            time.sleep(5)