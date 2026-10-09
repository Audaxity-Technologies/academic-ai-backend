from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.lecture import Lecture
from app.models.note import Note
from app.models.rag_chunk import RAGChunk
from app.models.transcript import Transcript

from app.rag.chunker import (
    build_note_chunks,
    build_transcript_chunks,
)
from app.rag.embeddings import embed_documents


def index_course(
    db: Session,
    course_id,
) -> int:

    lectures = db.scalars(
        select(Lecture)
        .where(Lecture.course_id == course_id)
        .order_by(Lecture.created_at)
    ).all()

    if not lectures:
        return 0

    db.execute(
        delete(RAGChunk).where(
            RAGChunk.course_id == course_id
        )
    )

    db.flush()

    all_chunks = []

    for lecture in lectures:

        note = db.scalar(
            select(Note).where(
                Note.lecture_id == lecture.id
            )
        )

        if note:
            all_chunks.extend(
                build_note_chunks(
                    note=note,
                    lecture=lecture,
                )
            )

        transcript = db.scalar(
            select(Transcript).where(
                Transcript.lecture_id == lecture.id
            )
        )

        if transcript:
            all_chunks.extend(
                build_transcript_chunks(
                    transcript=transcript,
                    lecture=lecture,
                )
            )

    if not all_chunks:
        db.commit()
        return 0

    texts = [
        chunk["content"]
        for chunk in all_chunks
    ]

    embeddings = embed_documents(texts)

    for chunk, embedding in zip(
        all_chunks,
        embeddings,
    ):
        chunk["chunk_metadata"] = chunk.pop("metadata")
        db.add(
            RAGChunk(
                **chunk,
                embedding=embedding,
            )
        )

    db.commit()

    return len(all_chunks)