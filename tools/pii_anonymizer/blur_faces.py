#!/usr/bin/env python3
"""
PII Anonymizer — Face Blur (STUB)

喺圖片 / 影片偵測人臉並模糊化，確保送 LLM Wiki Engine 前無人臉 PII。

狀態：STUB（介面已定義，實作待 P1）

計劃用嘅技術（之後裝）：
- MediaPipe Face Detection（輕量、跨平台）
- 或 OpenCV DNN face detector（cv2.dnn）

依賴（之後先裝）：
    pip install mediapipe opencv-python
"""

from pathlib import Path


class FaceBlur:
    """人臉模糊化器。P0 係 stub，detect/blur 拋出 NotImplementedError。"""

    def __init__(self, blur_strength: int = 51):
        """
        Args:
            blur_strength: 高斯模糊 kernel 大小（必須係奇數）
        """
        if blur_strength % 2 == 0:
            raise ValueError("blur_strength 必須係奇數")
        self.blur_strength = blur_strength
        # self._detector = None  # P1 先 load MediaPipe

    def detect_faces(self, image):
        """偵測圖片中嘅人臉，回傳 bounding box list。

        Args:
            image: numpy ndarray（BGR）或圖片路徑

        Returns:
            list[dict]: 每個 dict 含 {x, y, w, h, confidence}

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "FaceBlur.detect_faces() 尚未實作（P1 會用 MediaPipe）"
        )

    def blur_faces(self, image, inplace: bool = False):
        """偵測並模糊化圖片中所有人臉。

        Args:
            image: numpy ndarray（BGR）或圖片路徑
            inplace: 若 True 就地修改，False 就回傳副本

        Returns:
            處理後嘅 ndarray

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "FaceBlur.blur_faces() 尚未實作（P1 會用 MediaPipe + OpenCV）"
        )

    def process_file(self, input_path: str, output_path: str = None) -> str:
        """便利方法：讀檔 → 模糊 → 寫檔。

        Args:
            input_path: 輸入圖片路徑
            output_path: 輸出路徑（預設 input_path 加 _blurred 後綴）

        Returns:
            輸出檔案路徑

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "FaceBlur.process_file() 尚未實作（P1 會用 OpenCV imwrite）"
        )


# ===== P0 demo：純粹證明 import OK =====
if __name__ == "__main__":
    fb = FaceBlur()
    print("✅ FaceBlur stub 載入成功（P1 會接入 MediaPipe + OpenCV）")
    print(f"   blur_strength = {fb.blur_strength}")
