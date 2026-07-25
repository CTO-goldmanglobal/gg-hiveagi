"""
WikiEngine — Orchestrator

Pipeline（spec §5）：
    raw → strip_pii → generate → audit →
        pass        → 入庫
        fail+corrected → 自動修正入庫（帶 audit_log）
        fail 無corrected → 重試（temp +0.1）max_retries 次 → 仍 fail → quarantine

修正同 retry 政策全部喺呢度實現，generator/auditor 本身唔知 retry 存在。
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from .config import Config
from .models import RawData, DraftEntry, FinalEntry
from .client import RealLLMClient, MockLLMClient
from .generator import WikiGenerator
from .auditor import WikiAuditor
from .pii import strip_pii


class WikiEngine:
    """Orchestration Engine。"""

    def __init__(self, config: Config, mock_mode: bool = False,
                 audit_fail_mode: Optional[str] = None):
        """
        Args:
            config: API 配置
            mock_mode: True 用 MockLLMClient（唔使 API key）
            audit_fail_mode: mock 模式下強制 auditor 行某個分支
                             （"pass" / "corrected" / "quarantine"）。
                             🔒 必須喺呢度傳入，唔係 cli 事後 set（DeepSeek 原版 bug）。
        """
        self.config = config
        self.mock_mode = mock_mode

        if mock_mode:
            self.generator_client = MockLLMClient("generator", audit_fail_mode)
            self.auditor_client = MockLLMClient("auditor", audit_fail_mode)
        else:
            self.generator_client = RealLLMClient(config, "generator")
            self.auditor_client = RealLLMClient(config, "auditor")

        self.generator = WikiGenerator(self.generator_client)
        self.auditor = WikiAuditor(self.auditor_client)

    def process_one(self, raw: RawData, quarantine_path: Path) -> Optional[FinalEntry]:
        """
        處理單一 Raw Data。

        Returns:
            FinalEntry（成功，含 pass / corrected）或 None（quarantine）
        """
        # 1. PII Stripping
        stripped_dict = strip_pii(raw.model_dump())
        stripped_raw = RawData(**stripped_dict)

        # 2. Generate + Audit（含 retry）
        last_error: Optional[str] = None
        max_attempts = self.config.max_retries + 1

        for attempt in range(max_attempts):
            temp = 0.3 + (attempt * self.config.retry_temperature_increment)
            try:
                draft = self.generator.generate(stripped_raw, temperature=temp)
                audit_result = self.auditor.audit(stripped_raw, draft)

                if audit_result.verdict == "pass":
                    return self._build_final(
                        draft, stripped_raw,
                        audited=True, corrected=False,
                    )

                if audit_result.verdict == "fail" and audit_result.corrected is not None:
                    # 有修正 → 自動用 corrected 入庫（spec §5 自動修正政策）
                    return self._build_final(
                        audit_result.corrected, stripped_raw,
                        audited=True, corrected=True,
                        audit_log=f"auto-corrected: {'; '.join(audit_result.issues)}",
                    )

                # fail 無 corrected → 記錄並重試
                last_error = (
                    f"audit fail (attempt {attempt + 1}/{max_attempts}): "
                    f"{'; '.join(audit_result.issues) or 'no issues listed'}"
                )
                print(f"    ⚠️  {last_error}")

            except Exception as e:  # noqa: BLE001 — 所有錯誤都入 retry/quarantine
                last_error = f"error (attempt {attempt + 1}/{max_attempts}): {e}"
                print(f"    ⚠️  {last_error}")

        # 3. 全部 retry 都 fail → quarantine
        self._quarantine(raw.model_dump(), quarantine_path, last_error)
        return None

    @staticmethod
    def _build_final(
        draft: DraftEntry,
        raw: RawData,
        audited: bool = True,
        corrected: bool = False,
        audit_log: Optional[str] = None,
    ) -> FinalEntry:
        return FinalEntry(
            frontmatter=draft.frontmatter,
            body_human_description=draft.body_human_description,
            body_ai_analysis=draft.body_ai_analysis,
            body_related_links=draft.body_related_links,
            audited=audited,
            audited_corrected=corrected,
            audit_log=audit_log,
            raw_timestamp=raw.timestamp,
            raw_domain=raw.domain,
        )

    @staticmethod
    def _quarantine(
        raw_dict: Dict[str, Any],
        quarantine_path: Path,
        reason: Optional[str],
    ) -> None:
        quarantine_path.mkdir(parents=True, exist_ok=True)
        ts = raw_dict.get("timestamp", "unknown").replace(":", "-")
        filename = f"{ts}_quarantine.json"
        with open(quarantine_path / filename, "w", encoding="utf-8") as f:
            json.dump(
                {"raw": raw_dict, "reason": reason, "status": "quarantine"},
                f, indent=2, ensure_ascii=False,
            )
        print(f"    🚮 Quarantined → {quarantine_path / filename} ({reason})")
