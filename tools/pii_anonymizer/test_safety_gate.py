#!/usr/bin/env python3
"""
PII safety gate test — verifies the auto-vision path's blur enforcement.

This is the one thing CONTRIBUTING.md promises hardest ("code-enforced,
no bypass"). Without this test, a refactor that silently breaks blurring
would ship green. Run in CI to assert:

  1. anonymize_image() actually blurs a detected face — verified by
     comparing pixel variance in the face region before/after (a real
     assertion, not the self-reported `faces_blurred` counter).
  2. SafetyError raises when the underlying deps are absent (the gate
     refuses, not silently skips).

No external image fixtures — the synthetic face is generated in-process
via OpenCV geometric primitives. MediaPipe's blaze_face_short_range
detects it at ~0.54 confidence (above the 0.5 threshold), confirmed on
mediapipe==0.10.35 (pinned in requirements.txt because of this).

Usage:
    python tools/pii_anonymizer/test_safety_gate.py
    # exits 0 if both assertions hold, 1 otherwise
"""

import sys
import tempfile
from pathlib import Path


# Geometric centre of the synthetic face drawn by _generate_synthetic_face.
# Used to extract a region-of-interest for the pixel-variance assertion.
_FACE_CENTRE = (320, 240)
_FACE_ROI_RADIUS = 80


def _generate_synthetic_face(path: Path) -> None:
    """Draw a simple face MediaPipe can detect (oval + eyes + nose + mouth)."""
    import cv2
    import numpy as np

    img = np.full((480, 640, 3), 50, dtype=np.uint8)  # grey background
    # Skin-tone oval
    cv2.ellipse(img, (320, 240), (110, 150), 0, 0, 360, (180, 150, 120), -1)
    # Eyes
    for x in (285, 355):
        cv2.circle(img, (x, 215), 12, (40, 30, 20), -1)
    # Nose
    cv2.line(img, (320, 235), (320, 270), (130, 100, 80), 4)
    # Mouth
    cv2.ellipse(img, (320, 290), (40, 15), 0, 0, 180, (60, 40, 30), 3)
    cv2.imwrite(str(path), img)


def _face_roi_variance(image_path: Path) -> float:
    """
    Pixel-intensity variance in the central face ROI.

    Before blur: high (eyes/nose/mouth edges create contrast).
    After correct Gaussian blur: substantially lower (edges smoothed).

    Returns the standard deviation of grayscale pixel values in the ROI.
    """
    import cv2

    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Could not read image for variance check: {image_path}")
    cx, cy = _FACE_CENTRE
    r = _FACE_ROI_RADIUS
    roi = img[cy - r:cy + r, cx - r:cx + r]
    return float(roi.std())


def test_blur_detects_and_blurs_face() -> None:
    """
    The safety gate must detect a face AND actually blur it.

    Two assertions:
      (a) anonymize_image() reports faces_blurred >= 1
      (b) pixel variance in the face ROI drops substantially after blur

    Assertion (b) is the real one — (a) alone could pass if the code
    counted a face but wrote an unblurred copy (a regression that
    silently defeats the entire safety gate).
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from anonymize import anonymize_image

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "synthetic_face.png"
        out = Path(tmp) / "blurred.png"
        _generate_synthetic_face(src)

        # Variance before blur — expect high (eyes/nose/mouth edges).
        variance_before = _face_roi_variance(src)

        result_path, summary = anonymize_image(str(src), str(out))

        # Assertion (a): self-reported count (necessary, not sufficient).
        assert summary["faces_blurred"] >= 1, (
            f"SAFETY GATE BROKEN: anonymize_image() reported "
            f"faces_blurred={summary['faces_blurred']}, expected >= 1. "
            f"The PII blur pipeline is not detecting faces — a refactor "
            f"has silently disabled the safety gate that CONTRIBUTING.md "
            f"promises is 'code-enforced, no bypass'."
        )
        assert Path(result_path).exists(), "Blurred output file was not written"

        # Assertion (b): pixel-level — variance must drop after blur.
        # Gaussian smoothing reduces high-frequency content; the ROI's
        # std should fall meaningfully. Threshold: at least 40% reduction.
        variance_after = _face_roi_variance(Path(result_path))
        reduction_ratio = variance_after / variance_before if variance_before > 0 else 1.0
        assert reduction_ratio < 0.6, (
            f"SAFETY GATE BROKEN: face ROI variance did not drop after blur. "
            f"before={variance_before:.2f}, after={variance_after:.2f}, "
            f"ratio={reduction_ratio:.2f} (expected < 0.6). "
            f"The code reports a face was blurred but the pixels are "
            f"substantially unchanged — anonymize_image() may be counting "
            f"a detection without writing the blurred result."
        )

        print(
            f"✅ Face detection + blur works (verified at pixel level): "
            f"{summary['faces_blurred']} face(s) blurred, "
            f"ROI variance {variance_before:.1f} → {variance_after:.1f} "
            f"({(1 - reduction_ratio) * 100:.0f}% reduction)"
        )


def test_safety_gate_raises_when_deps_absent() -> None:
    """
    The safety gate must raise SafetyError (not silently skip) when blur
    dependencies are missing.

    Implementation note: this works by poisoning sys.modules["mediapipe"]
    to None. On Python ≥3.4 a `None` value in sys.modules forces
    `import mediapipe` to raise ImportError (this is documented CPython
    behaviour, unlike the legacy meta-path finder API). Do NOT add a
    MetaPathFinder with find_module/load_module — those were removed in
    Python 3.12 and are silently ignored on 3.13/3.14, which would make
    this test pass for the wrong reason if the sys.modules line were
    ever removed.
    """
    # Pre-flight: if mediapipe isn't installed, the test is trivially true
    # but meaningless. Skip with a clear message rather than pass silently.
    try:
        import mediapipe  # noqa: F401
    except ImportError:
        print("⚠️  mediapipe not installed — skipping dep-absence test (trivially passes)")
        return

    sys.path.insert(0, str(Path(__file__).parent))
    from anonymize import SafetyError, anonymize_image

    # Poison: a None value in sys.modules forces import to raise ImportError.
    # See https://docs.python.org/3/library/sys.html#sys.modules
    real_mediapipe = sys.modules.pop("mediapipe", None)
    sys.modules.pop("blur_faces", None)  # force re-import with mediapipe=None
    sys.modules["mediapipe"] = None

    try:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "any.png"
            src.write_bytes(b"\x89PNG fake image bytes")
            try:
                anonymize_image(str(src))
                raise AssertionError(
                    "SAFETY GATE BROKEN: anonymize_image() did NOT raise "
                    "SafetyError when mediapipe was unimportable. The gate "
                    "must refuse, not silently skip — a refactor has added "
                    "a bypass."
                )
            except SafetyError:
                print("✅ Safety gate refuses when deps absent: SafetyError raised")
                return
    finally:
        # Restore
        sys.modules.pop("mediapipe", None)
        if real_mediapipe is not None:
            sys.modules["mediapipe"] = real_mediapipe
        sys.modules.pop("blur_faces", None)


def main() -> int:
    print("━" * 60)
    print("PII Safety Gate Test")
    print("━" * 60)
    failures = 0
    for name, fn in [
        ("blur_detects_and_blurs_face", test_blur_detects_and_blurs_face),
        ("safety_gate_raises_when_deps_absent", test_safety_gate_raises_when_deps_absent),
    ]:
        print(f"\n→ {name}")
        try:
            fn()
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failures += 1
        except Exception as e:  # noqa: BLE001
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            failures += 1
    print("\n" + "━" * 60)
    if failures:
        print(f"❌ {failures} test(s) failed — safety gate is broken")
        return 1
    print("✅ All safety gate tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
