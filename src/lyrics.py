import re
from pathlib import Path

# 줄 앞의 숫자 인덱스 제거: "1 가사", "1\t가사", "1. 가사" 등
_LINE_NUM_RE = re.compile(r"^\d+[\.\t\s]+")


def parse_lyrics(lyrics_path: str) -> list[str]:
    """Read lyrics txt and return non-empty lines in order.
    Strips leading line numbers (e.g. '1  가사' → '가사').
    """
    text = Path(lyrics_path).read_text(encoding="utf-8")
    lines = []
    for raw in text.splitlines():
        line = _LINE_NUM_RE.sub("", raw).strip()
        if line:
            lines.append(line)
    return lines
