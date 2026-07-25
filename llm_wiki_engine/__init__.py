"""
LLM Wiki Engine — Project Hive.AGI P1

將 Raw Data 轉化為結構化 Wiki Entry，經 Dual-LLM 審計後自動入庫：
    Generator: MiniMax M3
    Auditor:   DeepSeek V4 Flash
"""

from .config import Config, load_config
from .engine import WikiEngine
from .models import RawData, DraftEntry, AuditResult, FinalEntry
from .client import LLMClient, RealLLMClient, MockLLMClient

__version__ = "1.0.0"

__all__ = [
    "WikiEngine",
    "Config",
    "load_config",
    "RawData",
    "DraftEntry",
    "AuditResult",
    "FinalEntry",
    "LLMClient",
    "RealLLMClient",
    "MockLLMClient",
]
