from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.ai.syllabus import alignment
from app.ai.syllabus.alignment import SyllabusAlignmentEngine, Verification, coverage_stats, topic_scope


def topic(embedding=True):
    return SimpleNamespace(id=uuid4(), title="Transactions", description=None,
                           embedding=[0.1] * 384 if embedding else None, parent=None, unit=None)


def test_scope_and_cosine_sql():
    db = Mock()
    db.scalars.return_value = []
    course, version = uuid4(), uuid4()
    assert SyllabusAlignmentEngine(db).retrieve(topic_scope(course, version), [0.1] * 384, 10) == []
    sql = db.scalars.call_args.args[0].compile(dialect=postgresql.dialect())
    assert "syllabus_topics.course_id =" in str(sql)
    assert "syllabus_topics.syllabus_document_id =" in str(sql)
    assert "embedding IS NOT NULL" in str(sql) and "<=>" in str(sql)
    assert course in sql.params.values() and version in sql.params.values()


def test_strongest_status_exact_evidence_and_full_denominator(monkeypatch):
    taught, partial, mentioned, absent = topic(), topic(False), topic(), topic()
    db = Mock()
    db.scalars.return_value = [taught, partial, mentioned, absent]
    engine = SyllabusAlignmentEngine(db)
    transcript = "Transactions are atomic. Savepoints help. Indexes. Transactions again."
    chunks = [(0, transcript[:50]), (50, transcript[50:])]
    monkeypatch.setattr(alignment, "transcript_chunks", lambda *_: iter(chunks))
    monkeypatch.setattr(alignment, "embed_query", lambda _: [0.1] * 384)
    monkeypatch.setattr(alignment, "embed_documents", lambda _: [[0.2] * 384])
    engine.retrieve = Mock(return_value=[taught, partial, mentioned, absent])

    def verdict(topic, status, confidence, *excerpts):
        return Verification(topic_id=topic.id, status=status, confidence=confidence, excerpts=list(excerpts))

    engine.verify = Mock(side_effect=[
        [verdict(taught, "covered", .8, "Transactions are atomic.", "Transactions are atomic."),
         verdict(partial, "partially_covered", .7, "Savepoints help."),
         verdict(mentioned, "mentioned", .6, "Indexes."),
         verdict(absent, "covered", .99, "Invented quote")],
        [verdict(taught, "mentioned", .99, "Transactions again.")],
    ])
    rows = engine.align(transcript, topic_scope(uuid4(), uuid4()), [
        {"text": "Transactions are atomic.", "start": 1.0, "end": 3.0},
    ])
    assert [row["status"] for row in rows] == ["covered", "partially_covered", "mentioned", "not_covered"]
    assert rows[0]["confidence"] == .8
    assert len(rows[0]["evidence"]) == 2
    assert rows[0]["evidence"][0]["start_time"] == 1.0
    assert rows[0]["evidence"][1]["start_time"] is None
    assert rows[3]["needs_review"] and not rows[3]["evidence"]
    assert partial.embedding == [0.2] * 384
    assert coverage_stats(row["status"] for row in rows)["coverage_percentage"] == 37.5


def test_invalid_response_and_unknown_candidate(monkeypatch):
    candidate = topic()
    monkeypatch.setattr(alignment, "embed_query", lambda _: [0.1] * 384)
    db = Mock()
    db.scalars.return_value = [candidate]
    engine = SyllabusAlignmentEngine(db)
    engine.retrieve = Mock(return_value=[candidate])
    client = Mock()
    monkeypatch.setattr(alignment, "llm_client", client)
    client.generate_content.return_value = {"verifications": [{"topic_id": "fake"}]}
    with pytest.raises(ValidationError):
        engine.align("A transcript.", topic_scope(uuid4(), uuid4()))
    client.generate_content.return_value = {"verifications": [
        {"topic_id": str(uuid4()), "status": "mentioned", "confidence": 1, "excerpts": ["A transcript."]}
    ]}
    with pytest.raises(ValueError, match="candidate UUID"):
        engine.align("A transcript.", topic_scope(uuid4(), uuid4()))
    engine.retrieve.side_effect = RuntimeError("retrieval failed")
    with pytest.raises(RuntimeError, match="retrieval failed"):
        engine.align("A transcript.", topic_scope(uuid4(), uuid4()))


def test_no_topics_and_no_candidates(monkeypatch):
    db = Mock()
    db.scalars.return_value = []
    engine = SyllabusAlignmentEngine(db)
    assert engine.align(None, topic_scope(uuid4(), None)) == []
    assert coverage_stats([])["coverage_percentage"] == 0
    db.scalars.return_value = [topic()]
    engine.retrieve = Mock(return_value=[])
    monkeypatch.setattr(alignment, "embed_query", lambda _: [0.1] * 384)
    assert engine.align("An unrelated lecture.", topic_scope(uuid4(), None))[0]["status"] == "not_covered"


def test_whisper_generator_preserves_offsets(monkeypatch):
    from app.ai.speech import transcription

    segments = iter([SimpleNamespace(text=" Atomicity", start=1, end=2),
                     SimpleNamespace(text=" means all or nothing.", start=2, end=4)])
    model = Mock()
    model.transcribe.return_value = segments, SimpleNamespace(language="en")
    monkeypatch.setattr(transcription, "get_model", lambda: model)
    result = transcription.transcribe_audio("fixture.wav")
    assert result["transcript"] == "Atomicity means all or nothing."
    assert [(item["start"], item["end"]) for item in result["segments"]] == [(1, 2), (2, 4)]

