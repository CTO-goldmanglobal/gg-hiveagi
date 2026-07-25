#!/usr/bin/env python3
"""
Seed Package Validator v1.0
用 JSON Schema 校驗 Seed Package

用法:
    python validate_seed.py --path seed_output/seed_goldman_20260725/
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError


# ===== JSON Schema for manifest.json =====
MANIFEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "schema_version", "contributor_id", "contributor_type",
        "created_at", "total_entries", "domains",
        "language", "geo_regions", "license", "description", "contact"
    ],
    "properties": {
        "schema_version": {"type": "string", "pattern": "^1\\.0$"},
        "contributor_id": {"type": "string"},
        "contributor_type": {"enum": ["individual", "organization"]},
        "created_at": {"type": "string", "format": "date-time"},
        "total_entries": {"type": "integer", "minimum": 1},
        "domains": {
            "type": "array",
            "items": {"enum": ["tourism", "legal", "medical", "industrial", "education", "other"]}
        },
        "language": {"type": "string", "pattern": "^[a-z]{2}(-[A-Z]{2})?$"},
        "geo_regions": {
            "type": "array",
            "items": {"type": "string", "pattern": "^[A-Z]{2}-[A-Z0-9]{2,}$"}
        },
        "license": {"enum": ["CC-BY-NC-SA-4.0"]},
        "description": {"type": "string", "maxLength": 500},
        "contact": {"type": "string", "format": "email"}
    }
}

# ===== Entry Frontmatter 校驗 =====
REQUIRED_FRONTMATTER = ["timestamp", "gps_lat", "gps_lng", "trigger_type", "domain"]

VALID_TRIGGER_TYPES = {
    "aesthetic_gaze", "anomaly_detection", "professional_judgment", "manual", "other"
}

VALID_DOMAINS = {"tourism", "legal", "medical", "industrial", "education", "other"}

# 簡易 ISO 8601 timestamp pattern (例如 2026-07-25T19:30:00Z)
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)


def parse_frontmatter(md_text):
    """從 Markdown 提取 YAML frontmatter（--- ... --- 之間）。"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def validate_entry(entry_path):
    """校驗單一 entry Markdown，回傳 (ok: bool, errors: list)。"""
    errors = []
    text = entry_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    if fm is None:
        errors.append(f"{entry_path.name}: 無法解析 frontmatter（缺 --- 圍欄或 YAML 無效）")
        return False, errors

    # required keys
    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            errors.append(f"{entry_path.name}: 缺少 required frontmatter `{key}`")

    # type / enum 校驗（只喺 key 存在時做）
    # YAML 會自動將未加引號嘅 timestamp 解析成 datetime object；接納並轉回 ISO string
    if "timestamp" in fm and isinstance(fm["timestamp"], datetime):
        fm["timestamp"] = fm["timestamp"].isoformat().replace("+00:00", "Z")
    if "timestamp" in fm and not isinstance(fm["timestamp"], str):
        errors.append(f"{entry_path.name}: timestamp 必須係 string")
    elif "timestamp" in fm and not TIMESTAMP_PATTERN.match(str(fm["timestamp"])):
        errors.append(f"{entry_path.name}: timestamp 唔符合 ISO 8601（{fm['timestamp']}）")

    for float_key in ("gps_lat", "gps_lng"):
        if float_key in fm and not isinstance(fm[float_key], (int, float)):
            errors.append(f"{entry_path.name}: {float_key} 必須係 number（收到 {type(fm[float_key]).__name__}）")

    if "trigger_type" in fm and fm["trigger_type"] not in VALID_TRIGGER_TYPES:
        errors.append(
            f"{entry_path.name}: trigger_type `{fm['trigger_type']}` 唔係有效值 "
            f"({sorted(VALID_TRIGGER_TYPES)})"
        )

    if "domain" in fm and fm["domain"] not in VALID_DOMAINS:
        errors.append(
            f"{entry_path.name}: domain `{fm['domain']}` 唔係有效值 "
            f"({sorted(VALID_DOMAINS)})"
        )

    return len(errors) == 0, errors


def validate_seed_package(package_path):
    """校驗整個 Seed Package。回傳 overall ok。"""
    pkg = Path(package_path)
    if not pkg.is_dir():
        print(f"❌ 路徑唔係目錄: {pkg}")
        return False

    manifest_file = pkg / "manifest.json"
    entries_dir = pkg / "entries"

    all_ok = True

    # --- 1. manifest.json ---
    if not manifest_file.exists():
        print(f"❌ 缺少 manifest.json")
        all_ok = False
    else:
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            validate(instance=manifest, schema=MANIFEST_SCHEMA)
            print(f"✅ manifest.json 通過 JSON Schema 校驗")
        except json.JSONDecodeError as e:
            print(f"❌ manifest.json JSON 解析失敗: {e}")
            all_ok = False
        except ValidationError as e:
            print(f"❌ manifest.json 唔符合 schema: {e.message} (path: {list(e.absolute_path)})")
            all_ok = False

    # --- 2. entries/ ---
    if not entries_dir.is_dir():
        print(f"❌ 缺少 entries/ 目錄")
        all_ok = False
    else:
        entry_files = sorted(entries_dir.glob("entry_*.md"))
        if not entry_files:
            print(f"❌ entries/ 入面無 entry_*.md 檔案")
            all_ok = False
        else:
            print(f"🔍 校驗 {len(entry_files)} 個 entry ...")
            for ef in entry_files:
                ok, errs = validate_entry(ef)
                if ok:
                    print(f"  ✅ {ef.name}")
                else:
                    all_ok = False
                    for err in errs:
                        print(f"  ❌ {err}")

            # --- 3. entry count 一致性 ---
            if manifest_file.exists():
                try:
                    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                    if manifest.get("total_entries") != len(entry_files):
                        print(
                            f"❌ 數量唔一致: manifest.total_entries="
                            f"{manifest.get('total_entries')} vs 實際 entry 數={len(entry_files)}"
                        )
                        all_ok = False
                except json.JSONDecodeError:
                    pass  # 上面已報錯

    print()
    print("✅ 校驗通過！" if all_ok else "❌ 校驗失敗，請修正上述問題。")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="校驗 Seed Package")
    parser.add_argument(
        "--path", required=True,
        help="Seed Package 目錄路徑（例如 seed_output/seed_goldman_20260725/）"
    )
    args = parser.parse_args()

    ok = validate_seed_package(args.path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
