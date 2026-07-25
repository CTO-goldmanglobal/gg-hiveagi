"""
LLM JSON extraction —— robust parsing for LLM responses.

Reasoning models（MiniMax M3、DeepSeek reasoner 系列）會喺最終 JSON 之前
先輸出一段 `<think>...</think>` chain-of-thought。直接 json.loads 會失敗。

呢度嘅 `extract_json` 處理：
  - 純 JSON（冇 think block）—— 以前嘅正常情況
  - `<think>...</think>` 後跟 JSON —— MiniMax M3 嘅實際行為
  - ```json ... ``` fenced code block —— 某啲 provider 嘅習慣
  - JSON 前後有噪音文字 —— 盡力搵第一個完整 JSON object
"""

import json
import re
from typing import Optional


_THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCED_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Optional[dict]:
    """
    由 LLM response text 抽出第一個 JSON object。

    Returns:
        dict（成功）或 None（搵唔到有效 JSON）。
    """
    if not text:
        return None

    candidate = text.strip()

    # 1. 嘗試直接 parse（最理想：純 JSON）
    obj = _try_parse(candidate)
    if obj is not None:
        return obj

    # 2. 移除 <think>...</think> block（reasoning models）
    no_think = _THINK_PATTERN.sub("", candidate).strip()
    obj = _try_parse(no_think)
    if obj is not None:
        return obj

    # 3. 試 ```json ... ``` fenced block
    fenced = _FENCED_PATTERN.search(no_think)
    if fenced:
        obj = _try_parse(fenced.group(1).strip())
        if obj is not None:
            return obj

    # 4. 最後手段：掃描搵第一個 { ... } 平衡段
    obj = _scan_for_json_object(no_think)
    if obj is not None:
        return obj

    return None


def _try_parse(s: str) -> Optional[dict]:
    """json.loads，失敗返 None。"""
    if not s:
        return None
    try:
        result = json.loads(s)
        return result if isinstance(result, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def _scan_for_json_object(text: str) -> Optional[dict]:
    """
    掃描 text，搵第一個 brace-balanced 段並嘗試 parse。
    處理 JSON 前後有隨意文字嘅情況。
    """
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    obj = _try_parse(candidate)
                    if obj is not None:
                        return obj
                    break  # 呢個段唔係有效 JSON，搵下一個 {
        start = text.find("{", start + 1)
    return None
