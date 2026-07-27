"""
Selection-rationale logging — captures the human-override signal.

The valuable data is NOT "the ranker picked frame X" (that's an LLM
judgment). It's the DELTA between the model's ranking and what the human
editor actually shipped: where they promoted, demoted, rejected, or added.

This module computes that delta and writes:
  - selection_log.jsonl  (one line per frame, kept AND cut)
  - selection_summary.json (per-run aggregate)

See selection_schema.md for the full schema, scope, and PII rules.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_run_id(config_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{config_name}_{ts}"


def compute_override_log(
    analyses: List[Dict[str, Any]],
    ranker_selection: List[Dict[str, Any]],
    final_script: List[Dict[str, Any]],
    run_id: str,
    editor_id: str,
    config_name: str,
) -> List[Dict[str, Any]]:
    """
    Compute the per-frame override log by diffing model vs human selection.

    Args:
        analyses: full frame analysis list (from analyze_frames)
        ranker_selection: the model's ranking output (list of analysis dicts
                          in ranked order, from select_and_script)
        final_script: the human editor's final script
                      ([{frame_index, duration_sec, voiceover_text}, ...])
        run_id: unique run identifier
        editor_id: who made the editorial decisions
        config_name: which client config (e.g. "ech")

    Returns:
        List of log-entry dicts, one per frame in `analyses`.
    """
    # Build lookup: frame_index → ranker_rank + ranker metadata
    ranker_map: Dict[int, Dict] = {}
    for rank, entry in enumerate(ranker_selection, 1):
        fidx = entry.get("frame_index")
        if fidx is not None:
            rationale = entry.get("_ranker_rationale", {})
            ranker_map[fidx] = {
                "ranker_rank": rank,
                "ranker_reason": rationale.get("reason", ""),
                "ranker_shot_type": rationale.get("shot_type", ""),
            }

    # Build lookup: frame_index → final_rank
    final_map: Dict[int, int] = {}
    for rank, seg in enumerate(final_script, 1):
        fidx = seg.get("frame_index")
        if fidx is not None:
            final_map[fidx] = rank

    log_entries = []
    for analysis in analyses:
        fidx = analysis.get("frame_index")
        in_ranker = fidx in ranker_map
        in_final = fidx in final_map

        ranker_rank = ranker_map.get(fidx, {}).get("ranker_rank")
        ranker_reason = ranker_map.get(fidx, {}).get("ranker_reason", "")
        ranker_shot_type = ranker_map.get(fidx, {}).get("ranker_shot_type", "")
        final_rank = final_map.get(fidx)

        # Determine human_action
        if in_ranker and in_final:
            if ranker_rank == final_rank:
                human_action = "accepted"
            elif final_rank < ranker_rank:
                human_action = "promoted"
            else:
                human_action = "demoted"
        elif in_ranker and not in_final:
            human_action = "rejected"
        elif not in_ranker and in_final:
            human_action = "added"
        else:
            human_action = "rejected_by_both"

        # Source info
        frame_path = analysis.get("frame_path", "")
        source = _extract_source(frame_path)

        entry = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "editor_id": editor_id,
            "config": config_name,
            "frame_index": fidx,
            "ranker_rank": ranker_rank,
            "ranker_reason": ranker_reason,
            "ranker_shot_type": ranker_shot_type,
            "final_rank": final_rank,
            "human_action": human_action,
            "human_reason": "",  # optional, editor fills manually
            "trigger_type": analysis.get("trigger_type", "manual"),
            "frame_analysis_summary": (analysis.get("ai_analysis", "") or "")[:200],
            "source": source,
            "timestamp": _now_iso(),
        }
        log_entries.append(entry)

    return log_entries


def _extract_source(frame_path: str) -> Dict[str, Any]:
    """
    Extract source clip name + approximate timestamp from a frame path.
    Frame paths look like: .../frames/<clip_stem>/frame_000007.jpg
    """
    if not frame_path:
        return {}
    p = Path(frame_path)
    clip_stem = p.parent.name if p.parent else ""
    # frame_000007 → (7-1) * interval. We don't know interval here, so
    # store the frame number and let consumers compute timestamp if needed.
    frame_num = None
    try:
        frame_num = int(p.stem.split("_")[1])
    except (IndexError, ValueError):
        pass
    return {
        "clip": clip_stem,
        "frame_number": frame_num,
    }


def write_log(log_entries: List[Dict[str, Any]],
              run_dir: Path) -> tuple:
    """
    Write selection_log.jsonl + selection_summary.json to run_dir.

    Returns:
        (log_path, summary_path)
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # selection_log.jsonl — one JSON object per line
    log_path = run_dir / "selection_log.jsonl"
    with open(log_path, "w", encoding="utf-8") as f:
        for entry in log_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # selection_summary.json
    summary = _compute_summary(log_entries)
    summary_path = run_dir / "selection_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return log_path, summary_path


def _compute_summary(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(log_entries)
    ranker_kept = sum(1 for e in log_entries if e.get("ranker_rank") is not None)
    final_kept = sum(1 for e in log_entries if e.get("final_rank") is not None)

    override_types = {"promoted": 0, "demoted": 0, "rejected": 0, "added": 0}
    shot_type_dist: Dict[str, int] = {}

    for e in log_entries:
        action = e.get("human_action", "")
        if action in override_types:
            override_types[action] += 1
        # shot_type distribution of FINAL selection only
        if e.get("final_rank") is not None:
            st = e.get("ranker_shot_type", "unknown")
            shot_type_dist[st] = shot_type_dist.get(st, 0) + 1

    overrides = sum(override_types.values())

    # Carry run-level metadata from first entry
    first = log_entries[0] if log_entries else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": first.get("run_id", ""),
        "editor_id": first.get("editor_id", ""),
        "config": first.get("config", ""),
        "total_frames": total,
        "ranker_kept": ranker_kept,
        "final_kept": final_kept,
        "overrides": overrides,
        "override_types": override_types,
        "shot_type_distribution_final": shot_type_dist,
    }
