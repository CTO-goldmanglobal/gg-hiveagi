#!/usr/bin/env python3
"""
PII Anonymizer — Face Blur

用 MediaPipe Tasks API（FaceDetector）偵測人臉，再逐個 bbox 做 Gaussian blur。
喺圖片送 LLM vision API 之前必須先過呢度（spec §6 鐵律）。

⚠️  mediapipe API 變遷：
    舊版（<0.10）用 mp.solutions.face_detection。
    新版（≥0.10.14，我哋用 0.10.35）改用 mp.tasks.python.vision.FaceDetector，
    並需要一個 .task model 檔案（會自動由 Google storage 下載到 ~/.hiveagi_models）。

CLI:
    python blur_faces.py <input_image> [--out <output>] [--strength 51]
    python blur_faces.py <input_image> --report-only
"""

import argparse
import sys
import urllib.request
from pathlib import Path
from typing import Tuple, Optional


MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
MODEL_CACHE = Path.home() / ".hiveagi_models" / "blaze_face_short_range.tflite"


def _ensure_model() -> Path:
    """下載 face detection model（首次用時，cache 喺 ~/.hiveagi_models）。"""
    if MODEL_CACHE.exists():
        return MODEL_CACHE
    MODEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    print(f"⬇️  Downloading face detection model → {MODEL_CACHE} (first run, one-time)", file=sys.stderr)
    urllib.request.urlretrieve(MODEL_URL, MODEL_CACHE)
    return MODEL_CACHE


class FaceBlur:
    """人臉偵測（MediaPipe Tasks）+ Gaussian blur。"""

    def __init__(self, blur_strength: int = 51,
                 min_confidence: float = 0.5):
        if blur_strength % 2 == 0:
            raise ValueError("blur_strength must be odd")
        if not 0 <= min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        self.blur_strength = blur_strength
        self.min_confidence = min_confidence

    def detect_faces(self, image_path: str) -> list:
        """偵測人臉，回傳 bbox list [{x, y, w, h, confidence}]。"""
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision

        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        h, w = image.shape[:2]

        # MediaPipe Tasks 要 mp.Image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
        )

        model_path = _ensure_model()
        options = mp_vision.FaceDetectorOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
            min_detection_confidence=self.min_confidence,
        )

        boxes = []
        with mp_vision.FaceDetector.create_from_options(options) as detector:
            result = detector.detect(mp_image)
            for det in result.detections:
                bbox = det.bounding_box
                boxes.append({
                    "x": max(0, bbox.origin_x),
                    "y": max(0, bbox.origin_y),
                    "w": bbox.width,
                    "h": bbox.height,
                    "confidence": det.categories[0].score if det.categories else 0.0,
                })
        return boxes

    def process_file(self, input_path: str,
                     output_path: Optional[str] = None,
                     report_only: bool = False) -> Tuple[str, int]:
        """讀檔 → (模糊) → 寫檔。"""
        import cv2
        boxes = self.detect_faces(input_path)

        if report_only:
            return "", len(boxes)

        in_path = Path(input_path)
        if output_path is None:
            output_path = str(in_path.parent / f"{in_path.stem}_faced{in_path.suffix}")

        image = cv2.imread(str(input_path))
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {input_path}")

        for box in boxes:
            x, y, w, h = box["x"], box["y"], box["w"], box["h"]
            pad = max(w, h) // 4
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(image.shape[1], x + w + pad)
            y1 = min(image.shape[0], y + h + pad)
            roi = image[y0:y1, x0:x1]
            if roi.size > 0:
                blurred = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)
                image[y0:y1, x0:x1] = blurred

        cv2.imwrite(output_path, image)
        return output_path, len(boxes)


def main():
    parser = argparse.ArgumentParser(description="Face blur (MediaPipe Tasks)")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("--out", help="Output path")
    parser.add_argument("--strength", type=int, default=51,
                        help="Gaussian blur kernel (odd, default 51)")
    parser.add_argument("--report-only", action="store_true",
                        help="Detect only, do not write file")
    args = parser.parse_args()

    fb = FaceBlur(blur_strength=args.strength)
    out, count = fb.process_file(args.input, args.out, report_only=args.report_only)
    if args.report_only:
        print(f"👁️  Detected {count} face(s) (report only)")
    else:
        print(f"✅ Blurred {count} face(s) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
