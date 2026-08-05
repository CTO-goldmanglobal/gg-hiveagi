"""
videogen/render.py — EDL-driven video renderer.

Replaces the old frame-based compose_reel() with a clean EDL-driven approach:
  1. Extract each shot's segment from its source clip (clip_start → clip_end)
  2. Concatenate segments per timeline positions (sequential cuts)
  3. Mux audio track (VO segments concatenated + optional music) if provided

This produces a BASE video — no branding overlays (logo/endcard/subtitle-styling).
Those are ECH-specific and belong in a separate finish() step. This keeps the
renderer generic and reusable across clients.

The EDL is the single source of truth: shot order, durations, and source
segments all come from validate_edl()'d EDL. No separate "script" or
"analyses" inputs (unlike the old compose_reel).

Usage:
    from videogen.render import render_video
    result = render_video(edl, work_dir, audio_path="mixed.mp3")
    # result.video_path → the rendered MP4
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from .edl import EDL, Shot, compute_total_duration
from .produce import RenderResult

logger = logging.getLogger(__name__)

DEFAULT_RESOLUTION = "1920:1080"   # scale target (16:9 landscape)
DEFAULT_FPS = 30
DEFAULT_CRF = 23                    # quality (lower = better; 18-28 is normal)


def _run_ffmpeg(args: List[str], timeout: int = 120) -> None:
    """Run an ffmpeg command, raising on failure."""
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    logger.debug("ffmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit {result.returncode}): {result.stderr[:500]}"
        )


def _extract_segment(
    shot: Shot,
    out_path: Path,
    resolution: str = DEFAULT_RESOLUTION,
    fps: int = DEFAULT_FPS,
) -> Path:
    """Extract one shot's video segment from its source clip.

    Extracts clip_start_sec → clip_end_sec, scales to target resolution,
    sets consistent fps, drops audio (audio is muxed separately).
    Re-encodes to ensure clean concatenation.
    """
    if not shot.source_path:
        raise ValueError(f"Shot '{shot.shot_id}' has no source_path")
    src = Path(shot.source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source clip not found: {src}")

    duration = shot.duration_sec
    _run_ffmpeg([
        "-ss", str(shot.clip_start_sec),
        "-t", str(duration),
        "-i", str(src),
        "-vf", f"scale={resolution}:force_original_aspect_ratio=decrease,"
               f"pad={resolution}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(DEFAULT_CRF),
        "-an",                    # no audio — muxed separately
        "-pix_fmt", "yuv420p",
        str(out_path),
    ])
    return out_path


def _concat_segments(segment_paths: List[Path], out_path: Path) -> Path:
    """Concatenate video segments using the concat demuxer."""
    # Write the concat list file
    list_path = out_path.parent / "concat_list.txt"
    list_path.write_text(
        "\n".join(f"file '{p.absolute()}'" for p in segment_paths),
        encoding="utf-8",
    )
    _run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(out_path),
    ])
    return out_path


def _concat_vo_segments(edl: EDL, vo_dir: Path, out_path: Path) -> Optional[Path]:
    """Concatenate VO segments into one audio track matching the timeline.

    Returns None if no VO segments exist (silent video).
    """
    vo_paths: List[Path] = []
    for shot in edl.edl:
        if shot.silent or not shot.vo_segment:
            continue
        vo_path = vo_dir / shot.vo_segment
        if vo_path.exists():
            vo_paths.append(vo_path)

    if not vo_paths:
        return None

    list_path = out_path.parent / "vo_concat_list.txt"
    list_path.write_text(
        "\n".join(f"file '{p.absolute()}'" for p in vo_paths),
        encoding="utf-8",
    )
    _run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_path),
        "-c", "copy",
        str(out_path),
    ])
    return out_path


def _mux_audio(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    """Mux an audio track onto a silent video."""
    _run_ffmpeg([
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        str(out_path),
    ])
    return out_path


def _probe_video(path: Path) -> dict:
    """Probe a video file for metadata."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet",
         "-show_entries", "format=duration:stream=codec_name,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=15, check=True,
    )
    import json
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_name") in ("h264", "hevc", "vp9")), streams[0] if streams else {})
    return {
        "duration": float(data.get("format", {}).get("duration", 0)),
        "width": vstream.get("width", 0),
        "height": vstream.get("height", 0),
        "codec": vstream.get("codec_name", "unknown"),
    }


def render_video(
    edl: EDL,
    work_dir: Path | str,
    audio_path: Optional[str] = None,
    resolution: str = DEFAULT_RESOLUTION,
    fps: int = DEFAULT_FPS,
) -> RenderResult:
    """Render an EDL into a final video file.

    Three phases:
    1. Extract each shot's segment from its source clip (re-encoded for clean concat)
    2. Concatenate segments per timeline order (sequential cuts)
    3. Mux audio (provided audio_path, or auto-concatenated VO segments from edl)

    Args:
        edl: a validated EDL (call validate_edl first)
        work_dir: directory for intermediate files
        audio_path: optional pre-mixed audio track (VO + music). If None and
                    the EDL has vo_segments in work_dir/vo/, auto-concatenates them.
        resolution: target resolution (default 1920:1080)
        fps: target framerate (default 30)

    Returns:
        RenderResult with video_path, duration, codec, resolution
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    segments_dir = work_dir / "segments"
    segments_dir.mkdir(exist_ok=True)

    if not edl.edl:
        raise ValueError("Cannot render an empty EDL")

    # Phase 1: extract each shot's segment
    logger.info("Rendering EDL: %d shots, %.1fs total", len(edl.edl), edl.total_duration_sec)
    segment_paths: List[Path] = []
    for i, shot in enumerate(edl.edl):
        seg_path = segments_dir / f"shot_{i:03d}_{shot.shot_id}.mp4"
        _extract_segment(shot, seg_path, resolution=resolution, fps=fps)
        segment_paths.append(seg_path)
        logger.info("  extracted shot %d/%d: %s (%.1fs)", i + 1, len(edl.edl), shot.shot_id, shot.duration_sec)

    # Phase 2: concat segments into draft video
    draft_path = work_dir / "draft.mp4"
    _concat_segments(segment_paths, draft_path)
    logger.info("Concatenated %d segments → %s", len(segment_paths), draft_path)

    # Phase 3: audio
    final_path = work_dir / "final.mp4"
    vo_dir = work_dir / "vo"

    if audio_path:
        # Pre-mixed audio provided (from the finish skill's mix_audio)
        _mux_audio(draft_path, Path(audio_path), final_path)
    elif vo_dir.exists():
        # Auto-concatenate VO segments from the work dir
        vo_track = work_dir / "vo_track.mp3"
        mixed = _concat_vo_segments(edl, vo_dir, vo_track)
        if mixed:
            _mux_audio(draft_path, mixed, final_path)
        else:
            # No VO — copy draft as final (silent video)
            import shutil
            shutil.copy2(draft_path, final_path)
    else:
        # No audio at all — copy draft as final
        import shutil
        shutil.copy2(draft_path, final_path)

    logger.info("Final video: %s", final_path)

    # Probe the result
    meta = _probe_video(final_path)
    return RenderResult(
        video_path=str(final_path),
        duration_sec=meta["duration"],
        codec=meta["codec"],
        resolution=f"{meta['width']}x{meta['height']}",
    )
