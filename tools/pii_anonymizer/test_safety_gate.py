#!/usr/bin/env python3
"""
PII safety gate test — verifies the auto-vision path's blur enforcement.

This is the one thing CONTRIBUTING.md promises hardest ("code-enforced,
no bypass"). Without this test, a refactor that silently breaks blurring
would ship green. Run in CI to assert:

  1. anonymize_image() successfully detects + blurs a synthetic face
     (proves the real MediaPipe + OpenCV pipeline is wired correctly)
  2. SafetyError raises when the underlying deps are absent
     (proves the gate refuses, not silently skips)

No external image fixtures — the synthetic face is generated in-process
via OpenCV geometric primitives. MediaPipe's blaze_face_short_range
detects it at ~0.54 confidence (above the 0.5 threshold), confirmed
stable across runs.

Usage:
    python tools/pii_anonymizer/test_safety_gate.py
    # exits 0 if both assertions hold, 1 otherwise
"""

import sys
import tempfile
from pathlib import Path


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


def test_blur_detects_and_blurs_face() -> None:
    """The safety gate must detect a face and report it as blurred."""
    sys.path.insert(0, str(Path(__file__).parent))
    from anonymize import anonymize_image

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "synthetic_face.png"
        out = Path(tmp) / "blurred.png"
        _generate_synthetic_face(src)

        result_path, summary = anonymize_image(str(src), str(out))

        assert summary["faces_blurred"] >= 1, (
            f"SAFETY GATE BROKEN: anonymize_image() reported "
            f"faces_blurred={summary['faces_blurred']}, expected >= 1. "
            f"The PII blur pipeline is not detecting faces — a refactor "
            f"has silently disabled the safety gate that CONTRIBUTING.md "
            f"promises is 'code-enforced, no bypass'."
        )
        assert Path(result_path).exists(), "Blurred output file was not written"
        print(
            f"✅ Face detection + blur works: "
            f"{summary['faces_blurred']} face(s), {summary['plates_blurred']} plate(s) blurred"
        )


def test_safety_gate_raises_when_deps_absent() -> None:
    """
    The safety gate must raise SafetyError (not silently skip) when blur
    dependencies are missing. We simulate this by hiding mediapipe from
    the import system.
    """
    import importlib

    # Pre-flight: if mediapipe isn't installed, the test is trivially true
    # but meaningless. Skip with a clear message rather than pass silently.
    try:
        import mediapipe  # noqa: F401
    except ImportError:
        print("⚠️  mediapipe not installed — skipping dep-absence test (trivially passes)")
        return

    sys.path.insert(0, str(Path(__file__).parent))
    from anonymize import SafetyError, anonymize_image

    # Hide mediapipe by poisoning sys.modules so `import mediapipe` fails
    real_mediapipe = sys.modules.pop("mediapipe", None)
    # Also poison the blur_faces module so it re-imports with mediapipe hidden
    sys.modules.pop("blur_faces", None)

    class _ImportBlocker:
        """Meta-path finder that rejects 'mediapipe' imports."""
        def find_module(self, name, path=None):  # noqa: D401
            if name == "mediapipe" or name.startswith("mediapipe."):
                return self
        def load_module(self, name):  # noqa: D401
            raise ImportError(f"Import blocked for test: {name}")

    blocker = _ImportBlocker()
    sys.meta_path.insert(0, blocker)
    sys.modules["mediapipe"] = None  # belt and suspenders

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
            except SafetyError as e:
                print(f"✅ Safety gate refuses when deps absent: SafetyError raised")
                return
    finally:
        # Restore
        sys.meta_path.remove(blocker)
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
