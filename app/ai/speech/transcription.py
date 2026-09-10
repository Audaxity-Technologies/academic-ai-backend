from faster_whisper import WhisperModel


MODEL_SIZE = "base"

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8",
)


def transcribe_audio(file_path: str) -> dict:
    segments, info = model.transcribe(
        file_path,
        beam_size=5,
    )

    transcript = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return {
        "language": info.language,
        "transcript": transcript,
    }