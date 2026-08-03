"""
Clip-pool data models — the enforced schema for the candidate-pool pipeline.

Why this module exists: every stage of clip_pool (fetch → pretag → judge →
adapt) used to communicate via ad-hoc dicts whose shape lived only in
schema.md prose and in ~24 duplicated magic-string keys (`"candidate_id"`,
`"source_type"`, `"local_path"` …). A misspelled key would fail silently
under `.get()`, and LLM tag output flowed straight to disk unvalidated —
the "DAG of hopes" failure mode reviewers named as the top code risk.

This module is the single source of truth for those shapes, in code. It
mirrors the disk format exactly (`model_dump(exclude_none=True)` round-trips
to the existing JSON), so it is backward-compatible: no data migration.

Models follow the house pattern from llm_wiki_engine/models.py:
  pydantic v2 BaseModel + Literal enums + ConfigDict(extra="ignore").

The provenance gate (videogen/provenance.py) stays the security authority;
these models carry `source_type` as a required field so the gate's input
cannot be silently dropped at a type boundary — see g0_experiment.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── schema version (single source of truth; was hardcoded in fetch.py + judge.py)
MANIFEST_SCHEMA_VERSION: Literal[1] = 1

# ── controlled vocabularies ──────────────────────────────────────────────────
# These mirror the enumerations currently baked into TAG_PROMPT in llm_tags.py.
# Keeping them here means the prompt, the model, and any future validator all
# read from one definition.
ShotType = Literal[
    "landscape",
    "architecture",
    "people",
    "detail",
    "food",
    "action",
    "aerial",
]
CameraPerspective = Literal[
    "eye_level",
    "top_angle",
    "low_angle",
    "high_angle",
    "first_person_pov",
    "drone",
    "shoulder_cam",
]
TimeOfDay = Literal[
    "dawn",
    "morning",
    "midday",
    "afternoon",
    "golden_hour",
    "dusk",
    "night",
    "unknown",
]
Mood = Literal["calm", "epic", "intimate", "energetic", "serene", "dramatic"]
CommercialGrade = Literal["broadcast", "professional", "amateur", "personal"]
Decision = Literal["accepted", "rejected"]
Orientation = Literal["landscape", "portrait", "square"]


# ── candidate (one row in pool_manifest.json → shots[].candidates[]) ─────────
class Candidate(BaseModel):
    """A single fetched clip proposed to the human editor.

    `source_type` is REQUIRED on every candidate so the provenance gate
    (is_labs_eligible) always has its input. Dropping it here is what let
    g0_experiment.py process clips with no Labs eligibility check.
    """

    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    source_type: str = Field(
        ..., description="provenance prefix, e.g. stock:pexels, human_capture:glasses"
    )
    source_url: str = ""
    local_path: str
    orientation: str
    duration_sec: float = 0.0
    width: int | None = None
    height: int | None = None
    photographer: str = ""
    license: str = ""
    keywords_matched: list[str] = Field(default_factory=list)


class Shot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    shot_id: str
    label: str = ""
    candidates: list[Candidate] = Field(default_factory=list)


class PoolManifest(BaseModel):
    """pool_manifest.json — the pool index written by fetch_pool()."""

    model_config = ConfigDict(extra="ignore")

    schema_version: int = MANIFEST_SCHEMA_VERSION
    tour: str
    source_type: str = ""
    fetched_at: str = ""
    total_clips: int = 0
    shots: list[Shot] = Field(default_factory=list)


# ── clip tag (clip_tags.json → {candidate_id: {tags: ClipTag, frames_tagged}}) ─
class ClipTag(BaseModel):
    """One frame's worth of MiniMax vision tags.

    The enum fields enforce the exact vocabulary the TAG_PROMPT asks for.
    The free-text fields (subject_action, description) are unconstrained
    because they carry genuine information, not categorical signal.
    """

    model_config = ConfigDict(extra="ignore")

    shot_type: ShotType | None = None
    camera_perspective: CameraPerspective | None = None
    time_of_day: TimeOfDay | None = None
    mood: Mood | None = None
    commercial_grade: CommercialGrade | None = None
    subject_action: str = ""
    description: str = ""


# ── verdict (one line of judgment_log.jsonl) ─────────────────────────────────
class Verdict(BaseModel):
    """A human accept/reject + the reason (the reason = the seed)."""

    model_config = ConfigDict(extra="ignore")

    schema_version: int = MANIFEST_SCHEMA_VERSION
    tour: str
    shot_id: str
    candidate_id: str
    source_type: str
    decision: Decision
    reason: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    editor_id: str
    timestamp: str


# ── the unified local-path resolver (was duplicated 7× across the package) ────
def resolve_local_path(pool_dir: Path, local_path: str) -> Path:
    """Resolve a candidate's ``local_path`` to an existing on-disk file.

    ``local_path`` is stored relative to ``pool_dir.parent`` (e.g.
    ``"pool/<shot>/<orient>/<id>.mp4"``). Most callers have it in hand as a
    plain string; this centralises the two-step fallback that every stage
    previously inlined:

      1. try ``pool_dir.parent / local_path``  (the normal case)
      2. fall back to ``pool_dir / local_path.removeprefix("pool/")``
         (handles paths that were stored relative to pool_dir itself)

    Returns the first path that exists. If neither exists, returns the
    primary (parent-relative) path so the caller's downstream ``VideoCapture``
    produces a clean "could not open" rather than a confusing wrong path.
    """
    pool_dir = Path(pool_dir)
    # Defense-in-depth: ``local_path`` originates from fetch.py's controlled
    # relative path, but reject absolute paths and parent-traversal so a
    # malformed manifest entry can never escape the pool tree. This is a
    # local research tool, so we raise (not silently skip) on tampering.
    if local_path.startswith("/") or "\x00" in local_path:
        raise ValueError(f"rejecting absolute/null local_path: {local_path!r}")
    if ".." in Path(local_path).parts:
        raise ValueError(f"rejecting parent-traversal in local_path: {local_path!r}")

    primary = pool_dir.parent / local_path
    if primary.exists():
        return primary
    # Stored relative to pool_dir itself, with a leading "pool/" prefix.
    # removeprefix (not str.replace) — replace would wrongly strip a "pool/"
    # segment that appears mid-path (e.g. "tours/pool/..."), yielding a wrong file.
    alt = pool_dir / local_path.removeprefix("pool/")
    if alt.exists():
        return alt
    # Nothing on disk — surface the primary path so the failure is traceable
    # to the actual stored value, not to the fallback guess.
    return primary
