"""
Vision pipeline —— frame → blur → MiniMax M3 → RawData

⚠️  Safety gate（spec §6 鐵律，code-enforced）：
    任何 frame 送 LLM vision API 之前必須先過 PII blur。
    blur 失敗 / 缺 deps → SafetyError → 拒絕送 LLM。
    冇 `--skip-blur`。呢個係刻意嘅設計。

External dep（heavy）：
    pip install -r tools/pii_anonymizer/requirements.txt
    （opencv-python, mediapipe）

用法（程式化）：
    from llm_wiki_engine.vision import process_frame
    raw = process_frame("frames/0001.jpg", location="Sydney")
    # raw 係 RawData pydantic model
"""

import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .config import Config
from .llm_json import extract_json
from .models import RawData


# SafetyError 由 anonymize 提供；為咗避免循環 import，呢度重新定義
class SafetyError(Exception):
    """PII safety gate 失敗 —— 唔可以送 LLM。"""


# Generator system prompt for vision（image-aware 版本，基於 prompts/generator_system.txt）
VISION_SYSTEM_PROMPT = """You are a "human-perspective knowledge engineer".

Task: Based on a single frame provided by the participant (taken from their first-person-perspective video) and their brief description, infer and write out a standardized Markdown note.

⚠️ Important rules:
- The image has already been PII-blurred (faces and license plates have been blurred out). Do not attempt to identify any blurred regions.
- Do not fabricate facts. If the image or description provides no information, leave it blank or mark it as "unknown".
- Do not mention any identifiable individual (even if the image was not fully blurred).

The output must be JSON containing:
{
  "frontmatter": {
    "timestamp": "<filled in by the caller; you fill in a placeholder>",
    "gps_lat": <float or null>,
    "gps_lng": <float or null>,
    "trigger_type": "<inferred from the image: aesthetic_gaze / anomaly_detection / professional_judgment / manual / other>",
    "domain": "<inferred from the image: tourism / legal / medical / industrial / education / other>",
    "tags": "<comma-separated tags>",
    "human_label": "<provided by the participant, or empty>"
  },
  "body_human_description": "<preserve the participant's original text>",
  "body_ai_analysis": "<infer the scene, emotion, and professional judgment from the image + description, 200-300 words>",
  "body_related_links": ["[[wikilink_1]]", "[[wikilink_2]]"]
}

Language: Write your response in the SAME language as the participant's human_description input (Cantonese / English / Mandarin). English is the default skeleton when the input gives no language signal.
"""


def _encode_image_b64(image_path: Path) -> tuple:
    """讀圖片 → base64 data URI。回傳 (data_uri, mime_type)。"""
    mime, _ = mimetypes.guess_type(str(image_path))
    if mime is None or not mime.startswith("image/"):
        mime = "image/jpeg"  # 預設
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}", mime


def _blur_frame(frame_path: Path, work_dir: Path) -> Path:
    """
    Safety gate：對 frame 做 PII blur。

    Returns:
        blurred image 嘅 path（喺 work_dir 度）

    Raises:
        SafetyError: blur 失敗、deps 缺失、或圖片讀唔到
    """
    # 將 pii_anonymizer 加落 sys.path（佢唔係 package，係 flat scripts）
    repo_root = Path(__file__).resolve().parents[1]
    pii_dir = repo_root / "tools" / "pii_anonymizer"
    if str(pii_dir) not in sys.path:
        sys.path.insert(0, str(pii_dir))

    try:
        from anonymize import anonymize_image, SafetyError as AnonSafetyError
    except ImportError as e:
        raise SafetyError(
            f"Failed to load PII anonymize module: {e}."
            "Install deps: pip install -r tools/pii_anonymizer/requirements.txt"
        ) from e

    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = work_dir / f"{frame_path.stem}_anon{frame_path.suffix}"

    try:
        result_path, summary = anonymize_image(
            str(frame_path), str(out_path)
        )
        return Path(result_path)
    except AnonSafetyError as e:
        raise SafetyError(str(e)) from e
    except Exception as e:
        raise SafetyError(f"blur failed unexpectedly: {e}") from e


def _call_minimax_vision(
    config: Config,
    image_data_uri: str,
    participant_hint: str,
    temperature: float = 0.3,
) -> dict:
    """
    Call MiniMax M3 with image. OpenAI-compatible content array.

    participant_hint: 參與者提供嘅簡短文字（location、context）。
    """
    user_content = [
        {"type": "text", "text": f"參與者提示：{participant_hint or '（冇額外提示）'}"},
        {"type": "text", "text": "請根據呢張 frame + 提示，輸出 JSON。"},
        {
            "type": "image_url",
            "image_url": {"url": image_data_uri, "detail": "default"},
        },
    ]

    payload = json.dumps({
        "model": config.minimax_model,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature,
        "max_tokens": 600,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{config.minimax_base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {config.minimax_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:300]
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"MiniMax vision HTTP {e.code}: {body}") from e

    parsed = extract_json(content)
    if parsed is None:
        raise ValueError(f"MiniMax vision returned invalid JSON: {content[:200]}")
    return parsed


def process_frame(
    frame_path: str,
    config: Config,
    timestamp: Optional[str] = None,
    gps: Optional[dict] = None,
    location_hint: str = "",
    participant_description: str = "",
    work_dir: Optional[Path] = None,
) -> RawData:
    """
    對單一 frame 跑完整 vision pipeline：blur → MiniMax M3 → RawData。

    Args:
        frame_path: 原始 frame 圖片路徑
        config: API config（需有 MiniMax key）
        timestamp: ISO 8601（預設 now）
        gps: {"lat": float, "lng": float}（預設 {0,0}）
        location_hint: 例如 "Sydney Harbour"
        participant_description: 參與者嘅簡短文字（可空）
        work_dir: blur 中間檔目錄（預設 frame 旁邊）

    Returns:
        RawData pydantic model

    Raises:
        SafetyError: blur 失敗 —— frame 冇送 LLM
        RuntimeError: MiniMax API 失敗
        ValueError: LLM output 唔符合 schema
    """
    from datetime import datetime, timezone
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    if gps is None:
        gps = {"lat": 0.0, "lng": 0.0}

    frame = Path(frame_path)
    if not frame.exists():
        raise FileNotFoundError(f"Frame does not exist: {frame}")

    if work_dir is None:
        work_dir = frame.parent / "_anon"
    work_dir = Path(work_dir)

    # === SAFETY GATE ===
    # 冇 try/except bypass。blur 失敗 → raise SafetyError → caller 必須處理。
    blurred = _blur_frame(frame, work_dir)
    if not blurred.exists():
        raise SafetyError(f"blur reported success but output does not exist: {blurred}")

    # 編碼 + call
    image_uri, _ = _encode_image_b64(blurred)
    hint = location_hint
    if participant_description:
        hint = f"{location_hint} | description: {participant_description}"

    raw_dict = _call_minimax_vision(config, image_uri, hint)

    # 將 caller 提供嘅確定欄位覆蓋 LLM 嘅推測
    # （timestamp / gps / human_description 由人提供，唔信 LLM 推測）
    frontmatter = raw_dict.get("frontmatter", {})
    frontmatter["timestamp"] = timestamp
    frontmatter["gps_lat"] = gps.get("lat", 0.0)
    frontmatter["gps_lng"] = gps.get("lng", 0.0)
    if participant_description:
        raw_dict["body_human_description"] = participant_description

    # 組成 RawData（用 nested gps，對齊 P1 contract）
    raw_payload = {
        "timestamp": timestamp,
        "gps": gps,
        "trigger_type": frontmatter.get("trigger_type", "manual"),
        "domain": frontmatter.get("domain", "other"),
        "human_description": raw_dict.get("body_human_description", ""),
        "human_label": frontmatter.get("human_label", ""),
        "tags": [t.strip() for t in str(frontmatter.get("tags", "")).split(",") if t.strip()],
    }

    try:
        raw = RawData(**raw_payload)
    except ValidationError as e:
        raise ValueError(f"Vision output does not match RawData schema: {e}") from e

    # 將 ai_analysis / related_links attach 去 raw 嘅 extra（model_config extra=ignore 會丟）
    # 所以 caller 要自己處理 —— 我哋將完整 result 放喺 raw._vision_extra
    raw._vision_extra = {
        "ai_analysis": raw_dict.get("body_ai_analysis", ""),
        "related_links": raw_dict.get("body_related_links", []),
        "frontmatter": frontmatter,
    }
    return raw
