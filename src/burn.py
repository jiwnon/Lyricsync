import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ALIGNMENT_MAP = {
    "하단 중앙": 2,
    "상단 중앙": 8,
    "중앙": 5,
}


def hex_to_ass_color(hex_color: str) -> str:
    """#RRGGBB → &H00BBGGRR (ASS opaque color, BGR order)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _first_subtitle_time(srt_path: str) -> float:
    """Return start time of first subtitle entry in seconds."""
    text = Path(srt_path).read_text(encoding="utf-8-sig")
    m = re.search(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->", text)
    if not m:
        return 0.0
    return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000


def _prepare_srt(srt_path: str) -> str:
    """Copy SRT to a simple temp path and return ffmpeg-safe escaped path."""
    tmp = Path(tempfile.gettempdir()) / "lyricsync_sub.srt"
    shutil.copy2(srt_path, tmp)
    # ffmpeg subtitles filter on Windows: forward slashes + escape drive colon
    p = str(tmp).replace("\\", "/")
    p = re.sub(r"^([A-Za-z]):/", r"\1\\:/", p)
    return p


def _force_style(font: str, size: int, fg: str, outline_col: str, outline: int, alignment: int) -> str:
    return (
        f"FontName={font},FontSize={size},"
        f"PrimaryColour={hex_to_ass_color(fg)},"
        f"OutlineColour={hex_to_ass_color(outline_col)},"
        f"Outline={outline},Alignment={alignment},Bold=0"
    )


def preview_frame(
    video_path: str,
    srt_path: str,
    font: str,
    font_size: int,
    primary_color: str,
    outline_color: str,
    outline: int,
    position: str,
) -> str:
    """Extract a single frame at the first subtitle timestamp with subtitles burned in."""
    alignment = ALIGNMENT_MAP.get(position, 2)
    style = _force_style(font, font_size, primary_color, outline_color, outline, alignment)
    srt = _prepare_srt(srt_path)
    ts = _first_subtitle_time(srt_path)
    out = str(Path(tempfile.gettempdir()) / "lyricsync_preview.jpg")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", video_path,
            "-vf", f"subtitles={srt}:force_style='{style}'",
            "-frames:v", "1",
            out,
        ],
        check=True,
        capture_output=True,
    )
    return out


def render_video(
    video_path: str,
    srt_path: str,
    font: str,
    font_size: int,
    primary_color: str,
    outline_color: str,
    outline: int,
    position: str,
) -> str:
    """Burn subtitles into the full video and return the output mp4 path."""
    alignment = ALIGNMENT_MAP.get(position, 2)
    style = _force_style(font, font_size, primary_color, outline_color, outline, alignment)
    srt = _prepare_srt(srt_path)
    stem = Path(video_path).stem
    out = str(Path(tempfile.gettempdir()) / f"{stem}_subtitled.mp4")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt}:force_style='{style}'",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "copy",
            out,
        ],
        check=True,
        capture_output=True,
    )
    return out
