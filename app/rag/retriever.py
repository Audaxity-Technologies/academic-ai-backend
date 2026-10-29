from collections import defaultdict
from functools import lru_cache
from typing import TYPE_CHECKING

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rag_chunk import RAGChunk
from app.models.note import Note
from app.core.constants import NoteStatus
from app.rag.embeddings import embed_query

if TYPE_CHECKING:
    from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


@lru_cache(maxsize=128)
def _get_bm25_index(course_id: int) -> tuple[list[RAGChunk], "BM25Okapi"]:
    """
    Cache BM25 index per course_id to avoid rebuilding on every search.
    Cache key is course_id (int).
    """
    from app.database.database import SessionLocal

    db = SessionLocal()
    try:
        chunks = db.scalars(
            select(RAGChunk)
            .join(Note, Note.lecture_id == RAGChunk.lecture_id)
            .where(
                RAGChunk.course_id == course_id,
                Note.status == NoteStatus.APPROVED,
            )
        ).all()

        if not chunks:
            return [], None

        corpus = [
            _tokenize(chunk.content)
            for chunk in chunks
        ]

        bm25 = BM25Okapi(corpus, k1=1.5, b=0.75)

        return chunks, bm25
    finally:
        db.close()


def _invalidate_bm25_cache(course_id: int):
    """Invalidate BM25 cache for a specific course (call after indexing)."""
    _get_bm25_index.cache_clear()


def vector_search(
    db: Session,
    query: str,
    course_id,
    limit: int = 10,
) -> list[tuple]:

    query_embedding = embed_query(query)

    distance = RAGChunk.embedding.cosine_distance(
        query_embedding
    )

    rows = db.execute(
        select(
            RAGChunk,
            distance.label("distance"),
        )
        .join(Note, Note.lecture_id == RAGChunk.lecture_id)
        .where(
            RAGChunk.course_id == course_id,
            Note.status == NoteStatus.APPROVED,
        )
        .order_by(distance)
        .limit(limit)
    ).all()

    return rows


def bm25_search(
    db: Session,
    query: str,
    course_id,
    limit: int = 10,
) -> list[RAGChunk]:

    chunks, bm25 = _get_bm25_index(course_id)

    if not chunks or bm25 is None:
        return []

    query_tokens = _tokenize(query)

    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        chunk
        for chunk, _score in ranked[:limit]
    ]


def hybrid_search(
    db: Session,
    query: str,
    course_id,
    candidate_limit: int = 10,
    final_limit: int = 5,
) -> list[RAGChunk]:

    # Use vector search first (faster, no cache needed)
    vector_rows = vector_search(
        db=db,
        query=query,
        course_id=course_id,
        limit=candidate_limit,
    )

    if not vector_rows:
        # Fallback to BM25 if vector search returns nothing
        return bm25_search(
            db=db,
            query=query,
            course_id=course_id,
            limit=final_limit,
        )

    # Use BM25 only if we have enough vector results
    bm25_chunks = bm25_search(
        db=db,
        query=query,
        course_id=course_id,
        limit=candidate_limit,
    )

    scores = defaultdict(float)
    chunks_by_id = {}

    rrf_k = 60

    for rank, (chunk, _distance) in enumerate(
        vector_rows,
        start=1,
    ):
        chunks_by_id[chunk.id] = chunk
        scores[chunk.id] += 1 / (rrf_k + rank)

    for rank, chunk in enumerate(
        bm25_chunks,
        start=1,
    ):
        chunks_by_id[chunk.id] = chunk
        scores[chunk.id] += 1 / (rrf_k + rank)

    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True,
    )

    return [
        chunks_by_id[chunk_id]
        for chunk_id in ranked_ids[:final_limit]
    ]
