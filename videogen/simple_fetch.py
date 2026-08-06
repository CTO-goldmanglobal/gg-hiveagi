"""
videogen/simple_fetch.py — the production clip fetcher.

For production video creation: fetch a few candidates per shot, pick the best by
cheap opencv motion metric, return one clip per shot. NO 98-clip manifest, NO M3
vision tagging, NO judging loop. Those are research-substrate tools; this is the
"make a video" tool.

The clips are disposable: download, use, delete. Only the final rendered MP4
matters long-term (it goes to YouTube).

Usage from produce.py (simple mode):
    clips = simple_fetch(plan, work_dir / "pool")
    # clips: list[ClipAssignment] — one per shot, ready for build_edl

The "plan" is the brief's clip_hints enriched with search terms (from ingest_brief's
generated_keywords, or hand-written in the brief for production runs).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .clip_pool.fetch import _pexels_search, _pick_file, _download, _get_pexels_key
from .clip_pool.metrics import measure_clip, flag_issues
from .edl import Provenance
from .timeline import ClipAssignment

logger = logging.getLogger(__name__)

# How many candidates to fetch per shot before picking. 3 is enough to find a good
# one without wasting bandwidth; the motion metric is cheap.
_CANDIDATES_PER_SHOT = 3

# Motion floor: below this the clip is "static" (likely a still image or very slow).
# From the metrics.py calibration: accepted clips scored 1.0-5.0; below ~1.5 is static.
_MOTION_FLOOR = 1.0


def _orientation_from_aspect(aspect: str) -> str:
    """Map brief aspect_ratio to Pexels orientation param."""
    if "9:16" in aspect or "portrait" in aspect.lower():
        return "portrait"
    return "landscape"


def _fetch_one_shot(
    shot_id: str,
    search_terms: List[str],
    orientation: str,
    out_dir: Path,
    api_key: str,
    candidates_per_shot: int = _CANDIDATES_PER_SHOT,
) -> Optional[Dict[str, Any]]:
    """Fetch candidates for one shot, measure them, pick the best by motion.

    Returns the winner dict: {candidate_id, local_path, duration_sec, motion_score,
    source_type, license} or None if nothing downloaded.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates: List[Dict[str, Any]] = []

    for term in search_terms:
        if len(candidates) >= candidates_per_shot:
            break
        results = _pexels_search(term, api_key, orientation, per_page=candidates_per_shot * 2)
        # Prefer longer clips (VO segments are typically 8-13s; a 7s clip fails EDL validation).
        # Sort by duration descending so we try the longest matches first.
        results.sort(key=lambda v: float(v.get("duration", 0)), reverse=True)
        for video in results:
            if len(candidates) >= candidates_per_shot:
                break
            vid_id = video.get("id")
            # Skip clips shorter than 8s (VO segments are rarely shorter than that)
            vid_dur = float(video.get("duration", 0))
            if vid_dur < 8.0 and len(candidates) > 0:
                continue  # accept one short clip as last resort, prefer >= 8s
            file = _pick_file(video, min_w=720, min_h=720 if orientation == "portrait" else 1280)
            if not file:
                continue
            download_url = file.get("link")
            if not download_url:
                continue
            # Skip if we already have this video
            cid = f"pexels_{vid_id}"
            if any(c["candidate_id"] == cid for c in candidates):
                continue

            local_path = out_dir / f"{cid}.mp4"
            if _download(download_url, local_path):
                candidates.append({
                    "candidate_id": cid,
                    "local_path": str(local_path),
                    "source_type": "stock:pexels",
                    "license": "Pexels License",
                    "duration_sec": float(video.get("duration", 0)),
                    "search_term": term,
                    "pexels_user": video.get("user", {}).get("name", ""),
                })
                logger.info("simple_fetch: %s downloaded %s (from '%s')",
                            shot_id, cid, term)

    if not candidates:
        logger.warning("simple_fetch: %s — no candidates downloaded for terms %s",
                       shot_id, search_terms)
        return None

    # Measure motion on each candidate (cheap opencv — no vision API call)
    for cand in candidates:
        try:
            metrics = measure_clip(Path(cand["local_path"]), max_frames=30)
            cand["motion_score"] = metrics.get("motion_score") or 0.0
            cand["brightness"] = metrics.get("brightness")
            cand["flags"] = flag_issues(metrics)
        except Exception as e:  # noqa: BLE001
            logger.warning("simple_fetch: measure failed for %s: %s",
                           cand["candidate_id"], e)
            cand["motion_score"] = 0.0
            cand["flags"] = []

    # Pick the best: highest motion, no "static" flag. Fall back to least-bad.
    clean = [c for c in candidates if not any("static" in f for f in c.get("flags", []))]
    pool = clean if clean else candidates
    pool.sort(key=lambda c: c.get("motion_score", 0), reverse=True)
    winner = pool[0]

    # Delete the losers (disposable — we only keep the winner + the final render)
    for cand in candidates:
        if cand["candidate_id"] != winner["candidate_id"]:
            try:
                Path(cand["local_path"]).unlink(missing_ok=True)
            except OSError:
                pass  # best-effort cleanup

    logger.info("simple_fetch: %s → %s (motion=%.2f, %d candidates, kept 1)",
                shot_id, winner["candidate_id"], winner.get("motion_score", 0),
                len(candidates))
    return winner


def simple_fetch(
    brief: Any,
    work_dir: Path,
    *,
    api_key: Optional[str] = None,
) -> List[ClipAssignment]:
    """Fetch one good clip per shot for production. No tagging, no judging.

    Args:
        brief: Brief with clip_hints (each hint's generated_keywords or prompt
               tokens become the Pexels search terms for that shot).
        work_dir: where to write the pool/<shot>/ dirs.
        api_key: Pexels key (auto-resolved from Keychain/env if None).

    Returns:
        list[ClipAssignment] — one per clip_hint, in order. Each has source_path
        + Golden-Rule Provenance (pexels/stock). Caller passes these to build_edl.

    Raises:
        RuntimeError: if Pexels key can't be resolved, or if a shot has zero
            downloadable candidates (the pipeline can't proceed without a clip).
    """
    key = api_key or _get_pexels_key()
    import re

    # Determine orientation from the brief's aspect_ratios (first one wins)
    aspect = (brief.aspect_ratios[0] if brief.aspect_ratios else "16:9")
    orientation = _orientation_from_aspect(aspect)

    assignments: List[ClipAssignment] = []
    for i, hint in enumerate(brief.clip_hints):
        shot_id = f"shot{i+1}"

        # Search terms: prefer generated_keywords from H2, fall back to hint prompt tokens
        terms = (brief.generated_keywords or {}).get(shot_id) or []
        if not terms:
            prompt = str(hint.get("prompt", ""))
            terms = [t for t in re.findall(r"[a-z0-9]+", prompt.lower()) if len(t) >= 3]
            if terms:
                # Rejoin into a single search phrase (Pexels handles multi-word)
                terms = [" ".join(terms[:3])]

        if not terms:
            terms = [brief.tour_slug.replace("-", " ")]

        pool_dir = work_dir / "pool" / shot_id / aspect.replace(":", "")
        winner = _fetch_one_shot(shot_id, terms, orientation, pool_dir, key)

        if winner is None:
            raise RuntimeError(
                f"simple_fetch: shot '{shot_id}' could not download any clips "
                f"for search terms {terms}. Check Pexels API key + network."
            )

        # Clip window: full clip, renderer trims to VO duration later
        clip_end = float(winner.get("duration_sec", 10))
        assignments.append(ClipAssignment(
            shot_id=shot_id,
            source_path=winner["local_path"],
            clip_start_sec=0.0,
            clip_end_sec=clip_end,
            provenance=Provenance(
                source="pexels",
                asset_id=winner["candidate_id"],
                licence="Pexels",
                authenticity="stock",
            ),
        ))

    logger.info("simple_fetch: %d shots → %d clips fetched (production mode)",
                len(brief.clip_hints), len(assignments))
    return assignments
