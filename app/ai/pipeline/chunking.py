import re

SENTENCE_END_RE = re.compile(r'[.!?]\s')
SINGLE_PASS_TOKEN_THRESHOLD = 20000  # Tokens below this skip chunking entirely


def _estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Estimate token count using character heuristic. Can be swapped for real tokenizer later."""
    return int(len(text) / chars_per_token)


def _find_sentence_boundary(text: str, search_from: int, direction: str = "backward") -> int:
    """Find nearest sentence-ending punctuation. Returns index just after it, or -1."""
    if direction == "backward":
        matches = list(SENTENCE_END_RE.finditer(text, 0, search_from))
        return matches[-1].end() if matches else -1
    else:
        match = SENTENCE_END_RE.search(text, search_from)
        return match.end() if match else -1


def chunk_transcript(
    transcript: str,
    chunk_size_tokens: int = 3000,
    overlap_tokens: int = 300,
    chars_per_token: float = 4.0,
    min_chunk_chars: int = 500,
) -> list[str]:
    """
    Chunk transcript into overlapping segments at sentence boundaries.
    Skips chunking if transcript is below SINGLE_PASS_TOKEN_THRESHOLD.
    """
    # Check if we should skip chunking entirely
    estimated_tokens = _estimate_tokens(transcript, chars_per_token)
    if estimated_tokens < SINGLE_PASS_TOKEN_THRESHOLD:
        print(f"[CHUNKER] Transcript estimated at {estimated_tokens} tokens, below threshold {SINGLE_PASS_TOKEN_THRESHOLD} — skipping chunking")
        return [transcript]
    
    chunk_size = int(chunk_size_tokens * chars_per_token)
    overlap = int(overlap_tokens * chars_per_token)

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    transcript = transcript.strip()
    transcript_length = len(transcript)
    chunks = []
    start = 0

    while start < transcript_length:
        end = min(start + chunk_size, transcript_length)

        if end < transcript_length:
            boundary = _find_sentence_boundary(transcript, end, "backward")
            if boundary != -1 and boundary > start:
                end = boundary

        chunk = transcript[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= transcript_length:
            break

        # advance from the actual end used, not the original fixed offset,
        # so overlap is measured against real content boundaries
        next_start = end - overlap
        boundary = _find_sentence_boundary(transcript, next_start, "forward")
        start = boundary if boundary != -1 and boundary < end else next_start

    # merge a too-small trailing chunk into the previous one instead of
    # sending a near-empty chunk through the full pipeline
    if len(chunks) > 1 and len(chunks[-1]) < min_chunk_chars:
        chunks[-2] = chunks[-2] + " " + chunks.pop()

    print(f"[CHUNKER] Created {len(chunks)} chunks from {estimated_tokens} estimated tokens")
    return chunks