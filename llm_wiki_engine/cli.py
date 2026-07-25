"""
CLI 入口 — 支援 process / process-one / --mock
"""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .config import load_config
from .engine import WikiEngine
from .models import RawData


def _entry_filename(result) -> str:
    """由 FinalEntry 衍生安全檔名（避免 ':' 喺 filename）。"""
    ts = (result.raw_timestamp or "unknown").replace(":", "-")
    domain = result.raw_domain or "other"
    return f"{ts}_{domain}.md"


def cmd_process(args) -> int:
    inbox_path = Path(args.inbox)
    entries_path = Path(args.entries)
    quarantine_path = Path(args.quarantine)

    if not inbox_path.exists():
        print(f"❌ Inbox 目錄不存在: {inbox_path}", file=sys.stderr)
        return 1

    entries_path.mkdir(parents=True, exist_ok=True)
    quarantine_path.mkdir(parents=True, exist_ok=True)

    json_files = sorted(inbox_path.glob("*.json"))
    if not json_files:
        print(f"⚠️  Inbox 入面冇 JSON 檔案: {inbox_path}")
        return 0

    engine = _build_engine(args)
    print(f"📂 搵到 {len(json_files)} 個 JSON，開始處理 ...")

    ok_count, fail_count = 0, 0
    for json_file in json_files:
        print(f"  📄 {json_file.name}")
        try:
            raw_data = json.loads(json_file.read_text(encoding="utf-8"))
            raw = RawData(**raw_data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"    ❌ Raw Data 無效: {e}")
            fail_count += 1
            continue

        result = engine.process_one(raw, quarantine_path)
        if result is not None:
            out = entries_path / _entry_filename(result)
            out.write_text(result.to_markdown(), encoding="utf-8")
            tag = " (corrected)" if result.audited_corrected else ""
            print(f"    ✅ 寫入 {out.name}{tag}")
            ok_count += 1
        else:
            fail_count += 1

    print(f"\n✅ 完成：{ok_count} 入庫，{fail_count} quarantine/失敗")
    return 0


def cmd_process_one(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    quarantine_path = Path(args.quarantine)

    if not input_path.exists():
        print(f"❌ 輸入檔案不存在: {input_path}", file=sys.stderr)
        return 1

    try:
        raw_data = json.loads(input_path.read_text(encoding="utf-8"))
        raw = RawData(**raw_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"❌ Raw Data 無效: {e}", file=sys.stderr)
        return 1

    quarantine_path.mkdir(parents=True, exist_ok=True)
    engine = _build_engine(args)

    result = engine.process_one(raw, quarantine_path)
    if result is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.to_markdown(), encoding="utf-8")
        tag = " (corrected)" if result.audited_corrected else ""
        print(f"✅ 寫入 {output_path}{tag}")
        return 0
    else:
        print("❌ 處理失敗，已放入 quarantine", file=sys.stderr)
        return 1


def _build_engine(args) -> WikiEngine:
    config = load_config(mock_mode=args.mock)
    return WikiEngine(
        config,
        mock_mode=args.mock,
        audit_fail_mode=getattr(args, "audit_fail_mode", None),
    )


def _run_preflight(args) -> int:
    # 延遲 import，令 preflight 喺 deps 缺失時仍然可以報告
    from .preflight import run_preflight
    return run_preflight(quick=args.quick)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm_wiki_engine",
        description="LLM Wiki Engine — 將 Raw Data 轉為結構化 Wiki Entry",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # preflight
    p_pre = subparsers.add_parser(
        "preflight", help="檢查 real-mode 依賴（env keys / kubo / MiniMax / DeepSeek）"
    )
    p_pre.add_argument(
        "--quick", action="store_true",
        help="淨係檢查 env + daemon，唔打真 API",
    )
    p_pre.set_defaults(func=lambda a: _run_preflight(a))

    # process
    p_proc = subparsers.add_parser("process", help="批量處理 Inbox 目錄")
    p_proc.add_argument("--inbox", required=True, help="Inbox 目錄（存放 Raw Data JSON）")
    p_proc.add_argument("--entries", required=True, help="輸出 Entries 目錄")
    p_proc.add_argument("--quarantine", default="./quarantine", help="Quarantine 目錄")
    p_proc.add_argument("--mock", action="store_true", help="Mock 模式（唔使 API key）")
    p_proc.add_argument(
        "--audit-fail-mode",
        choices=["pass", "corrected", "quarantine"],
        default=None,
        help="Mock 模式強制 audit 結果（測試分支用）",
    )
    p_proc.set_defaults(func=cmd_process)

    # process-one
    p_one = subparsers.add_parser("process-one", help="處理單一 JSON 檔案")
    p_one.add_argument("--input", required=True, help="輸入 JSON 檔案")
    p_one.add_argument("--output", required=True, help="輸出 .md 檔案")
    p_one.add_argument("--quarantine", default="./quarantine", help="Quarantine 目錄")
    p_one.add_argument("--mock", action="store_true", help="Mock 模式")
    p_one.add_argument(
        "--audit-fail-mode",
        choices=["pass", "corrected", "quarantine"],
        default=None,
    )
    p_one.set_defaults(func=cmd_process_one)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except ValueError as e:
        # Config 報錯（缺 key）
        print(f"❌ Config Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
