from faster_whisper import WhisperModel


MODEL_SIZE = "base"

model = WhisperModel(
    MODEL_SIZE,
    device="cuda",
    compute_type="float16",
)


def transcribe_audio(file_path: str) -> str:
    segments, _ = model.transcribe(
        file_path,
        beam_size=5,
    )

    transcript = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return transcript