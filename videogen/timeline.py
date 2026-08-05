"""
videogen/timeline.py — VO is the master clock (H3, bug #1 fix).

The #1 bug in Circle F was VO/footage desync: cuts were planned to arbitrary
durations, then VO was generated to different lengths. The fix: **VO drives
the cut.** Each shot's visual duration IS its VO segment's measured duration.

This module has two parts:
  1. generate_vo_segments() — TTS network call (MiniMax speech-2.8-hd),
     one MP3 per script segment, measures actual duration via ffprobe.
  2. build_edl() — PURE function that assigns VO segments to clips and
     builds a valid EDL using compute_total_duration() from edl.py.

build_edl is deliberately separate from generate_vo_segments so it can be
tested without network calls. The test feeds synthetic durations.

Design (from edl-schema.md §2 + the audit):
  - Default transitions are CUTS (no crossfade overlap). This guarantees VO
    windows are non-overlapping and total = sum = max(start+dur).
  - Crossfades are a RENDERING decision (compose/finish), not a TIMING
    decision (EDL). The EDL records authoritative timeline positions; the
    renderer may dissolve between them without changing the timeline.
  - total_duration_sec is ALWAYS derived from compute_total_duration(),
    never from a manual sum. (The H1 fix.)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .edl import (
    EDL,
    EDL_SCHEMA_VERSION,
    Provenance,
    Shot,
    Transition,
    compute_total_duration,
)

logger = logging.getLogger(__name__)


# --- models ------------------------------------------------------------------

class VOSegment(BaseModel):
    """One TTS-generated voiceover segment + its measured duration."""
    shot_id: str
    text: str
    mp3_path: str
    duration_sec: float


class ClipAssignment(BaseModel):
    """Which source clip fills a shot, and which window of it to use."""
    shot_id: str
    source_path: str
    clip_start_sec: float = 0.0
    clip_end_sec: float = 0.0
    provenance: Provenance


# --- TTS (network) -----------------------------------------------------------

MINIMAX_TTS_URL = "https://api.minimax.chat/v1/t2a_v2"
DEFAULT_VOICE_ID = "English_expressive_narrator"
DEFAULT_SPEED = 0.9


def _resolve_minimax_key() -> str:
    """Resolve MiniMax API key from env or .env (never prints the value)."""
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY not found in env or .env")


def _tts_segment(
    text: str,
    out_path: Path,
    api_key: str,
    voice_id: str = DEFAULT_VOICE_ID,
    speed: float = DEFAULT_SPEED,
) -> bool:
    """Generate one VO segment via MiniMax speech-2.8-hd. Returns success."""
    payload = json.dumps({
        "model": "speech-2.8-hd",
        "text": text,
        "voice_setting": {"voice_id": voice_id, "speed": speed},
        "audio_setting": {"format": "mp3", "sample_rate": 32000},
    }).encode("utf-8")
    req = urllib.request.Request(
        MINIMAX_TTS_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        import urllib.error
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        audio_hex = data.get("data", {}).get("audio", "")
        if not audio_hex:
            logger.error("TTS returned no audio for: %s", text[:50])
            return False
        out_path.write_bytes(bytes.fromhex(audio_hex))
        return True
    except Exception as e:
        logger.error("TTS failed for segment: %s", e)
        return False


def _probe_duration(path: Path) -> float:
    """Measure an audio file's duration via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15, check=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning("ffprobe failed on %s: %s — falling back to 0", path, e)
        return 0.0


def generate_vo_segments(
    script: List[Dict[str, str]],
    work_dir: Path,
    voice_id: str = DEFAULT_VOICE_ID,
    speed: float = DEFAULT_SPEED,
    api_key: Optional[str] = None,
) -> List[VOSegment]:
    """Generate one VO MP3 per script segment via MiniMax TTS.

    Args:
        script: [{shot_id: "...", text: "..."}, ...]
        work_dir: where to write the MP3 files
        voice_id: MiniMax voice ID
        speed: TTS speed factor
        api_key: MiniMax key (auto-resolved if None)

    Returns:
        List[VOSegment] with measured durations. The measured duration IS
        the shot's visual duration (VO drives the cut).
    """
    key = api_key or _resolve_minimax_key()
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    vo_dir = work_dir / "vo"
    vo_dir.mkdir(exist_ok=True)

    segments: List[VOSegment] = []
    for item in script:
        shot_id = item["shot_id"]
        text = item["text"]
        mp3_path = vo_dir / f"{shot_id}.mp3"

        if not _tts_segment(text, mp3_path, key, voice_id, speed):
            raise RuntimeError(f"TTS failed for shot {shot_id}")

        duration = _probe_duration(mp3_path)
        if duration <= 0:
            raise RuntimeError(f"Could not measure VO duration for shot {shot_id}")

        segments.append(VOSegment(
            shot_id=shot_id, text=text,
            mp3_path=str(mp3_path), duration_sec=duration,
        ))
        logger.info("VO %s: %.2fs", shot_id, duration)

    return segments


# --- EDL builder (pure, testable) -------------------------------------------

def build_edl(
    vo_segments: List[VOSegment],
    clip_assignments: List[ClipAssignment],
    transition_type: str = "cut",
    transition_dur: float = 0.0,
    tour: str = "untitled",
) -> EDL:
    """Build a valid EDL from VO segments + clip assignments.

    VO DRIVES THE CUT: each shot's duration_sec = its VO segment's measured
    duration. Positions are cumulative (cuts). total_duration_sec is derived
    from compute_total_duration(), never from a manual sum.

    Args:
        vo_segments: measured VO per shot (from generate_vo_segments)
        clip_assignments: which source clip fills each shot
        transition_type: "cut" (default) or "xfade"
        transition_dur: crossfade duration (only used if transition_type="xfade")
        tour: tour slug for the EDL

    Returns:
        A valid EDL. Call validate_edl() to confirm before writing.
    """
    assignment_map = {a.shot_id: a for a in clip_assignments}

    shots: List[Shot] = []
    timeline_cursor = 0.0

    for vo in vo_segments:
        assignment = assignment_map.get(vo.shot_id)
        if assignment is None:
            raise ValueError(
                f"No clip assignment for shot '{vo.shot_id}' — "
                f"every VO segment needs a source clip"
            )

        # VO drives the cut: visual duration = VO duration
        duration = vo.duration_sec

        shot = Shot(
            shot_id=vo.shot_id,
            source_path=assignment.source_path,
            clip_start_sec=assignment.clip_start_sec,
            clip_end_sec=assignment.clip_end_sec,
            timeline_start_sec=timeline_cursor,
            duration_sec=duration,
            vo_segment=Path(vo.mp3_path).name,
            vo_duration_sec=vo.duration_sec,
            subtitle_text=vo.text,
            transition=Transition(type=transition_type, duration_sec=transition_dur),
            purpose=f"VO-driven cut: {duration:.2f}s",
            provenance=assignment.provenance,
        )
        shots.append(shot)

        # Advance the cursor. For cuts: next start = current start + duration.
        # For xfades: the transition overlap is a render-time concern that
        # doesn't change VO timing (VO windows stay non-overlapping).
        timeline_cursor += duration

    total = compute_total_duration(shots)

    return EDL(
        schema_version=EDL_SCHEMA_VERSION,
        tour=tour,
        total_duration_sec=total,
        edl=shots,
    )
