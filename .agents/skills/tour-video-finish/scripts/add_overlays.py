"""
add_overlays.py — add logo watermark layer + semi-transparent text card.

Two overlay types:
  1. Logo watermark: small ECH logo at top center, fading on/off throughout
  2. End card text layer: semi-transparent box holding tour name + price + URL
     over the footage (the ducks/birds clip), NOT replacing it

Uses Pillow for compositing (same approach as burn_subtitles.py).
Works without ffmpeg libass/drawtext.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def _probe_dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(path)], capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0


def add_overlays(video_path, logo_path, out_path,
                 brand="ExploreChina Holidays", price="From A$1,499",
                 url="explorechinaholidays.com.au",
                 card_start=None, card_duration=8.0):
    """
    Add logo watermark (on/off at top center) + end card text overlay.
    """
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    total_dur = _probe_dur(video_path)
    if card_start is None:
        card_start = max(0, total_dur - card_duration)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Load logo
    logo_pil = Image.open(logo_path).convert("RGBA")
    # Logo watermark size: ~12% of frame width (small, not intrusive)
    wm_w = int(w * 0.12)
    if logo_pil.width > wm_w:
        scale = wm_w / logo_pil.width
        logo_wm = logo_pil.resize((wm_w, int(logo_pil.height * scale)))
    else:
        logo_wm = logo_pil.copy()
    wm_w, wm_h = logo_wm.size

    # Larger logo for end card (~20% width)
    card_logo_w = int(w * 0.20)
    scale2 = card_logo_w / logo_pil.width
    logo_card = logo_pil.resize((card_logo_w, int(logo_pil.height * scale2)))
    cl_w, cl_h = logo_card.size

    # Fonts
    def load_font(bold, size):
        paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for fp in paths:
            if Path(fp).exists():
                return ImageFont.truetype(fp, size)
        return ImageFont.load_default()

    f_brand = load_font(True, int(h * 0.038))
    f_price = load_font(True, int(h * 0.055))
    f_url = load_font(False, int(h * 0.028))

    # Logo watermark position: top center, safe-zone margin (10% from top)
    # Broadcast safe zone: keep all graphics within 90% of frame (10% margin all sides)
    wm_x = (w - wm_w) // 2
    wm_y = int(h * 0.07)  # 7% from top — inside title-safe area

    # Logo on/off schedule: appear for 4s, off for 6s, repeat
    def logo_visible(t):
        cycle = t % 10.0  # 10-second cycle
        return cycle < 4.0  # visible first 4s of each 10s cycle

    print(f"  📺 adding overlays to {w}x{h} ({total_frames} frames)")
    print(f"     logo watermark: {wm_w}x{wm_h} at top center, on/off every 10s")
    print(f"     end card: {card_start:.1f}s → {total_dur:.1f}s with semi-transparent layer")

    temp_avi = out_path.parent / "_overlay_temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(str(temp_avi), fourcc, fps, (w, h))

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img, 'RGBA')

        # --- LOGO WATERMARK (on/off throughout) ---
        if logo_visible(timestamp):
            # Fade in/out: 0.5s fade at start and end of visibility
            cycle = timestamp % 10.0
            if cycle < 0.5:
                alpha = int(180 * (cycle / 0.5))  # fade in
            elif cycle > 3.5:
                alpha = int(180 * ((4.0 - cycle) / 0.5))  # fade out
            else:
                alpha = 180  # full (slightly transparent)

            wm_faded = logo_wm.copy()
            wm_faded.putalpha(wm_faded.getchannel('A').point(lambda a: int(a * alpha / 255)))
            pil_img.paste(wm_faded, (wm_x, wm_y), wm_faded)

        # --- END CARD OVERLAY (last N seconds, semi-transparent layer) ---
        if timestamp >= card_start:
            # Fade in the card over 0.8s
            card_progress = min(1.0, (timestamp - card_start) / 0.8)
            card_alpha = int(220 * card_progress)

            # Semi-transparent panel: light warm grey/pink
            # Position: lower 40% of frame
            panel_h = int(h * 0.42)
            panel_y = h - panel_h
            panel_x = int(w * 0.1)
            panel_w = int(w * 0.8)

            # Draw semi-transparent rounded panel (warm white/grey)
            panel_color = (250, 248, 244, int(200 * card_progress))  # warm white
            draw.rounded_rectangle(
                [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                radius=20,
                fill=panel_color,
            )

            # Logo on card (centered, upper part of panel)
            card_logo_x = (w - cl_w) // 2
            card_logo_y = panel_y + int(h * 0.03)
            cl_faded = logo_card.copy()
            cl_faded.putalpha(cl_faded.getchannel('A').point(lambda a: int(a * card_progress)))
            pil_img.paste(cl_faded, (card_logo_x, card_logo_y), cl_faded)

            # Text positions (below logo, centered)
            text_y = card_logo_y + cl_h + int(h * 0.02)

            # Brand name (charcoal)
            bw = draw.textbbox((0,0), brand, font=f_brand)
            brand_w = bw[2] - bw[0]
            brand_h = bw[3] - bw[1]
            draw.text(((w - brand_w) // 2, text_y), brand,
                      fill=(23, 23, 23, card_alpha), font=f_brand)
            text_y += brand_h + int(h * 0.015)

            # Price (China Red #C8202F)
            pw = draw.textbbox((0,0), price, font=f_price)
            price_w = pw[2] - pw[0]
            price_h = pw[3] - pw[1]
            draw.text(((w - price_w) // 2, text_y), price,
                      fill=(200, 32, 47, card_alpha), font=f_price)
            text_y += price_h + int(h * 0.012)

            # URL (charcoal, smaller)
            uw = draw.textbbox((0,0), url, font=f_url)
            url_w = uw[2] - uw[0]
            draw.text(((w - url_w) // 2, text_y), url,
                      fill=(23, 23, 23, card_alpha), font=f_url)

        frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        writer.write(frame)

        if frame_idx % max(1, total_frames // 10) == 0:
            print(f"     ...{frame_idx}/{total_frames} ({100*frame_idx//total_frames}%)", flush=True)

    cap.release()
    writer.release()

    # Encode with audio from original
    probe = subprocess.run(
        ["ffprobe","-v","error","-select_streams","a","-show_entries",
         "stream=codec_type","-of","csv=p=0",str(video_path)],
        capture_output=True, text=True)
    has_audio = "audio" in probe.stdout

    if has_audio:
        cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error",
               "-i", str(temp_avi), "-i", str(video_path),
               "-map","0:v:0","-map","1:a:0",
               "-c:v","libx264","-preset","fast","-crf","20",
               "-pix_fmt","yuv420p","-r",str(int(fps)),
               "-c:a","aac","-b:a","192k","-shortest",
               str(out_path)]
    else:
        cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error",
               "-i", str(temp_avi),
               "-c:v","libx264","-preset","fast","-crf","20",
               "-pix_fmt","yuv420p", str(out_path)]

    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    temp_avi.unlink(missing_ok=True)

    return out_path.exists()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add logo watermark + end card overlay")
    parser.add_argument("--video", required=True)
    parser.add_argument("--logo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--brand", default="ExploreChina Holidays")
    parser.add_argument("--price", default="From A$1,499")
    parser.add_argument("--url", default="explorechinaholidays.com.au")
    parser.add_argument("--card-duration", type=float, default=8.0)
    args = parser.parse_args()

    ok = add_overlays(
        Path(args.video), Path(args.logo), Path(args.out),
        brand=args.brand, price=args.price, url=args.url,
        card_duration=args.card_duration)
    print(f"\n{'✅' if ok else '❌'} {'overlays added' if ok else 'failed'}: {args.out}")
