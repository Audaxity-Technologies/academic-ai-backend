from functools import lru_cache

from sentence_transformers import CrossEncoder


MODEL_NAME = "BAAI/bge-reranker-base"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(
        MODEL_NAME,
        max_length=512,
    )


def rerank(
    query: str,
    chunks,
    top_k: int = 5,
):
    if not chunks:
        return []

    model = get_reranker()

    pairs = [
        [query, chunk.content]
        for chunk in chunks
    ]

    scores = model.predict(
        pairs,
        show_progress_bar=False,
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