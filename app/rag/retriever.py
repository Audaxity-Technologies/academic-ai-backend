from collections import defaultdict

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rag_chunk import RAGChunk
from app.rag.embeddings import embed_query


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def vector_search(
    db: Session,
    query: str,
    course_id,
    limit: int = 20,
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
        .where(
            RAGChunk.course_id == course_id
        )
        .order_by(distance)
        .limit(limit)
    ).all()

    return rows


def bm25_search(
    db: Session,
    query: str,
    course_id,
    limit: int = 20,
) -> list[RAGChunk]:

    chunks = db.scalars(
        select(RAGChunk)
        .where(
            RAGChunk.course_id == course_id
        )
    ).all()

    if not chunks:
        return []

    corpus = [
        _tokenize(chunk.content)
        for chunk in chunks
    ]

    bm25 = BM25Okapi(corpus)

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
    candidate_limit: int = 20,
    final_limit: int = 8,
) -> list[RAGChunk]:

    vector_rows = vector_search(
        db=db,
        query=query,
        course_id=course_id,
        limit=candidate_limit,
    )

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