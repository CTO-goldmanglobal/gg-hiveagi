"""
CLI entry: `python -m ech_videogen make --clips <dir> --out reel.mp4`

Runs the full 4-stage pipeline:
  ingest → analyze → select+script → compose
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


def cmd_make(args) -> int:
    clips_dir = Path(args.clips).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = Path(args.work_dir or "./ech_output").resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if not clips_dir.is_dir():
        print(f"❌ clips dir not found: {clips_dir}", file=sys.stderr)
        return 1

    print("═" * 60)
    print("  ECH VideoGen — Explore China Holiday auto-Reel generator")
    print("═" * 60)
    print(f"  clips:    {clips_dir}")
    print(f"  out:      {out_path}")
    print(f"  work_dir: {work_dir}")
    print(f"  target:   {args.duration}s, top {args.top_n} frames, {args.location}")
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
    analyses = analyze_frames(all_frames, location_hint=args.location)
    # Persist
    (work_dir / "analysis.json").write_text(
        json.dumps(analyses, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    ok = sum(1 for a in analyses if a.get("ai_analysis"))
    print(f"  analyzed: {ok}/{len(analyses)} succeeded\n")

    # === STAGE 3: SELECT + SCRIPT ===
    print("▶ Stage 3: SELECT + SCRIPT (LLM rank + narration)")
    from llm_wiki_engine.config import load_config
    config = load_config(mock_mode=False)
    script = select_and_script(
        analyses, config,
        top_n=args.top_n,
        target_duration_sec=args.duration,
        location_hint=args.location,
    )
    (work_dir / "script.json").write_text(
        json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if not script:
        print("❌ empty script", file=sys.stderr)
        return 1
    print()

    # === STAGE 4: COMPOSE ===
    print("▶ Stage 4: COMPOSE (ffmpeg segments + xfade + subtitles + 9:16)")
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
        crossfade_sec=args.crossfade,
    )

    total_duration = sum(s["duration_sec"] for s in script)
    print()
    print("═" * 60)
    print(f"  ✅ Reel ready: {out_path}")
    print(f"     {total_duration:.1f}s, {len(script)} segments, 9:16 vertical")
    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ech_videogen",
        description="Explore China Holiday auto-Reel generator (Goldman Forge)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_make = sub.add_parser("make", help="Generate a Reel from a directory of clips")
    p_make.add_argument("--clips", required=True, help="Directory of source video clips")
    p_make.add_argument("--out", required=True, help="Output .mp4 path")
    p_make.add_argument("--work-dir", default=None, help="Intermediate artifacts dir (default ./ech_output)")
    p_make.add_argument("--interval", type=float, default=5.0,
                        help="Frame sampling interval in seconds (default 5)")
    p_make.add_argument("--top-n", type=int, default=8,
                        help="Number of frames to select (default 8)")
    p_make.add_argument("--duration", type=int, default=45,
                        help="Target Reel duration in seconds (default 45)")
    p_make.add_argument("--location", default="China",
                        help="Location hint for the LLM (e.g. 'Beijing', 'Guilin')")
    p_make.add_argument("--crossfade", type=float, default=0.5,
                        help="Crossfade duration between segments (default 0.5s)")
    p_make.set_defaults(func=cmd_make)

    args = parser.parse_args(argv)
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
