"""
Map lyrics lines to ASR word timestamps.

Strategy:
  1. Flatten lyrics lines → word list, remembering which line each word belongs to.
  2. Normalize both lyrics words and ASR words (strip punctuation, lowercase).
  3. Use SequenceMatcher to find equal/replace blocks — these anchor lyrics words
     to ASR word indices.
  4. Fill unmatched lyrics words by linear interpolation between anchors.
  5. For each lyrics line: start = first word's start, end = last word's end.
"""

import re
import unicodedata
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[^\w]", "", text, flags=re.UNICODE)
    return text


def _build_lyrics_word_list(lines: list[str]) -> tuple[list[str], list[int]]:
    """Returns (words, line_ids) where line_ids[i] is the line index of words[i]."""
    words, line_ids = [], []
    for line_idx, line in enumerate(lines):
        for w in line.split():
            words.append(w)
            line_ids.append(line_idx)
    return words, line_ids


def _sequence_match(lyrics_norm: list[str], asr_norm: list[str]) -> dict[int, int]:
    """Map lyrics word index → ASR word index using SequenceMatcher."""
    mapping: dict[int, int] = {}
    matcher = SequenceMatcher(None, lyrics_norm, asr_norm, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for di in range(i2 - i1):
                mapping[i1 + di] = j1 + di
        elif tag == "replace":
            # Proportional mapping for replaced blocks
            l_count = i2 - i1
            a_count = j2 - j1
            for di in range(l_count):
                ratio = di / max(l_count - 1, 1)
                aj = j1 + round(ratio * (a_count - 1))
                mapping[i1 + di] = min(aj, j2 - 1)

    return mapping


def _interpolate_mapping(mapping: dict[int, int], total: int, asr_len: int) -> list[int]:
    """Fill all indices 0..total-1 by interpolating between known anchor points."""
    result = [None] * total

    for i, j in mapping.items():
        result[i] = j

    # Forward fill from anchors + linear interpolation between them
    keys = sorted(mapping.keys())

    if not keys:
        # No matches at all: spread evenly
        for i in range(total):
            result[i] = round(i / max(total - 1, 1) * (asr_len - 1))
        return result

    # Before first anchor
    for i in range(keys[0]):
        result[i] = max(0, mapping[keys[0]] - (keys[0] - i))

    # Between anchors
    for k in range(len(keys) - 1):
        a, b = keys[k], keys[k + 1]
        ja, jb = mapping[a], mapping[b]
        for i in range(a + 1, b):
            t = (i - a) / (b - a)
            result[i] = ja + round(t * (jb - ja))

    # After last anchor
    for i in range(keys[-1] + 1, total):
        result[i] = min(asr_len - 1, mapping[keys[-1]] + (i - keys[-1]))

    return result


def align_lyrics_to_timestamps(
    lyrics_lines: list[str],
    asr_words: list[dict],
) -> list[dict]:
    """
    Returns list of segments:
      [{text: str, start: float, end: float}, ...]
    one entry per non-empty lyrics line.
    """
    if not asr_words:
        raise ValueError("ASR returned no word timestamps. Check audio quality or language setting.")

    lyrics_words, line_ids = _build_lyrics_word_list(lyrics_lines)

    lyrics_norm = [_normalize(w) for w in lyrics_words]
    asr_norm = [_normalize(w["word"]) for w in asr_words]

    raw_mapping = _sequence_match(lyrics_norm, asr_norm)
    full_mapping = _interpolate_mapping(raw_mapping, len(lyrics_words), len(asr_words))

    # Collect per-line start/end from assigned ASR word timestamps
    line_starts: dict[int, float] = {}
    line_ends: dict[int, float] = {}

    for lw_idx, asr_idx in enumerate(full_mapping):
        line_idx = line_ids[lw_idx]
        asr_idx = max(0, min(asr_idx, len(asr_words) - 1))
        t_start = asr_words[asr_idx]["start"]
        t_end = asr_words[asr_idx]["end"]

        if line_idx not in line_starts or t_start < line_starts[line_idx]:
            line_starts[line_idx] = t_start
        if line_idx not in line_ends or t_end > line_ends[line_idx]:
            line_ends[line_idx] = t_end

    segments = []
    for i, line in enumerate(lyrics_lines):
        start = line_starts.get(i, 0.0)
        end = line_ends.get(i, start + 2.0)
        if end <= start:
            end = start + 0.5
        segments.append({"text": line, "start": round(start, 3), "end": round(end, 3)})

    return segments
