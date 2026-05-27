from pathlib import Path


def parse_lyrics(lyrics_path: str) -> list[str]:
    """Read lyrics txt and return non-empty lines in order."""
    text = Path(lyrics_path).read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]
