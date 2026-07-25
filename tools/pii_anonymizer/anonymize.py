#!/usr/bin/env python3
"""
anonymize.py —— 統一嘅 PII 入口（face + plate blur）

呢個係 vision pipeline 嘅 safety gate：
    任何 frame 送 LLM vision API 之前必須過 `anonymize_image()`。
如果 blur 失敗（例如 deps 缺失、圖片讀唔到），返 None ——
vision.py 會拒絕送 LLM（spec §6 鐵律，code-enforced，無 bypass）。
"""

import sys
from pathlib import Path
from typing import Optional


class SafetyError(Exception):
    """PII safety gate 失敗 —— 唔可以送 LLM。"""


def anonymize_image(input_path: str,
                    output_path: Optional[str] = None,
                    face_strength: int = 51,
                    plate_strength: int = 71) -> tuple:
    """
    對一張圖片做人臉 + 車牌模糊化。

    順序：先 face blur，再 plate blur（兩個 cascade 唔衝突）。

    Args:
        input_path: 輸入圖片
        output_path: 輸出（預設：input 加 _anon 後綴）
        face_strength: 人臉 blur kernel（奇數）
        plate_strength: 車牌 blur kernel（奇數）

    Returns:
        (output_path, summary_dict)
        summary_dict = {"faces_blurred": int, "plates_blurred": int}

    Raises:
        SafetyError: deps 缺失或圖片讀唔到 —— 唔可以送 LLM
    """
    in_path = Path(input_path)
    if not in_path.exists():
        raise SafetyError(f"圖片唔存在：{input_path}")

    if output_path is None:
        output_path = str(in_path.parent / f"{in_path.stem}_anon{in_path.suffix}")

    # 先複製原檔到 output_path（face 同 plate 分兩步，串聯喺同一檔）
    import shutil
    shutil.copy2(input_path, output_path)

    summary = {"faces_blurred": 0, "plates_blurred": 0}

    # 1. Face blur
    try:
        from blur_faces import FaceBlur
        fb = FaceBlur(blur_strength=face_strength)
        output_path, face_count = fb.process_file(output_path, output_path)
        summary["faces_blurred"] = face_count
    except ImportError as e:
        raise SafetyError(
            f"MediaPipe 未安裝 —— 唔可以做人臉 blur → 拒絕送 LLM。"
            f"裝佢：pip install -r tools/pii_anonymizer/requirements.txt （{e}）"
        ) from e
    except Exception as e:
        raise SafetyError(f"人臉 blur 失敗：{e}") from e

    # 2. Plate blur（串聯喺已 blur face 嘅檔上）
    try:
        from blur_plates import PlateBlur
        pb = PlateBlur(blur_strength=plate_strength)
        output_path, plate_count = pb.process_file(output_path, output_path)
        summary["plates_blurred"] = plate_count
    except ImportError as e:
        raise SafetyError(
            f"OpenCV 未安裝 —— 唔可以做車牌 blur → 拒絕送 LLM。"
            f"裝佢：pip install -r tools/pii_anonymizer/requirements.txt （{e}）"
        ) from e
    except Exception as e:
        # plate cascade 載唔到都算 safety fail（雖然次要）
        raise SafetyError(f"車牌 blur 失敗：{e}") from e

    return output_path, summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python anonymize.py <image> [--out <output>]")
        sys.exit(1)
    inp = sys.argv[1]
    out = None
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    try:
        result, summary = anonymize_image(inp, out)
        print(f"✅ Anonymized → {result}")
        print(f"   人臉模糊: {summary['faces_blurred']}")
        print(f"   車牌模糊: {summary['plates_blurred']}")
    except SafetyError as e:
        print(f"❌ Safety gate 失敗：{e}", file=sys.stderr)
        sys.exit(1)
