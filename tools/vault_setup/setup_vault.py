#!/usr/bin/env python3
"""
Obsidian Vault Setup v1.0
自動建立 Hive.AGI 嘅 Obsidian Vault 目錄結構、Templates、_SCHEMA.md、_README.md

用法:
    python setup_vault.py                       # 預設 ./HiveAGI_Vault
    python setup_vault.py --target ~/HiveAGI    # 自訂路徑
"""

import argparse
import shutil
from pathlib import Path


# Vault 目錄結構（對應 specs/vault-structure-spec.md）
VAULT_DIRS = [
    "00_Inbox",
    "01_Entries",
    "02_Topics",
    "03_SeedPackages",
    "04_Templates",
    "99_Archive",
]

SCHEMA_MD = """# Hive.AGI Vault — Schema

> 呢個 Vault 採用 Project Hive.AGI 嘅結構規範。
> 完整 spec 見 repo `specs/vault-structure-spec.md`。

## 目錄用途

| 目錄 | 用途 |
| :--- | :--- |
| `00_Inbox/` | 硬件 / App 採集嘅 Raw Data（JSON）暫存區 |
| `01_Entries/` | LLM Wiki Engine 生成嘅標準化 Markdown 筆記 |
| `02_Topics/` | MOC（Map of Content），按領域匯總 |
| `03_SeedPackages/` | 輸出嘅 Seed Package（可交換） |
| `04_Templates/` | Obsidian Templates |
| `99_Archive/` | 歸檔舊筆記 |

## 命名規範

- Inbox JSON：`YYYY-MM-DD_HHMM_Location.json`
- Entry Markdown：`YYYY-MM-DD_Location_Subject.md`
- MOC：`_MOC_Domain.md`
- Seed Package Folder：`seed_contributor_YYYYMMDD_vX/`

## 雙向鏈接

- 用 `[[Page Name]]`
- 每個 Entry 至少關聯一個 MOC

## License

- Code: AGPL-3.0
- Seed Data: CC-BY-NC-SA-4.0

聯絡：cto@goldmanglobal.com.au
"""

VAULT_README = """# Hive.AGI Vault

呢個係你嘅 Project Hive.AGI Obsidian Vault。

## 快速開始

1. 用 Obsidian 開啟呢個資料夾作為 Vault
2. Raw Data 放入 `00_Inbox/`
3. （P1）運行 LLM Wiki Engine 生成筆記到 `01_Entries/`
4. 用 Seed Generator 產出 Seed Package 到 `03_SeedPackages/`

## 結構說明

見 `_SCHEMA.md`。

## 聯絡

cto@goldmanglobal.com.au
"""

# 04_Templates 入面嘅 seed MOC 種子檔
SEED_MOCS = {
    "_MOC_Tourism.md": """# 🗺️ MOC — Tourism

- [[]]
""",
    "_MOC_Industrial.md": """# 🗺️ MOC — Industrial

- [[]]
""",
    "_MOC_Legal.md": """# 🗺️ MOC — Legal

- [[]]
""",
}


def setup_vault(target):
    vault = Path(target).expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)

    print(f"🔧 建立 Vault 於: {vault}")

    # 1. 目錄
    for d in VAULT_DIRS:
        (vault / d).mkdir(exist_ok=True)
        print(f"  📁 {d}/")

    # 2. Templates（由 repo templates/ 複製；若搵唔到就用內建）
    templates_src = Path(__file__).parent / "templates"
    templates_dst = vault / "04_Templates"
    if templates_src.is_dir():
        for tpl in templates_src.glob("*.md"):
            shutil.copy2(tpl, templates_dst / tpl.name)
            print(f"  📄 04_Templates/{tpl.name} (copied)")
    else:
        # fallback：寫一個最細 entry template
        (templates_dst / "entry_template.md").write_text(
            "---\ntimestamp: \ngps_lat: \ngps_lng: \ntrigger_type: manual\n"
            "domain: other\ntags: \nhuman_label: \n---\n\n## 人類描述\n\n",
            encoding="utf-8",
        )
        print("  📄 04_Templates/entry_template.md (fallback)")

    # 3. Seed MOCs
    topics = vault / "02_Topics"
    for name, content in SEED_MOCS.items():
        (topics / name).write_text(content, encoding="utf-8")
        print(f"  📄 02_Topics/{name}")

    # 4. _SCHEMA.md 同 _README.md
    (vault / "_SCHEMA.md").write_text(SCHEMA_MD, encoding="utf-8")
    print("  📄 _SCHEMA.md")
    (vault / "_README.md").write_text(VAULT_README, encoding="utf-8")
    print("  📄 _README.md")

    # 5. .gitkeep 俾空目錄可以入 git
    for d in VAULT_DIRS:
        gk = vault / d / ".gitkeep"
        if not any(gk.parent.iterdir()):
            gk.touch()

    print()
    print(f"✅ Vault 建立完成！用 Obsidian 開啟: {vault}")
    print(f"   下一步：將 Raw Data 放入 {vault / '00_Inbox'}/")


def main():
    parser = argparse.ArgumentParser(description="建立 Hive.AGI Obsidian Vault")
    parser.add_argument(
        "--target", default="./HiveAGI_Vault",
        help="Vault 目標路徑（預設 ./HiveAGI_Vault）"
    )
    args = parser.parse_args()
    setup_vault(args.target)


if __name__ == "__main__":
    main()
