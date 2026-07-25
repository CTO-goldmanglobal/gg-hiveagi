# Obsidian Vault Structure Specification v1.0

## 1. 目錄結構

```
~/HiveAGI/                         # Vault Root
│
├── 00_Inbox/                      # Raw Data 暫存區
│   ├── 2026-07-25_1930_SydneyHarbour.json
│   └── 2026-07-25_1945_OperaHouse.json
│
├── 01_Entries/                    # LLM Wiki 生成嘅筆記
│   ├── 2026-07-25_Sydney_Harbour_Sunset.md
│   └── 2026-07-25_Opera_House_Night.md
│
├── 02_Topics/                     # MOC (Map of Content)
│   ├── _MOC_Tourism.md
│   ├── _MOC_Legal.md
│   └── _MOC_Industrial.md
│
├── 03_SeedPackages/               # 輸出嘅 Seed Package
│   ├── seed_goldman_2026Q3_v1/
│   │   ├── manifest.json
│   │   └── entries/
│   └── seed_goldman_2026Q3_v1.md
│
├── 04_Templates/                  # Templates
│   ├── entry_template.md
│   └── schema_template.md
│
├── 99_Archive/                    # 歸檔舊筆記
│
├── _SCHEMA.md                     # 核心 Schema 文件
└── _README.md                     # Vault 使用說明
```

---

## 2. 命名規範

| 類型 | 格式 | 範例 |
| :--- | :--- | :--- |
| Inbox JSON | `YYYY-MM-DD_HHMM_Location.json` | `2026-07-25_1930_SydneyHarbour.json` |
| Entry Markdown | `YYYY-MM-DD_Location_Subject.md` | `2026-07-25_Sydney_Harbour_Sunset.md` |
| MOC | `_MOC_Domain.md` | `_MOC_Tourism.md` |
| Seed Package Folder | `seed_contributor_YYYYMMDD_vX/` | `seed_goldman_20260725_v1/` |

---

## 3. 雙向鏈接 Convention

- 使用 `[[Page Name]]` 格式
- 每個 Entry 至少關聯一個 MOC（例如 `[[_MOC_Tourism]]`）
- 同一主題嘅 Entry 要互相鏈接

---

## 4. 自動化流程

| 階段 | 動作 | 目標 |
| :--- | :--- | :--- |
| 1 | 硬件觸發 → JSON 寫入 `/00_Inbox/` | Raw Data 採集 |
| 2 | LLM Wiki Engine 讀取 `/00_Inbox/` | 轉化為 Markdown |
| 3 | Markdown 寫入 `/01_Entries/` | 結構化筆記 |
| 4 | MOC 自動更新 | 鏈接關聯 |
| 5 | Seed Package Generator 讀取 `/01_Entries/` | 輸出 Seed Package |
| 6 | Seed Package 寫入 `/03_SeedPackages/` | 準備 P2P 交換 |
