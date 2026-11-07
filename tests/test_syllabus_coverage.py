from contextlib import nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.core.constants import UserRole
from app.services import syllabus_alignment_service as alignment
from app.services import syllabus_coverage_service as coverage


def test_course_takes_strongest_status_once_per_topic(monkeypatch):
    unit = SimpleNamespace(title="Databases")
    course_id, version, unit_id = uuid4(), uuid4(), uuid4()
    topics = [
        SimpleNamespace(id=uuid4(), title=title, syllabus_unit_id=unit_id, parent_id=None,
                        number=None, syllabus_document_id=version, unit=unit)
        for title in ("Transactions", "Locking", "Indexes", "Optimization")
    ]
    lectures = [SimpleNamespace(id=uuid4(), title=title, created_at=datetime.now(UTC))
                for title in ("First", "Second")]

    def row(index, status):
        return SimpleNamespace(syllabus_topic_id=topics[index].id, status=status,
                               confidence=.9, evidence=[], needs_review=False, explanation=None)

    db = Mock()
    db.execute.return_value = [
        (row(0, "mentioned"), lectures[0]), (row(0, "covered"), lectures[1]),
        (row(1, "partially_covered"), lectures[0]), (row(2, "mentioned"), lectures[1]),
    ]
    loader = Mock(return_value=topics)
    monkeypatch.setattr(coverage, "load_topics", loader)
    report = coverage.course_progress(db, course_id, version, SimpleNamespace(role=UserRole.STUDENT))
    loader.assert_called_once_with(db, course_id, version)
    assert "notes.status" in str(db.execute.call_args.args[0])
    assert report["total_topics"] == 4
    assert report["coverage_percentage"] == report["units"][0]["coverage_percentage"] == 37.5
    assert [report[key] for key in ("covered", "partially_covered", "mentioned", "not_covered")] == [1, 1, 1, 1]
    assert len(report["units"][0]["topics"][0]["history"]) == 2
    assert [item["coverage_percentage"] for item in report["lectures"]] == [12.5, 25.0]


def test_legacy_notes_evidence_is_not_credited():
    row = SimpleNamespace(status="covered", confidence=.99, evidence=["Generated summary"],
                          needs_review=False, explanation=None)
    topic = SimpleNamespace(id=uuid4(), title="Locking", syllabus_document_id=None)
    item = coverage.normalized_mapping(row, topic)
    assert item["status"] == "not_covered"
    assert item["needs_review"] and item["evidence"] == []


def test_failure_then_retry_uses_version_scoped_upserts(monkeypatch):
    lecture = SimpleNamespace(id=uuid4(), course_id=uuid4(), alignment_status="pending",
                              transcript=SimpleNamespace(content="Verbatim text", segments=None))
    db = Mock()
    db.scalar.return_value = lecture
    db.begin_nested.side_effect = nullcontext
    version = uuid4()
    monkeypatch.setattr(alignment, "active_version", lambda *_: version)
    engine = Mock()
    monkeypatch.setattr(alignment, "SyllabusAlignmentEngine", lambda *_: engine)
    row = {"syllabus_topic_id": uuid4(), "syllabus_topic": "Transactions", "status": "not_covered",
           "confidence": 0.0, "evidence": [], "explanation": None, "needs_review": False}
    engine.align.side_effect = [RuntimeError("provider down"), [row], [row]]
    assert alignment.align_saved_lecture(db, lecture.id)["status"] == "failed"
    assert lecture.alignment_status == "failed"
    db.execute.assert_not_called()
    for _ in range(2):
        assert alignment.align_saved_lecture(db, lecture.id)["status"] == "completed"
    assert lecture.alignment_error is None
    for call in db.execute.call_args_list:
        sql = str(call.args[0])
        assert "ON CONFLICT ON CONSTRAINT uq_syllabus_mappings_lecture_topic DO UPDATE" in sql
        assert "DELETE" not in sql
    assert db.commit.call_count == 3

