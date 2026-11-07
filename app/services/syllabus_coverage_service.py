from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.ai.syllabus.alignment import STATUS_RANK, coverage_stats, topic_scope
from app.core.constants import NoteStatus, UserRole
from app.models.lecture import Lecture
from app.models.note import Note
from app.models.syllabus import SyllabusTopic
from app.models.syllabus_document import SyllabusDocument
from app.models.syllabus_mapping import SyllabusMapping
from app.services.syllabus_alignment_service import active_version


def checked_version(db, course_id, version, legacy=False):
    if legacy and version:
        raise HTTPException(422, "Choose either a syllabus version or legacy topics.")
    if legacy:
        return None
    if version is None:
        return active_version(db, course_id)
    document = db.get(SyllabusDocument, version)
    if not document or document.course_id != course_id or not document.confirmed_at:
        raise HTTPException(404, "Confirmed syllabus version not found.")
    return version


def load_topics(db, course_id, version):
    return list(db.scalars(topic_scope(course_id, version).options(
        joinedload(SyllabusTopic.unit)
    ).order_by(SyllabusTopic.position, SyllabusTopic.id)))


def normalized_mapping(row, topic):
    status = "partially_covered" if row.status == "partial" else row.status
    evidence = [item for item in row.evidence if isinstance(item, dict) and item.get("text")]
    unverified = (topic.syllabus_document_id is None and status != "not_covered"
                  and not any("transcript_offset" in item for item in evidence))
    if unverified:
        status = "not_covered"
        evidence = []
    return {"syllabus_topic_id": topic.id, "syllabus_topic": topic.title,
            "status": status if status in STATUS_RANK else "not_covered",
            "confidence": 0.0 if unverified else row.confidence, "evidence": evidence,
            "explanation": ("Historical mapping needs transcript verification."
                            if unverified else row.explanation),
            "needs_review": row.needs_review or unverified}


def course_progress(db, course_id, version, user):
    topics = load_topics(db, course_id, version)
    by_id = {topic.id: topic for topic in topics}
    query = select(SyllabusMapping, Lecture).join(
        Lecture, Lecture.id == SyllabusMapping.lecture_id
    ).where(Lecture.course_id == course_id, SyllabusMapping.syllabus_topic_id.in_(by_id))
    if user.role == UserRole.STUDENT:
        query = query.join(Note, Note.lecture_id == Lecture.id).where(Note.status == NoteStatus.APPROVED)
    history = defaultdict(list)
    by_lecture = defaultdict(list)
    lectures = {}
    for row, lecture in db.execute(query.order_by(Lecture.created_at.desc(), Lecture.id)):
        mapping = normalized_mapping(row, by_id[row.syllabus_topic_id])
        item = {**mapping, "lecture_id": lecture.id, "lecture_title": lecture.title}
        history[row.syllabus_topic_id].append(item)
        lectures[lecture.id] = lecture
        by_lecture[lecture.id].append(mapping["status"])
    units = {}
    statuses = []
    for topic in topics:
        items = history[topic.id]
        strongest = max(
            (item["status"] for item in items), key=STATUS_RANK.__getitem__, default="not_covered"
        )
        statuses.append(strongest)
        unit = units.setdefault(topic.syllabus_unit_id, {
            "id": topic.syllabus_unit_id, "title": topic.unit.title if topic.unit else "Manual topics",
            "topics": [],
        })
        unit["topics"].append({
            "id": topic.id, "title": topic.title, "unit_id": topic.syllabus_unit_id,
            "parent_id": topic.parent_id, "number": topic.number, "status": strongest,
            "history": [item for item in items if item["status"] != "not_covered" or item["needs_review"]],
        })
    for unit in units.values():
        unit.update(coverage_stats(topic["status"] for topic in unit["topics"]))
    return {
        **coverage_stats(statuses), "syllabus_document_id": version, "units": list(units.values()),
        "lectures": [
            {"lecture_id": lecture.id, "lecture_title": lecture.title, "created_at": lecture.created_at,
             **coverage_stats(items + ["not_covered"] * (len(topics) - len(items)))}
            for lecture_id, lecture in lectures.items() for items in [by_lecture[lecture_id]]
        ],
    }


def lecture_progress(db, lecture, version=None, legacy=False):
    rows = db.execute(select(SyllabusMapping, SyllabusTopic).join(
        SyllabusTopic, SyllabusTopic.id == SyllabusMapping.syllabus_topic_id
    ).where(
        SyllabusMapping.lecture_id == lecture.id, SyllabusTopic.course_id == lecture.course_id
    ).order_by(SyllabusTopic.position, SyllabusTopic.id)).all()
    versions = list(dict.fromkeys(topic.syllabus_document_id for _, topic in rows))
    if version is None and not legacy:
        active = active_version(db, lecture.course_id)
        if active in versions or not versions:
            version = active
        else:
            version = db.scalar(select(SyllabusDocument.id).where(
                SyllabusDocument.id.in_([item for item in versions if item is not None])
            ).order_by(SyllabusDocument.version.desc()).limit(1))
    version = checked_version(db, lecture.course_id, version, legacy or (version is None and bool(versions)))
    topics = load_topics(db, lecture.course_id, version)
    by_id = {topic.id: topic for topic in topics}
    mappings = [normalized_mapping(row, topic) for row, topic in rows if topic.id in by_id]
    stats = coverage_stats([item["status"] for item in mappings] +
                           ["not_covered"] * (len(topics) - len(mappings)))
    return {**stats, "lecture_id": lecture.id, "syllabus_document_id": version,
            "status": lecture.alignment_status, "message": lecture.alignment_error,
            "available_versions": versions, "mappings": mappings}

