import subprocess
import tempfile
from pathlib import Path


def extract_audio(video_path: str, output_path: str | None = None) -> str:
    """Extract mono 16kHz WAV from video file using ffmpeg."""
    if output_path is None:
        stem = Path(video_path).stem
        output_path = str(Path(tempfile.gettempdir()) / f"{stem}_audio.wav")

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn",          # no video
            "-ac", "1",     # mono
            "-ar", "16000", # 16kHz (WhisperX requirement)
            "-f", "wav", output_path,
        ],
        check=True,
        capture_output=True,
    )
    return output_path
