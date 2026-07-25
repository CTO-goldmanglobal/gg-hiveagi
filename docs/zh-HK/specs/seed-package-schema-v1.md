[English](../../../specs/seed-package-schema-v1.md) | 繁體中文

# Seed Package Schema v1.0

## 1. 概覽

Seed Package 係 Project Hive.AGI 嘅核心交换单位。每個 Seed Package 包含：

- 一個 `manifest.json`（貢獻者中繼資料、領域分類、統計）
- 一個 `entries/` 資料夾（每個 entry 係一個獨立嘅 Markdown 檔案）
- 一個 `README.md`（人類可讀嘅使用說明）

---

## 2. 目錄結構

```
seed_package/
├── manifest.json
├── entries/
│   ├── entry_001.md
│   ├── entry_002.md
│   └── ...
└── README.md
```

---

## 3. manifest.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "schema_version",
    "contributor_id",
    "contributor_type",
    "created_at",
    "total_entries",
    "domains",
    "language",
    "geo_regions",
    "license",
    "description",
    "contact"
  ],
  "properties": {
    "schema_version": { "type": "string", "pattern": "^1\\.0$" },
    "contributor_id": { "type": "string" },
    "contributor_type": { "enum": ["individual", "organization"] },
    "created_at": { "type": "string", "format": "date-time" },
    "total_entries": { "type": "integer", "minimum": 1 },
    "domains": {
      "type": "array",
      "items": { "enum": ["tourism", "legal", "medical", "industrial", "education", "other"] }
    },
    "language": { "type": "string", "pattern": "^[a-z]{2}(-[A-Z]{2})?$" },
    "geo_regions": {
      "type": "array",
      "items": { "type": "string", "pattern": "^[A-Z]{2}-[A-Z0-9]{2,}$" }
    },
    "license": { "enum": ["CC-BY-NC-SA-4.0"] },
    "description": { "type": "string", "maxLength": 500 },
    "contact": { "type": "string", "format": "email" },
    "version": { "type": "string" },
    "tags": { "type": "array", "items": { "type": "string" } }
  }
}
```

---

## 4. Entry Frontmatter Schema

每個 `entry_XXX.md` 必須包含 frontmatter（YAML 格式）：

```yaml
---
timestamp: "2026-07-25T19:30:00Z"       # ISO 8601
gps_lat: -33.8568                        # float
gps_lng: 151.2153                        # float
trigger_type: "aesthetic_gaze"           # enum
domain: "tourism"                        # enum
tags: "sunset, container terminal, golden hour"   # 逗號分隔
human_label: "beautiful"                 # 選填
hardware: "basic_ai_glasses"             # 選填
trigger_duration: 2.5                    # 選填，float
---
```

### trigger_type 枚舉

| 值 | 描述 |
| :--- | :--- |
| `aesthetic_gaze` | 審美注視（風景 / 建築 / 藝術） |
| `anomaly_detection` | 異常偵測（工業 / 工程） |
| `professional_judgment` | 專業判斷（法律 / 醫療） |
| `manual` | 人手標記 |
| `other` | 其他 |

### domain 枚舉

| 值 | 描述 |
| :--- | :--- |
| `tourism` | 旅遊 / 文化 |
| `legal` | 法律 / 專業服務 |
| `medical` | 醫療 / 健康 |
| `industrial` | 工業 / 工程 |
| `education` | 教育 / 學習 |
| `other` | 其他 |

---

## 5. Entry 正文結構（Markdown）

```markdown
---
[frontmatter]
---

## 人類描述
[貢獻者寫嘅原始描述]

## AI 分析
[由 LLM Wiki Engine 自動產生]

## 相關連結
- [[wikilink_1]]
- [[wikilink_2]]

---
*由 [generator] 產生*
```

---

## 6. 驗證規則

| 規則 | 描述 |
| :--- | :--- |
| manifest.json 必須符合 JSON Schema | 由 `validate_seed.py` 驗證 |
| 每個 entry 必須有齊所有必需 frontmatter 欄位 | timestamp、gps_lat、gps_lng、trigger_type、domain |
| trigger_type 必須係其中一個枚舉值 | 睇上面個表 |
| domain 必須係其中一個枚舉值 | 睇上面個表 |
| Entry 總數 = manifest.total_entries | 必須一致 |
