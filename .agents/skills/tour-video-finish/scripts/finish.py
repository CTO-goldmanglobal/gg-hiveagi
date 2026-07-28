"""
finish.py — orchestrator: takes a silent draft + assets → finished video.

Runs 4 steps in order:
  1. TTS voiceover (or use provided VO file)
  2. Music + VO mix with ducking
  3. Subtitle burn-in
  4. End card overlay (logo + price + URL)

Each step is also runnable independently (see SKILL.md).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def _run(cmd: list, label: str) -> bool:
    """Run a step, return success."""
    print(f"\n{'═'*60}")
    print(f"  {label}")
    print(f"{'═'*60}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ failed: {result.stderr[:300]}")
        return False
    # Print any stdout from the step
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines()[-5:]:
            print(f"  {line}")
    return True


def cmd_finish(args) -> int:
    draft = Path(args.draft).resolve()
    script_path = Path(args.script).resolve()
    out_path = Path(args.out).resolve()
    work_dir = out_path.parent / "finishing_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    if not draft.exists():
        print(f"❌ draft not found: {draft}", file=sys.stderr)
        return 1
    if not script_path.exists():
        print(f"❌ script not found: {script_path}", file=sys.stderr)
        return 1

    logo = Path(args.logo).resolve() if args.logo else None
    music = Path(args.music).resolve() if args.music else None

    py = sys.executable
    current_video = draft

    print("═" * 60)
    print("  TOUR VIDEO FINISH — 4-step pipeline")
    print("═" * 60)
    print(f"  draft:   {draft.name}")
    print(f"  script:  {script_path.name}")
    print(f"  music:   {music.name if music else '(none — skip)'}")
    print(f"  logo:    {logo.name if logo else '(none — skip end card)'}")
    print(f"  output:  {out_path.name}")

    # === STEP 1: Voiceover ===
    vo_path = None
    if args.vo:
        vo_path = Path(args.vo).resolve()
        if vo_path.exists():
            print(f"\n  ℹ️  using provided VO: {vo_path.name}")
        else:
            vo_path = None

    if not vo_path and not args.skip_vo:
        vo_path = work_dir / "vo.mp3"
        ok = _run([
            py, str(SCRIPT_DIR / "tts_vo.py"),
            "--script", str(script_path),
            "--out", str(vo_path),
        ], "STEP 1/4 — Voiceover (MiniMax TTS)")
        if not ok:
            print("  ⚠️  VO failed — continuing without VO")
            vo_path = None

    # === STEP 2: Music + VO mix ===
    audio_path = None
    if music and music.exists():
        audio_path = work_dir / "audio_mixed.mp3"
        mix_cmd = [
            py, str(SCRIPT_DIR / "mix_audio.py"),
            "--music", str(music),
            "--out", str(audio_path),
            "--vo-level", str(args.vo_level),
            "--music-level", str(args.music_level),
        ]
        if vo_path and vo_path.exists():
            mix_cmd.extend(["--vo", str(vo_path)])
        ok = _run(mix_cmd, "STEP 2/4 — Music + VO mix")
        if not ok:
            audio_path = None
    elif vo_path and vo_path.exists():
        audio_path = vo_path  # VO only, no music

    # === STEP 3: Subtitles ===
    subbed_path = work_dir / "video_subbed.mp4"
    ok = _run([
        py, str(SCRIPT_DIR / "burn_subtitles.py"),
        "--video", str(current_video.resolve()),
        "--script", str(script_path.resolve()),
        "--out", str(subbed_path.resolve()),
    ], "STEP 3/4 — Subtitles")
    if ok and subbed_path.exists():
        current_video = subbed_path
    else:
        print(f"  ⚠️  subtitle step did not produce output, using video without subs")

    # === STEP 4: End card ===
    if logo and logo.exists():
        card_path = work_dir / "video_card.mp4"
        card_cmd = [
            py, str(SCRIPT_DIR / "render_endcard.py"),
            "--video", str(current_video),
            "--logo", str(logo),
            "--out", str(card_path),
        ]
        if args.brand:
            card_cmd.extend(["--brand", args.brand])
        if args.price:
            card_cmd.extend(["--price", args.price])
        if args.url:
            card_cmd.extend(["--url", args.url])
        ok = _run(card_cmd, "STEP 4/4 — End card (brand overlay)")
        if ok:
            current_video = card_path

    # === FINAL: mux audio + video ===
    print(f"\n{'═'*60}")
    print(f"  FINAL — muxing audio + video")
    print(f"{'═'*60}")

    if audio_path and audio_path.exists():
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(current_video),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback: copy video without audio
            print(f"  ⚠️  audio mux failed, copying video only: {result.stderr[:200]}")
            subprocess.run(["cp", str(current_video), str(out_path)])
    else:
        subprocess.run(["cp", str(current_video), str(out_path)])

    # Probe final duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True,
    )
    dur = result.stdout.strip() or "?"
    size_mb = out_path.stat().st_size / (1024 * 1024)

    print(f"\n  ✅ FINAL: {out_path}")
    print(f"     {dur}s, {size_mb:.1f}MB")
    print(f"{'═'*60}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="tour-video-finish",
        description="Finish a tour promo video (VO + music + subs + end card)",
    )
    parser.add_argument("--draft", required=True, help="Silent draft .mp4")
    parser.add_argument("--script", required=True, help="selection_draft.json or script JSON")
    parser.add_argument("--music", default=None, help="Music track MP3/WAV")
    parser.add_argument("--vo", default=None, help="Pre-recorded VO file (skip TTS)")
    parser.add_argument("--logo", default=None, help="Brand logo PNG for end card")
    parser.add_argument("--brand", default="ExploreChina Holidays")
    parser.add_argument("--price", default="From A$1,499")
    parser.add_argument("--url", default="explorechinaholidays.com.au")
    parser.add_argument("--out", required=True, help="Output FINAL .mp4")
    parser.add_argument("--skip-vo", action="store_true", help="Skip TTS generation")
    parser.add_argument("--vo-level", type=float, default=-16, help="VO target LUFS (default -16)")
    parser.add_argument("--music-level", type=float, default=-25, help="Music target LUFS (default -25)")
    return cmd_finish(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
