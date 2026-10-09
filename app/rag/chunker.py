from typing import Any


def _clean(text: str | None) -> str:
    if not text:
        return ""

    return " ".join(text.strip().split())


def build_note_chunks(
    note,
    lecture,
) -> list[dict[str, Any]]:
    """
    Convert a structured Note into retrieval chunks.

    Each section becomes a semantic retrieval unit.
    Q&A pairs are also indexed because students frequently
    ask questions using wording close to generated Q&A.
    """

    content = note.content or {}

    chunks: list[dict[str, Any]] = []

    sections = content.get("sections", [])

    for index, section in enumerate(sections):
        heading = _clean(section.get("heading"))
        explanation = _clean(section.get("explanation"))

        parts = []

        if heading:
            parts.append(f"Topic: {heading}")

        if explanation:
            parts.append(f"Explanation: {explanation}")

        definitions = section.get("definitions") or []

        if definitions:
            definition_text = "\n".join(
                f"{_clean(item.get('term'))}: "
                f"{_clean(item.get('definition'))}"
                for item in definitions
            )

            parts.append(f"Definitions:\n{definition_text}")

        examples = section.get("examples") or []

        if examples:
            example_text = "\n".join(
                f"{_clean(item.get('description'))}: "
                f"{_clean(item.get('illustration'))}"
                for item in examples
            )

            parts.append(f"Examples:\n{example_text}")

        formulas = section.get("formulas") or []

        if formulas:
            parts.append(
                "Formulas:\n" + "\n".join(
                    _clean(formula)
                    for formula in formulas
                )
            )

        emphasis = section.get("instructor_emphasis") or []

        if emphasis:
            parts.append(
                "Instructor emphasis:\n"
                + "\n".join(_clean(x) for x in emphasis)
            )

        misconceptions = section.get("common_misconceptions") or []

        if misconceptions:
            parts.append(
                "Common misconceptions:\n"
                + "\n".join(_clean(x) for x in misconceptions)
            )

        text = "\n\n".join(x for x in parts if x)

        if text:
            chunks.append(
                {
                    "course_id": lecture.course_id,
                    "lecture_id": lecture.id,
                    "note_id": note.id,
                    "source_type": "note_section",
                    "title": heading or note.title,
                    "content": text,
                    "chunk_index": index,
                    "metadata": {
                        "lecture_title": lecture.title,
                        "note_title": note.title,
                        "section_heading": heading,
                    },
                }
            )

    questions = content.get("questions_and_answers") or []

    base_index = len(chunks)

    for index, qa in enumerate(questions):
        question = _clean(qa.get("question"))
        answer = _clean(qa.get("answer"))

        if not question or not answer:
            continue

        chunks.append(
            {
                "course_id": lecture.course_id,
                "lecture_id": lecture.id,
                "note_id": note.id,
                "source_type": "note_qa",
                "title": question,
                "content": f"Question: {question}\nAnswer: {answer}",
                "chunk_index": base_index + index,
                "metadata": {
                    "lecture_title": lecture.title,
                    "note_title": note.title,
                },
            }
        )

    return chunks


def build_transcript_chunks(
    transcript,
    lecture,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[dict[str, Any]]:
    """
    Split lecture transcript into overlapping retrieval chunks.
    """

    text = _clean(transcript.content)

    if not text:
        return []

    words = text.split()

    chunks = []
    start = 0
    index = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))

        chunk_text = " ".join(words[start:end])

        chunks.append(
            {
                "course_id": lecture.course_id,
                "lecture_id": lecture.id,
                "note_id": None,
                "source_type": "transcript",
                "title": lecture.title,
                "content": chunk_text,
                "chunk_index": index,
                "metadata": {
                    "lecture_title": lecture.title,
                    "start_word": start,
                    "end_word": end,
                },
            }
        )

        index += 1

        if end >= len(words):
            break

        start = end - overlap

    return chunks