"""
tts_vo.py — generate voiceover via MiniMax TTS.

Reads the script from selection_draft.json, sends each shot's VO text to
MiniMax speech-2.8-hd, concatenates into one continuous VO track.

The VO is the brand voice — warm, calm, trustworthy Australian-English.
See references/vo-direction.md for casting + delivery notes.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Script VO per shot (same as cut.py CUT_PLAN)
CUT_PLAN = [
    {"shot": "shot1_hook",        "duration": 6.0,
     "vo": "China doesn't reveal itself all at once. It unfolds — over twelve days, five cities, and five thousand years."},
    {"shot": "shot2_beijing",     "duration": 8.0,
     "vo": "It begins in Beijing — at Tiananmen Square, and the Forbidden City, where emperors ruled, and history still stands."},
    {"shot": "shot3_great_wall",  "duration": 8.0,
     "vo": "You'll walk the Great Wall — not a postcard version, the real one. Stone by stone, two thousand years in the making."},
    {"shot": "shot4_warriors",    "duration": 10.0,
     "vo": "In Xi'an, you stand before the Terracotta Warriors. Eight thousand soldiers, carved one by one — every face different. Every face waiting."},
    {"shot": "shot5_water_towns", "duration": 8.0,
     "vo": "Then the pace softens — the gardens of Suzhou, the still water of Wuxi. China, catching its breath."},
    {"shot": "shot6_tea",         "duration": 6.0,
     "vo": "In Hangzhou, you taste it — Dragon Well tea, poured where it's grown."},
    {"shot": "shot7_shanghai",    "duration": 4.0,
     "vo": "And Shanghai — where a four-hundred-year-old garden meets a tomorrow that's already here."},
    {"shot": "shot8_trust",       "duration": 5.0,
     "vo": "Twelve days. Flights, hotels, and the stories — all included. From fourteen ninety-nine. Your legend starts here."},
]


def _get_api_key() -> str:
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY not found in env or .env")


def _tts_segment(text: str, out_path: Path, api_key: str,
                 voice_id: str = "English_expressive_narrator",
                 speed: float = 0.9) -> bool:
    """Generate one VO segment via MiniMax T2A v2."""
    payload = json.dumps({
        "model": "speech-2.8-hd",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.minimax.io/v1/t2a_v2",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # MiniMax T2A v2 returns hex-encoded audio in data.audio
        audio_hex = data.get("data", {}).get("audio", "")
        if not audio_hex:
            # Some responses use base64 in data.audio
            print(f"  ⚠️  no audio in response: {json.dumps(data)[:200]}")
            return False
        audio_bytes = bytes.fromhex(audio_hex)
        out_path.write_bytes(audio_bytes)
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"  ⚠️  TTS error: {e}")
        return False


def cmd_tts(args) -> int:
    api_key = _get_api_key()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use script from selection_draft if provided, else CUT_PLAN
    if args.script and Path(args.script).exists():
        draft = json.loads(Path(args.script).read_text())
        # selection_draft has selections but we use CUT_PLAN for VO text
        # (the VO is fixed by the script, not the footage selection)

    segments_dir = out_path.parent / "vo_segments"
    segments_dir.mkdir(exist_ok=True)

    print("═" * 60)
    print("  Voiceover generation — MiniMax speech-2.8-hd")
    print("═" * 60)
    print(f"  voice: {args.voice}")
    print(f"  speed: {args.speed}")
    print(f"  segments: {len(CUT_PLAN)}")
    print()

    seg_paths = []
    for i, beat in enumerate(CUT_PLAN):
        seg_path = segments_dir / f"vo_{i:02d}.mp3"
        if seg_path.exists() and not args.force:
            print(f"  ✓ cached vo_{i:02d}")
            seg_paths.append(seg_path)
            continue
        print(f"  🎙️  [{i+1}/{len(CUT_PLAN)}] {beat['shot']}: \"{beat['vo'][:50]}...\"")
        ok = _tts_segment(beat["vo"], seg_path, api_key,
                          voice_id=args.voice, speed=args.speed)
        if ok:
            seg_paths.append(seg_path)
            print(f"     ✅ {seg_path.name} ({seg_path.stat().st_size // 1024}KB)")
        else:
            print(f"     ❌ failed, skipping")

    if not seg_paths:
        print("\n❌ no VO segments generated", file=sys.stderr)
        return 1

    # Concatenate all segments
    print(f"\n  🔗 concatenating {len(seg_paths)} segments...")
    if len(seg_paths) == 1:
        import shutil
        shutil.copy2(seg_paths[0], out_path)
    else:
        list_file = out_path.parent / "vo_concat.txt"
        with open(list_file, "w") as f:
            for sp in seg_paths:
                f.write(f"file '{sp.resolve()}'\n")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        list_file.unlink(missing_ok=True)
        if result.returncode != 0:
            print(f"❌ concat failed: {result.stderr[:200]}", file=sys.stderr)
            return 1

    # Probe duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(out_path)],
        capture_output=True, text=True,
    )
    dur = result.stdout.strip() or "?"
    print(f"\n  ✅ VO: {out_path} ({dur}s)")
    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate voiceover via MiniMax TTS")
    parser.add_argument("--script", default=None, help="selection_draft.json (for context)")
    parser.add_argument("--out", required=True, help="Output VO .mp3")
    parser.add_argument("--voice", default="English_expressive_narrator",
                        help="MiniMax voice_id (default: English_expressive_narrator)")
    parser.add_argument("--speed", type=float, default=0.9,
                        help="Speech speed (default 0.9 = slightly slower, calmer)")
    parser.add_argument("--force", action="store_true", help="Re-generate cached segments")
    return cmd_tts(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
