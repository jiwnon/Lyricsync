"""
End-to-end pipeline:
  video + lyrics.txt → SRT
"""

from pathlib import Path

from src.audio import extract_audio
from src.lyrics import parse_lyrics
from src.transcribe import load_model, get_word_timestamps
from src.align import align_lyrics_to_timestamps
from src.srt_writer import write_srt


def run(
    video_path: str,
    lyrics_path: str,
    output_path: str | None = None,
    model_size: str = "large-v2",
    language: str = "ko",
    progress_callback=None,
) -> tuple[list[dict], str]:
    """
    Returns (segments, srt_path).
    progress_callback(step: str) is called at each stage if provided.
    """

    def log(msg: str):
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)

    log("오디오 추출 중...")
    audio_path = extract_audio(video_path)

    log(f"WhisperX 모델 로드 중 ({model_size})...")
    model, device = load_model(model_size=model_size, language=language)

    log("음성 인식 + 타임스탬프 추출 중...")
    asr_words = get_word_timestamps(audio_path, model, device, language=language)

    log("가사 파싱 중...")
    lyrics_lines = parse_lyrics(lyrics_path)

    log("가사-타임스탬프 정렬 중...")
    segments = align_lyrics_to_timestamps(lyrics_lines, asr_words)

    if output_path is None:
        output_path = str(Path(video_path).with_suffix(".srt"))

    log(f"SRT 저장 중: {output_path}")
    write_srt(segments, output_path)

    log("완료!")
    return segments, output_path
