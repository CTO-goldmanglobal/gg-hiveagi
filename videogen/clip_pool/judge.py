"""
Stage 2 — Judge. The human verdict + reason, captured as seed.

This is the core of the "beauty standard" learning loop. For every candidate
in the pool, the human decides accept/reject and says WHY. That reason — not
the verdict alone — is the human perspective that becomes hybrid seed.

The tool surfaces metrics (brightness/motion/shake) and flags as TRIAGE, so
the human can skip obvious rejects faster. But the human always decides.

Usage:
  python -m videogen.clip_pool judge --pool-dir <pool/>

Workflow:
  - Reads pool_manifest.json + measures metrics for every clip (cached)
  - For each clip: shows path, metrics, flags, asks verdict (a/r/s) + reason
  - Appends to judgment_log.jsonl (append-only; re-judging adds a new line)
  - On exit: writes judgment_summary.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from .metrics import measure_clip, flag_issues, compute_shot_stats

SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_or_measure_metrics(manifest: Dict[str, Any], pool_dir: Path,
                             force: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Measure metrics for every clip, with a disk cache (clip_metrics.json).
    Returns {candidate_id: metrics_dict}.
    """
    cache_path = pool_dir / "clip_metrics.json"
    cache = {}
    if cache_path.exists() and not force:
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cache = {}

    for shot in manifest.get("shots", []):
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            if cid in cache and not force:
                continue
            local = pool_dir.parent / cand["local_path"]
            if not local.exists():
                # local_path is relative to tour_dir (pool's parent)
                local = pool_dir / cand["local_path"].replace("pool/", "", 1)
            if not local.exists():
                print(f"  ⚠️  {cid}: file missing, skipping metrics")
                continue
            print(f"  📐 measuring {cid} ...", end="", flush=True)
            m = measure_clip(local)
            cache[cid] = m
            print(f" bright={m['brightness']:.0f} motion={m['motion_score']:.2f}")
            cache_path.write_text(
                json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    return cache


def _load_existing_verdicts(pool_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load existing judgment_log.jsonl, return {candidate_id: latest_entry}."""
    log_path = pool_dir / "judgment_log.jsonl"
    if not log_path.exists():
        return {}
    latest = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            cid = entry.get("candidate_id")
            if cid:
                latest[cid] = entry  # last wins
        except json.JSONDecodeError:
            continue
    return latest


def _append_verdict(pool_dir: Path, entry: Dict[str, Any]) -> Path:
    """Append one verdict to judgment_log.jsonl."""
    log_path = pool_dir / "judgment_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return log_path


def _write_summary(pool_dir: Path, manifest: Dict[str, Any]) -> Path:
    """Recompute + write judgment_summary.json from the full log."""
    log_path = pool_dir / "judgment_log.jsonl"
    entries = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Latest verdict per candidate wins
    latest: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        cid = e.get("candidate_id")
        if cid:
            latest[cid] = e

    accepted = sum(1 for e in latest.values() if e.get("decision") == "accepted")
    rejected = sum(1 for e in latest.values() if e.get("decision") == "rejected")

    per_shot = {}
    for shot in manifest.get("shots", []):
        sid = shot["shot_id"]
        shot_acc = [e for e in latest.values()
                    if e.get("shot_id") == sid and e.get("decision") == "accepted"]
        shot_rej = [e for e in latest.values()
                    if e.get("shot_id") == sid and e.get("decision") == "rejected"]
        per_shot[sid] = {
            "accepted": len(shot_acc),
            "rejected": len(shot_rej),
            "total_candidates": len(shot.get("candidates", [])),
        }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "tour": manifest.get("tour", ""),
        "source_type": manifest.get("source_type", ""),
        "total_judged": len(latest),
        "accepted": accepted,
        "rejected": rejected,
        "total_candidates": sum(len(s.get("candidates", []))
                                for s in manifest.get("shots", [])),
        "per_shot": per_shot,
        "updated_at": _now_iso(),
    }
    summary_path = pool_dir / "judgment_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary_path


def run_judge(pool_dir: Path, editor_id: str = "founder",
              shot_filter: Optional[str] = None,
              only_undecided: bool = False) -> int:
    """
    Interactive judge loop. Walks each candidate, asks for verdict + reason.

    Args:
        pool_dir: the pool/ directory
        editor_id: who is judging
        shot_filter: only judge this shot_id (None = all)
        only_undecided: skip clips already judged

    Returns:
        exit code
    """
    pool_dir = Path(pool_dir).resolve()
    manifest_path = pool_dir / "pool_manifest.json"
    if not manifest_path.exists():
        print(f"❌ pool_manifest.json not found in {pool_dir}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tour = manifest.get("tour", "pool")
    source_type = manifest.get("source_type", "unknown")

    print("═" * 60)
    print(f"  Clip Pool — JUDGE · tour: {tour}")
    print("═" * 60)
    print(f"  editor:    {editor_id}")
    print(f"  source:    {source_type}")
    if shot_filter:
        print(f"  shot:      {shot_filter} (filtered)")
    print()

    # Measure metrics (cached)
    print("▶ Measuring clip metrics (motion / brightness / shake) ...")
    metrics_cache = _load_or_measure_metrics(manifest, pool_dir)
    existing = _load_existing_verdicts(pool_dir)
    print(f"  {len(metrics_cache)} clips measured, {len(existing)} already judged\n")

    # Build the candidate list to walk
    candidates = []
    for shot in manifest.get("shots", []):
        if shot_filter and shot["shot_id"] != shot_filter:
            continue
        sid = shot["shot_id"]
        shot_mets = [metrics_cache.get(c["candidate_id"], {})
                     for c in shot.get("candidates", [])]
        shot_stats = compute_shot_stats(shot_mets)
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            if only_undecided and cid in existing:
                continue
            candidates.append((shot, cand, shot_stats))

    if not candidates:
        print("  Nothing to judge (all decided, or no matching clips).")
        _write_summary(pool_dir, manifest)
        return 0

    print(f"  {len(candidates)} candidate(s) to judge.\n")
    print("  Commands:  a=accept  r=reject  s=skip  q=quit")
    print("             After a/r, type your reason (the WHY — this is the seed)")
    print()

    decided = 0
    for idx, (shot, cand, shot_stats) in enumerate(candidates, 1):
        cid = cand["candidate_id"]
        local = pool_dir.parent / cand["local_path"]
        if not local.exists():
            local = pool_dir / cand["local_path"].replace("pool/", "", 1)
        m = metrics_cache.get(cid, {})
        flags = flag_issues(m, shot_stats)

        prev = existing.get(cid)
        prev_tag = ""
        if prev:
            prev_tag = f"  [previously: {prev['decision'].upper()} — {prev.get('reason','')[:50]}]"

        print("─" * 60)
        print(f"  [{idx}/{len(candidates)}] {shot['shot_id']} — {shot['label']}")
        print(f"  {cid}  ({cand['orientation']}, {cand.get('duration_sec','?')}s){prev_tag}")
        print(f"  file: {local}")
        if m:
            print(f"  📐  brightness={_fmt(m.get('brightness'))}  "
                  f"motion={_fmt(m.get('motion_score'))}  "
                  f"shake={_fmt(m.get('shake_score'))}  "
                  f"contrast={_fmt(m.get('contrast'))}")
        if flags:
            print(f"  🚩  {' · '.join(flags)}")

        # Try to open the clip for preview
        try:
            if sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", str(local)])
        except Exception:  # noqa: BLE001
            pass

        verdict = input("  verdict (a/r/s/q): ").strip().lower()
        if verdict in ("q", "quit"):
            print("\n  quitting (progress saved)...")
            break
        if verdict == "s" or verdict == "":
            print("  ⏭️  skipped\n")
            continue

        if verdict not in ("a", "r"):
            print("  ⏭️  not a/r, skipping\n")
            continue

        decision = "accepted" if verdict == "a" else "rejected"
        reason = input(f"  why {decision}? (the reason = the seed): ").strip()
        if not reason:
            reason = "(no reason given)"

        entry = {
            "schema_version": SCHEMA_VERSION,
            "tour": tour,
            "shot_id": shot["shot_id"],
            "candidate_id": cid,
            "source_type": source_type,
            "decision": decision,
            "reason": reason,
            "metrics": m,
            "flags": flags,
            "editor_id": editor_id,
            "timestamp": _now_iso(),
        }
        _append_verdict(pool_dir, entry)
        existing[cid] = entry
        decided += 1
        print(f"  ✅ logged: {decision} — \"{reason}\"\n")

    summary_path = _write_summary(pool_dir, manifest)
    print("═" * 60)
    print(f"  Judge session complete. {decided} new verdict(s) this session.")
    print(f"  📝 judgment_log.jsonl updated")
    print(f"  📊 judgment_summary.json: {summary_path}")
    print("═" * 60)
    return 0


def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)
