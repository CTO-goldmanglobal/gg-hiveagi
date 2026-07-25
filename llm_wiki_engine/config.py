"""
Config 管理 — 讀 .env，提供 API Credentials
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """API Configuration"""

    # Generator: MiniMax M3
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_model: str = "MiniMax-M3"
    minimax_api_key: Optional[str] = None

    # Auditor: DeepSeek V4 Flash
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_api_key: Optional[str] = None

    mock_mode: bool = False

    # Retry policy（spec §5）
    max_retries: int = 2
    retry_temperature_increment: float = 0.1

    @classmethod
    def from_env(cls, mock_mode: bool = False) -> "Config":
        """從 .env 載入配置。"""
        # 嘗試載入 .env（向上搵，直至 project root）
        for candidate in (Path(".env"), Path(__file__).resolve().parents[1] / ".env"):
            if candidate.exists():
                load_dotenv(candidate)
                break

        minimax_key = os.getenv("MINIMAX_API_KEY")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")

        # 非 mock 模式必須有齊兩個 key
        if not mock_mode:
            missing = []
            if not minimax_key:
                missing.append("MINIMAX_API_KEY")
            if not deepseek_key:
                missing.append("DEEPSEEK_API_KEY")
            if missing:
                raise ValueError(
                    "Missing credentials: " + ", ".join(missing) + "\n"
                    "Either create a .env file (see llm_wiki_engine/.env.example) "
                    "or run with --mock for offline testing."
                )

        return cls(
            minimax_base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
            minimax_model=os.getenv("MINIMAX_MODEL", "MiniMax-M3"),
            minimax_api_key=minimax_key,
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            deepseek_api_key=deepseek_key,
            mock_mode=mock_mode,
            max_retries=int(os.getenv("MAX_RETRIES", "2")),
            retry_temperature_increment=float(os.getenv("RETRY_TEMP_INCREMENT", "0.1")),
        )


def load_config(mock_mode: bool = False) -> Config:
    """方便函數：載入配置。"""
    return Config.from_env(mock_mode=mock_mode)
