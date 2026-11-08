from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import question_paper_service as papers


def page(text, number=1):
    return {"pages": [{"page_number": number, "text": text}], "source_pages": [text], "warnings": []}


def test_extraction_checks_source_quotes_marks_and_page(monkeypatch):
    monkeypatch.setattr(papers.llm_client, "generate_content", lambda **_: {"questions": [
        {"text": "Find x² for x = 2.", "number": "1", "marks_label": "[4 marks]"},
        {"text": "Explain hashing.", "number": "2", "marks_label": "[9 marks]"},
        {"text": "Invented question about calculus.", "marks_label": "[8 marks]"},
    ]})
    questions, warnings = papers.extract_questions(page(
        "1. Find x² for x = 2. [4 marks]\n2. Explain hashing.\n3. Other question [9 marks]",
        number=3,
    ))
    assert [question.text for question in questions] == ["Find x² for x = 2.", "Explain hashing."]
    assert [question.marks for question in questions] == [4, None]
    assert [question.number for question in questions] == ["1", "2"]
    assert all(question.page == 3 for question in questions)
    assert "Omitted 1" in warnings[0]


def test_reject_page_when_no_question_is_source_verified(monkeypatch):
    monkeypatch.setattr(papers.llm_client, "generate_content", lambda **_: {
        "questions": [{"text": "Invented question."}],
    })
    with pytest.raises(ValueError, match="No complete questions"):
        papers.extract_questions(page("Read all instructions before starting."))


def test_analysis_does_not_infer_missing_marks_years_or_false_math_repeats():
    topic = str(uuid4())
    first, second = uuid4(), uuid4()
    question = {"text": "Solve x+1 = 0.", "marks": 2, "topic_id": topic, "topic_title": "Algebra"}
    missing = {"text": "Solve x-1 = 0.", "marks": None, "topic_id": None, "topic_title": None}
    result = papers.analyze_papers([
        SimpleNamespace(id=first, exam_year=2023, questions=[question, question, missing]),
        SimpleNamespace(id=second, exam_year=None, questions=[{**question, "marks": None}]),
    ])
    assert result["paper_count"] == result["questions_with_marks"] == 2
    assert result["earliest_year"] == result["latest_year"] == 2023
    assert result["papers_with_year"] == 1
    assert result["marks_distribution"] == {2: 2}
    assert result["repeated_questions"] == [{"text": question["text"], "paper_ids": [first, second]}]
    assert result["suggested_topic_frequency"][0]["paper_count"] == 2

