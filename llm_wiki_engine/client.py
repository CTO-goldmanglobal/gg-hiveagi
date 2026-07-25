"""
LLM Client — Abstract + Real (OpenAI SDK) + Mock

兩個 provider 都係 OpenAI-compatible，所以 RealLLMClient 淨係換 base_url。
MockLLMClient 令 pipeline 可以喺冇 API key 嘅情況下行得通，用嚟
smoke test 成個 orchestration + 三個 audit 分支。
"""

import json
from abc import ABC, abstractmethod
from typing import Optional

from openai import OpenAI

from .config import Config


class LLMClient(ABC):
    """抽象 LLM Client。"""

    @abstractmethod
    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        response_format: Optional[str] = None,
    ) -> str:
        """Call LLM，return response content（raw string）。"""
        raise NotImplementedError


class RealLLMClient(LLMClient):
    """真實 API Client — OpenAI-compatible（MiniMax / DeepSeek）。"""

    def __init__(self, config: Config, client_type: str):
        if client_type == "generator":
            self.client = OpenAI(
                base_url=config.minimax_base_url,
                api_key=config.minimax_api_key,
            )
            self.model = config.minimax_model
        elif client_type == "auditor":
            self.client = OpenAI(
                base_url=config.deepseek_base_url,
                api_key=config.deepseek_api_key,
            )
            self.model = config.deepseek_model
        else:
            raise ValueError(f"Unknown client_type: {client_type}")

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        response_format: Optional[str] = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class MockLLMClient(LLMClient):
    """
    Mock Client — 用 canned JSON 模擬。

    audit_fail_mode 控制 auditor 嘅回應，用嚟測試三個分支：
      - "pass"        → verdict=pass
      - "corrected"   → verdict=fail + corrected
      - "quarantine"  → verdict=fail, 冇 corrected
      - None          → 預設 pass
    """

    def __init__(self, client_type: str, audit_fail_mode: Optional[str] = None):
        self.client_type = client_type
        # 🔒 喺 constructor 度 capture，唔係之後再 set（DeepSeek 原版嘅 bug）
        self.audit_fail_mode = audit_fail_mode

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        response_format: Optional[str] = None,
    ) -> str:
        if self.client_type == "generator":
            return self._mock_generator_response(user_prompt)
        elif self.client_type == "auditor":
            return self._mock_auditor_response(user_prompt)
        return "{}"

    def _mock_generator_response(self, user_prompt: str) -> str:
        """模擬 MiniMax M3 生成 Draft Entry。"""
        try:
            data = json.loads(user_prompt)
        except json.JSONDecodeError:
            data = {}

        gps = data.get("gps", {})
        timestamp = data.get("timestamp", "2026-07-25T19:30:00Z")
        trigger_type = data.get("trigger_type", "aesthetic_gaze")
        domain = data.get("domain", "tourism")
        tags = data.get("tags", ["日落", "貨櫃碼頭"])
        if isinstance(tags, list):
            tags = ", ".join(tags)
        human_label = data.get("human_label", "") or ""
        human_desc = data.get("human_description", "")

        # 模擬「如果 human_label = 靚 → 加 #aesthetic」（spec §4 規則）
        extra_tags = []
        if human_label == "靚":
            extra_tags.append("aesthetic")
        all_tags = tags + (", " + ", ".join(f"#{t}" for t in extra_tags) if extra_tags else "")

        return json.dumps({
            "frontmatter": {
                "timestamp": timestamp,
                "gps_lat": gps.get("lat", -33.8568),
                "gps_lng": gps.get("lng", 151.2153),
                "trigger_type": trigger_type,
                "domain": domain,
                "tags": all_tags,
                "human_label": human_label,
            },
            "body_human_description": human_desc,
            "body_ai_analysis": (
                f"[Mock MiniMax 分析] {human_desc} "
                "呢個觸發展現咗人類視角下嘅獨特觀察，值得記錄同連結到更廣嘅知識網絡。"
            ),
            "body_related_links": ["[[悉尼港口]]", "[[工業美學]]"],
        }, ensure_ascii=False)

    def _mock_auditor_response(self, user_prompt: str) -> str:
        """模擬 DeepSeek V4 Flash Audit，根據 audit_fail_mode 決定結果。"""
        verdict = "pass"
        issues: list = []
        corrected = None

        if self.audit_fail_mode == "corrected":
            verdict = "fail"
            issues = ["tags 唔夠齊全，缺 '悉尼' 標籤"]
            try:
                raw = json.loads(user_prompt)
                draft_fm = raw.get("draft", {}).get("frontmatter", {})
            except json.JSONDecodeError:
                draft_fm = {}
            corrected = {
                "frontmatter": {
                    "timestamp": draft_fm.get("timestamp", "2026-07-25T19:30:00Z"),
                    "gps_lat": draft_fm.get("gps_lat", -33.8568),
                    "gps_lng": draft_fm.get("gps_lng", 151.2153),
                    "trigger_type": draft_fm.get("trigger_type", "aesthetic_gaze"),
                    "domain": draft_fm.get("domain", "tourism"),
                    "tags": (draft_fm.get("tags", "") + ", 悉尼").lstrip(", "),
                    "human_label": draft_fm.get("human_label", "靚"),
                },
                "body_human_description": raw.get("draft", {}).get("body_human_description", ""),
                "body_ai_analysis": "[Auditor 修正] 增加 '悉尼' 地理標籤以提升可檢索性。",
                "body_related_links": ["[[悉尼港口]]", "[[工業美學]]"],
            }
        elif self.audit_fail_mode == "quarantine":
            verdict = "fail"
            issues = ["內容嚴重偏離主題", "無法自動修正"]

        return json.dumps({
            "verdict": verdict,
            "issues": issues,
            "corrected": corrected,
        }, ensure_ascii=False)
