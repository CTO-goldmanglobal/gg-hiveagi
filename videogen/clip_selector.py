"""
videogen/clip_selector.py — pick the best pool candidate per shot.

The selection layer that turns a tagged candidate pool + a brief's clip_hints
into one ClipAssignment per shot. This fills the produce.select_clips() stub.

WHY A SEPARATE MODULE (not inline in produce.py):
  select_clips is pure and testable: it scores candidates by tag relevance +
  measured quality, applies the "minus method" (subtract the bad), and emits
  typed ClipAssignments. Keeping it isolated lets it grow (weighted hints,
  model-based reranking) without bloating the orchestrator.

DESIGN (mirrors the house pattern from clip_pool/metrics.py + judge.py):
  - Measure, then decide. Relevance/quality are SCORES; disqualification is a
    HARD filter (commercial_grade amateur|personal, low-motion/shake flags).
  - The brief's clip_hints drive RELEVANCE — the hint prompt is the target the
    tags must match. Quality is secondary: a perfectly-shot but irrelevant clip
    loses to a relevant one.
  - Provenance is translated, not invented: a candidate's manifest source_type
    ("stock:pexels") becomes the EDL source ("pexels") + licence + authenticity.
    This is the one real mismatch documented in docs/edl-schema.md §5.

The heavyweight measurement (measure_clip, reads the video file) is INJECTED
so tests stay pure and fast — no cv2, no ffmpeg. Real mode passes nothing and
gets the default measurer (imported lazily so importing this module never
pulls cv2 or the clip_pool package init).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .edl import Provenance
from .timeline import ClipAssignment, VOSegment

logger = logging.getLogger(__name__)

# Handle padding: each shot's source window extends past the VO window so the
# renderer has in/out handles. Matches _mock_clip_assignments in produce.py.
HANDLE_PAD_SEC = 2.0

# Hint-token noise to drop before matching against tag fields. Kept tiny — we
# only want to stop function words ("the great wall") from counting as matches,
# not strip genuine content tokens.
_HINT_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "over", "with", "for", "at",
    "in", "on", "to", "is", "shot", "video", "clip",
})

# Commercial grades that fail the "broadcast/professional" bar. The LLM tagger
# distinguishes broadcast | professional | amateur | personal (clip_pool/models.py).
_DISQUALIFIED_GRADES = frozenset({"amateur", "personal"})

# Motion calibration (from clip_pool/metrics.py flag_issues): accepted clips
# scored ~1.0–5.0 mean-absdiff; below ~1.5 reads as static. Map that range onto
# 0.0–1.0 so quality nudges, never dominates (relevance sorts first).
_MOTION_FLOOR = 0.5
_MOTION_CEIL = 5.0


# --- brief ↔ shot resolution ------------------------------------------------

def hint_for_shot(brief: Any, shot_id: str) -> Dict[str, Any]:
    """Resolve the brief's clip_hint for a shot.

    Shot IDs are index-aligned with clip_hints in the mock convention
    (shot1 ↔ clip_hints[0], shot2 ↔ clip_hints[1], …). Falls back to a generic
    hint when the index is out of range or clip_hints is empty, so a sparse
    brief never crashes selection.
    """
    hints = getattr(brief, "clip_hints", None) or []
    m = re.match(r"shot(\d+)$", shot_id)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(hints):
            return hints[idx]
    # Fall back: try a direct scene/id match, else a permissive generic hint
    for h in hints:
        if str(h.get("scene")) == shot_id or str(h.get("id")) == shot_id:
            return h
    return {"scene": shot_id, "prompt": "", "duration_sec": 0}


# --- provenance translation (the Golden Rule) -------------------------------

def _edl_provenance_for(candidate: Dict[str, Any]) -> Provenance:
    """Translate a manifest candidate into an EDL Provenance object.

    The pool uses source_type prefixes ("stock:pexels", "human_capture:glasses")
    and a free-form "license" string. The EDL uses a flat source enum
    (pexels|ai_generated|company_owned|human_capture) — see docs/edl-schema.md
    §5. This is the single place that translation happens.

    Unknown source_types map to company_owned + the raw label as licence — an
    honest default rather than a silent pexels/stock mismatch that would pass
    the validator but mislabel the asset downstream.
    """
    source_type = str(candidate.get("source_type", "")).lower()
    asset_id = str(candidate.get("candidate_id", "")) or None
    raw_licence = str(candidate.get("license", "")).strip()

    if source_type.startswith("stock:pexels") or source_type == "pexels":
        source, authenticity = "pexels", "stock"
        licence = raw_licence or "Pexels"
    elif source_type.startswith("ai_generated"):
        source, authenticity = "ai_generated", "illustrative"
        licence = raw_licence or "Generated"
    elif source_type.startswith("human_capture"):
        source, authenticity = "human_capture", "documentary"
        licence = raw_licence or "Captured"
    elif source_type.startswith("company_owned"):
        source, authenticity = "company_owned", "documentary"
        licence = raw_licence or "Owned"
    else:
        # Unknown — label honestly so the QA gate can catch it later.
        source, authenticity = "company_owned", "illustrative"
        licence = raw_licence or source_type or "Unknown"

    # Normalize the common "Pexels License" → "Pexels" so result.json reads clean
    if licence.lower() in {"pexels license", "pexels licence"}:
        licence = "Pexels"

    return Provenance(
        source=source, asset_id=asset_id, licence=licence, authenticity=authenticity,
    )


# --- scoring -----------------------------------------------------------------

def _tag_text(tags: Dict[str, Any]) -> str:
    """Flatten a candidate's tag fields into one lowercase string for matching."""
    fields = ("shot_type", "camera_perspective", "time_of_day", "mood",
              "commercial_grade", "subject_action", "description")
    return " ".join(str(tags.get(f, "")) for f in fields).lower()


def _hint_tokens(prompt: str) -> List[str]:
    """Tokenize a hint prompt, dropping stopwords and short tokens."""
    toks = re.findall(r"[a-z0-9]+", prompt.lower())
    return [t for t in toks if len(t) >= 3 and t not in _HINT_STOPWORDS]


def _relevance_score(tags_for_cand: Optional[Dict[str, Any]], hint_prompt: str) -> float:
    """Token-overlap relevance between a hint prompt and a candidate's tags.

    Returns 0.0–1.0: the fraction of hint tokens that appear (as substrings) in
    the flattened tag text. Substring (not exact) matching lets "dawn" match
    time_of_day "dawn" and "golden" match "golden_hour". Empty hint or empty
    tags → 0.0 (no signal — don't let it bias the quality tie-breaker).
    """
    if not tags_for_cand or not hint_prompt:
        return 0.0
    bag = _tag_text(tags_for_cand)
    if not bag.strip():
        return 0.0
    tokens = _hint_tokens(hint_prompt)
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in bag)
    return hits / len(tokens)


def _quality_score(metrics: Optional[Dict[str, Any]]) -> float:
    """Normalized physical quality from measured metrics.

    Rewards motion (a moving clip cuts better than a static one) and dings
    extreme brightness. Returns 0.0 when metrics is missing/empty — quality is
    a tie-breaker, so an unmeasured candidate must not be biased up or down.
    """
    if not metrics:
        return 0.0
    motion = metrics.get("motion_score")
    if motion is None:
        return 0.0
    score = (float(motion) - _MOTION_FLOOR) / (_MOTION_CEIL - _MOTION_FLOOR)
    score = max(0.0, min(1.0, score))
    brightness = metrics.get("brightness")
    if brightness is not None:
        b = float(brightness)
        if b < 30 or b > 235:  # near-black or blown-out
            score *= 0.8
    return score


def _hard_disqualify(tags_for_cand: Optional[Dict[str, Any]],
                     flags: List[str]) -> Tuple[bool, List[str]]:
    """The 'minus method' — hard reasons to drop a candidate before scoring wins.

    Returns (disqualified, reasons). A disqualified candidate is only chosen if
    every candidate in the shot is disqualified (least-bad fallback), because
    build_edl still requires a source clip for every VO segment.
    """
    reasons: List[str] = []
    grade = (tags_for_cand or {}).get("commercial_grade")
    if grade and str(grade).lower() in _DISQUALIFIED_GRADES:
        reasons.append(f"commercial_grade={grade}")
    for f in flags or []:
        if "static" in f or "shake" in f:
            reasons.append(f)
    return bool(reasons), reasons


def _handle_sec(source_duration_sec: float, vo_duration_sec: float) -> Tuple[float, float]:
    """Choose clip_start/clip_end so the source window covers the VO + handles.

    clip_end - clip_start must be >= shot duration (the EDL handle rule). VO
    drives the cut, so shot duration == vo_duration. We add HANDLE_PAD_SEC of
    handle when the source is long enough; when the source is shorter we cap at
    the source length (and if that's still < vo_duration, validation will
    honestly flag it rather than silently overclaiming).
    """
    need = vo_duration_sec + HANDLE_PAD_SEC
    if not source_duration_sec or source_duration_sec <= 0:
        # Unknown source length (e.g. mock candidate) — trust VO + handle.
        return 0.0, need
    return 0.0, min(float(source_duration_sec), need)


# --- per-shot selection ------------------------------------------------------

def _select_for_shot(
    candidates: List[Dict[str, Any]],
    tags: Dict[str, Any],
    metrics_by_cand: Dict[str, Dict[str, Any]],
    shot_stats: Dict[str, float],
    hint: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """Pick the best candidate for one shot.

    Returns (winner, ai_reason, dropped) where dropped lists passed-over
    candidates + why, for the selection log. Falls back to least-bad if every
    candidate is disqualified.
    """
    from .clip_pool.metrics import flag_issues

    prompt = str(hint.get("prompt", ""))
    scored: List[Tuple[Tuple[Any, ...], Dict[str, Any], bool]] = []
    dropped: List[Dict[str, Any]] = []

    for cand in candidates:
        cid = str(cand.get("candidate_id", ""))
        cand_tags = (tags.get(cid) or {}).get("tags", {})
        m = metrics_by_cand.get(cid, {})
        flags = flag_issues(m, shot_stats) if m else []
        disqualified, reasons = _hard_disqualify(cand_tags, flags)

        rel = _relevance_score(cand_tags, prompt)
        qual = _quality_score(m)
        motion = float(m.get("motion_score") or 0.0)
        kw = len(cand.get("keywords_matched") or [])

        # Sort key (higher is better across all five):
        #   1. not disqualified — clean candidates beat disqualified ones
        #   2. relevance        — the hint prompt is the primary target
        #   3. quality          — measured physical fit (motion/brightness)
        #   4. raw motion       — fine-grained tie-break within equal quality
        #   5. keyword count    — free signal already on the Candidate
        key = (not disqualified, rel, qual, motion, kw)
        scored.append((key, cand, disqualified))

        if disqualified:
            dropped.append({"candidate_id": cid, "reason": ", ".join(reasons)})

    if not scored:
        return None, "no candidates in pool", dropped

    scored.sort(key=lambda s: s[0], reverse=True)
    (winner_key, winner, winner_dq) = scored[0]

    win_tags = (tags.get(str(winner.get("candidate_id", ""))) or {}).get("tags", {})
    bits = [str(win_tags.get(f)) for f in
            ("shot_type", "mood", "commercial_grade", "camera_perspective")
            if win_tags.get(f)]
    tag_summary = ", ".join(bits) or "no tags"
    status = "fallback (all disqualified)" if winner_dq else "best fit"
    return winner, f"{status}: {tag_summary}", dropped


# --- default measurer (real mode) -------------------------------------------

def _default_measure(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Default measurer: resolve the candidate's local_path + measure it.

    measure_clip returns empty metrics on an unreadable file, so a missing path
    degrades gracefully (quality 0) rather than raising.
    """
    from .clip_pool.metrics import measure_clip
    local = candidate.get("local_path", "")
    if not local:
        return {}
    return measure_clip(Path(local))


# --- the public selector -----------------------------------------------------

def select_clips(
    brief: Any,
    pool: Dict[str, Any],
    tags: Dict[str, Any],
    vo_segments: List[VOSegment],
    *,
    measure_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> List[ClipAssignment]:
    """Select the best candidate per shot from the tagged pool.

    One ClipAssignment per VO segment (VO drives the cut). Each carries a
    translated Provenance (Golden Rule). Respects the brief's clip_hints: the
    hint prompt is the relevance target the candidate tags must match.

    Args:
        brief: Brief with clip_hints (the per-shot intent).
        pool: pool-manifest dict — {shots: [{shot_id, candidates: [...]}]}.
        tags: {candidate_id: {tags: {...}, ...}} from clip_pool.llm_tags.
        vo_segments: one per shot; defines shot_id + the duration the source
            window must cover.
        measure_fn: injected candidate→metrics measurer (default reads the file
            via clip_pool.metrics.measure_clip). Tests pass a stub to avoid
            reading real video files.

    Returns:
        list[ClipAssignment], one per vo_segment, in VO order.

    Raises:
        ValueError: if a shot has no candidates at all. build_edl requires a
            source clip for every VO segment; failing here is clearer than
            failing downstream in timeline assembly.
    """
    from .clip_pool.metrics import compute_shot_stats

    if measure_fn is None:
        measure_fn = _default_measure

    # Index the pool by shot_id for O(1) lookup.
    shots_by_id: Dict[str, Dict[str, Any]] = {}
    for shot in pool.get("shots", []):
        shots_by_id[str(shot.get("shot_id", ""))] = shot

    assignments: List[ClipAssignment] = []
    for vo in vo_segments:
        shot = shots_by_id.get(vo.shot_id, {})
        candidates = list(shot.get("candidates", []))
        if not candidates:
            raise ValueError(
                f"select_clips: shot '{vo.shot_id}' has no candidates in the "
                f"pool — every VO segment needs at least one source clip"
            )

        # Measure each candidate (injected; real mode reads the file).
        metrics_by_cand: Dict[str, Dict[str, Any]] = {}
        for cand in candidates:
            cid = str(cand.get("candidate_id", ""))
            try:
                metrics_by_cand[cid] = measure_fn(cand)
            except Exception as e:  # noqa: BLE001 — one bad clip must not kill the shot
                logger.warning("measure failed for %s: %s — treating as unmeasured", cid, e)
                metrics_by_cand[cid] = {}

        shot_stats = compute_shot_stats(list(metrics_by_cand.values()))
        hint = hint_for_shot(brief, vo.shot_id)

        winner, ai_reason, dropped = _select_for_shot(
            candidates, tags or {}, metrics_by_cand, shot_stats, hint,
        )

        for d in dropped:
            logger.info("select_clips: %s shot %s dropped — %s",
                        d["candidate_id"], vo.shot_id, d["reason"])
        logger.info("select_clips: shot %s → %s (%s)",
                    vo.shot_id, winner.get("candidate_id"), ai_reason)

        source_dur = float(winner.get("duration_sec") or 0.0)
        clip_start, clip_end = _handle_sec(source_dur, vo.duration_sec)

        assignments.append(ClipAssignment(
            shot_id=vo.shot_id,
            source_path=str(winner.get("local_path", "")),
            clip_start_sec=clip_start,
            clip_end_sec=clip_end,
            provenance=_edl_provenance_for(winner),
        ))

    return assignments
