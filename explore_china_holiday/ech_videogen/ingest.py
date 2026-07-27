"""
Stage 1 — INGEST
ffprobe video metadata + sample candidate frames via ffmpeg.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def probe_clip(clip_path: Path) -> Dict:
    """Use ffprobe to get duration, width, height, fps of a clip."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(clip_path),
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(out)
        stream = data.get("streams", [{}])[0]
        # r_frame_rate is "30/1" — convert to float
        fr = stream.get("r_frame_rate", "30/1")
        num, den = fr.split("/")
        fps = float(num) / float(den) if float(den) else 30.0
        duration = float(data.get("format", {}).get("duration")
                         or stream.get("duration", 0))
        return {
            "path": str(clip_path),
            "width": int(stream.get("width", 1920)),
            "height": int(stream.get("height", 1080)),
            "fps": fps,
            "duration": duration,
        }
    except (subprocess.CalledProcessError, ValueError, KeyError) as e:
        return {"path": str(clip_path), "error": str(e)}


def sample_frames(clip_path: Path, out_dir: Path,
                  interval_sec: float = 5.0,
                  quality: int = 3) -> List[Path]:
    """
    Sample one frame every `interval_sec` seconds via ffmpeg.
    Returns sorted list of frame paths: frame_000001.jpg, frame_000002.jpg, ...
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    # Use fps filter (1/interval = frames per second)
    fps_filter = f"fps=1/{interval_sec}"
    out_pattern = str(out_dir / "frame_%06d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", str(clip_path),
        "-vf", fps_filter,
        "-qscale:v", str(quality),
        out_pattern,
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  frame sampling failed for {clip_path.name}: {e}")
        return []
    return sorted(out_dir.glob("frame_*.jpg"))


def ingest_clips(clips_dir: Path, frames_out: Path,
                 interval_sec: float = 5.0) -> Dict:
    """
    Walk clips_dir, probe each, sample frames into frames_out/<clip_stem>/.

    Returns:
        {
            "clips": [{path, width, height, fps, duration}, ...],
            "frames": {clip_stem: [Path, ...], ...},
            "total_frames": int,
        }
    """
    if not ffmpeg_available():
        raise RuntimeError("ffmpeg/ffprobe not installed. macOS: brew install ffmpeg")

    clips = sorted(
        p for p in clips_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm")
    )
    if not clips:
        raise FileNotFoundError(f"No video clips found in {clips_dir}")

    result = {"clips": [], "frames": {}, "total_frames": 0}
    for clip in clips:
        print(f"  📼 probing {clip.name} ...")
        meta = probe_clip(clip)
        result["clips"].append(meta)
        if "error" in meta:
            continue
        clip_frames_dir = frames_out / clip.stem
        frames = sample_frames(clip, clip_frames_dir, interval_sec)
        result["frames"][clip.stem] = frames
        result["total_frames"] += len(frames)
        print(f"     {meta['duration']:.1f}s, {meta['width']}x{meta['height']} "
              f"→ {len(frames)} frames")

    return result
