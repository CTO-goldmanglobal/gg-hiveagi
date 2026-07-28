"""
Clip metrics — quantifies the visual signals behind human editorial judgment.

Derived from the founder's review of circle #1 (Legends of China Warriors),
which articulated four rules. Three of them are directly measurable:

  1. "Video needs moving content"           → motion_score (mean frame diff)
  2. "Reject still / personal-video feel"   → motion_score + shake_score
  3. "Find less-contrast clips to link"     → brightness + contrast (per shot)
  4. "Minus method" (subtract the bad)      → this module FLAGS candidates; the
                                               human still decides.

This module does NOT decide. It measures, so the judge tool can surface the
candidates most likely to waste a human's time (near-static, jarringly bright,
shaky) and highlight continuity problems within a shot (brightness spread).

The human verdict + reason remains the seed. Metrics are a triage aid.
"""

from pathlib import Path
from typing import Dict, Any, Optional


def measure_clip(path: Path, max_frames: int = 60) -> Dict[str, float]:
    """
    Measure brightness, contrast, motion, and shake on a video clip.

    Args:
        path: path to the .mp4
        max_frames: sample at most this many frames (evenly across the clip)

    Returns:
        {
            "brightness": float,      # mean luma 0-255 (0=black, 255=white)
            "brightness_std": float,  # frame-to-frame brightness variation
            "contrast": float,        # mean intra-frame pixel std (0-255)
            "motion_score": float,    # mean absdiff between consecutive frames
            "shake_score": float,     # high-frequency frame-to-frame jitter
                                      #   (motion of a static scene = shake)
            "duration_sec": float,
            "frames_sampled": int,
        }
    """
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return _empty_metrics()

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = total_frames / fps if fps > 0 else 0.0

    # Sample evenly across the clip
    n = min(max_frames, max(total_frames, 1))
    step = max(1, total_frames // n) if total_frames > 0 else 1

    brightnesses = []
    contrasts = []
    motions = []
    shakes = []
    prev_gray = None
    prev_gray_blur = None
    sampled = 0

    for i in range(0, max(total_frames, 1), step):
        if sampled >= max_frames:
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightnesses.append(float(gray.mean()))
        contrasts.append(float(gray.std()))

        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            motions.append(float(diff.mean()))

            # Shake estimate: blur both frames, measure residual motion.
            # A static scene (no real motion) still shows small diffs from
            # sensor noise / compression → that residual ≈ shake. If blurred
            # frames differ a lot relative to raw frames, the camera is
            # jittering on a static subject.
            gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
            diff_blur = cv2.absdiff(gray_blur, prev_gray_blur)
            shakes.append(float(diff_blur.mean()))

        prev_gray = gray
        prev_gray_blur = cv2.GaussianBlur(gray, (5, 5), 0) if prev_gray is not None else gray
        sampled += 1

    cap.release()

    if sampled == 0:
        return _empty_metrics()

    import numpy as np
    return {
        "brightness": float(np.mean(brightnesses)),
        "brightness_std": float(np.std(brightnesses)) if len(brightnesses) > 1 else 0.0,
        "contrast": float(np.mean(contrasts)),
        "motion_score": float(np.mean(motions)) if motions else 0.0,
        "shake_score": float(np.mean(shakes)) if shakes else 0.0,
        "duration_sec": round(duration, 1),
        "frames_sampled": sampled,
    }


def _empty_metrics() -> Dict[str, Any]:
    return {
        "brightness": None, "brightness_std": None, "contrast": None,
        "motion_score": None, "shake_score": None,
        "duration_sec": 0.0, "frames_sampled": 0,
    }


def flag_issues(metrics: Dict[str, Any], shot_stats: Optional[Dict[str, float]] = None) -> list:
    """
    Flag likely problems based on metrics. Returns a list of flag strings.

    These are TRIAGE hints, not verdicts. The human decides.
    Thresholds are initial estimates from a 7-clip calibration (circle #1
    founder review) — they will tighten as more judgments accumulate.

    Args:
        metrics: output of measure_clip()
        shot_stats: optional {"brightness_mean": x, "brightness_std": y}
                    for the shot this clip belongs to, to detect outliers.
    """
    flags = []
    m = metrics.get("motion_score")
    s = metrics.get("shake_score")
    b = metrics.get("brightness")

    if m is not None and m < 1.5:
        # From calibration: rejected "still" clips scored 0.82–1.51;
        # accepted clips scored 1.03–4.97. <1.5 is a reasonable "likely
        # static" flag, though pexels_2881972 (accept) was 1.03 — so this
        # is a flag, not a reject.
        flags.append("low-motion (likely static)")

    if s is not None and m is not None and s > 0.6 and m < 2.0:
        # High shake relative to low motion = jittery static scene
        flags.append("possible camera shake")

    if shot_stats and b is not None:
        sm = shot_stats.get("brightness_mean")
        ss = shot_stats.get("brightness_std", 0)
        if sm is not None and ss is not None and ss > 0:
            # More than 1.5 std devs from the shot mean = brightness outlier
            z = abs(b - sm) / ss
            if z > 1.5:
                flags.append(f"brightness outlier (z={z:.1f}, may cut jarringly)")

    return flags


def compute_shot_stats(clip_metrics: list) -> Dict[str, float]:
    """
    Compute aggregate brightness stats for a shot, for outlier detection.

    Args:
        clip_metrics: list of measure_clip() outputs for one shot.

    Returns:
        {"brightness_mean": float, "brightness_std": float}
    """
    import numpy as np
    brights = [c["brightness"] for c in clip_metrics if c.get("brightness") is not None]
    if not brights:
        return {"brightness_mean": 0.0, "brightness_std": 0.0}
    return {
        "brightness_mean": float(np.mean(brights)),
        "brightness_std": float(np.std(brights)),
    }
