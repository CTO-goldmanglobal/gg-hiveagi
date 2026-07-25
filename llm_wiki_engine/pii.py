"""
PII Stripping — 文字脫敏 + 圖片脫敏（stub）

喺 Raw Data 送 LLM API 之前必須過呢度（spec §6 鐵律）。
"""

import re
from typing import Any, Dict


def strip_pii(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    從 Raw Data 移除 PII。

    - 文字：email / 電話 / 稱謂+姓名 regex
    - 圖片：暫時只 warning（MediaPipe/HyperLPR 接入係 P1.5）
    """
    result = raw.copy()

    # 1. 文字 PII
    if "human_description" in result and isinstance(result["human_description"], str):
        result["human_description"] = _strip_text_pii(result["human_description"])
    if "human_label" in result and isinstance(result["human_label"], str):
        result["human_label"] = _strip_text_pii(result["human_label"])

    # 2. 圖片 PII（stub）
    if any(k in result for k in ("image_path", "image_data", "video_path")):
        print(
            "⚠️  Image/video PII stripping is not implemented yet (see tools/pii_anonymizer/)."
            "The images in this record are sent to the LLM un-anonymized — please complete P1.5 in production."
        )

    return result


def _strip_text_pii(text: str) -> str:
    """Strip email / 電話 / 稱謂+姓名。"""
    # Email
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        text,
    )
    # 澳洲電話（02/03/04/07/08 + 04xx mobile；含 +61 國際格式）
    text = re.sub(
        r"(?:\+61\s?|0)[2-478](?:[ \-]?[0-9]){8}",
        "[PHONE]",
        text,
    )
    # 稱謂 + 姓名（Mr/Ms/Mrs/Dr/Prof + 大寫開頭英文名）
    text = re.sub(
        r"\b(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b",
        "[NAME]",
        text,
    )
    return text
