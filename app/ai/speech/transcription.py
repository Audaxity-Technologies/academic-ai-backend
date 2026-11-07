from functools import lru_cache


MODEL_SIZE = "base"

@lru_cache(maxsize=1)
def get_model():
    from faster_whisper import WhisperModel
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> dict:
    segments, info = get_model().transcribe(
        file_path,
        beam_size=5,
    )

    # Preserve segments with timestamps for evidence extraction
    segments_with_timestamps = [
        {
            "text": segment.text.strip(),
            "start": segment.start,
            "end": segment.end,
        }
        for segment in segments
    ]

    return {
        "language": info.language,
        "transcript": " ".join(segment["text"] for segment in segments_with_timestamps),
        "segments": segments_with_timestamps,
    }
