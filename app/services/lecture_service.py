from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.pipeline.syllabus_mapping import process_syllabus_mapping
from app.core.constants import LectureSourceType, LectureStatus, NoteStatus
from app.models.lecture import Lecture
from app.models.note import Note
from app.models.transcript import Transcript
from app.repositories.lecture_repository import LectureRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.syllabus_mapping_repository import SyllabusMappingRepository
from app.repositories.syllabus_repository import SyllabusRepository
from app.repositories.transcript_repository import TranscriptRepository


class LectureService:
    def __init__(self, db: Session):
        self.db = db
        self.lecture_repository = LectureRepository(db)
        self.transcript_repository = TranscriptRepository(db)
        self.note_repository = NoteRepository(db)

    def create_lecture(
        self,
        course_id: UUID,
        title: str,
        source_type: LectureSourceType,
        source_path: str | None = None,
    ) -> Lecture:

        lecture = Lecture(
            course_id=course_id,
            title=title,
            source_type=source_type,
            source_path=source_path,
            status=LectureStatus.PROCESSING,
        )

        return self.lecture_repository.create(lecture)

    def save_transcript(
        self,
        lecture: Lecture,
        content: str,
        language: str | None = None,
        transcript_path: str | None = None,
    ) -> Transcript:

        transcript = Transcript(
            lecture_id=lecture.id,
            content=content,
            language=language,
        )

        if transcript_path:
            lecture.transcript_path = transcript_path

        self.transcript_repository.create(transcript)

        return transcript

    def save_note(
        self,
        lecture: Lecture,
        title: str,
        content: dict,
        pdf_path: str | None = None,
        html_path: str | None = None,
    ) -> Note:

        note = Note(
            lecture_id=lecture.id,
            title=title,
            content=content,
            pdf_path=pdf_path,
            html_path=html_path,
            status=NoteStatus.DRAFT,
        )

        self.note_repository.create(note)

        lecture.pdf_path = pdf_path
        lecture.html_path = html_path

        return note

    def mark_completed(self, lecture: Lecture) -> Lecture:
        lecture.status = LectureStatus.COMPLETED
        return self.lecture_repository.update(lecture)

    def mark_failed(self, lecture: Lecture) -> Lecture:
        lecture.status = LectureStatus.FAILED
        return self.lecture_repository.update(lecture)

    def get_lecture(self, lecture_id: UUID) -> Lecture | None:
        return self.lecture_repository.get_by_id(lecture_id)

    def get_course_lectures(self, course_id: UUID) -> list[Lecture]:
        return self.lecture_repository.get_by_course(course_id)

    def map_syllabus(
        self,
        lecture: Lecture,
        note_content: dict,
    ) -> dict:
        """
        Map lecture notes to syllabus topics and save mappings.
        Returns the mapping result with coverage percentage.
        """
        syllabus_repo = SyllabusRepository(self.db)
        mapping_repo = SyllabusMappingRepository(self.db)

        # Get all syllabus topics for the course
        topics = syllabus_repo.get_by_course(lecture.course_id)

        if not topics:
            return {
                "mappings": [],
                "coverage_percentage": 0.0,
                "message": "No syllabus topics defined for this course"
            }

        # Extract topic names for mapping
        topic_names = [topic.title for topic in topics]
        topic_records = {topic.title: topic.id for topic in topics}

        # Run AI mapping
        mapping_result = process_syllabus_mapping(
            syllabus_topics=topic_names,
            lecture_notes=note_content
        )

        # Save mappings to database
        mapping_repo.save_mappings(
            lecture_id=lecture.id,
            topic_records=topic_records,
            mappings=mapping_result["mappings"]
        )

        self.db.commit()

        return mapping_result