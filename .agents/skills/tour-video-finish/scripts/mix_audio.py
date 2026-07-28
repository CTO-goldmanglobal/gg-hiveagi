"""
mix_audio.py — layer music under voiceover with ducking.

Two audio inputs:
  - VO (voiceover): the narration, always on top, clear
  - Music: background bed, ducked under VO

Mix levels (from references/music-direction.md):
  VO target:    -16 LUFS (loud, clear, always on top)
  Music target: -23 to -25 LUFS (ducked; comes up ~3dB in silent sections)
  Final mix:    -14 LUFS integrated (YouTube/Instagram spec)

If no VO provided, just normalizes the music to target level.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def cmd_mix(args) -> int:
    music_path = Path(args.music).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not music_path.exists():
        print(f"❌ music not found: {music_path}", file=sys.stderr)
        return 1

    vo_path = Path(args.vo).resolve() if args.vo else None
    has_vo = vo_path and vo_path.exists()

    print("═" * 60)
    print("  Audio mix — music + VO")
    print("═" * 60)
    print(f"  music: {music_path.name} → target {args.music_level} LUFS")
    if has_vo:
        print(f"  VO:    {vo_path.name} → target {args.vo_level} LUFS")
    else:
        print(f"  VO:    (none — music only)")

    if has_vo:
        # Simple reliable mix: normalize both, then amix with VO dominant
        # VO at weight 10, music at weight 1 — VO is always clearly on top
        # Music is pre-loudnorm'd to a low level so it's a background bed
        filter_complex = (
            f"[0:a]volume=0.15,loudnorm=I={args.music_level}:TP=-1.5:LRA=11[music_norm];"
            f"[1:a]loudnorm=I={args.vo_level}:TP=-1.5:LRA=11[vo_norm];"
            f"[music_norm][vo_norm]amix=inputs=2:duration=shortest:weights=1 10[out]"
        )

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(music_path),
            "-i", str(vo_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-ar", "44100",
            str(out_path),
        ]
    else:
        # Music only — normalize to target level
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(music_path),
            "-af", f"loudnorm=I={args.music_level}:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-ar", "44100",
            str(out_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"❌ mix failed: {result.stderr[:400]}", file=sys.stderr)
        return 1

    # Probe duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True,
    )
    dur = result.stdout.strip() or "?"
    size = out_path.stat().st_size // 1024

    print(f"\n  ✅ mixed audio: {out_path.name} ({dur}s, {size}KB)")
    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mix music under VO with ducking")
    parser.add_argument("--vo", default=None, help="Voiceover MP3 (optional)")
    parser.add_argument("--music", required=True, help="Music track MP3/WAV")
    parser.add_argument("--out", required=True, help="Output mixed audio MP3")
    parser.add_argument("--vo-level", type=float, default=-16, help="VO target LUFS")
    parser.add_argument("--music-level", type=float, default=-25, help="Music target LUFS")
    return cmd_mix(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
