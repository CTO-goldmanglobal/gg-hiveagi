"""
LLM pre-tagger — content dimension tagging via MiniMax M3 vision.

The metrics module (metrics.py) answers "will this clip cut jarringly? is it
static?" — the PHYSICAL signals. This module answers "what IS this clip?" —
the CONTENT signals:

  shot_type          landscape | architecture | people | detail | food | action | aerial
  camera_perspective eye_level | top_angle | low_angle | high_angle | first_person_pov | drone | shoulder_cam
  time_of_day        dawn | morning | midday | afternoon | golden_hour | dusk | night | unknown
  subject_action     free text — what's happening
  mood               calm | epic | intimate | energetic | serene | dramatic
  commercial_grade   broadcast | professional | amateur | personal

Why this matters (from the founder's review of circle #1):
  - POV/action-cam clips aren't "reject" — they're a DIFFERENT CATEGORY
    (camera_perspective: first_person_pov). They might serve a future cut.
  - A Great Wall clip isn't just "Great Wall" — it's "drone / morning / epic /
    tourists climbing / mountains+clouds." Content fit matters, not just location.
  - The LLM catches what the eye catches: it independently tagged the POV clip
    as "first_person_pov / personal" — matching the founder's "like AI glasses,
    not commercial-grade" judgment.

The LLM sees still FRAMES, not video. So we extract 2-3 representative frames
per clip and tag those. Motion/mood inference is from the LLM's understanding
of what the frame depicts, plus our metrics layer for actual motion data.

Output is cached to clip_tags.json (like clip_metrics.json). Re-runnable.
"""

import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional

from llm_wiki_engine.llm_json import extract_json

TAG_PROMPT = (
    'Tag this video frame for a tourism video editor. '
    'Return JSON only, no reasoning:\n'
    '{"shot_type":"landscape|architecture|people|detail|food|action|aerial",'
    '"camera_perspective":"eye_level|top_angle|low_angle|high_angle|first_person_pov|drone|shoulder_cam",'
    '"time_of_day":"dawn|morning|midday|afternoon|golden_hour|dusk|night|unknown",'
    '"subject_action":"<what is happening>",'
    '"mood":"calm|epic|intimate|energetic|serene|dramatic",'
    '"commercial_grade":"broadcast|professional|amateur|personal",'
    '"description":"<one sentence>"}'
)


def _get_api_key() -> str:
    """Resolve MiniMax API key from .env or env var."""
    # env var first
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    # .env file
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY not found in env or .env")


def _extract_frames(clip_path: Path, n_frames: int = 2,
                    quality: int = 80) -> List[bytes]:
    """Extract n representative frames (evenly spaced) as JPEG bytes."""
    import cv2
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return []

    # Sample at 1/3 and 2/3 positions (avoids intro/outro cards)
    positions = [total // 3, total * 2 // 3] if n_frames >= 2 else [total // 2]
    if n_frames >= 3:
        positions = [total // 4, total // 2, total * 3 // 4]

    frames = []
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        # Downscale large frames to keep API cost reasonable (max 1280 wide)
        h, w = frame.shape[:2]
        if w > 1280:
            scale = 1280 / w
            frame = cv2.resize(frame, (1280, int(h * scale)))
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok:
            frames.append(buf.tobytes())
    cap.release()
    return frames


def _tag_frame(frame_bytes: bytes, api_key: str,
               model: str = "MiniMax-M3", timeout: int = 90) -> Optional[Dict[str, Any]]:
    """Send one frame to MiniMax M3 vision, return parsed tags or None."""
    data_uri = f"data:image/jpeg;base64,{base64.b64encode(frame_bytes).decode()}"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "Tag video frames for editors. Output JSON only."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri, "detail": "default"}},
                {"type": "text", "text": TAG_PROMPT},
            ]},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,  # M3 emits <think> before JSON; needs headroom
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://api.minimax.io/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw = data["choices"][0]["message"]["content"]
        return extract_json(raw)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError) as e:
        return None


def _merge_frame_tags(frame_tags: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge tags from multiple frames of the same clip.
    Takes the most informative values (non-generic, most specific)."""
    if not frame_tags:
        return {}
    if len(frame_tags) == 1:
        return frame_tags[0]

    merged = {}
    # For categorical fields, prefer agreement; if they differ, note both
    for key in ["shot_type", "camera_perspective", "time_of_day",
                "mood", "commercial_grade"]:
        vals = [t.get(key, "") for t in frame_tags if t.get(key)]
        if not vals:
            merged[key] = ""
        elif len(set(vals)) == 1:
            merged[key] = vals[0]
        else:
            # Multiple frames disagree — record all unique values
            merged[key] = " / ".join(sorted(set(vals)))
    # Free-text fields: take the longest (most descriptive)
    for key in ["subject_action", "description"]:
        texts = [t.get(key, "") for t in frame_tags if t.get(key)]
        merged[key] = max(texts, key=len) if texts else ""
    return merged


def pretag_clip(clip_path: Path, api_key: str, n_frames: int = 2) -> Dict[str, Any]:
    """
    Tag a single clip: extract frames, send to LLM, merge results.

    Returns:
        {
            "tags": {shot_type, camera_perspective, ...},
            "frames_tagged": int,
        }
    """
    frames = _extract_frames(clip_path, n_frames=n_frames)
    if not frames:
        return {"tags": {}, "frames_tagged": 0, "error": "no frames extracted"}

    all_tags = []
    for fb in frames:
        tags = _tag_frame(fb, api_key)
        if tags:
            all_tags.append(tags)

    if not all_tags:
        return {"tags": {}, "frames_tagged": 0, "error": "all frames failed LLM call"}

    merged = _merge_frame_tags(all_tags)
    return {"tags": merged, "frames_tagged": len(all_tags)}


def pretag_pool(manifest: Dict[str, Any], pool_dir: Path,
                api_key: Optional[str] = None,
                n_frames: int = 2, force: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Pre-tag every clip in the pool. Cached to clip_tags.json.

    Args:
        manifest: pool manifest dict
        pool_dir: pool directory
        api_key: MiniMax key (auto-resolved if None)
        n_frames: frames to sample per clip (default 2)
        force: re-tag even if cached

    Returns:
        {candidate_id: {tags: {...}, frames_tagged: int}}
    """
    key = api_key or _get_api_key()
    cache_path = pool_dir / "clip_tags.json"
    cache = {}
    if cache_path.exists() and not force:
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cache = {}

    total = 0
    tagged = 0
    for shot in manifest.get("shots", []):
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            if cid in cache and not force:
                continue
            total += 1
            local = pool_dir.parent / cand["local_path"]
            if not local.exists():
                local = pool_dir / cand["local_path"].replace("pool/", "", 1)
            if not local.exists():
                print(f"  ⚠️  {cid}: file missing, skipping")
                continue

            print(f"  🏷️  tagging {cid} ...", end="", flush=True)
            result = pretag_clip(local, key, n_frames=n_frames)
            cache[cid] = result
            tags = result.get("tags", {})
            if tags:
                tagged += 1
                print(f" {tags.get('shot_type','?')} / "
                      f"{tags.get('camera_perspective','?')} / "
                      f"{tags.get('mood','?')}")
            else:
                print(f" ⚠️ failed ({result.get('error','')})")

            # Write incrementally (re-runnable, crash-safe)
            cache_path.write_text(
                json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8"
            )

    print(f"\n  tagged {tagged}/{total} new clips ({len(cache)} total in cache)")
    return cache
