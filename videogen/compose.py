"""
Stage 4 — COMPOSE
ffmpeg assembly: per-segment clips from the source footage (matched by
frame timestamp), concat with crossfade, burn subtitles, 9:16 vertical crop.

Strategy: rather than stitching still frames (which looks like a slideshow),
we extract a short VIDEO SEGMENT around each selected frame's timestamp
from the source clip, then concat those segments with crossfades. This
keeps motion in the final Reel — critical for tourism appeal.
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from .ingest import probe_clip


def _find_source_clip_for_frame(frame_path: Path, clips_meta: List[Dict]) -> Optional[Dict]:
    """Match a sampled frame back to its source clip.

    Frames are sampled into frames_out/<clip_stem>/frame_NNNNNN.jpg,
    so the clip stem is the frame's parent dir name.
    """
    clip_stem = frame_path.parent.name
    for meta in clips_meta:
        if Path(meta["path"]).stem == clip_stem:
            return meta
    return None


def _frame_to_timestamp(frame_path: Path, interval_sec: float) -> float:
    """
    Reconstruct the approximate source timestamp of a sampled frame.
    Frames are sampled at fps=1/interval, so frame_N.jpg ≈ (N-1)*interval seconds.
    """
    stem = frame_path.stem  # "frame_000007"
    try:
        n = int(stem.split("_")[1])
        return (n - 1) * interval_sec
    except (IndexError, ValueError):
        return 0.0


def _extract_segment(src_clip: Path, start_sec: float, duration_sec: float,
                     out_path: Path, target_w: int = 1080, target_h: int = 1920) -> bool:
    """
    Extract a video segment from src_clip starting at start_sec for duration_sec,
    scaled + center-cropped to 9:16 (1080x1920).

    Returns True on success.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # crop to 9:16 then scale: crop=ih*9/16:ih (center), then scale to target
    vf = (
        f"crop=ih*9/16:ih,"
        f"scale={target_w}:{target_h}:flags=lanczos,"
        f"setsar=1"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{max(0, start_sec):.3f}",
        "-i", str(src_clip),
        "-t", f"{duration_sec:.3f}",
        "-vf", vf,
        "-r", "30",
        "-an",  # drop audio for MVP (subtitles only)
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


def _concat_with_crossfade(segments: List[Path], out_path: Path,
                           crossfade_sec: float = 0.5) -> bool:
    """
    Concat segments with crossfade transitions.

    Uses the xfade filter chained across all segments. For N segments,
    builds an xfade chain. Offset = cumulative duration minus crossfade.
    """
    if not segments:
        return False
    if len(segments) == 1:
        shutil.copy2(segments[0], out_path)
        return True

    # Build the xfade filtergraph
    # First probe each segment for its duration
    inputs = []
    for s in segments:
        inputs.extend(["-i", str(s)])

    # Build filter: [0][1]xfade=...[v01]; [v01][2]xfade=...[v012]; ...
    filter_parts = []
    prev_label = "0"
    cumulative = 0.0
    for i in range(1, len(segments)):
        # probe duration of previous segment
        meta = probe_clip(segments[i - 1])
        prev_dur = meta.get("duration", 5.0)
        cumulative += prev_dur
        offset = max(0, cumulative - crossfade_sec)
        out_label = f"v{i}" if i < len(segments) - 1 else "vout"
        filter_parts.append(
            f"[{prev_label}][{i}]xfade=transition=fade:duration={crossfade_sec}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        cumulative = offset  # xfade overlaps

    filter_complex = ";".join(filter_parts)
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path.exists()
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  xfade concat failed ({e}); falling back to hard concat")
        return _hard_concat(segments, out_path)


def _hard_concat(segments: List[Path], out_path: Path) -> bool:
    """Fallback: concat list + demuxer (no transition)."""
    concat_list = out_path.parent / "concat_list.txt"
    concat_list.write_text(
        "\n".join(f"file '{s.resolve()}'" for s in segments),
        encoding="utf-8",
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path.exists()
    except subprocess.CalledProcessError:
        return False


def _subtitles_filter_available() -> bool:
    """
    Check whether this ffmpeg build has the `subtitles` filter (needs libass).
    Many slim builds (e.g. default homebrew on macOS) don't include it.
    """
    try:
        out = subprocess.check_output(
            ["ffmpeg", "-hide_banner", "-filters"],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="ignore")
        return " subtitles " in f" {out} " or "\nsubtitles " in out
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _burn_subtitles(video_path: Path, srt_path: Path, out_path: Path) -> bool:
    """
    Burn SRT subtitles into the video.

    Returns True if subtitles were burned in. Returns False (and does NOT
    raise) if the `subtitles` filter is unavailable in this ffmpeg build —
    in that case the caller copies the draft through unmodified.

    Style: white text on semi-transparent black box, bottom-third, mobile-readable.
    """
    if not _subtitles_filter_available():
        print("  ⚠️  ffmpeg has no `subtitles` filter (libass not compiled in)")
        print("      → skipping burn-in. SRT is at:", srt_path)
        print("      → TikTok / Instagram will auto-caption from the SRT or")
        print("        their own speech-to-text when you upload.")
        print("      → to enable burn-in: brew install ffmpeg --with-libass")
        return False

    # Style: white text, black box, bottom-third (above TikTok safe zone).
    style = (
        "FontName=Arial,"
        "FontSize=14,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&HAA000000,"
        "BorderStyle=4,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=80"
    )
    # Escape colons in path for subtitles filter
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"subtitles='{srt_escaped}':force_style='{style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path.exists()
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  subtitle burn failed: {e}")
        return False


def compose_reel(script: List[Dict[str, Any]],
                 analyses: List[Dict[str, Any]],
                 clips_meta: List[Dict],
                 interval_sec: float,
                 work_dir: Path,
                 out_path: Path,
                 crossfade_sec: float = 0.5) -> Path:
    """
    Full compose: extract segments → concat with xfade → burn subtitles (if available).

    Args:
        script: [{frame_index, duration_sec, voiceover_text}, ...]
        analyses: full analysis list (to look up frame_path by frame_index)
        clips_meta: clip metadata from ingest (to find source clip paths)
        interval_sec: frame sampling interval (to reconstruct timestamps)
        work_dir: temp dir for intermediate segment files
        out_path: final .mp4 path

    Returns:
        Path to the final composed Reel.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    segments_dir = work_dir / "segments"
    segments_dir.mkdir(exist_ok=True)

    by_index = {a["frame_index"]: a for a in analyses}

    print(f"  ✂️  extracting {len(script)} segments ...")
    segments = []
    for i, seg in enumerate(script):
        fidx = seg["frame_index"]
        duration = seg["duration_sec"]
        analysis = by_index.get(fidx)
        if not analysis:
            print(f"     ⚠️  frame_index {fidx} not in analyses; skipping")
            continue
        frame_path = Path(analysis["frame_path"])
        clip_meta = _find_source_clip_for_frame(frame_path, clips_meta)
        if not clip_meta:
            print(f"     ⚠️  no source clip for {frame_path}; skipping")
            continue
        src_clip = Path(clip_meta["path"])
        start = max(0, _frame_to_timestamp(frame_path, interval_sec) - 0.5)
        seg_out = segments_dir / f"seg_{i:03d}.mp4"
        if _extract_segment(src_clip, start, duration, seg_out):
            segments.append(seg_out)
            print(f"     ✓ seg {i}: frame#{fidx}, {duration:.1f}s from {src_clip.name}")
        else:
            print(f"     ✗ seg {i}: extraction failed")

    if not segments:
        raise RuntimeError("No segments extracted — cannot compose Reel")

    print(f"  🔗 concatenating {len(segments)} segments with crossfade ...")
    draft = work_dir / "draft_no_subs.mp4"
    if not _concat_with_crossfade(segments, draft, crossfade_sec):
        raise RuntimeError("ffmpeg concat failed")
    print(f"     ✓ draft (no subtitles): {draft}")

    srt_path = work_dir / "subtitles.srt"
    if srt_path.exists():
        print(f"  📝 burning subtitles ...")
        if _burn_subtitles(draft, srt_path, out_path):
            print(f"     ✓ final with subtitles: {out_path}")
        else:
            shutil.copy2(draft, out_path)
            print(f"     → final (no burn-in): {out_path}")
            print(f"     → SRT for manual use: {srt_path}")
    else:
        shutil.copy2(draft, out_path)
        print(f"     ⚠️  no SRT found; final has no subtitles: {out_path}")

    return out_path
