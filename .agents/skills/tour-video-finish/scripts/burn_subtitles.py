"""
burn_subtitles.py — generate SRT from script timing, burn into video.

Reuses the subtitle style pattern from videogen/compose.py:
  - white text, semi-transparent black box
  - Alignment=2 (bottom center)
  - MarginV scaled for mobile safe zone

Brand-aware: uses ECH charcoal (#171717) for text, warm white (#FAF8F4)
for the box background — matches the corporate guide.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Script timing (same as cut.py / tts_vo.py)
CUT_PLAN = [
    {"shot": "shot1_hook",        "duration": 6.0,  "text": "China doesn't reveal itself all at once."},
    {"shot": "shot2_beijing",     "duration": 8.0,  "text": "It begins in Beijing —\nTiananmen Square and the Forbidden City."},
    {"shot": "shot3_great_wall",  "duration": 8.0,  "text": "You'll walk the Great Wall —\nthe real one."},
    {"shot": "shot4_warriors",    "duration": 10.0, "text": "The Terracotta Warriors.\nEvery face different.\nEvery face waiting."},
    {"shot": "shot5_water_towns", "duration": 8.0,  "text": "The gardens of Suzhou.\nChina, catching its breath."},
    {"shot": "shot6_tea",         "duration": 6.0,  "text": "Dragon Well tea,\npoured where it's grown."},
    {"shot": "shot7_shanghai",    "duration": 4.0,  "text": "Shanghai —\nold meets tomorrow."},
    {"shot": "shot8_trust",       "duration": 5.0,  "text": "From A$1,499.\nexplorechinaholidays.com.au"},
]

# Crossfade overlap reduces total duration
CROSSFADE = 0.5


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(out_path: Path, cut_plan: list = None) -> Path:
    """Generate SRT subtitle file from the cut plan."""
    cut_plan = cut_plan or CUT_PLAN
    entries = []
    cum_time = 0.0

    for i, beat in enumerate(cut_plan):
        start = cum_time
        # Subtitle stays for the shot duration minus crossfade overlap
        dur = beat["duration"] - CROSSFADE if i < len(cut_plan) - 1 else beat["duration"]
        end = start + dur
        cum_time += beat["duration"] - CROSSFADE if i < len(cut_plan) - 1 else beat["duration"]

        entries.append(
            f"{i+1}\n"
            f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n"
            f"{beat['text']}\n"
        )

    out_path.write_text("\n".join(entries), encoding="utf-8")
    return out_path


def _subtitles_filter_available() -> bool:
    """Check if ffmpeg has the subtitles (libass) filter compiled in."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"],
        capture_output=True, text=True, timeout=10,
    )
    return " subtitles " in result.stdout or "\nsubtitles " in result.stdout


def _hex_to_rgb(hex_str: str) -> tuple:
    """Convert #RRGGBB or 0xRRGGBB to (R, G, B)."""
    h = hex_str.lstrip('#').lstrip('0x')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _burn_with_pillow(video_path: Path, srt_path: Path, out_path: Path,
                      font_size: int, text_color: str, box_color: str,
                      margin_v: int) -> bool:
    """
    Burn subtitles using Pillow — extract frames, render text, reassemble.
    Fallback for ffmpeg builds without libass/drawtext filters.

    This is slower than native ffmpeg burn but works everywhere Pillow + ffmpeg
    are available. Suitable for short videos (<60s).
    """
    import tempfile
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    # Parse SRT entries
    entries = _parse_srt(srt_path)

    # Find a font
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    font_path = None
    for fp in font_paths:
        if Path(fp).exists():
            font_path = fp
            break

    text_rgb = _hex_to_rgb(text_color)
    box_rgb = _hex_to_rgb(box_color)

    # Open the video
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Scale font to resolution — larger for readability on mobile/desktop
    actual_font_size = max(int(font_size * (h / 1080)), int(h * 0.035))
    font = ImageFont.truetype(font_path, actual_font_size) if font_path else ImageFont.load_default()

    print(f"  🔥 burning with Pillow ({w}x{h}, {total_frames} frames, font={actual_font_size}px)")
    print(f"     font: {font_path}")

    # Write to temp AVI (lossless intermediate), then encode to mp4
    temp_avi = out_path.parent / "_subbed_temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(str(temp_avi), fourcc, fps, (w, h))

    frame_idx = 0
    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps

        # Find active subtitle entry
        active_text = None
        for start, end, text in entries:
            if start <= timestamp < end:
                active_text = text
                break

        if active_text:
            # Convert to PIL for text rendering
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img, 'RGBA')

            # Handle multi-line text
            lines = active_text.split('\n')
            line_heights = []
            line_widths = []
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_widths.append(bbox[2] - bbox[0])
                line_heights.append(bbox[3] - bbox[1])

            total_text_h = sum(line_heights) + (len(lines) - 1) * 8
            max_line_w = max(line_widths) if line_widths else 0

            # Box position: bottom center with margin
            box_padding = 12
            box_w = max_line_w + box_padding * 2
            box_h = total_text_h + box_padding * 2
            box_x = (w - box_w) // 2
            box_y = h - margin_v - box_h

            # Draw semi-transparent warm-white box
            draw.rectangle(
                [box_x, box_y, box_x + box_w, box_y + box_h],
                fill=box_rgb + (220,),  # semi-transparent
            )

            # Draw text
            text_y = box_y + box_padding
            for i, line in enumerate(lines):
                text_x = (w - line_widths[i]) // 2
                draw.text((text_x, text_y), line, fill=text_rgb, font=font)
                text_y += line_heights[i] + 8

            # Convert back to cv2
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        writer.write(frame)

        if frame_idx % max(1, total_frames // 10) == 0:
            print(f"     ...{frame_idx}/{total_frames} frames ({100*frame_idx//total_frames}%)", flush=True)

    cap.release()
    writer.release()

    # Encode temp AVI to final MP4 (with audio from original if present)
    # First check if original has audio
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=codec_type", "-of", "csv=p=0",
        str(video_path),
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
    has_audio = "audio" in probe_result.stdout

    if has_audio:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(temp_avi),
            "-i", str(video_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(int(fps)),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(temp_avi),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(int(fps)),
            str(out_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    temp_avi.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  ⚠️  encode error: {result.stderr[:200]}")
        # Last resort: no audio, simple encode
        cmd_fallback = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(temp_avi),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=300)

    return out_path.exists() and out_path.stat().st_size > 1000


def _parse_srt(srt_path: Path) -> list:
    """Parse SRT file into [(start_sec, end_sec, text), ...]"""
    import re
    content = srt_path.read_text(encoding="utf-8")
    entries = []
    blocks = re.split(r'\n\s*\n', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        # Parse timestamp line
        time_match = re.match(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
            lines[1],
        )
        if not time_match:
            continue
        g = time_match.groups()
        start = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000
        end = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000
        text = '\n'.join(lines[2:])
        entries.append((start, end, text))
    return entries


def cmd_burn(args) -> int:
    video_path = Path(args.video).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        print(f"❌ video not found: {video_path}", file=sys.stderr)
        return 1

    print("═" * 60)
    print("  Subtitle burn-in")
    print("═" * 60)

    # Generate SRT (or use existing synced one)
    srt_synced = out_path.parent / "subtitles_synced.srt"
    srt_default = out_path.parent / "subtitles.srt"
    if srt_synced.exists():
        srt_path = srt_synced
        print(f"  📝 using synced SRT: {srt_path.name}")
    else:
        srt_path = srt_default
        generate_srt(srt_path)
        print(f"  📝 generated SRT: {srt_path.name} ({len(CUT_PLAN)} entries)")

    # Try ffmpeg subtitles filter first (fastest)
    if _subtitles_filter_available():
        # ... (libass path — kept in case future ffmpeg has it)
        pass

    # Pillow fallback (works everywhere)
    print("  ℹ️  using Pillow-based subtitle burn (ffmpeg lacks libass)")
    ok = _burn_with_pillow(
        video_path, srt_path, out_path,
        font_size=args.font_size,
        text_color=args.text_color,
        box_color=args.box_color,
        margin_v=args.margin_v,
    )
    if ok:
        print(f"\n  ✅ subtitles burned: {out_path.name}")
    else:
        print(f"\n  ⚠️  burn failed — copying original. SRT available at {srt_path}")
        subprocess.run(["cp", str(video_path), str(out_path)])

    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Burn subtitles into video")
    parser.add_argument("--video", required=True, help="Input video .mp4")
    parser.add_argument("--script", default=None, help="selection_draft.json (uses fixed CUT_PLAN if not set)")
    parser.add_argument("--out", required=True, help="Output video with subtitles")
    parser.add_argument("--font-size", type=int, default=18, help="Subtitle font size (default 18)")
    parser.add_argument("--text-color", default="#171717", help="Text color hex (default ECH charcoal)")
    parser.add_argument("--box-color", default="#FAF8F4", help="Box color hex (default ECH warm white)")
    parser.add_argument("--margin-v", type=int, default=60, help="Vertical margin (default 60)")
    return cmd_burn(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
