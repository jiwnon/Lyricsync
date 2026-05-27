import torch
import whisperx


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model(model_size: str = "large-v2", language: str = "ko", device: str | None = None):
    device = device or get_device()
    compute_type = "float16" if device == "cuda" else "int8"
    model = whisperx.load_model(
        model_size, device, compute_type=compute_type, language=language
    )
    return model, device


def get_word_timestamps(
    audio_path: str,
    model,
    device: str,
    language: str = "ko",
    batch_size: int = 16,
) -> list[dict]:
    """
    Run WhisperX ASR + forced alignment.
    Returns flat list of word-level dicts: {word, start, end}.
    ASR transcript is used only for timing — text is discarded later.
    """
    audio = whisperx.load_audio(audio_path)

    result = model.transcribe(audio, batch_size=batch_size, language=language)

    align_model, metadata = whisperx.load_align_model(
        language_code=language, device=device
    )
    aligned = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    words = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                words.append(
                    {"word": w["word"].strip(), "start": w["start"], "end": w["end"]}
                )
    return words
