LECTURE_NOTES_PROMPT = """
You are an AI assistant that converts lecture transcripts into
clear, accurate, and well-structured study notes.

The transcript may contain:
- Speech-to-text errors
- Filler words
- Repeated sentences
- Grammatical mistakes
- Informal spoken language

Your task is to:

1. Identify the main topic of the lecture.
2. Correct obvious transcription errors when the intended meaning is clear.
3. Remove filler words and unnecessary repetition.
4. Create a concise summary.
5. Extract the important concepts.
6. Organize the content into structured study notes.
7. Preserve important technical terms, definitions, examples,
   formulas, and explanations.

Return ONLY valid JSON in this format:

{{
    "title": "Lecture title",
    "summary": "Short summary of the lecture",
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

Lecture transcript:

{transcript}
"""