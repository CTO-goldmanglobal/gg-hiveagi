# PII Anonymizer

喺 Raw Data（圖片 / 影片）送 LLM Wiki Engine 之前，移除人臉同車牌等 PII。
**確保只有人類視角嘅「場景知識」入 wiki，而唔係可識別個人嘅資料。**

## 狀態

🚧 **P0：STUB。** 介面已定義，實作留待 P1。

| 模組 | 狀態 | 計劃技術 |
| :--- | :--- | :--- |
| `blur_faces.py` | STUB | MediaPipe Face Detection + OpenCV Gaussian blur |
| `blur_plates.py` | STUB | HyperLPR / YOLOv8 plate detector + OpenCV blur |

## 設計原則

1. **送 LLM 前必做** — `strip_pii()` 喺 API call 之前執行（見 `specs/api-protocol-v1.md` §8）
2. **不可逆** — 模糊化係破壞性操作，原图唔保留
3. **可校驗** — 處理後會回報 detected count 俾貢獻者確認

## P1 之後會加嘅嘢

- 影片支援（逐幀處理）
- 聲音 PII（聲紋 / 姓名 / 電話）文字掃描
- 設定檔控制 blur 強度同邊啲類型要處理

## 介面預覽

```python
from blur_faces import FaceBlur
from blur_plates import PlateBlur

fb = FaceBlur(blur_strength=51)
fb.process_file("raw/frame_001.jpg", "anon/frame_001.jpg")

pb = PlateBlur(blur_strength=71)
pb.process_file("raw/frame_001.jpg", "anon/frame_001.jpg")
```

## 聯絡

cto@goldmanglobal.com.au
