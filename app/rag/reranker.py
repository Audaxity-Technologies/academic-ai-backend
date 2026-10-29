from __future__ import annotations
from functools import lru_cache
from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder


MODEL_NAME = "BAAI/bge-reranker-base"
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "true").lower() == "true"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    from sentence_transformers import CrossEncoder
    return CrossEncoder(
        MODEL_NAME,
        max_length=512,
        device="cpu",
    )


def rerank(
    query: str,
    chunks,
    top_k: int = 3,
):
    """
    Rerank chunks using cross-encoder.
    Disabled by default for performance; enable via ENABLE_RERANKER=true env var.
    """
    if not chunks:
        return []

    if not ENABLE_RERANKER:
        # Skip reranking, return chunks with dummy scores
        return [
            {
                "chunk": chunk,
                "score": 0.5,
            }
            for chunk in chunks[:top_k]
        ]

    model = get_reranker()

    pairs = [
        [query, chunk.content]
        for chunk in chunks
    ]

    scores = model.predict(
        pairs,
        show_progress_bar=False,
        batch_size=8,
    )

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: float(x[1]),
        reverse=True,
    )

    return [
        {
            "chunk": chunk,
            "score": float(score),
        }
        for chunk, score in ranked[:top_k]
    ]
