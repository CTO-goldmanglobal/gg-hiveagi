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
        print(f"❌ Inbox directory does not exist: {inbox_path}", file=sys.stderr)
        return 1

    entries_path.mkdir(parents=True, exist_ok=True)
    quarantine_path.mkdir(parents=True, exist_ok=True)

    json_files = sorted(inbox_path.glob("*.json"))
    if not json_files:
        print(f"⚠️  No JSON files in Inbox: {inbox_path}")
        return 0

    engine = _build_engine(args)
    print(f"📂 Found {len(json_files)} JSON file(s), starting processing ...")

    ok_count, fail_count = 0, 0
    for json_file in json_files:
        print(f"  📄 {json_file.name}")
        try:
            raw_data = json.loads(json_file.read_text(encoding="utf-8"))
            raw = RawData(**raw_data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"    ❌ Invalid Raw Data: {e}")
            fail_count += 1
            continue

        result = engine.process_one(raw, quarantine_path)
        if result is not None:
            out = entries_path / _entry_filename(result)
            out.write_text(result.to_markdown(), encoding="utf-8")
            tag = " (corrected)" if result.audited_corrected else ""
            print(f"    ✅ Written {out.name}{tag}")
            ok_count += 1
        else:
            fail_count += 1

    print(f"\n✅ Done: {ok_count} committed, {fail_count} quarantine/failed")
    return 0


def cmd_process_one(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    quarantine_path = Path(args.quarantine)

    if not input_path.exists():
        print(f"❌ Input file does not exist: {input_path}", file=sys.stderr)
        return 1

    try:
        raw_data = json.loads(input_path.read_text(encoding="utf-8"))
        raw = RawData(**raw_data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"❌ Invalid Raw Data: {e}", file=sys.stderr)
        return 1

    quarantine_path.mkdir(parents=True, exist_ok=True)
    engine = _build_engine(args)

    result = engine.process_one(raw, quarantine_path)
    if result is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.to_markdown(), encoding="utf-8")
        tag = " (corrected)" if result.audited_corrected else ""
        print(f"✅ Written {output_path}{tag}")
        return 0
    else:
        print("❌ Processing failed, moved to quarantine", file=sys.stderr)
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


def cmd_process_video(args) -> int:
    """Path 2: 對一個 frames 目錄逐個跑 vision → 寫 RawData JSON 去 inbox。"""
    from pathlib import Path
    from datetime import datetime, timezone
    from .vision import process_frame, SafetyError

    frames_dir = Path(args.frames)
    inbox_dir = Path(args.inbox)
    inbox_dir.mkdir(parents=True, exist_ok=True)

    if not frames_dir.is_dir():
        print(f"❌ frames directory does not exist: {frames_dir}", file=sys.stderr)
        return 1

    config = load_config(mock_mode=False)  # vision 一定要 real mode

    frame_files = sorted(
        p for p in frames_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    )
    if not frame_files:
        print(f"⚠️  No images in {frames_dir}", file=sys.stderr)
        return 1

    print(f"🔎 Vision processing {len(frame_files)} frame(s) ...")
    ok, fail = 0, 0
    for i, frame in enumerate(frame_files, 1):
        print(f"  [{i}/{len(frame_files)}] {frame.name}")
        try:
            raw = process_frame(
                str(frame), config,
                timestamp=datetime.now(timezone.utc).isoformat(),
                location_hint=args.location or "",
                participant_description="",
            )
            # 寫 RawData JSON 去 inbox
            out = inbox_dir / f"{frame.stem}.json"
            payload = raw.model_dump()
            # 保留 vision extra（ai_analysis 等）
            extra = getattr(raw, "_vision_extra", None)
            if extra:
                payload["_vision_extra"] = extra
            out.write_text(
                __import__("json").dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"      ✅ → {out.name}")
            ok += 1
        except SafetyError as e:
            print(f"      🚫 SAFETY: {e}")
            fail += 1
        except Exception as e:  # noqa: BLE001
            print(f"      ❌ {type(e).__name__}: {e}")
            fail += 1

    print(f"\n✅ Vision done: {ok} succeeded, {fail} failed")
    print(f"Next step: python -m llm_wiki_engine process --inbox {inbox_dir} --entries ...")
    return 0 if fail == 0 else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm_wiki_engine",
        description="LLM Wiki Engine — convert Raw Data into structured Wiki Entries",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # preflight
    p_pre = subparsers.add_parser(
        "preflight", help="Check real-mode dependencies (env keys / kubo / MiniMax / DeepSeek)"
    )
    p_pre.add_argument(
        "--quick", action="store_true",
        help="Only check env + daemon, do not hit the real API",
    )
    p_pre.set_defaults(func=lambda a: _run_preflight(a))

    # process
    p_proc = subparsers.add_parser("process", help="Batch process an Inbox directory")
    p_proc.add_argument("--inbox", required=True, help="Inbox directory (holding Raw Data JSON)")
    p_proc.add_argument("--entries", required=True, help="Output Entries directory")
    p_proc.add_argument("--quarantine", default="./quarantine", help="Quarantine directory")
    p_proc.add_argument("--mock", action="store_true", help="Mock mode (no API key needed)")
    p_proc.add_argument(
        "--audit-fail-mode",
        choices=["pass", "corrected", "quarantine"],
        default=None,
        help="Mock mode forces the audit result (for testing branches)",
    )
    p_proc.set_defaults(func=cmd_process)

    # process-one
    p_one = subparsers.add_parser("process-one", help="Process a single JSON file")
    p_one.add_argument("--input", required=True, help="Input JSON file")
    p_one.add_argument("--output", required=True, help="Output .md file")
    p_one.add_argument("--quarantine", default="./quarantine", help="Quarantine directory")
    p_one.add_argument("--mock", action="store_true", help="Mock mode")
    p_one.add_argument(
        "--audit-fail-mode",
        choices=["pass", "corrected", "quarantine"],
        default=None,
    )
    p_one.set_defaults(func=cmd_process_one)

    # process-video (Path 2: auto-vision with enforced PII blur)
    p_vid = subparsers.add_parser(
        "process-video",
        help="Auto-vision: frames → blur → MiniMax M3 → RawData JSON (requires real mode + PII deps)"
    )
    p_vid.add_argument("--frames", required=True, help="Frame image directory")
    p_vid.add_argument("--inbox", required=True, help="RawData JSON output directory")
    p_vid.add_argument("--location", default="", help="Location hint (e.g. Sydney Harbour)")
    p_vid.set_defaults(func=cmd_process_video)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except ValueError as e:
        # Config 報錯（缺 key）
        print(f"❌ Config Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
