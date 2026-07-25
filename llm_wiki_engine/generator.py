"""
WikiGenerator — 用 MiniMax M3 生成 Draft Entry
"""

import json
from pathlib import Path

from pydantic import ValidationError

from .client import LLMClient
from .llm_json import extract_json
from .models import RawData, DraftEntry


class WikiGenerator:
    """生成 Draft Entry（主力 LLM：MiniMax M3）。"""

    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = self._load_system_prompt()

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = Path(__file__).parent / "prompts" / "generator_system.txt"
        return prompt_path.read_text(encoding="utf-8")

    def generate(self, raw: RawData, temperature: float = 0.3) -> DraftEntry:
        """Generate Draft Entry from Raw Data。

        Args:
            raw: 已 strip PII 嘅原始數據
            temperature: 生成溫度（預設 0.3；retry 時由 engine 調高）
        """
        user_data = {
            "timestamp": raw.timestamp,
            "gps": {"lat": raw.gps_lat, "lng": raw.gps_lng},
            "trigger_type": raw.trigger_type,
            "domain": raw.domain,
            "human_label": raw.human_label,
            "human_description": raw.human_description,
            "tags": raw.tags,
        }
        user_prompt = json.dumps(user_data, ensure_ascii=False)

        response = self.client.chat_completion(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format="json_object",
        )

        try:
            data = extract_json(response)
            if data is None:
                raise ValueError("搵唔到有效 JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Generator 返回嘅 JSON 無效: {e}\nRaw: {response[:200]}"
            ) from e

        try:
            return DraftEntry(**data)
        except ValidationError as e:
            raise ValueError(f"Generator output 唔符合 DraftEntry schema: {e}") from e
