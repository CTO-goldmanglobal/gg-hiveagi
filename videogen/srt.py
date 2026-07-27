"""
SRT subtitle generation.
Converts a script [{frame_index, duration_sec, voiceover_text}, ...] into
a .srt file with sequential timings.
(Generic pipeline core — moved from ech_videogen.)
"""

from pathlib import Path
from typing import List, Dict


def _format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _wrap_text(text: str, max_chars: int = 42) -> str:
    if len(text) <= max_chars:
        return text
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + (1 if current_len > 0 else 0)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def script_to_srt(script: List[Dict], out_path: Path,
                  max_chars_per_line: int = 42) -> Path:
    """Convert a script to an SRT file."""
    lines = []
    current_time = 0.0
    for i, segment in enumerate(script, 1):
        duration = float(segment.get("duration_sec", 5.0))
        text = segment.get("voiceover_text", "").strip()
        if not text:
            current_time += duration
            continue
        start = _format_timestamp(current_time)
        end = _format_timestamp(current_time + duration)
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(_wrap_text(text, max_chars_per_line))
        lines.append("")
        current_time += duration

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
