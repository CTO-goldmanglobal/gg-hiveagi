"""
composite.py — render ALL overlays in one pass per frame.

Combines: subtitles + logo watermark + end card panel.
Previous approach ran these as separate passes, which caused each pass to
overwrite the frame (losing prior overlays). This single-pass renderer draws
everything onto each frame in one Pillow composite operation.

This is the AUDITED renderer — run composite_audit.py after to verify.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _probe_dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(path)], capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0


def _parse_srt(srt_path):
    """Parse SRT — split on index numbers, not blank lines (multi-line text breaks blank-line split)."""
    content = srt_path.read_text(encoding="utf-8")
    entries = []
    # Split on the pattern: number on its own line followed by timestamp
    # Each cue starts with a line that's just a number
    blocks = re.split(r'\n(?=\d+\s*\n\d{2}:\d{2}:\d{2},\d{3})', content.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        # Find the timestamp line (line[1] after the index number)
        ts_line = None
        text_start = 0
        for i, line in enumerate(lines):
            if '-->' in line:
                ts_line = line
                text_start = i + 1
                break
        if not ts_line:
            continue
        m = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', ts_line)
        if not m:
            continue
        g = m.groups()
        start = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000
        end = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000
        text = '\n'.join(lines[text_start:]) if text_start < len(lines) else ""
        entries.append((start, end, text))
    return entries


def _load_font(bold, size):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in paths:
        if Path(fp).exists():
            return __import__("PIL").ImageFont.truetype(fp, size)
    return __import__("PIL").ImageFont.load_default()


def composite_all(video_path, logo_path, srt_path, out_path,
                   brand="ExploreChina Holidays", price="From A$1,499",
                   url="explorechinaholidays.com.au",
                   card_start=None, card_duration=8.0):
    """Render subtitles + logo watermark + end card in ONE pass."""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    total_dur = _probe_dur(video_path)
    if card_start is None:
        card_start = max(0, total_dur - card_duration)

    subs = _parse_srt(srt_path)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Logo
    logo_pil = Image.open(logo_path).convert("RGBA")
    wm_w = int(w * 0.12)
    scale = wm_w / logo_pil.width
    logo_wm = logo_pil.resize((wm_w, int(logo_pil.height * scale)))
    wm_w, wm_h = logo_wm.size

    card_logo_w = int(w * 0.20)
    scale2 = card_logo_w / logo_pil.width
    logo_card = logo_pil.resize((card_logo_w, int(logo_pil.height * scale2)))
    cl_w, cl_h = logo_card.size

    # Fonts
    f_sub = _load_font(True, max(int(h * 0.038), 36))
    f_brand = _load_font(True, int(h * 0.038))
    f_price = _load_font(True, int(h * 0.055))
    f_url = _load_font(False, int(h * 0.028))

    wm_x = (w - wm_w) // 2
    wm_y = int(h * 0.07)

    def logo_visible(t):
        cycle = t % 10.0
        return cycle < 4.0

    print(f"  🎬 compositing ALL overlays ({w}x{h}, {total_frames} frames)")
    print(f"     subtitles: {len(subs)} cues from {srt_path.name}")
    print(f"     logo: on/off at ({wm_x},{wm_y}), {wm_w}x{wm_h}")
    print(f"     end card: {card_start:.1f}s → {total_dur:.1f}s")

    temp_avi = out_path.parent / "_composite_temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    writer = cv2.VideoWriter(str(temp_avi), fourcc, fps, (w, h))

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_idx / fps
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img, 'RGBA')

        # === LAYER 1: LOGO WATERMARK ===
        if logo_visible(timestamp):
            cycle = timestamp % 10.0
            if cycle < 0.5:
                alpha = int(180 * (cycle / 0.5))
            elif cycle > 3.5:
                alpha = int(180 * ((4.0 - cycle) / 0.5))
            else:
                alpha = 180
            wm_faded = logo_wm.copy()
            wm_faded.putalpha(wm_faded.getchannel('A').point(lambda a: int(a * alpha / 255)))
            pil_img.paste(wm_faded, (wm_x, wm_y), wm_faded)

        # === LAYER 2: SUBTITLES ===
        active_sub = None
        for start, end, text in subs:
            if start <= timestamp < end:
                active_sub = text
                break

        if active_sub:
            lines = active_sub.split('\n')
            line_data = []
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=f_sub)
                line_data.append((line, bbox[2]-bbox[0], bbox[3]-bbox[1]))

            lh = max(ld[2] for ld in line_data)
            total_h = lh * len(lines) + 8 * (len(lines) - 1)
            max_w = max(ld[1] for ld in line_data)

            pad = 16
            box_w = max_w + pad * 2
            box_h = total_h + pad * 2
            box_x = (w - box_w) // 2
            box_y = h - int(h * 0.12) - box_h  # 12% from bottom

            # Semi-transparent dark box for subtitle readability
            draw.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h],
                                   radius=8, fill=(0, 0, 0, 160))

            ty = box_y + pad
            for line_text, lw, _ in line_data:
                tx = (w - lw) // 2
                draw.text((tx, ty), line_text, fill=(255, 255, 255, 255), font=f_sub)
                ty += lh + 8

        # === LAYER 3: END CARD PANEL ===
        if timestamp >= card_start:
            card_progress = min(1.0, (timestamp - card_start) / 0.8)
            card_alpha = int(220 * card_progress)

            panel_h = int(h * 0.42)
            panel_y = h - panel_h
            panel_x = int(w * 0.1)
            panel_w = int(w * 0.8)

            draw.rounded_rectangle(
                [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                radius=20, fill=(250, 248, 244, int(200 * card_progress)))

            card_logo_x = (w - cl_w) // 2
            card_logo_y = panel_y + int(h * 0.03)
            cl_faded = logo_card.copy()
            cl_faded.putalpha(cl_faded.getchannel('A').point(lambda a: int(a * card_progress)))
            pil_img.paste(cl_faded, (card_logo_x, card_logo_y), cl_faded)

            text_y = card_logo_y + cl_h + int(h * 0.02)
            bw = draw.textbbox((0,0), brand, font=f_brand)
            draw.text(((w-(bw[2]-bw[0]))//2, text_y), brand,
                      fill=(23,23,23,card_alpha), font=f_brand)
            text_y += (bw[3]-bw[1]) + int(h * 0.015)

            pw = draw.textbbox((0,0), price, font=f_price)
            draw.text(((w-(pw[2]-pw[0]))//2, text_y), price,
                      fill=(200,32,47,card_alpha), font=f_price)
            text_y += (pw[3]-pw[1]) + int(h * 0.012)

            uw = draw.textbbox((0,0), url, font=f_url)
            draw.text(((w-(uw[2]-uw[0]))//2, text_y), url,
                      fill=(23,23,23,card_alpha), font=f_url)

        frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        writer.write(frame)

        if frame_idx % max(1, total_frames // 10) == 0:
            print(f"     ...{frame_idx}/{total_frames} ({100*frame_idx//total_frames}%)", flush=True)

    cap.release()
    writer.release()

    # Encode with audio
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
               "-c:a","aac","-b:a","192k","-shortest", str(out_path)]
    else:
        cmd = ["ffmpeg","-y","-hide_banner","-loglevel","error",
               "-i", str(temp_avi),
               "-c:v","libx264","-preset","fast","-crf","20",
               "-pix_fmt","yuv420p", str(out_path)]

    subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    temp_avi.unlink(missing_ok=True)
    return out_path.exists()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Composite all overlays in one pass")
    p.add_argument("--video", required=True)
    p.add_argument("--logo", required=True)
    p.add_argument("--srt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--brand", default="ExploreChina Holidays")
    p.add_argument("--price", default="From A$1,499")
    p.add_argument("--url", default="explorechinaholidays.com.au")
    p.add_argument("--card-duration", type=float, default=8.0)
    args = p.parse_args()

    ok = composite_all(Path(args.video), Path(args.logo), Path(args.srt),
                       Path(args.out), brand=args.brand, price=args.price,
                       url=args.url, card_duration=args.card_duration)
    print(f"\n{'✅' if ok else '❌'} {'composite complete' if ok else 'failed'}: {args.out}")
