"""
Stage 2 — ANALYZE (the Labs↔Forge seam)

Iterates frames, calls llm_wiki_engine.vision.process_frame() on each.
This module never touches MiniMax / DeepSeek / PII directly — all of that
stays inside Labs. The PII safety gate (face/plate blur) is automatically
enforced on every frame, for free.

Output: a list of frame-analysis dicts the SELECT stage consumes.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any


# Locate the repo root so `llm_wiki_engine` is importable.
# Explicit env var wins; fallback is one parent up from this file
# (videogen/ is at repo root, so parents[1] is correct).
_REPO_ROOT = Path(os.environ.get(
    "VIDEOGEN_REPO_ROOT",
    Path(__file__).resolve().parents[1],
))


def _ensure_labs_importable():
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))


def analyze_frames(frames: List[Path],
                   location_hint: str = "China",
                   force_english: bool = True,
                   verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Run vision analysis on each frame via the Labs pipeline.

    Args:
        frames: list of frame image paths
        location_hint: e.g. "Beijing", "Guilin", "China" — passed to LLM
        force_english: if True, the participant_description hints English output
                       (the vision pipeline follows input language by default;
                        commercial reels target English-speaking markets)
        verbose: print progress

    Returns:
        List of dicts, one per frame.

    Raises:
        ImportError: if llm_wiki_engine or its deps aren't available
        SafetyError: if PII blur fails (propagates from Labs)
    """
    _ensure_labs_importable()
    from llm_wiki_engine.vision import process_frame
    from llm_wiki_engine.config import load_config

    config = load_config(mock_mode=False)  # vision needs real MiniMax

    hint = "(tourism footage frame — respond in English)" if force_english \
           else "(tourism footage frame)"

    results = []
    for i, frame in enumerate(frames):
        if verbose:
            print(f"  👁️  [{i + 1}/{len(frames)}] {frame.parent.name}/{frame.name}")
        try:
            raw = process_frame(
                str(frame),
                config,
                location_hint=location_hint,
                participant_description=hint,
            )
            extra = getattr(raw, "_vision_extra", {}) or {}
            results.append({
                "frame_path": str(frame),
                "frame_index": i,
                "trigger_type": raw.trigger_type,
                "domain": raw.domain,
                "tags": raw.tags,
                "ai_analysis": extra.get("ai_analysis", ""),
                "related_links": extra.get("related_links", []),
            })
            if verbose and extra.get("ai_analysis"):
                preview = extra["ai_analysis"][:80].replace("\n", " ")
                print(f"       → {preview}...")
        except Exception as e:
            print(f"       ⚠️  {type(e).__name__}: {e}")
            results.append({
                "frame_path": str(frame),
                "frame_index": i,
                "error": f"{type(e).__name__}: {e}",
                "ai_analysis": "",
                "tags": [],
                "related_links": [],
                "trigger_type": "manual",
                "domain": "tourism",
            })
    return results
