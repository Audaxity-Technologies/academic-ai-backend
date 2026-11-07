import logging

from sqlalchemy import select

from app.ai.syllabus.alignment import SyllabusAlignmentEngine, coverage_stats, topic_scope
from app.models.lecture import Lecture
from app.models.syllabus_document import SyllabusDocument
from app.repositories.syllabus_mapping_repository import SyllabusMappingRepository

logger = logging.getLogger(__name__)


def active_version(db, course_id):
    return db.scalar(select(SyllabusDocument.id).where(
        SyllabusDocument.course_id == course_id, SyllabusDocument.is_active.is_(True)
    ))


def align_saved_lecture(db, lecture_id, document_id=None):
    lecture = db.scalar(select(Lecture).where(Lecture.id == lecture_id).with_for_update())
    if lecture is None:
        raise ValueError("Lecture not found")
    try:
        with db.begin_nested():
            document_id = document_id or active_version(db, lecture.course_id)
            transcript = lecture.transcript
            mappings = SyllabusAlignmentEngine(db).align(
                transcript.content if transcript else None,
                topic_scope(lecture.course_id, document_id),
                transcript.segments if transcript else None,
            )
            SyllabusMappingRepository(db).save_mappings(lecture_id, mappings)
        lecture.alignment_status = "completed" if mappings else "no_syllabus"
        lecture.alignment_error = None
        db.commit()
        return {"status": lecture.alignment_status, "syllabus_document_id": document_id,
                "mappings": mappings, **coverage_stats(item["status"] for item in mappings)}
    except Exception:
        logger.exception("Syllabus alignment failed for lecture %s", lecture_id)
        try:
            lecture.alignment_status = "failed"
            lecture.alignment_error = "Syllabus alignment failed. Retry from the lecture."
            db.commit()
        except Exception:
            logger.exception("Could not record alignment failure for lecture %s", lecture_id)
            db.rollback()
        return {"status": "failed", "mappings": [], "coverage_percentage": 0.0,
                "message": "Syllabus alignment failed. Retry from the lecture."}


def run_lecture_alignment(lecture_id):
    from app.database.session import SessionLocal

    with SessionLocal() as db:
        try:
            align_saved_lecture(db, lecture_id)
        except Exception:
            logger.exception("Could not start syllabus alignment for lecture %s", lecture_id)

