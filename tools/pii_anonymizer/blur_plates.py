#!/usr/bin/env python3
"""
PII Anonymizer — License Plate Blur (STUB)

偵測並模糊化車牌，確保送 LLM Wiki Engine 前無車牌 PII。

狀態：STUB（介面已定義，實作待 P1）

計劃用嘅技術（之後裝）：
- OpenALPR / HyperLPR（車牌專用）
- 或 YOLOv8 訓練嘅 plate detector

依賴（之後先裝）：
    pip install opencv-python
    # 車牌 detector 二選一
    pip install hyperlpr3
"""

from pathlib import Path


class PlateBlur:
    """車牌模糊化器。P0 係 stub。"""

    def __init__(self, blur_strength: int = 51):
        if blur_strength % 2 == 0:
            raise ValueError("blur_strength 必須係奇數")
        self.blur_strength = blur_strength

    def detect_plates(self, image):
        """偵測圖片中嘅車牌，回傳 bounding box list。

        Args:
            image: numpy ndarray（BGR）或圖片路徑

        Returns:
            list[dict]: 每個 dict 含 {x, y, w, h, text, confidence}
                        text 係 OCR 出嘅車牌字串（仅 debugging 用，唔會送 LLM）

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "PlateBlur.detect_plates() 尚未實作（P1 會用 HyperLPR / YOLO）"
        )

    def blur_plates(self, image, inplace: bool = False):
        """偵測並模糊化圖片中所有車牌。

        Args:
            image: numpy ndarray（BGR）或圖片路徑
            inplace: 若 True 就地修改

        Returns:
            處理後嘅 ndarray

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "PlateBlur.blur_plates() 尚未實作（P1 會用 OpenCV）"
        )

    def process_file(self, input_path: str, output_path: str = None) -> str:
        """便利方法：讀檔 → 模糊 → 寫檔。

        Args:
            input_path: 輸入圖片路徑
            output_path: 輸出路徑（預設加 _blurred 後綴）

        Returns:
            輸出檔案路徑

        Raises:
            NotImplementedError: P0 stub
        """
        raise NotImplementedError(
            "PlateBlur.process_file() 尚未實作（P1 會用 OpenCV imwrite）"
        )


# ===== P0 demo =====
if __name__ == "__main__":
    pb = PlateBlur()
    print("✅ PlateBlur stub 載入成功（P1 會接入 HyperLPR / YOLO + OpenCV）")
    print(f"   blur_strength = {pb.blur_strength}")
