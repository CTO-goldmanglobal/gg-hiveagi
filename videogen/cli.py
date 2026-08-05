"""
CLI entry: `python -m videogen make --config ech --clips <dir> --out reel.mp4`

Generic pipeline core. The --config flag selects which client's prompts
and settings to use (ech, future: realestate, education, ...).
"""

import argparse
import json
import sys
from pathlib import Path

from .ingest import ingest_clips
from .analyze import analyze_frames
from .select import select_and_script
from .srt import script_to_srt
from .compose import compose_reel
from . import load_config


def cmd_make(args) -> int:
    clips_dir = Path(args.clips).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = Path(args.work_dir or "./videogen_output").resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if not clips_dir.is_dir():
        print(f"❌ clips dir not found: {clips_dir}", file=sys.stderr)
        return 1

    config = load_config(args.config)

    print("═" * 60)
    print(f"  VideoGen — config: {config.name}")
    print("═" * 60)
    print(f"  clips:    {clips_dir}")
    print(f"  out:      {out_path}")
    print(f"  work_dir: {work_dir}")
    print(f"  target:   {args.duration}s, top {args.top_n} frames, {args.location}")
    print(f"  aspect:   {config.target_aspect}, lang: {config.language}")
    print()

    # === STAGE 1: INGEST ===
    print("▶ Stage 1: INGEST (probe + sample frames)")
    frames_dir = work_dir / "frames"
    ingest_result = ingest_clips(clips_dir, frames_dir, args.interval)
    all_frames = []
    for clip_frames in ingest_result["frames"].values():
        all_frames.extend(clip_frames)
    print(f"  total: {len(ingest_result['clips'])} clips, {len(all_frames)} frames\n")
    if not all_frames:
        print("❌ no frames sampled", file=sys.stderr)
        return 1

    # === STAGE 2: ANALYZE (via Labs vision pipeline) ===
    print("▶ Stage 2: ANALYZE (Labs vision — MiniMax M3 + PII blur gate)")
    force_en = (config.language == "en")
    analyses = analyze_frames(all_frames, location_hint=args.location,
                              force_english=force_en)
    (work_dir / "analysis.json").write_text(
        json.dumps(analyses, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    ok = sum(1 for a in analyses if a.get("ai_analysis"))
    print(f"  analyzed: {ok}/{len(analyses)} succeeded\n")

    # === STAGE 3: SELECT + SCRIPT ===
    print("▶ Stage 3: SELECT + SCRIPT (LLM rank + narration)")
    from llm_wiki_engine.config import load_config as load_llm_config
    llm_config = load_llm_config(mock_mode=False)
    script, selected = select_and_script(
        analyses, llm_config,
        top_n=args.top_n,
        target_duration_sec=args.duration,
        location_hint=args.location,
        ranker_prompt_path=config.frame_ranker_prompt,
        writer_prompt_path=config.script_writer_prompt,
    )
    (work_dir / "script.json").write_text(
        json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Persist the ranker's selection (model baseline) for the finalize step
    (work_dir / "ranker_selection.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if not script:
        print("❌ empty script", file=sys.stderr)
        return 1
    print()

    # === STAGE 4: COMPOSE ===
    print("▶ Stage 4: COMPOSE (ffmpeg segments + xfade + subtitles)")
    srt_path = work_dir / "subtitles.srt"
    script_to_srt(script, srt_path)
    print(f"  📝 subtitles: {srt_path}")

    compose_reel(
        script=script,
        analyses=analyses,
        clips_meta=ingest_result["clips"],
        interval_sec=args.interval,
        work_dir=work_dir,
        out_path=out_path,
        crossfade_sec=config.crossfade_sec,
    )

    total_duration = sum(s["duration_sec"] for s in script)
    print()
    print("═" * 60)
    print(f"  ✅ Reel ready: {out_path}")
    print(f"     {total_duration:.1f}s, {len(script)} segments, {config.target_aspect}")
    print("═" * 60)
    print()
    print("  Next: review the draft. Edit script.json if you want to change")
    print("  frame order / durations / subtitles, then run:")
    print(f"    python -m videogen finalize --run-dir {work_dir} --editor-id <you>")
    return 0


def cmd_finalize(args) -> int:
    """
    Compute the human-override signal: diff the model's ranker selection
    against the (possibly edited) script.json, and log every frame's fate.
    """
    from .selection_log import compute_override_log, write_log, _generate_run_id

    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"❌ run dir not found: {run_dir}", file=sys.stderr)
        return 1

    # Load the three inputs
    analyses_path = run_dir / "analysis.json"
    ranker_path = run_dir / "ranker_selection.json"
    script_path = run_dir / "script.json"

    if not analyses_path.exists():
        print(f"❌ analysis.json not found in {run_dir}", file=sys.stderr)
        return 1
    if not ranker_path.exists():
        print(f"❌ ranker_selection.json not found in {run_dir}", file=sys.stderr)
        print("   Did you run `make` with the updated pipeline?", file=sys.stderr)
        return 1
    if not script_path.exists():
        print(f"❌ script.json not found in {run_dir}", file=sys.stderr)
        return 1

    analyses = json.loads(analyses_path.read_text(encoding="utf-8"))
    ranker_selection = json.loads(ranker_path.read_text(encoding="utf-8"))
    final_script = json.loads(script_path.read_text(encoding="utf-8"))

    config_name = args.config or "ech"
    run_id = args.run_id or _generate_run_id(config_name)
    editor_id = args.editor_id or "founder"

    print("═" * 60)
    print("  VideoGen finalize — computing human-override signal")
    print("═" * 60)
    print(f"  run_dir:   {run_dir}")
    print(f"  editor_id: {editor_id}")
    print(f"  run_id:    {run_id}")
    print()

    log_entries = compute_override_log(
        analyses=analyses,
        ranker_selection=ranker_selection,
        final_script=final_script,
        run_id=run_id,
        editor_id=editor_id,
        config_name=config_name,
    )

    log_path, summary_path = write_log(log_entries, run_dir)

    # Load summary for display
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    print(f"  📝 selection_log.jsonl: {log_path}")
    print(f"  📊 selection_summary.json: {summary_path}")
    print()
    print(f"  Total frames:     {summary['total_frames']}")
    print(f"  Ranker kept:      {summary['ranker_kept']}")
    print(f"  Final kept:       {summary['final_kept']}")
    print(f"  Overrides:        {summary['overrides']}")
    if summary["overrides"] > 0:
        ot = summary["override_types"]
        parts = [f"{k}={v}" for k, v in ot.items() if v]
        print(f"  Override types:   {', '.join(parts)}")
    if summary.get("shot_type_distribution_final"):
        dist = summary["shot_type_distribution_final"]
        parts = [f"{k}={v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])]
        print(f"  Shot types:       {', '.join(parts)}")
    print()
    print("  ⚠️  This log contains source.clip filenames + timestamps.")
    print("      Review PII before publishing. See videogen/selection_schema.md.")
    print("═" * 60)
    return 0


def cmd_produce(args) -> int:
    """H4: one-command video production (brief → video)."""
    from .produce import produce
    result = produce(
        brief_path=args.brief,
        out_dir=args.out,
        mock=args.mock,
    )
    print("═" * 60)
    print(f"  Status:     {result.status}")
    print(f"  Tour:       {result.tour_slug}")
    print(f"  Duration:   {result.video.get('duration_sec', 0):.1f}s")
    print(f"  QC:         {result.qc_report.get('decision', '?')}")
    print(f"  Output:     {args.out}/")
    print(f"    result.json  ({len(result.media_provenance)} provenance entries)")
    print(f"    edl.json")
    if args.mock:
        print("  ⚠️  Mock mode — no real video rendered.")
        print("      result.json + edl.json are valid for integration testing.")
    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="videogen",
        description="Generic auto-video pipeline (Goldman Forge)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_make = sub.add_parser("make", help="Generate a draft Reel")
    p_make.add_argument("--config", default="ech",
                        help="Named config (ech, future: realestate, ...)")
    p_make.add_argument("--clips", required=True, help="Directory of source video clips")
    p_make.add_argument("--out", required=True, help="Output .mp4 path")
    p_make.add_argument("--work-dir", default=None,
                        help="Intermediate artifacts dir (default ./videogen_output)")
    p_make.add_argument("--interval", type=float, default=5.0,
                        help="Frame sampling interval in seconds (default 5)")
    p_make.add_argument("--top-n", type=int, default=8,
                        help="Number of frames to select (default 8)")
    p_make.add_argument("--duration", type=int, default=None,
                        help="Target Reel duration in seconds (default: from config)")
    p_make.add_argument("--location", default=None,
                        help="Location hint (default: from config)")
    p_make.add_argument("--crossfade", type=float, default=None,
                        help="Crossfade duration (default: from config)")
    p_make.set_defaults(func=cmd_make)

    # finalize subcommand — computes human-override signal
    p_final = sub.add_parser("finalize",
                             help="Log human-override signal (diff model vs edited script)")
    p_final.add_argument("--run-dir", required=True,
                         help="Work dir from a previous `make` run")
    p_final.add_argument("--editor-id", default="founder",
                         help="Who made the editorial decisions (default: founder)")
    p_final.add_argument("--config", default="ech",
                         help="Config name (default: ech)")
    p_final.add_argument("--run-id", default=None,
                         help="Override run_id (default: auto-generated)")
    p_final.set_defaults(func=cmd_finalize)

    # produce subcommand — the one-command orchestrator (H4)
    p_produce = sub.add_parser("produce",
                               help="One-command video production (brief → video)")
    p_produce.add_argument("--brief", default=None,
                           help="Path to brief.yaml (canonical input). If omitted with --mock, uses a mock brief.")
    p_produce.add_argument("--out", default="forge-output",
                           help="Output directory for result.json + edl.json (default: forge-output)")
    p_produce.add_argument("--mock", action="store_true",
                           help="Mock mode: skip network + stubs, use synthetic data. Produces valid result.json + edl.json.")
    p_produce.set_defaults(func=cmd_produce)

    args = parser.parse_args(argv)

    # Apply config defaults where CLI didn't override
    if args.command == "make":
        config = load_config(args.config)
        if args.duration is None:
            args.duration = config.target_duration_sec
        if args.location is None:
            args.location = config.location_default

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
