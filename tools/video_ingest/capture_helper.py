#!/usr/bin/env python3
"""
capture_helper.py —— Path 1 manual capture 嘅互動 helper。

你喺 terminal 行呢個，配合 video player 播片：
  1. 播片見到值得記錄嘅 moment → 暫停 / 記低時間
  2. 喺 helper 度填 timestamp、location、trigger_type、domain、描述
  3. helper 寫一個 RawData JSON 去 00_Inbox/
  4. 繼續播片，重複

呢個 path 完全唔接觸 LLM vision API，零 PII 風險。
你最後跑 `python -m llm_wiki_engine process --inbox 00_Inbox --entries ...`
就會用 P1 engine（純文字）做 analyze。

純 stdlib（input/json/datetime），冇新依賴。
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


TRIGGER_TYPES = ["aesthetic_gaze", "anomaly_detection",
                 "professional_judgment", "manual", "other"]
DOMAINS = ["tourism", "legal", "medical", "industrial", "education", "other"]


def _prompt(label: str, choices=None, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    choice_hint = f" ({'/'.join(choices)})" if choices else ""
    while True:
        val = input(f"{label}{choice_hint}{hint}: ").strip() or default
        if choices and val not in choices:
            print(f"  無效選項，揀：{choices}")
            continue
        return val


def _gps_prompt() -> dict:
    """互動填 GPS（可 skip）。"""
    raw = input("GPS lat,lng（例如 -33.8568,151.2153，留空 skip）：").strip()
    if not raw:
        return {"lat": 0.0, "lng": 0.0}
    try:
        parts = raw.split(",")
        return {"lat": float(parts[0]), "lng": float(parts[1])}
    except (ValueError, IndexError):
        print("  ⚠️  格式錯，用 0,0")
        return {"lat": 0.0, "lng": 0.0}


def capture_one(video_name: str, inbox_dir: Path) -> Path:
    """互動收集一筆 RawData，寫去 inbox_dir。回傳寫出嘅檔案路徑。"""
    print(f"\n── 新 capture（來源 video: {video_name}）──")

    timestamp = datetime.now(timezone.utc).isoformat()
    video_time = _prompt("Video 時間點（HH:MM:SS）", default="00:00:00")
    location = _prompt("地點名稱（例如 SydneyHarbour）", default="unknown")
    gps = _gps_prompt()
    trigger_type = _prompt("trigger_type", choices=TRIGGER_TYPES,
                          default="aesthetic_gaze")
    domain = _prompt("domain", choices=DOMAINS, default="tourism")
    human_label = _prompt("人類標籤（靚 / 異常 / 留空）", default="")
    print("人類描述（多行，最後一行淨係打 . 結束）：")
    desc_lines = []
    while True:
        line = input()
        if line.strip() == ".":
            break
        desc_lines.append(line)
    human_description = "\n".join(desc_lines).strip()
    if not human_description:
        human_description = f"(captured at {video_time} from {video_name})"

    tags_raw = input("tags（逗號分隔，可留空）：").strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    raw_data = {
        "timestamp": timestamp,
        "gps": gps,
        "trigger_type": trigger_type,
        "domain": domain,
        "human_description": human_description,
        "human_label": human_label,
        "tags": tags,
        # 額外 metadata（唔影響 P1 parse，但保留溯源）
        "source_video": video_name,
        "source_video_time": video_time,
        "location_label": location,
    }

    inbox_dir.mkdir(parents=True, exist_ok=True)
    # 檔名：YYYY-MM-DD_HHMM_<location>.json（vault-structure-spec convention）
    now = datetime.now()
    pad = lambda n: f"{n:02d}"
    stamp = f"{now.year}-{pad(now.month)}-{pad(now.day)}_{pad(now.hour)}{pad(now.minute)}"
    slug = location.replace(" ", "_")[:40] if location != "unknown" else "capture"
    out_path = inbox_dir / f"{stamp}_{slug}.json"
    out_path.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"✅ 寫咗 → {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="互動 manual capture helper（Path 1，純文字，零 PII）"
    )
    parser.add_argument("--video", help="來源 video 檔名（淨係做 metadata 標記）")
    parser.add_argument("--inbox", default="./00_Inbox",
                        help="Inbox 輸出目錄（預設 ./00_Inbox）")
    args = parser.parse_args()

    video_name = args.video or "manual"
    inbox_dir = Path(args.inbox)

    print("Hive.AGI manual capture helper")
    print("Ctrl-C 離開。每筆完成後會問你繼續唔繼續。\n")

    count = 0
    try:
        while True:
            capture_one(video_name, inbox_dir)
            count += 1
            more = input("\n繼續 capture 下一筆？[Y/n]: ").strip().lower()
            if more == "n":
                break
    except (KeyboardInterrupt, EOFError):
        print()

    print(f"\n📝 收集咗 {count} 筆。下一步：")
    print(f"   python -m llm_wiki_engine process \\")
    print(f"       --inbox {inbox_dir} --entries ./01_Entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
