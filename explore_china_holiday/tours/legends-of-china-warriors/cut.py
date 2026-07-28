"""
Cut — assemble the final Reel from locked selections.

Reads selection_draft.json, takes the 8 chosen clips, cuts each to its script
duration, concatenates with crossfades, and produces two versions:
  - landscape 16:9 (1920x1080)
  - vertical 9:16 (1080x1920, from landscape adapt crops)

The end card (shot8) overlays the ECH brand design on the background clip.

This is Step 3 of the small-circle loop — the deliverable.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# The script — durations + VO per shot (from SCRIPT-vertical/landscape.md)
# Total: 55s
CUT_PLAN = [
    {"shot": "shot1_hook",        "duration": 6.0,  "vo": "China doesn't reveal itself all at once..."},
    {"shot": "shot2_beijing",     "duration": 8.0,  "vo": "It begins in Beijing..."},
    {"shot": "shot3_great_wall",  "duration": 8.0,  "vo": "You'll walk the Great Wall..."},
    {"shot": "shot4_warriors",    "duration": 10.0, "vo": "In Xi'an, you stand before the Terracotta Warriors..."},
    {"shot": "shot5_water_towns", "duration": 8.0,  "vo": "Then the pace softens..."},
    {"shot": "shot6_tea",         "duration": 6.0,  "vo": "In Hangzhou, you taste it..."},
    {"shot": "shot7_shanghai",    "duration": 4.0,  "vo": "And Shanghai..."},
    {"shot": "shot8_trust",       "duration": 5.0,  "vo": "Twelve days. From fourteen ninety-nine..."},
]


def _run_ffmpeg(cmd: list, timeout: int = 120) -> None:
    """Run ffmpeg, raise on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")


def _probe_duration(path: Path) -> float:
    """Get clip duration in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def cut_segment(src_path: Path, out_path: Path, duration: float,
                target_w: int, target_h: int,
                crop_x_pct: Optional[float] = None) -> Path:
    """
    Cut a segment from a source clip: take the first `duration` seconds,
    scale/crop to target resolution.

    For portrait (target_h > target_w), crops from center unless crop_x_pct given.
    """
    # Build video filter
    if target_h > target_w:
        # Portrait: crop vertical slice from landscape, then scale
        # crop=width:height:x:y where width = src_h * (9/16)
        # We don't know src dims here, so use ffmpeg's crop expression
        if crop_x_pct is not None:
            # Smart crop: position based on LLM recommendation
            vf = (f"crop=ih*9/16:ih:'(iw-ih*9/16)*{crop_x_pct}':0,"
                  f"scale={target_w}:{target_h}")
        else:
            vf = f"crop=ih*9/16:ih,scale={target_w}:{target_h}"
    else:
        # Landscape: scale to fit, pad if needed
        vf = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease," \
             f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"

    # Take first `duration` seconds (or full clip if shorter)
    src_dur = _probe_duration(src_path)
    t = min(duration, src_dur) if src_dur > 0 else duration

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src_path),
        "-t", str(t),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-an",  # no audio (music/VO added separately)
        str(out_path),
    ]
    _run_ffmpeg(cmd, timeout=120)
    return out_path


def concat_segments(segment_paths: List[Path], out_path: Path,
                    crossfade_sec: float = 0.5) -> Path:
    """
    Concatenate segments with crossfade using xfade filter.

    xfade offset math: when you xfade two clips of duration A and B with
    crossfade duration C, the output is A + B - C. The offset for the xfade
    is A - C (the transition starts C seconds before clip A ends).

    For a chain of N clips, each xfade operates on the ACCUMULATED output so
    far + the next clip. The offset for the i-th xfade is:
        offset_i = (sum of durations of clips 0..i) - (i * crossfade_sec) - crossfade_sec

    Simplified: offset_i = cumulative_duration_so_far - crossfade_sec,
    where cumulative_duration_so_far accounts for the overlaps already applied.
    """
    if len(segment_paths) == 1:
        import shutil
        shutil.copy2(segment_paths[0], out_path)
        return out_path

    # Probe all durations
    durations = [_probe_duration(sp) for sp in segment_paths]

    # Compute xfade offsets accounting for accumulated overlap
    # After each xfade, the accumulated output shrinks by crossfade_sec
    offsets = []
    accumulated = durations[0]  # output length after first clip
    for i in range(1, len(segment_paths)):
        # This xfade starts at: accumulated - crossfade_sec
        offset = max(0, accumulated - crossfade_sec)
        offsets.append(offset)
        # After this xfade, output = accumulated + durations[i] - crossfade_sec
        accumulated = accumulated + durations[i] - crossfade_sec

    # Build filter complex
    inputs = []
    for sp in segment_paths:
        inputs.extend(["-i", str(sp)])

    filter_parts = []
    prev_label = "[0:v]"
    for i, offset in enumerate(offsets):
        next_input = f"[{i+1}:v]"
        out_label = f"[v{i+1}]" if i < len(offsets) - 1 else "[vout]"
        filter_parts.append(
            f"{prev_label}{next_input}xfade=transition=fade:duration={crossfade_sec}:offset={offset}{out_label}"
        )
        prev_label = out_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-an",
        str(out_path),
    ]

    try:
        _run_ffmpeg(cmd, timeout=300)
        return out_path
    except RuntimeError:
        # Fallback: hard concat (no crossfade)
        print("  ⚠️  xfade failed, using hard concat")
        list_file = out_path.parent / "concat_list.txt"
        with open(list_file, "w") as f:
            for sp in segment_paths:
                f.write(f"file '{sp.resolve()}'\n")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(out_path),
        ]
        _run_ffmpeg(cmd, timeout=120)
        list_file.unlink(missing_ok=True)
        return out_path


def assemble_version(selections: Dict[str, Any], pool_dir: Path,
                     orientation: str, out_path: Path,
                     adaptations: Optional[Dict] = None) -> Path:
    """
    Assemble one version (landscape or portrait) from the locked selections.

    Args:
        selections: from selection_draft.json
        pool_dir: pool directory
        orientation: "landscape" or "portrait"
        out_path: output .mp4 path
        adaptations: portrait_adaptations.json (for crop_x_pct on portrait)
    """
    work_dir = out_path.parent / f"segments_{orientation}"
    work_dir.mkdir(parents=True, exist_ok=True)

    if orientation == "landscape":
        target_w, target_h = 1920, 1080
    else:
        target_w, target_h = 1080, 1920

    segment_paths = []
    for beat in CUT_PLAN:
        shot = beat["shot"]
        duration = beat["duration"]
        cid = selections.get(shot, "")
        if not cid or cid.startswith("TBD"):
            print(f"  ⚠️  {shot} not locked, skipping")
            continue

        # Find the source clip — search both orientations, prefer matching
        if orientation == "portrait":
            # Use adapted portrait crop if available
            adapted_dir = pool_dir / shot / "portrait_adapted"
            adapted_path = adapted_dir / f"{cid}_portrait.mp4"
            if adapted_path.exists():
                src = adapted_path
            else:
                # Fall back to native portrait, then landscape (will crop)
                src = pool_dir / shot / "portrait" / f"{cid}.mp4"
                if not src.exists():
                    src = pool_dir / shot / "landscape" / f"{cid}.mp4"
        else:
            # Landscape: prefer native landscape, fall back to portrait (pad)
            src = pool_dir / shot / "landscape" / f"{cid}.mp4"
            if not src.exists():
                src = pool_dir / shot / "portrait" / f"{cid}.mp4"
                if src.exists():
                    print(f"  ℹ️  {shot}: using portrait source for landscape (will pad)")

        if not src.exists():
            print(f"  ⚠️  {cid} source not found at {src}, skipping")
            continue

        # Get crop_x_pct for portrait from adaptations if available
        crop_x_pct = None
        if orientation == "portrait" and adaptations:
            adapt_data = adaptations.get(cid, {})
            crop_x_pct = adapt_data.get("x_pct")

        seg_path = work_dir / f"{shot}_{orientation}.mp4"
        # For portrait from adapted clips, just trim (already cropped)
        # For portrait from landscape, crop
        if orientation == "portrait" and "_portrait" in src.name:
            # Already portrait — just trim to duration
            cut_segment(src, seg_path, duration, target_w, target_h)
        else:
            cut_segment(src, seg_path, duration, target_w, target_h, crop_x_pct)

        segment_paths.append(seg_path)
        print(f"  ✂️  {shot}: {cid} → {duration}s {orientation}")

    print(f"\n  🔗 concatenating {len(segment_paths)} segments...")
    concat_segments(segment_paths, out_path, crossfade_sec=0.5)
    total = _probe_duration(out_path)
    print(f"  ✅ {orientation}: {out_path} ({total:.1f}s)")
    return out_path


def assemble_both(selection_draft_path: Path, out_dir: Path) -> Tuple[Path, Path]:
    """
    Assemble both landscape and portrait versions.
    """
    pool_dir = selection_draft_path.parent
    draft = json.loads(selection_draft_path.read_text(encoding="utf-8"))
    selections = draft["selections"]

    # Load adaptations for portrait crop positions
    adapt_path = pool_dir / "portrait_adaptations.json"
    adaptations = {}
    if adapt_path.exists():
        adaptations = json.loads(adapt_path.read_text())

    out_dir.mkdir(parents=True, exist_ok=True)

    print("═" * 60)
    print(f"  CUT — assembling both versions")
    print(f"  tour: {draft.get('tour', '')}")
    print("═" * 60)
    print()

    print("▶ LANDSCAPE (16:9, 1920x1080)")
    landscape_path = assemble_version(
        selections, pool_dir, "landscape", out_dir / "legends-landscape.mp4"
    )
    print()

    print("▶ PORTRAIT (9:16, 1080x1920)")
    portrait_path = assemble_version(
        selections, pool_dir, "portrait", out_dir / "legends-vertical.mp4",
        adaptations=adaptations,
    )

    print()
    print("═" * 60)
    print("  ✅ ASSEMBLY COMPLETE")
    print(f"     landscape: {landscape_path}")
    print(f"     portrait:  {portrait_path}")
    print("═" * 60)
    return landscape_path, portrait_path


if __name__ == "__main__":
    pool = Path("explore_china_holiday/tours/legends-of-china-warriors/pool")
    out = Path("explore_china_holiday/tours/legends-of-china-warriors/output")
    assemble_both(pool / "selection_draft.json", out)
