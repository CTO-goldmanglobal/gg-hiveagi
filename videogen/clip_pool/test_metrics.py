"""
Tests for videogen/clip_pool/metrics.py — the visual-signal triage layer.

Layered like the module itself:
- flag_issues() / compute_shot_stats() / _empty_metrics(): pure dict/list in →
  out. Tested directly with crafted inputs (deterministic contract tests).
- measure_clip(): the real cv2 pipeline. Tested with tiny synthetic videos
  written via cv2.VideoWriter, asserting *relationships* (a static clip has
  less motion than a moving one) rather than exact floats, so the tests don't
  depend on codec/compression quirks.

Metrics does not decide — it measures for triage. These tests hold that
contract: flags are hints, empty metrics never crash the judge.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from videogen.clip_pool.metrics import (  # noqa: E402
    _empty_metrics,
    compute_shot_stats,
    flag_issues,
    measure_clip,
)

# --- helpers: synthesize tiny mp4s so measure_clip has real input ----------


def _write_clip(path: Path, frames: list, size=(32, 32), fps=10) -> None:
    """Write a list of HxWx3 uint8 arrays as an mp4."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, size)
    assert writer.isOpened(), f"could not open VideoWriter for {path}"
    for frame in frames:
        writer.write(frame)
    writer.release()


def _static_clip(path: Path, n=15, value=128) -> None:
    """Identical frames → near-zero motion (a 'still / personal-video' case)."""
    frame = np.full((32, 32, 3), value, dtype=np.uint8)
    _write_clip(path, [frame] * n)


def _moving_clip(path: Path, n=15, seed=0, fps=10) -> None:
    """Independent random-noise frames → large frame-to-frame diff = motion."""
    rng = np.random.default_rng(seed)
    frames = [rng.integers(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(n)]
    _write_clip(path, frames, fps=fps)


METRIC_KEYS = {
    "brightness",
    "brightness_std",
    "contrast",
    "motion_score",
    "shake_score",
    "duration_sec",
    "frames_sampled",
}


class TestEmptyMetrics:
    def test_shape(self):
        m = _empty_metrics()
        assert set(m.keys()) == METRIC_KEYS
        # measurement fields are None (unknown), counters are zero
        for k in ("brightness", "brightness_std", "contrast", "motion_score", "shake_score"):
            assert m[k] is None
        assert m["duration_sec"] == 0.0
        assert m["frames_sampled"] == 0


class TestMeasureClip:
    def test_nonexistent_path_returns_empty(self, tmp_path):
        # No file → cap can't open → _empty_metrics(). Must not raise.
        m = measure_clip(tmp_path / "does_not_exist.mp4")
        assert m == _empty_metrics()

    def test_returns_all_expected_keys(self, tmp_path):
        clip = tmp_path / "moving.mp4"
        _moving_clip(clip)
        m = measure_clip(clip)
        assert set(m.keys()) == METRIC_KEYS

    def test_static_clip_is_low_motion(self, tmp_path):
        clip = tmp_path / "static.mp4"
        _static_clip(clip)
        m = measure_clip(clip)
        # identical frames → frame-to-frame diff is near zero (modulo codec
        # noise). Must fall under the 1.5 "likely static" flag threshold.
        assert m["motion_score"] is not None
        assert m["motion_score"] < 1.5
        # and it should surface as a triage flag
        assert "low-motion (likely static)" in flag_issues(m)

    def test_moving_clip_beats_static(self, tmp_path):
        # Relationship assertion: robust to codec/compression variance.
        static_clip = tmp_path / "static.mp4"
        moving_clip = tmp_path / "moving.mp4"
        _static_clip(static_clip)
        _moving_clip(moving_clip)
        m_static = measure_clip(static_clip)
        m_moving = measure_clip(moving_clip)
        assert m_moving["motion_score"] > m_static["motion_score"]
        # a genuinely moving clip is not flagged as low-motion
        assert "low-motion (likely static)" not in flag_issues(m_moving)

    def test_max_frames_caps_sampling(self, tmp_path):
        clip = tmp_path / "moving.mp4"
        _moving_clip(clip, n=15)
        m = measure_clip(clip, max_frames=5)
        assert m["frames_sampled"] <= 5

    def test_duration_nonnegative_and_frames_sampled_positive(self, tmp_path):
        clip = tmp_path / "moving.mp4"
        _moving_clip(clip, n=12, fps=10)
        m = measure_clip(clip)
        assert m["duration_sec"] >= 0.0
        assert m["frames_sampled"] > 0

    def test_single_frame_clip_no_crash(self, tmp_path):
        # One readable frame → motions/shakes empty → scores fall back to 0.0,
        # brightness_std falls back to 0.0 (len==1 branch).
        clip = tmp_path / "one.mp4"
        _write_clip(clip, [np.full((32, 32, 3), 100, dtype=np.uint8)])
        m = measure_clip(clip)
        assert m["motion_score"] in (0.0, None) or m["motion_score"] == 0.0
        assert m["shake_score"] == 0.0 or m["shake_score"] is None


class TestFlagIssues:
    def test_low_motion_flag(self):
        flags = flag_issues({"motion_score": 0.8, "shake_score": 0.1, "brightness": 120.0})
        assert "low-motion (likely static)" in flags

    def test_no_low_motion_flag_above_threshold(self):
        flags = flag_issues({"motion_score": 2.0, "shake_score": 0.1, "brightness": 120.0})
        assert "low-motion (likely static)" not in flags

    def test_shake_flag(self):
        # high shake relative to low motion → jittery static scene
        flags = flag_issues({"motion_score": 1.0, "shake_score": 0.8, "brightness": 120.0})
        assert "possible camera shake" in flags

    def test_no_shake_when_motion_is_high(self):
        # lots of real motion → high shake diff is expected, not a defect
        flags = flag_issues({"motion_score": 2.5, "shake_score": 0.8, "brightness": 120.0})
        assert "possible camera shake" not in flags

    def test_brightness_outlier_within_shot(self):
        metrics = {"motion_score": 3.0, "shake_score": 0.2, "brightness": 200.0}
        # shot mean 120, std 10 → z = |200-120|/10 = 8.0 ≫ 1.5
        shot = {"brightness_mean": 120.0, "brightness_std": 10.0}
        flags = flag_issues(metrics, shot_stats=shot)
        assert any(f.startswith("brightness outlier") for f in flags)

    def test_no_brightness_outlier_when_in_range(self):
        metrics = {"motion_score": 3.0, "shake_score": 0.2, "brightness": 122.0}
        shot = {"brightness_mean": 120.0, "brightness_std": 10.0}
        flags = flag_issues(metrics, shot_stats=shot)
        assert not any(f.startswith("brightness outlier") for f in flags)

    def test_clean_metrics_yield_no_flags(self):
        metrics = {"motion_score": 3.0, "shake_score": 0.2, "brightness": 120.0}
        shot = {"brightness_mean": 120.0, "brightness_std": 10.0}
        assert flag_issues(metrics, shot_stats=shot) == []

    def test_empty_metrics_do_not_crash(self):
        # _empty_metrics() values are None — flag_issues must tolerate them
        # and return [] (nothing to flag).
        assert flag_issues(_empty_metrics()) == []

    def test_outlier_requires_nonzero_shot_std(self):
        # std 0 → division guard, no flag (avoids divide-by-zero).
        metrics = {"motion_score": 3.0, "shake_score": 0.2, "brightness": 200.0}
        shot = {"brightness_mean": 120.0, "brightness_std": 0.0}
        flags = flag_issues(metrics, shot_stats=shot)
        assert not any(f.startswith("brightness outlier") for f in flags)


class TestComputeShotStats:
    def test_empty_list_returns_zeros(self):
        assert compute_shot_stats([]) == {"brightness_mean": 0.0, "brightness_std": 0.0}

    def test_none_brightness_values_filtered(self):
        clips = [
            {"brightness": None},
            {"brightness": 100.0},
            {"brightness": None},
            {"brightness": 200.0},
        ]
        stats = compute_shot_stats(clips)
        assert stats["brightness_mean"] == pytest.approx(150.0)
        assert stats["brightness_std"] >= 0.0

    def test_all_none_returns_zeros(self):
        clips = [{"brightness": None}, {"brightness": None}]
        assert compute_shot_stats(clips) == {"brightness_mean": 0.0, "brightness_std": 0.0}

    def test_normal_stats(self):
        clips = [{"brightness": 100.0}, {"brightness": 120.0}, {"brightness": 140.0}]
        stats = compute_shot_stats(clips)
        assert stats["brightness_mean"] == pytest.approx(120.0)
        # std, not variance: np.std([100,120,140]) == 16.3299...
        assert stats["brightness_std"] == pytest.approx(16.329931, rel=1e-3)
