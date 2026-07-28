"""
render_endcard.py — overlay brand end card on the last shot of the video.

The end card appears during the final shot (shot8_trust, ~5s).
It overlays:
  - ECH logo (centered or top)
  - Tour name
  - Price ("From A$1,499")
  - URL ("explorechinaholidays.com.au")

Brand styling per ECH corporate guide:
  - 90% content / 10% brand
  - Calm, not aggressive
  - China Red (#C8202F) for price/CTA only
  - Charcoal (#171717) for text
  - Warm white (#FAF8F4) background gradient at bottom

The overlay uses ffmpeg drawtext + overlay filters.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def _probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _probe_resolution(path: Path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    parts = result.stdout.strip().split(",")
    return int(parts[0]), int(parts[1])


def _probe_logo_size(path: Path):
    """Get logo dimensions."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    parts = result.stdout.strip().split(",")
    return int(parts[0]), int(parts[1])


def _hex_to_rgb(hex_str: str) -> tuple:
    """Convert 0xRRGGBB or #RRGGBB to (R, G, B)."""
    h = hex_str.lstrip('#').lstrip('0x')
    # ffmpeg drawtext uses BGR; but for Pillow we use RGB
    # Our args are already RGB hex, so just parse directly
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _render_endcard_pillow(video_path: Path, logo_path: Path, out_path: Path,
                           brand: str, price: str, url: str,
                           card_duration: float,
                           text_color: str, accent_color: str) -> bool:
    """Render end card using Pillow — same approach as subtitle burn."""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    total_dur = _probe_duration(video_path)
    card_start = max(0, total_dur - card_duration)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    is_portrait = h > w

    # Load + scale logo
    logo_pil = Image.open(logo_path).convert("RGBA")
    max_logo_w = int(w * 0.25)
    if logo_pil.width > max_logo_w:
        scale = max_logo_w / logo_pil.width
        logo_pil = logo_pil.resize((max_logo_w, int(logo_pil.height * scale)))
    logo_w, logo_h = logo_pil.size

    # Fonts
    font_paths_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    font_paths_reg = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    def load_font(paths, size):
        for fp in paths:
            if Path(fp).exists():
                return ImageFont.truetype(fp, size)
        return ImageFont.load_default()

    font_brand = load_font(font_paths_bold, int(h * 0.035))
    font_price = load_font(font_paths_bold, int(h * 0.05))
    font_url = load_font(font_paths_reg, int(h * 0.028))

    text_rgb = _hex_to_rgb(text_color)
    accent_rgb = _hex_to_rgb(accent_color)

    # Positions
    logo_x = (w - logo_w) // 2
    logo_y = int(h * 0.20) if is_portrait else int(h * 0.15)

    print(f"  🏷️  rendering end card with Pillow ({w}x{h})")
    print(f"     logo: {logo_w}x{logo_h} at ({logo_x}, {logo_y})")
    print(f"     card window: {card_start:.1f}s → {total_dur:.1f}s")

    # Write to temp, then encode
    temp_avi = out_path.parent / "_endcard_temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(str(temp_avi), fourcc, fps, (w, h))

    # Pre-calculate text widths for centering
    def text_size(draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps
        if timestamp >= card_start:
            # Render end card overlay
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img, 'RGBA')

            # Fade in over 0.5s
            fade_progress = min(1.0, (timestamp - card_start) / 0.5)
            alpha = int(255 * fade_progress)

            # Paste logo with fade
            logo_faded = logo_pil.copy()
            logo_faded.putalpha(logo_faded.getchannel('A').point(lambda a: int(a * fade_progress)))
            pil_img.paste(logo_faded, (logo_x, logo_y), logo_faded)

            # Calculate text positions (below logo)
            text_y = logo_y + logo_h + int(h * 0.04)

            # Brand name
            bw, bh = text_size(draw, brand, font_brand)
            brand_color = text_rgb + (alpha,)
            draw.text(((w - bw) // 2, text_y), brand, fill=brand_color, font=font_brand)
            text_y += bh + int(h * 0.03)

            # Price (China Red accent)
            pw, ph = text_size(draw, price, font_price)
            price_color = accent_rgb + (alpha,)
            draw.text(((w - pw) // 2, text_y), price, fill=price_color, font=font_price)
            text_y += ph + int(h * 0.025)

            # URL
            uw, uh = text_size(draw, url, font_url)
            url_color = text_rgb + (alpha,)
            draw.text(((w - uw) // 2, text_y), url, fill=url_color, font=font_url)

            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        writer.write(frame)

        if frame_idx % max(1, total_frames // 10) == 0:
            print(f"     ...{frame_idx}/{total_frames} ({100*frame_idx//total_frames}%)", flush=True)

    cap.release()
    writer.release()

    # Encode with audio from original
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(temp_avi),
        "-i", str(video_path),
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(int(fps)),
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    temp_avi.unlink(missing_ok=True)

    if result.returncode != 0:
        # No audio fallback
        cmd2 = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(temp_avi),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(out_path),
        ]
        subprocess.run(cmd2, capture_output=True, text=True, timeout=300)

    return out_path.exists()


def cmd_endcard(args) -> int:
    video_path = Path(args.video).resolve()
    logo_path = Path(args.logo).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        print(f"❌ video not found: {video_path}", file=sys.stderr)
        return 1
    if not logo_path.exists():
        print(f"❌ logo not found: {logo_path}", file=sys.stderr)
        return 1

    print("═" * 60)
    print("  End card — brand overlay")
    print("═" * 60)
    print(f"  brand: {args.brand}")
    print(f"  price: {args.price}")
    print(f"  url:   {args.url}")

    ok = _render_endcard_pillow(
        video_path, logo_path, out_path,
        brand=args.brand, price=args.price, url=args.url,
        card_duration=args.card_duration,
        text_color=args.text_color, accent_color=args.accent_color,
    )
    if ok:
        print(f"\n  ✅ end card rendered: {out_path.name}")
    else:
        print(f"\n  ⚠️  failed — copying original")
        subprocess.run(["cp", str(video_path), str(out_path)])
    print("═" * 60)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render brand end card on video")
    parser.add_argument("--video", required=True, help="Input video .mp4")
    parser.add_argument("--logo", required=True, help="Brand logo PNG")
    parser.add_argument("--out", required=True, help="Output video with end card")
    parser.add_argument("--brand", default="ExploreChina Holidays")
    parser.add_argument("--price", default="From A$1,499")
    parser.add_argument("--url", default="explorechinaholidays.com.au")
    parser.add_argument("--card-duration", type=float, default=5.0,
                        help="Seconds of end card display (default 5)")
    parser.add_argument("--text-color", default="0x171717", help="Charcoal text (BGR hex)")
    parser.add_argument("--accent-color", default="0xC8202F", help="China Red accent (BGR hex)")
    return cmd_endcard(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
