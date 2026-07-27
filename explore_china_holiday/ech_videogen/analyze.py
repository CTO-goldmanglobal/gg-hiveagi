"""
Stage 2 — ANALYZE
The Labs↔Forge seam.

Iterates frames, calls llm_wiki_engine.vision.process_frame() on each.
ECH never touches MiniMax / DeepSeek / PII directly — all of that stays
inside Labs. This means:
  - The PII safety gate (face/plate blur) is automatically enforced on
    ECH clips. A tourist video with bystanders gets blurred before the
    LLM sees it, for free.
  - If Labs' vision API changes, ECH adapts in this one file.

Output: a list of frame-analysis dicts the SELECT stage consumes.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any


def _ensure_labs_importable():
    """Add repo root to sys.path so `llm_wiki_engine` is importable."""
    # ech_videogen/ is at explore_china_holiday/ech_videogen/
    # repo root is two parents up from this file's parent
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def analyze_frames(frames: List[Path],
                   location_hint: str = "China",
                   verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Run vision analysis on each frame via the Labs pipeline.

    Args:
        frames: list of frame image paths
        location_hint: e.g. "Beijing", "Guilin", "China" — passed to LLM
        verbose: print progress

    Returns:
        List of dicts, one per frame:
        [{
            "frame_path": str,
            "frame_index": int,
            "trigger_type": str,
            "domain": str,
            "tags": [str, ...],
            "ai_analysis": str,
            "related_links": [str, ...],
        }, ...]

    Raises:
        ImportError: if llm_wiki_engine or its deps aren't available
        SafetyError: if PII blur fails (propagates from Labs)
    """
    _ensure_labs_importable()
    from llm_wiki_engine.vision import process_frame
    from llm_wiki_engine.config import load_config

    config = load_config(mock_mode=False)  # vision needs real MiniMax

    results = []
    for i, frame in enumerate(frames):
        if verbose:
            print(f"  👁️  [{i + 1}/{len(frames)}] {frame.parent.name}/{frame.name}")
        try:
            raw = process_frame(
                str(frame),
                config,
                location_hint=location_hint,
                # Force English participant description — ECH reels target
                # English-speaking markets, so the analysis + downstream
                # script must be English regardless of input language.
                participant_description="(tourism footage frame — respond in English)",
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
            # Log + skip — don't kill the whole run for one bad frame
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
