"""
Landscape → Portrait adapter.

Two methods for producing vertical (9:16) clips from horizontal (16:9) source:

  Method 1 — CROP from landscape (this module)
    The landscape clips are 4K (3840×2160). We crop a tall, narrow slice
    to produce 9:16. Three crop modes:
      - center:    blind center crop (safe default)
      - smart:     LLM identifies the subject position, crops there
      - feature:   manual override — you specify the x-offset (0.0–1.0)

  Method 2 — re-fetch portrait from a second source (Pixabay, etc.)
    Different keyword pool that may have natively vertical footage.
    See fetch.py (future: multi-source support).

Crop math:
  Source:  3840 × 2160 (landscape)
  Target:  2160 × 3840 (portrait) — but we keep the SOURCE height (2160)
           and crop WIDTH down to 2160×(9/16)... no wait:

  Correct: portrait 9:16 means width:height = 9:16
    If we keep source height = 2160, then:
    target_width = 2160 × (9/16) = 1215
    So we crop 1215px wide × 2160px tall from the 3840px-wide source.
    The crop window is 1215 wide, positioned at x_offset within 3840.

  The output is then scaled to 1080×1920 for standard portrait delivery.

Why this matters: the founder's insight is that landscape 4K footage has
enough resolution to zoom into a feature (like a single Terracotta Warrior
face) for portrait. This avoids re-sourcing weak portrait pools entirely.
"""

import json
import subprocess
import urllib  # explicit parent import — Python 3.14 needs this for urllib.X refs
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .models import resolve_local_path


def probe_resolution(clip_path: Path) -> Tuple[int, int]:
    """Get (width, height) of a video via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(clip_path)],
        capture_output=True, text=True, timeout=10,
    )
    parts = result.stdout.strip().split(",")
    return int(parts[0]), int(parts[1])


def compute_crop_box(src_w: int, src_h: int,
                     target_ratio: float = 9.0 / 16.0,
                     x_pct: float = 0.5) -> Tuple[int, int, int, int]:
    """
    Compute the crop box for a portrait slice from a landscape frame.

    Args:
        src_w, src_h: source dimensions
        target_ratio: width/height (9/16 = 0.5625 for portrait)
        x_pct: 0.0 = left edge, 0.5 = center, 1.0 = right edge.
               The crop window is centered on this x position.

    Returns:
        (crop_w, crop_h, crop_x, crop_y) — all in source pixels.
        crop_x, crop_y are the top-left of the crop box.
    """
    # Keep full source height; compute width from ratio
    crop_h = src_h
    crop_w = int(src_h * target_ratio)
    # Clamp crop_w to source width
    crop_w = min(crop_w, src_w)
    # Position the crop window centered on x_pct
    center_x = int(src_w * x_pct)
    crop_x = max(0, min(src_w - crop_w, center_x - crop_w // 2))
    crop_y = 0  # full height
    return crop_w, crop_h, crop_x, crop_y


def smart_crop_x(clip_path: Path, api_key: str,
                 model: str = "MiniMax-M3") -> Tuple[float, str]:
    """
    Ask the LLM where the subject is, for smart portrait cropping.

    Returns:
        (x_pct, reason) — x_pct is 0.0–1.0 horizontal position to center on.
    """
    import base64
    import cv2
    from llm_wiki_engine.llm_json import extract_json

    # Extract middle frame
    cap = cv2.VideoCapture(str(clip_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return 0.5, "frame extraction failed, defaulting to center"

    # Downscale for API
    h, w = frame.shape[:2]
    if w > 1280:
        scale = 1280 / w
        frame = cv2.resize(frame, (1280, int(h * scale)))
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        return 0.5, "encode failed"

    data_uri = f"data:image/jpeg;base64,{base64.b64encode(buf.tobytes()).decode()}"
    prompt = (
        "This is a wide landscape video frame. I need to crop it to a vertical "
        "9:16 portrait frame (tall and narrow). Where should I center the crop "
        "to capture the most visually striking subject?\n\n"
        'Return JSON: {"crop_x_pct": <0.0-1.0>, "crop_reason": "<why>"}'
    )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You help editors crop landscape to portrait. Return JSON only."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri, "detail": "default"}},
                {"type": "text", "text": prompt},
            ]},
        ],
        "temperature": 0.2, "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.minimax.io/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw = data["choices"][0]["message"]["content"]
        result = extract_json(raw)
        if result and "crop_x_pct" in result:
            x = float(result["crop_x_pct"])
            x = max(0.0, min(1.0, x))  # clamp
            return x, result.get("crop_reason", "")
    except Exception:  # noqa: BLE001
        pass
    return 0.5, "LLM call failed, defaulting to center"


def crop_to_portrait(src_path: Path, out_path: Path,
                     mode: str = "center",
                     x_pct: Optional[float] = None,
                     api_key: Optional[str] = None,
                     target_w: int = 1080, target_h: int = 1920) -> Dict[str, Any]:
    """
    Crop a landscape clip to portrait (9:16).

    Args:
        src_path: source landscape .mp4
        out_path: output portrait .mp4
        mode: "center" | "smart" | "feature"
        x_pct: manual x position (0.0–1.0) for "feature" mode.
               If None and mode=="feature", defaults to 0.5.
        api_key: MiniMax key for "smart" mode (auto-resolved if None)
        target_w, target_h: output resolution (default 1080×1920)

    Returns:
        {"mode": str, "x_pct": float, "reason": str, "out_path": str}
    """
    src_w, src_h = probe_resolution(src_path)

    reason = ""
    if mode == "smart":
        from .llm_tags import _get_api_key
        key = api_key or _get_api_key()
        x_pct, reason = smart_crop_x(src_path, key)
    elif mode == "feature":
        if x_pct is None:
            x_pct = 0.5
        reason = f"manual feature crop at x={x_pct:.2f}"
    else:  # center
        x_pct = 0.5
        reason = "center crop"

    crop_w, crop_h, crop_x, crop_y = compute_crop_box(
        src_w, src_h, target_ratio=9.0 / 16.0, x_pct=x_pct
    )

    # ffmpeg crop filter: crop=w:h:x:y, then scale to target
    vf = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={target_w}:{target_h}"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",  # no audio (we add music/VO later)
        str(out_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[:300]}")

    return {
        "mode": mode,
        "x_pct": round(x_pct, 3),
        "reason": reason,
        "src_resolution": f"{src_w}x{src_h}",
        "crop_box": f"{crop_w}x{crop_h}+{crop_x}+{crop_y}",
        "out_resolution": f"{target_w}x{target_h}",
        "out_path": str(out_path),
    }


def adapt_pool_clips(pool_dir: Path, manifest: Dict[str, Any],
                     clip_ids: list, mode: str = "smart") -> Dict[str, Dict[str, Any]]:
    """
    Adapt specific landscape clips to portrait. Writes to pool/<shot>/portrait_adapted/.

    Every adapted clip carries a `derived_from` provenance chain so the crop
    is always traceable back to its source:
      derived_from.source_candidate_id  → which pool clip was cropped
      derived_from.source_pexels_id     → original stock ID
      derived_from.source_url           → Pexels page (photographer credit)
      derived_from.photographer         → who shot the original
      derived_from.license              → under what terms
      derived_from.crop_decision_by     → "llm:minimax-m3" or "human" or "center"

    Args:
        pool_dir: pool directory
        manifest: pool manifest
        clip_ids: list of candidate_ids to adapt (must be landscape clips)
        mode: "center" | "smart" | "feature"

    Returns:
        {candidate_id: crop_result_dict}
    """
    results = {}
    # Build lookup: candidate_id → (shot, candidate) dict
    cand_lookup = {}
    for shot in manifest.get("shots", []):
        for c in shot.get("candidates", []):
            cand_lookup[c["candidate_id"]] = (shot, c)

    tour = manifest.get("tour", "")
    source_type = manifest.get("source_type", "")

    for cid in clip_ids:
        if cid not in cand_lookup:
            print(f"  ⚠️  {cid} not found in manifest, skipping")
            continue
        shot, cand = cand_lookup[cid]
        if cand["orientation"] != "landscape":
            print(f"  ⚠️  {cid} is {cand['orientation']}, not landscape — skipping")
            continue

        local = resolve_local_path(pool_dir, cand["local_path"])

        out_dir = pool_dir / shot["shot_id"] / "portrait_adapted"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{cid}_portrait.mp4"

        print(f"  📐 adapting {cid} ({mode})...", end="", flush=True)
        result = crop_to_portrait(local, out_path, mode=mode)

        # Attach the provenance chain — "mark the zoom coming from"
        pexels_id = cand.get("candidate_id", "").replace("pexels_", "")
        result["derived_from"] = {
            "source_candidate_id": cid,
            "source_pexels_id": pexels_id,
            "source_url": cand.get("source_url", ""),
            "source_type": source_type,
            "photographer": cand.get("photographer", ""),
            "license": cand.get("license", ""),
            "tour": tour,
            "shot_id": shot["shot_id"],
            "crop_decision_by": "llm:minimax-m3" if mode == "smart" else mode,
        }
        result["adapted_candidate_id"] = f"{cid}_portrait"

        results[cid] = result
        print(f" x={result['x_pct']:.2f} → {out_path.name}")
        print(f"     {result['reason'][:80]}")
        print(f"     from: {cid} (pexels {pexels_id}, by {cand.get('photographer','?')})")

    return results
