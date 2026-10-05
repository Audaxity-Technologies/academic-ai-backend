import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


SYLLABUS_MAPPING_PROMPT = """
You are an academic curriculum mapping assistant.

Your task is to determine which syllabus topics were actually
covered in a lecture based on the lecture notes.

IMPORTANT RULES:

1. Every syllabus topic must appear exactly once.
2. Do not assume a topic was taught merely because it was mentioned.
3. "covered" means the lecture substantially teaches the topic.
4. "partially_covered" means only part of the topic was taught.
5. "mentioned" means the topic was referenced but not meaningfully taught.
6. "not_covered" means there is insufficient evidence that the topic was taught.
7. Do not invent information.
8. Evidence must come only from the lecture notes.
9. Confidence must be between 0 and 1.

SYLLABUS TOPICS:
{syllabus}

LECTURE NOTES:
{lecture_notes}

Return ONLY valid JSON in exactly this format:

{{
    "mappings": [
        {{
            "syllabus_topic": "Topic name",
            "status": "covered",
            "confidence": 0.95,
            "evidence": [
                "Evidence from the lecture notes"
            ]
        }}
    ]
}}
"""


def map_syllabus(
    syllabus_topics: list[str],
    lecture_notes: dict
) -> dict:

    prompt = SYLLABUS_MAPPING_PROMPT.format(
        syllabus=json.dumps(
            syllabus_topics,
            ensure_ascii=False
        ),
        lecture_notes=json.dumps(
            lecture_notes,
            ensure_ascii=False
        )
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)