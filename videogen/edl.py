"""
videogen/edl.py — the Edit Decision List (EDL) schema and validator.

This is the H1 keystone: every downstream module (timeline, compose, finish,
qa_gate) reads or writes the EDL. Getting the schema + validator right first
prevents rework.

THE AUDIT FIX (OpenAI §5 / v3 §5a):
    The old build plan (VIDEO-PIPELINE-BUILD-PLAN.md H1) said "durations sum
    to total_duration_sec". That is WRONG when crossfades overlap. With
    transitions:

        total = Σd_i − Σx_i          (d = shot duration, x = crossfade overlap)

    The correct computation derives total from timeline positions:

        total = max(timeline_start[i] + duration_sec[i])

    This validator uses the correct formula. A test explicitly proves that
    the old sum-based check would have passed a desynced EDL.

Usage:
    from videogen.edl import load_edl, write_edl, validate_edl, EDL

    edl = load_edl(Path("handoff/edl.json"))
    errors = validate_edl(edl)
    if errors:
        raise ValueError(f"EDL invalid: {errors}")
    write_edl(edl, Path("handoff/edl.json"))
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- constants ---------------------------------------------------------------

EDL_SCHEMA_VERSION = 1
TOTAL_DURATION_TOLERANCE_SEC = 0.5  # ±0.5s — humans can't perceive smaller desync

# EDL-level provenance sources (build plan §2.2 media_provenance).
# NOTE: these are NOT the same as videogen.provenance source types (stock/
# ai_generated/human_capture). The unification to 4-dimension provenance
# (v3 §3) is Gate 1 work — see docs/edl-schema.md §"Provenance gap".
EDL_SOURCES = {"pexels", "ai_generated", "company_owned", "human_capture"}
EDL_AUTHENTICITY = {"stock", "illustrative", "documentary"}

# Transition types
TRANSITION_XFADE = "xfade"
TRANSITION_CUT = "cut"
TRANSITION_NONE = "none"


# --- models ------------------------------------------------------------------

class Transition(BaseModel):
    """The transition OUT of this shot (into the next). The last shot's
    transition is ignored for total-duration computation."""
    type: str = TRANSITION_CUT
    duration_sec: float = 0.0


class Provenance(BaseModel):
    """Per-shot provenance — the Golden Rule (build plan §2.3): every shot
    MUST carry source, licence, and authenticity. The ECH ACA gate rejects
    videos with un-provenanced assets."""
    source: str           # pexels | ai_generated | company_owned | human_capture
    asset_id: Optional[str] = None
    licence: str          # "Pexels" | "Commercial" | "CC-BY-NC-SA-4.0" | ...
    authenticity: str     # stock | illustrative | documentary


class Shot(BaseModel):
    shot_id: str
    source_path: Optional[str] = None
    clip_start_sec: float = 0.0
    clip_end_sec: float = 0.0
    timeline_start_sec: float
    duration_sec: float
    vo_segment: Optional[str] = None
    vo_duration_sec: Optional[float] = None
    subtitle_text: Optional[str] = None
    transition: Transition = Field(default_factory=Transition)
    purpose: Optional[str] = None
    ai_reason: Optional[str] = None
    human_override: Optional[str] = None
    human_clip_start_sec: Optional[float] = None
    human_clip_end_sec: Optional[float] = None
    provenance: Optional[Provenance] = None
    silent: bool = False


class EDL(BaseModel):
    schema_version: int = EDL_SCHEMA_VERSION
    tour: str
    total_duration_sec: float
    edl: List[Shot]


# --- I/O ---------------------------------------------------------------------

def load_edl(path: Path | str) -> EDL:
    """Load and parse an EDL JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return EDL.model_validate(data)


def write_edl(edl: EDL, path: Path | str) -> None:
    """Write an EDL to disk as JSON."""
    Path(path).write_text(edl.model_dump_json(indent=2), encoding="utf-8")


# --- the validator -----------------------------------------------------------

def _overlap_sec(shot: Shot) -> float:
    """Crossfade overlap OUT of this shot (0 for cuts)."""
    if shot.transition.type == TRANSITION_XFADE:
        return shot.transition.duration_sec
    return 0.0


def compute_total_duration(shots: List[Shot]) -> float:
    """THE FIX — derive total from timeline positions, not from summing.

    total = max(timeline_start[i] + duration_sec[i])

    This accounts for crossfade overlaps. Summing durations would overcount
    by the total overlap, causing VO/footage desync (Circle F's 16-second bug).
    Returns 0.0 for an empty shot list (an empty EDL has zero duration).
    """
    if not shots:
        return 0.0
    return max(s.timeline_start_sec + s.duration_sec for s in shots)


def validate_edl(edl: EDL) -> List[str]:
    """Validate an EDL against the schema rules.

    Returns a list of error strings. Empty list = valid.
    Every downstream module (timeline, compose, qa_gate) should call this
    before consuming an EDL.
    """
    errors: List[str] = []

    # 1. Schema version
    if edl.schema_version != EDL_SCHEMA_VERSION:
        errors.append(
            f"schema_version is {edl.schema_version}, expected {EDL_SCHEMA_VERSION}"
        )

    # 2. Non-empty
    if not edl.edl:
        errors.append("edl is empty — at least one shot required")
        return errors  # nothing else to check

    # 3. Unique shot_ids
    ids = [s.shot_id for s in edl.edl]
    seen: set[str] = set()
    for sid in ids:
        if sid in seen:
            errors.append(f"duplicate shot_id: {sid}")
        seen.add(sid)

    # 4. timeline_start_sec consistency + ordering
    shots = sorted(edl.edl, key=lambda s: s.timeline_start_sec)
    if shots[0].timeline_start_sec != 0.0:
        errors.append(
            f"first shot timeline_start_sec is {shots[0].timeline_start_sec}, "
            f"expected 0.0"
        )

    for i in range(len(shots) - 1):
        expected_next_start = (
            shots[i].timeline_start_sec
            + shots[i].duration_sec
            - _overlap_sec(shots[i])
        )
        actual_next_start = shots[i + 1].timeline_start_sec
        if abs(actual_next_start - expected_next_start) > TOTAL_DURATION_TOLERANCE_SEC:
            errors.append(
                f"timeline gap: shot '{shots[i + 1].shot_id}' starts at "
                f"{actual_next_start}s, expected {expected_next_start}s "
                f"(prev end {shots[i].timeline_start_sec + shots[i].duration_sec}s "
                f"− overlap {_overlap_sec(shots[i])}s)"
            )

    # 5. THE FIX — total_duration derived from max(start + dur), NOT sum
    computed_total = compute_total_duration(shots)
    if abs(computed_total - edl.total_duration_sec) > TOTAL_DURATION_TOLERANCE_SEC:
        naive_sum = sum(s.duration_sec for s in shots)
        errors.append(
            f"total_duration_sec is {edl.total_duration_sec}s, but "
            f"max(start+dur) = {computed_total}s "
            f"(naive sum of durations = {naive_sum}s — that would be WRONG "
            f"if crossfades overlap). The total must equal max(start+dur)."
        )

    # 6. Each shot: source_path or human_override
    for s in edl.edl:
        if not s.source_path and not s.human_override:
            errors.append(
                f"shot '{s.shot_id}': no source_path and no human_override"
            )

    # 7. Each shot: vo_segment or silent
    for s in edl.edl:
        if not s.vo_segment and not s.silent:
            errors.append(
                f"shot '{s.shot_id}': no vo_segment and not marked silent"
            )

    # 8. Golden Rule — provenance present
    for s in edl.edl:
        if s.provenance is None:
            errors.append(
                f"shot '{s.shot_id}': missing provenance (Golden Rule: "
                f"source + licence + authenticity required)"
            )
        else:
            if s.provenance.source not in EDL_SOURCES:
                errors.append(
                    f"shot '{s.shot_id}': provenance.source '{s.provenance.source}' "
                    f"not in {EDL_SOURCES}"
                )
            if s.provenance.authenticity not in EDL_AUTHENTICITY:
                errors.append(
                    f"shot '{s.shot_id}': provenance.authenticity "
                    f"'{s.provenance.authenticity}' not in {EDL_AUTHENTICITY}"
                )
            if not s.provenance.licence:
                errors.append(
                    f"shot '{s.shot_id}': provenance.licence is empty"
                )

    # 9. Clip handles — source segment long enough for the shot
    for s in edl.edl:
        source_dur = s.clip_end_sec - s.clip_start_sec
        if source_dur < s.duration_sec - TOTAL_DURATION_TOLERANCE_SEC:
            errors.append(
                f"shot '{s.shot_id}': source clip {source_dur}s "
                f"(clip_start {s.clip_start_sec} → clip_end {s.clip_end_sec}) "
                f"is shorter than shot duration {s.duration_sec}s"
            )

    # 10. VO fits within the shot (audio/visual validated separately)
    for s in edl.edl:
        if s.vo_duration_sec is not None and not s.silent:
            if s.vo_duration_sec > s.duration_sec + TOTAL_DURATION_TOLERANCE_SEC:
                errors.append(
                    f"shot '{s.shot_id}': vo_duration {s.vo_duration_sec}s "
                    f"exceeds shot duration {s.duration_sec}s"
                )

    if errors:
        logger.warning("EDL validation failed with %d errors", len(errors))
    return errors
