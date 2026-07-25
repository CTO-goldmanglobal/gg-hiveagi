# Seed Package Generator

P0 核心工具：將「人類視角 Raw Data」轉為標準化 Seed Package。

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 生成 Seed Package（範例）

```bash
python generate_seed.py
```

輸出：

```
seed_output/seed_goldman_20260725/
├── manifest.json
├── entries/
│   ├── entry_001.md
│   └── entry_002.md
└── README.md
```

## 校驗 Seed Package

```bash
python validate_seed.py --path seed_output/seed_goldman_20260725/
```

校驗內容：
- `manifest.json` 符合 JSON Schema（見 `specs/seed-package-schema-v1.md`）
- 每個 entry 有齊 required frontmatter（timestamp, gps_lat, gps_lng, trigger_type, domain）
- `trigger_type` / `domain` 屬於列舉值
- `timestamp` 符合 ISO 8601
- entry 數量 = `manifest.total_entries`

## 程式化使用

```python
from generate_seed import SeedGenerator

entries = [
    {
        "timestamp": "2026-07-25T19:30:00Z",
        "gps": {"lat": -33.8568, "lng": 151.2153},
        "trigger_type": "aesthetic_gaze",
        "domain": "tourism",
        "human_label": "靚",
        "human_description": "夕陽穿過貨櫃之間嘅縫隙，形成金色光柱。",
        "tags": ["日落", "貨櫃碼頭"],
    }
]

gen = SeedGenerator(output_dir="./seed_output")
gen.generate_seed_package(entries, "seed_my_first_batch")
```

## 規範

Seed Package 格式規範見 [`specs/seed-package-schema-v1.md`](../../specs/seed-package-schema-v1.md)。

## 聯絡

cto@goldmanglobal.com.au
