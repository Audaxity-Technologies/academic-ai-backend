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
You are an academic syllabus coverage evaluator.

Your task is to determine which syllabus topics were ACTUALLY TAUGHT
in a lecture based ONLY on the provided lecture notes.

The goal is NOT to find general academic relationships between topics.

For EVERY syllabus topic, answer this question:

"Did this lecture actually teach this specific syllabus topic?"

IMPORTANT RULES:

1. Evaluate EVERY syllabus topic exactly once.

2. Use ONLY the provided lecture notes as evidence.

3. Do NOT use general academic knowledge to infer that a topic was taught.

4. Do NOT mark a syllabus topic as covered simply because it is
   related to another concept that was taught.

5. A prerequisite, sub-concept, or related concept does NOT automatically
   mean that the parent syllabus topic was covered.

6. A topic is "covered" ONLY when the lecture contains substantial
   teaching of that specific topic, such as:
   - explanation
   - definition
   - procedure
   - derivation
   - worked example
   - detailed discussion
   - application

7. A topic is "partially_covered" when a meaningful portion of that
   specific syllabus topic was taught, but the topic was not substantially
   completed.

8. A topic is "mentioned" when the topic is explicitly referenced or
   named, but there is not enough teaching to consider it covered.

9. A topic is "not_covered" when there is no meaningful evidence that
   the specific topic was taught.

10. Do NOT confuse related concepts with the syllabus topic itself.

    Example:

    Syllabus topic:
    "Relational Model"

    Lecture concepts:
    "Functional Dependencies"
    "Candidate Keys"
    "Normalization"

    These concepts may be related to databases, but they are NOT enough
    evidence to say that "Relational Model" was taught.

    Therefore:
    "Relational Model" → "not_covered"

11. Do NOT infer coverage from the lecture title alone unless the lecture
    content also provides meaningful evidence.

12. Do NOT infer coverage from a single keyword appearing in the notes.

13. Do NOT invent evidence.

14. Evidence must come directly from the lecture notes. Evidence should
    briefly explain WHY the specific syllabus topic received its status.

15. If there is no evidence for a topic, return an empty evidence list.

16. Confidence represents how confident you are that the STATUS is correct.
    It does NOT represent how much of the topic was covered.

17. Return EVERY syllabus topic exactly once.

18. Return ONLY valid JSON. Do not include markdown, explanations,
    comments, or additional fields.

STATUS DEFINITIONS:

"covered"
→ The specific syllabus topic was substantially taught.

"partially_covered"
→ A meaningful part of the specific syllabus topic was taught,
  but the topic was not fully covered.

"mentioned"
→ The topic was explicitly mentioned or referenced, but not meaningfully
  taught.

"not_covered"
→ There is insufficient evidence that the specific topic was taught.

SYLLABUS TOPICS:
{syllabus}

LECTURE NOTES:
{lecture_notes}

Return exactly this JSON structure:

{{
    "mappings": [
        {{
            "syllabus_topic": "Topic name",
            "status": "covered",
            "confidence": 0.95,
            "evidence": [
                "Specific evidence from the lecture notes"
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