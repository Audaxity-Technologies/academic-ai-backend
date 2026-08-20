import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.ai.llm.prompts import LECTURE_NOTES_PROMPT


load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_notes(transcript: str) -> dict:
    prompt = LECTURE_NOTES_PROMPT.format(
        transcript=transcript
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

            notes = json.loads(response.text)

            return notes

        except Exception as e:
            print(f"Gemini attempt {attempt + 1} failed: {e}")

            if attempt == max_retries - 1:
                raise

            time.sleep(5)