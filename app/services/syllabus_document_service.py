import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.ai.syllabus.structurer import inspect_hierarchy, parse_syllabus
from app.models.course import Course
from app.models.syllabus import SyllabusTopic
from app.models.syllabus_document import SyllabusDocument
from app.models.syllabus_unit import SyllabusUnit
from app.rag.embeddings import embed_documents
from app.schemas.syllabus_document import SyllabusHierarchy

logger = logging.getLogger(__name__)


PARSING_STAGES = {"extracting", "structuring", "validating"}


class DocumentConflict(ValueError):
    pass


class SyllabusDocumentService:
    def __init__(self, db: Session):
        self.db = db

    def upload_document(self, course_id: UUID, path: Path, filename: str):
        self.db.scalar(select(Course.id).where(Course.id == course_id).with_for_update())
        version = self.db.scalar(select(func.max(SyllabusDocument.version)).where(
            SyllabusDocument.course_id == course_id
        ))
        document = SyllabusDocument(
            course_id=course_id, file_path=str(path.resolve()), original_filename=filename,
            file_type=path.suffix[1:], version=(version or 0) + 1, is_active=False,
        )
        self.db.add(document)
        self.db.commit()
        return document

    def lock_document(self, document):
        self.db.refresh(document, with_for_update=True)
        if document.confirmed_at is not None:
            raise DocumentConflict("Confirmed versions are immutable. Upload a new version to make changes.")

    def parse(self, document):
        self.lock_document(document)
        if document.parsing_status == "completed" and document.hierarchy is not None:
            return
        if (document.parsing_status in PARSING_STAGES
                and document.updated_at > datetime.now(UTC) - timedelta(minutes=15)):
            raise DocumentConflict("This document is already being parsed.")
        attempt = uuid4()
        path = document.file_path
        document.parsing_attempt = attempt
        document.parsing_status = "extracting"
        document.parsing_error = None
        self.db.commit()

        def lock_attempt():
            self.lock_document(document)
            if document.parsing_attempt != attempt:
                raise DocumentConflict("A newer parsing attempt replaced this one.")

        def publish_stage(stage):
            lock_attempt()
            document.parsing_status = stage
            self.db.commit()

        try:
            hierarchy, report, _ = parse_syllabus(path, on_stage=publish_stage)
            lock_attempt()
            document.hierarchy = hierarchy.model_dump(mode="json")
            document.parsing_report = report.model_dump(mode="json")
            document.parsing_status = "completed"
            document.parsing_attempt = None
            document.parsed_at = func.now()
            self.db.commit()
        except Exception as exc:
            logger.exception("Syllabus parsing failed for %s", document.id)
            self.db.rollback()
            self.db.refresh(document, with_for_update=True)
            if document.parsing_attempt == attempt:
                document.parsing_status = "failed"
                document.parsing_attempt = None
                document.parsing_error = (
                    str(exc)[:500] if type(exc) is ValueError
                    else "Extraction or hierarchy validation failed. Check the server log and retry."
                )
                self.db.commit()
            raise

    def save_draft(self, document, hierarchy):
        self.lock_document(document)
        if document.parsing_status != "completed":
            raise ValueError("Parse the syllabus before editing it.")
        report = document.parsing_report
        warnings, topics, subtopics = inspect_hierarchy(hierarchy, report["pages_processed"])
        document.hierarchy = hierarchy.model_dump(mode="json")
        document.parsing_report = {
            **report,
            "units": len(hierarchy.units), "topics": topics, "subtopics": subtopics,
            "warnings": list(dict.fromkeys([*report["warnings"], *warnings])),
            "needs_review": bool(report["needs_review"] or warnings or hierarchy.needs_review),
        }
        self.db.commit()

    def confirm(self, document):
        self.db.scalar(select(Course.id).where(Course.id == document.course_id).with_for_update())
        self.db.refresh(document, with_for_update=True)
        if document.is_active and document.confirmed_at:
            return
        self.lock_document(document)
        if document.parsing_status != "completed" or document.hierarchy is None:
            raise ValueError("Parse and review the syllabus before confirming it.")
        hierarchy = SyllabusHierarchy.model_validate(document.hierarchy)
        _, topics, _ = inspect_hierarchy(hierarchy, document.parsing_report["pages_processed"])
        if not topics or any(not unit.topics for unit in hierarchy.units):
            raise ValueError("Every unit must have at least one topic before confirmation.")

        legacy_unit = self.db.scalar(select(SyllabusUnit.id).where(
            SyllabusUnit.syllabus_document_id == document.id
        ).limit(1))
        if legacy_unit is not None:
            raise DocumentConflict("This draft has legacy hierarchy rows. Upload a new version to preserve them.")
        topic_rows, embedding_inputs = [], []

        def add_topics(nodes, unit, parent, path):
            for node in nodes:
                context = (*path, node.title)
                topic = SyllabusTopic(
                    course_id=document.course_id, syllabus_document_id=document.id,
                    syllabus_unit_id=unit.id, parent=parent, title=node.title,
                    description=node.description, number=node.number, pages=node.pages,
                    position=len(topic_rows),
                )
                topic_rows.append(topic)
                embedding_inputs.append(" > ".join(context) + (
                    f"\n{node.description}" if node.description else ""
                ) + (
                    "\nSubtopics: " + ", ".join(child.title for child in node.subtopics)
                    if node.subtopics else ""
                ))
                add_topics(node.subtopics, unit, topic, context)

        for position, node in enumerate(hierarchy.units):
            unit = SyllabusUnit(
                syllabus_document_id=document.id, unit_number=position + 1,
                title=node.title, description=node.description, position=position,
                number=node.number, pages=node.pages,
                page_reference=", ".join(map(str, node.pages))[:100] or None,
            )
            self.db.add(unit)
            self.db.flush()
            add_topics(node.topics, unit, None, (node.title,))

        for topic, vector in zip(topic_rows, embed_documents(embedding_inputs), strict=True):
            topic.embedding = vector
        self.db.add_all(topic_rows)
        self.db.execute(update(SyllabusDocument).where(
            SyllabusDocument.course_id == document.course_id,
            SyllabusDocument.is_active.is_(True),
        ).values(is_active=False))
        document.is_active = True
        document.confirmed_at = func.now()
        self.db.commit()

