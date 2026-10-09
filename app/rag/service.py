from sqlalchemy.orm import Session

from app.ai.llm.llm_client import llm_client
from app.rag.retriever import hybrid_search
from app.rag.reranker import rerank


ANSWER_PROMPT = """
You are the academic tutor inside an educational platform.

Answer the student's question using ONLY the supplied academic context.

Rules:

1. Do not invent facts that are not supported by the context.
2. If the context is insufficient, clearly say that the available course
   material does not contain enough information.
3. Explain concepts clearly for a university student.
4. Prefer the terminology used in the course material.
5. For comparisons, use a structured explanation.
6. For technical questions, include examples when the context supports them.
7. Do not mention "retrieved chunks", "RAG", embeddings, or internal systems.
8. Cite the source numbers used for important claims.

Return JSON with exactly:

{
  "answer": "string",
  "confidence": 0.0,
  "sources": [1, 2]
}

Student question:
{question}

Academic context:

{context}
"""


def answer_question(
    db: Session,
    query: str,
    course_id,
):

    candidates = hybrid_search(
        db=db,
        query=query,
        course_id=course_id,
        candidate_limit=20,
        final_limit=10,
    )

    ranked = rerank(
        query=query,
        chunks=candidates,
        top_k=5,
    )

    if not ranked:
        return {
            "answer": (
                "I could not find relevant material in the "
                "available course content."
            ),
            "confidence": 0.0,
            "sources": [],
        }

    context_parts = []

    sources = []

    for index, item in enumerate(
        ranked,
        start=1,
    ):
        chunk = item["chunk"]

        context_parts.append(
            f"""
SOURCE {index}
Title: {chunk.title}
Type: {chunk.source_type}

{chunk.content}
"""
        )

        sources.append(
            {
                "id": index,
                "chunk_id": str(chunk.id),
                "title": chunk.title,
                "source_type": chunk.source_type,
                "lecture_id": (
                    str(chunk.lecture_id)
                    if chunk.lecture_id
                    else None
                ),
                "score": round(
                    item["score"],
                    4,
                ),
            }
        )

    context = "\n".join(context_parts)

    prompt = ANSWER_PROMPT.format(
        question=query,
        context=context,
    )

    result = llm_client.generate_content(
        prompt=prompt,
        response_mime_type="application/json",
    )

    used_sources = result.get(
        "sources",
        list(range(1, len(ranked) + 1)),
    )

    selected_sources = [
        source
        for source in sources
        if source["id"] in used_sources
    ]

    return {
        "answer": result.get(
            "answer",
            "I could not generate an answer.",
        ),
        "confidence": float(
            result.get("confidence", 0.0)
        ),
        "sources": selected_sources,
    }