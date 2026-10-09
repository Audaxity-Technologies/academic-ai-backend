
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.syllabus_mapping import SyllabusMapping


class SyllabusMappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_mappings(
        self,
        lecture_id: UUID,
        topic_records: dict[str, UUID],
        mappings: list[dict],
    ) -> None:
        for mapping in mappings:
            topic_id = topic_records.get(mapping["syllabus_topic"])

            if topic_id is None:
                continue

            self.db.add(
                SyllabusMapping(
                    lecture_id=lecture_id,
                    syllabus_topic_id=topic_id,
                    status=mapping["status"],
                    confidence=mapping["confidence"],
                    evidence=mapping["evidence"],
                )
            )
