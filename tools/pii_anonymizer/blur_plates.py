#!/usr/bin/env python3
"""
PII Anonymizer — License Plate Blur

偵測並模糊化車牌。

偵測策略：edge-based（形態學 + contour）—— 唔依賴 HAAR cascade 檔案
（opencv 5 已唔再 bundle 佢）。用 Sobel edge + 形態學閉運算搵出
高邊緣密度嘅長方形區域，再用長寬比過濾。

⚠️  準確度說明：
    呢個通用偵測器對 AU 車牌嘅 recall 中等（可能漏檢）。
    auto-vision pipeline 之後人手 review 「低置信度」frame 係必要步驟。
    要更準確可以後期接 HyperLPR / YOLOv8 訓練嘅 AU plate detector。

CLI:
    python blur_plates.py <input_image> [--out <output>] [--strength 71]

程式化:
    from blur_plates import PlateBlur
    pb = PlateBlur()
    out, count = pb.process_file("frame.jpg", "frame_plated.jpg")
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple, Optional


class PlateBlur:
    """車牌偵測（edge-based）+ Gaussian blur。"""

    # 車牌長寬比合理範圍（AU 標準 ≈ 3:1 到 5:1）
    PLATE_ASPECT_MIN = 2.0
    PLATE_ASPECT_MAX = 6.0

    def __init__(self, blur_strength: int = 71,
                 min_area: int = 800,
                 fill_ratio_min: float = 0.35):
        """
        Args:
            blur_strength: Gaussian kernel（奇數）
            min_area: 候選區最細面積（像素）
            fill_ratio_min: 候選區內 edge 密度下限（用嚟過濾平滑背景）
        """
        if blur_strength % 2 == 0:
            raise ValueError("blur_strength must be odd")
        self.blur_strength = blur_strength
        self.min_area = min_area
        self.fill_ratio_min = fill_ratio_min

    def detect_plates(self, image_path: str) -> list:
        """
        Edge-based 車牌偵測。

        Pipeline：
          gray → bilateral filter（保邊降噪）→ Sobel x → threshold →
          形態學閉運算（串連字元成塊）→ findContours →
          長寬比 + 面積 + edge fill ratio 過濾
        """
        import cv2
        import numpy as np

        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Cannot read image: {image_path}")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 保邊降噪（車牌字元邊緤要保留）
        filtered = cv2.bilateralFilter(gray, d=11, sigmaColor=17, sigmaSpace=17)

        # Sobel x —— 車牌字元有強垂直邊緣
        sobel_x = cv2.Sobel(filtered, cv2.CV_64F, 1, 0, ksize=3)
        sobel_x = np.uint8(np.absolute(sobel_x))

        # 二值化
        _, thresh = cv2.threshold(sobel_x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 形態學閉運算：水平方向閉運算串連字元成長條
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, rect_kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area < self.min_area:
                continue
            aspect = w / max(h, 1)
            if not (self.PLATE_ASPECT_MIN <= aspect <= self.PLATE_ASPECT_MAX):
                continue
            # edge fill ratio：候選區內白像素比例（車牌字元密度高）
            roi = closed[y:y + h, x:x + w]
            fill = float(np.count_nonzero(roi)) / max(roi.size, 1)
            if fill < self.fill_ratio_min:
                continue
            boxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h),
                          "confidence": float(fill)})
        return boxes

    def process_file(self, input_path: str,
                     output_path: Optional[str] = None,
                     report_only: bool = False) -> Tuple[str, int]:
        """讀檔 → (模糊) → 寫檔。"""
        import cv2
        boxes = self.detect_plates(input_path)

        if report_only:
            return "", len(boxes)

        in_path = Path(input_path)
        if output_path is None:
            output_path = str(in_path.parent / f"{in_path.stem}_plated{in_path.suffix}")

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
    parser = argparse.ArgumentParser(description="License plate blur (OpenCV HAAR)")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("--out", help="Output path")
    parser.add_argument("--strength", type=int, default=71,
                        help="Gaussian blur kernel (odd, default 71)")
    parser.add_argument("--report-only", action="store_true",
                        help="Detect plate count only, do not write file")
    args = parser.parse_args()

    pb = PlateBlur(blur_strength=args.strength)
    out, count = pb.process_file(args.input, args.out, report_only=args.report_only)
    if args.report_only:
        print(f"🚗 Detected {count} plate(s) (report only)")
        if count == 0:
            print("   (May have missed plates. AU plates differ from training data — please review manually)")
    else:
        print(f"✅ Blurred {count} plate(s) → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
