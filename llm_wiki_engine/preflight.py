"""
Preflight checker — real-mode readiness for the full Hive.AGI stack.

逐項獨立檢查，話俾你知邊樣 ready、邊樣未。每項都唔會因為前一項失敗而跳過。

用法：
    python -m llm_wiki_engine preflight          # 全部檢查
    python -m llm_wiki_engine preflight --quick  # 淨係 env + daemon，唔打真 API
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from typing import Optional

from .config import load_config


def _mark(ok: bool) -> str:
    return "✅" if ok else "❌"


def check_env_keys() -> bool:
    """檢查 .env 入面兩個 API key 有冇填（值絕對唔會顯示）。"""
    print("\n── 1. Environment (.env) ──")
    minimax = os.getenv("MINIMAX_API_KEY", "")
    deepseek = os.getenv("DEEPSEEK_API_KEY", "")
    group_id = os.getenv("MINIMAX_GROUP_ID", "")

    print(f"  {_mark(bool(minimax))} MINIMAX_API_KEY    "
          f"{'SET (' + str(len(minimax)) + ' chars)' if minimax else 'EMPTY'}")
    print(f"  {_mark(bool(deepseek))} DEEPSEEK_API_KEY  "
          f"{'SET (' + str(len(deepseek)) + ' chars)' if deepseek else 'EMPTY'}")
    print(f"  ℹ️  MINIMAX_GROUP_ID  "
          f"{'SET' if group_id else 'EMPTY (optional for chat)'}")

    if not (minimax and deepseek):
        print("\n  → 點填：用編輯器開 .env（唔好 paste 入 chat），填入兩個 key。")
        return False
    return True


def check_kubo() -> bool:
    """檢查 kubo (IPFS) daemon 有冇行緊。"""
    print("\n── 2. Kubo IPFS daemon (P2 real mode) ──")
    api_url = os.getenv("IPFS_API_URL", "http://127.0.0.1:5001")
    try:
        req = urllib.request.Request(f"{api_url}/api/v0/version", method="POST")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ver = data.get("Version", "?")
            print(f"  {_mark(True)} kubo daemon reachable at {api_url}")
            print(f"     version: {ver}")
            return True
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        print(f"  {_mark(False)} kubo daemon unreachable at {api_url}")
        print("     → 裝 kubo: https://docs.ipfs.tech/install/")
        print("     → 啟動：`ipfs daemon &`")
        print("     （P2 仍然可以用 --mock，淨係唔能 publish 到真 IPFS）")
        return False


def _ping_openai_compat(base_url: str, api_key: str, label: str) -> bool:
    """Ping 一個 OpenAI-compatible endpoint，用 /models 或者最平嘅 chat call。"""
    if not api_key:
        print(f"  {_mark(False)} {label}: 冇 key（skip）")
        return False

    # 先試 /models（多數 provider 支援，唔燒 token）
    try:
        req = urllib.request.Request(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"  {_mark(True)} {label}: auth OK，/models 200")
                return True
    except urllib.error.HTTPError as e:
        # 401 = key 錯；其他 status 可能係 endpoint 唔支援 /models，再試 chat ping
        if e.code == 401:
            print(f"  {_mark(False)} {label}: 401 Unauthorized — key 無效或過期")
            return False
        # fall through to chat ping
    except (urllib.error.URLError, OSError):
        print(f"  {_mark(False)} {label}: 連唔到 {base_url}（network / endpoint 錯）")
        return False

    # /models 唔得，做一個最細嘅 chat call（max_tokens=1）
    return _chat_ping(base_url, api_key, label)


def _chat_ping(base_url: str, api_key: str, label: str) -> bool:
    """最小 chat completion（1 token）去驗證 key + model。"""
    # 用 config 入面嘅 model 名
    model = (
        os.getenv("MINIMAX_MODEL", "MiniMax-M3") if "minimax" in label.lower()
        else os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    )
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                print(f"  {_mark(True)} {label}: chat ping OK（model={model}）")
                return True
            print(f"  {_mark(False)} {label}: HTTP {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:200]
        except Exception:  # noqa: BLE001
            pass
        print(f"  {_mark(False)} {label}: HTTP {e.code} — {body}")
        return False
    except (urllib.error.URLError, OSError) as e:
        print(f"  {_mark(False)} {label}: 連唔到 — {e}")
        return False


def check_minimax() -> bool:
    print("\n── 3. MiniMax M3 (generator) ──")
    return _ping_openai_compat(
        os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
        os.getenv("MINIMAX_API_KEY", ""),
        "MiniMax",
    )


def check_deepseek() -> bool:
    print("\n── 4. DeepSeek V4 Flash (auditor) ──")
    print("  （注意：deepseek-chat / deepseek-reasoner 已喺 2026-07-24 deprecate，")
    print("   必須用 deepseek-v4-flash）")
    return _ping_openai_compat(
        os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        os.getenv("DEEPSEEK_API_KEY", ""),
        "DeepSeek",
    )


def run_preflight(quick: bool = False) -> int:
    """跑全部檢查。quick=True 就唔打真 API（淨係 env + daemon）。"""
    print("═══════════════════════════════════════════════════════════════")
    print("  Hive.AGI Preflight — real-mode readiness check")
    print("═══════════════════════════════════════════════════════════════")

    # 載入 .env
    from dotenv import load_dotenv
    load_dotenv(".env")

    results = {}
    results["env"] = check_env_keys()
    results["kubo"] = check_kubo()

    if not quick:
        results["minimax"] = check_minimax()
        results["deepseek"] = check_deepseek()
    else:
        print("\n── 3. MiniMax / DeepSeek ──  (skipped, --quick)")

    # 總結
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Summary")
    print("═══════════════════════════════════════════════════════════════")
    for name, ok in results.items():
        print(f"  {_mark(ok)} {name}")
    print()

    all_ok = all(results.values())
    if all_ok:
        print("🎉 All green — real mode ready! Drop --mock and run:")
        print("   python -m llm_wiki_engine process \\")
        print("       --inbox llm_wiki_engine/test_samples --entries ./real_entries")
    else:
        print("⚠️  部分未 ready。上面嘅 ❌ 項各有 fix 提示。")
        print("    可以繼續用 --mock 開發；填好 / 啟動好對應項之後再跑 preflight。")

    return 0 if all_ok else 1


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    sys.exit(run_preflight(quick=quick))
