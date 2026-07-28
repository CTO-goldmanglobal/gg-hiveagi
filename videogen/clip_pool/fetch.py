"""
Stage 1 — fetch candidate clips into a viewable, source-tagged pool.

Unlike the existing ECH render_pack.py fetcher (which silently auto-picks ONE
clip per keyword), this fetches N candidates per keyword and surfaces ALL of
them for human judgment. No auto-selection. No silent picks.

The pool is source-tagged from creation (source_type from the keyword config).
The manifest + HTML gallery let a human see every candidate at once.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"
PEXELS_KEYCHAIN_SERVICE = "ech-pexels-api-key"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_keyword_config(config_path: Path) -> Dict[str, Any]:
    """Load a keyword YAML config. Requires PyYAML."""
    if yaml is None:
        raise ImportError(
            "PyYAML required to read keyword configs. "
            "pip install pyyaml"
        )
    text = Path(config_path).read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)
    # Basic validation
    if not isinstance(cfg, dict):
        raise ValueError(f"keyword config {config_path} is not a mapping")
    if "tour" not in cfg:
        raise ValueError(f"keyword config {config_path} missing 'tour' field")
    if "shots" not in cfg or not isinstance(cfg["shots"], list):
        raise ValueError(f"keyword config {config_path} missing 'shots' list")
    return cfg


def _get_pexels_key() -> str:
    """Resolve the Pexels API key. Keychain first (matches ECH convention),
    then env var. Never logs the value."""
    # 1. Keychain (macOS) — matches the ECH video-pipeline convention
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s",
                 PEXELS_KEYCHAIN_SERVICE, "-w"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                key = result.stdout.strip()
                if key:
                    return key
        except (subprocess.SubprocessError, OSError):
            pass
    # 2. Env var
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if key:
        return key
    raise RuntimeError(
        f"Pexels API key not found. Store in macOS Keychain "
        f"(security add-generic-password -a \"$USER\" -s "
        f"{PEXELS_KEYCHAIN_SERVICE} -w '<key>' -U) or set PEXELS_API_KEY env var."
    )


def _pexels_search(keyword: str, api_key: str, orientation: str,
                   per_page: int = 8, timeout: int = 30) -> List[Dict[str, Any]]:
    """Call Pexels /videos/search. Returns the raw 'videos' list (may be empty)."""
    params = urllib.parse.urlencode({
        "query": keyword,
        "per_page": per_page,
        "orientation": orientation,
    })
    url = f"{PEXELS_VIDEO_SEARCH}?{params}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": api_key, "User-Agent": "gg-hiveagi/clip_pool"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("videos", []) or []
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:200]
        except Exception:  # noqa: BLE001
            pass
        print(f"  [pexels] '{keyword}' ({orientation}) HTTP {e.code}: {body}")
        return []
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [pexels] '{keyword}' ({orientation}) network error: {e}")
        return []


def _pick_file(video: Dict[str, Any], min_w: int, min_h: int) -> Optional[Dict[str, Any]]:
    """Pick the best video file from a Pexels video object.
    Prefer highest-res mp4 >= min dims; relax to 720p if none."""
    files = video.get("video_files", []) or []
    # Sort: highest res first, mp4 first
    files_sorted = sorted(
        files,
        key=lambda f: (
            -((f.get("width") or 0) * (f.get("height") or 0)),
            0 if (f.get("file_type") or "").endswith("mp4") else 1,
        ),
    )
    # Try target resolution
    for f in files_sorted:
        w, h = f.get("width") or 0, f.get("height") or 0
        if w >= min_w and h >= min_h and (f.get("file_type", "").endswith("mp4")):
            return f
    # Relax to 720p
    for f in files_sorted:
        w, h = f.get("width") or 0, f.get("height") or 0
        if w >= 1280 and h >= 720 and (f.get("file_type", "").endswith("mp4")):
            return f
    # Last resort: any mp4
    for f in files_sorted:
        if (f.get("file_type", "")).endswith("mp4"):
            return f
    return None


def _download(url: str, out_path: Path, timeout: int = 120) -> bool:
    """Download a file. Returns True on success."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "gg-hiveagi/clip_pool"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(out_path, "wb") as fp:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    fp.write(chunk)
        return out_path.exists() and out_path.stat().st_size > 1024
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"  [pexels] download failed: {e}")
        if out_path.exists():
            out_path.unlink()
        return False


def _safe_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def fetch_pool(config_path: Path, pool_dir: Path,
               api_key: Optional[str] = None,
               orientations: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch candidates for every shot in the config. Writes clips into pool_dir,
    returns a manifest dict (caller writes it + the HTML gallery).

    Args:
        config_path: path to keywords.yaml
        pool_dir: where to write pool/<shot>/<orientation>/<id>.mp4
        api_key: Pexels key (auto-resolved if None)
        orientations: ["landscape","portrait"] if None (from config or default)

    Returns:
        manifest dict — see schema.md
    """
    cfg = load_keyword_config(config_path)
    source_type = cfg.get("source_type", "stock:pexels")
    per_keyword = int(cfg.get("candidates_per_keyword", 5))
    if orientations is None:
        orientations = cfg.get("orientations", ["landscape", "portrait"])

    key = api_key or _get_pexels_key()
    pool_dir.mkdir(parents=True, exist_ok=True)

    print("═" * 60)
    print(f"  Clip Pool — fetch · tour: {cfg['tour']}")
    print("═" * 60)
    print(f"  source_type:        {source_type}")
    print(f"  candidates/keyword: {per_keyword}")
    print(f"  orientations:       {', '.join(orientations)}")
    print(f"  pool_dir:           {pool_dir}")
    print()

    shots_manifest: List[Dict[str, Any]] = []
    total_clips = 0
    shots = cfg["shots"]

    for si, shot in enumerate(shots, 1):
        shot_id = shot["id"]
        label = shot.get("label", shot_id)
        keywords = shot.get("keywords", [])
        print(f"▶ Shot {si}/{len(shots)} — {shot_id} ({label})")
        shot_candidates: List[Dict[str, Any]] = []

        for orientation in orientations:
            min_dims = (1920, 1080) if orientation == "landscape" else (1080, 1920)
            seen_ids = set()
            for keyword in keywords:
                print(f"  [{orientation}] keyword: '{keyword}'")
                videos = _pexels_search(
                    keyword, key, orientation, per_page=max(per_keyword, 8)
                )
                added = 0
                for v in videos:
                    if added >= per_keyword:
                        break
                    vid = v.get("id")
                    if vid is None or vid in seen_ids:
                        continue
                    f = _pick_file(v, *min_dims)
                    if not f:
                        continue
                    link = f.get("link")
                    if not link:
                        continue
                    seen_ids.add(vid)
                    candidate_id = f"pexels_{vid}"
                    ext = "mp4"
                    out_dir = pool_dir / shot_id / orientation
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_path = out_dir / f"{candidate_id}.{ext}"
                    # Skip if already downloaded (re-runnable)
                    if out_path.exists() and out_path.stat().st_size > 1024:
                        print(f"    ✓ cached {candidate_id}")
                    else:
                        ok = _download(link, out_path)
                        if not ok:
                            continue
                        # Polite delay — don't hammer the CDN
                        time.sleep(0.3)
                    size_kb = out_path.stat().st_size // 1024
                    user = v.get("user", {}) or {}
                    candidate = {
                        "candidate_id": candidate_id,
                        "source_type": source_type,
                        "source_url": f"https://www.pexels.com/video/{vid}/",
                        "local_path": str(out_path.relative_to(pool_dir.parent)),
                        "orientation": orientation,
                        "duration_sec": round(float(v.get("duration", 0)), 1),
                        "width": f.get("width"),
                        "height": f.get("height"),
                        "photographer": user.get("name", ""),
                        "license": "Pexels License",
                        "keywords_matched": [keyword],
                    }
                    shot_candidates.append(candidate)
                    total_clips += 1
                    added += 1
                    print(f"    ✓ {candidate_id} "
                          f"({f.get('width')}x{f.get('height')}, "
                          f"{candidate['duration_sec']}s, {size_kb}KB)")

        shots_manifest.append({
            "shot_id": shot_id,
            "label": label,
            "candidates": shot_candidates,
        })
        print(f"  → {len(shot_candidates)} candidates for {shot_id}\n")

    manifest = {
        "schema_version": 1,
        "tour": cfg["tour"],
        "source_type": source_type,
        "fetched_at": _now_iso(),
        "total_clips": total_clips,
        "shots": shots_manifest,
    }
    print("═" * 60)
    print(f"  ✅ Pool fetched: {total_clips} candidates across {len(shots)} shots")
    print("═" * 60)
    return manifest
