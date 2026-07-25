"""
WikiAuditor — 用 DeepSeek V4 Flash 審查 Draft Entry
"""

import json
from pathlib import Path

from pydantic import ValidationError

from .client import LLMClient
from .llm_json import extract_json
from .models import RawData, DraftEntry, AuditResult


class WikiAuditor:
    """審查 Draft Entry（auditor LLM：DeepSeek V4 Flash）。"""

    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = self._load_system_prompt()

    @staticmethod
    def _load_system_prompt() -> str:
        prompt_path = Path(__file__).parent / "prompts" / "auditor_system.txt"
        return prompt_path.read_text(encoding="utf-8")

    def audit(self, raw: RawData, draft: DraftEntry) -> AuditResult:
        """Audit Draft Entry against Raw Data。

        Args:
            raw: 已 strip PII 嘅原始數據（用嚟對照）
            draft: generator 產出嘅草稿
        """
        user_data = {
            "raw": {
                "timestamp": raw.timestamp,
                "gps": {"lat": raw.gps_lat, "lng": raw.gps_lng},
                "trigger_type": raw.trigger_type,
                "domain": raw.domain,
                "human_label": raw.human_label,
                "human_description": raw.human_description,
                "tags": raw.tags,
            },
            "draft": {
                "frontmatter": draft.frontmatter,
                "body_human_description": draft.body_human_description,
                "body_ai_analysis": draft.body_ai_analysis,
                "body_related_links": draft.body_related_links,
            },
        }
        user_prompt = json.dumps(user_data, ensure_ascii=False)

        # Auditor 要 deterministic → temperature 0.0
        response = self.client.chat_completion(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
            response_format="json_object",
        )

        try:
            data = extract_json(response)
            if data is None:
                raise ValueError("No valid JSON object found")
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Auditor returned invalid JSON: {e}\nRaw: {response[:200]}"
            ) from e

        verdict = data.get("verdict", "fail")
        issues = data.get("issues", []) or []

        corrected = None
        if data.get("corrected"):
            try:
                corrected = DraftEntry(**data["corrected"])
            except ValidationError as e:
                # corrected 無效 → 當作 fail-without-correction
                issues.append(f"auditor-provided corrected version is invalid: {e}")

        return AuditResult(
            verdict=verdict if verdict in ("pass", "fail") else "fail",
            issues=issues,
            corrected=corrected,
        )
