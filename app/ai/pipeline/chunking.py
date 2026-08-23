def chunk_transcript(
    transcript: str,
    chunk_size: int = 12000,
    overlap: int = 1000,
) -> list[str]:

    chunks = []

    start = 0
    transcript_length = len(transcript)

    while start < transcript_length:
        end = start + chunk_size

        chunk = transcript[start:end]

        # Try to end at the last sentence
        if end < transcript_length:
            last_period = chunk.rfind(".")

            if last_period != -1:
                chunk = chunk[:last_period + 1]

        chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks