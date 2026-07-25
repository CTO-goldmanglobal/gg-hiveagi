# Seed Package Generator

A P0 core tool that converts "human-perspective Raw Data" into standardized Seed Packages.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Generate a Seed Package (Example)

```bash
python generate_seed.py
```

Output:

```
seed_output/seed_goldman_20260725/
├── manifest.json
├── entries/
│   ├── entry_001.md
│   └── entry_002.md
└── README.md
```

## Validate the Seed Package

```bash
python validate_seed.py --path seed_output/seed_goldman_20260725/
```

Validation checks:
- `manifest.json` conforms to the JSON Schema (see `specs/seed-package-schema-v1.md`)
- Each entry has all required frontmatter (timestamp, gps_lat, gps_lng, trigger_type, domain)
- `trigger_type` / `domain` are valid enumerated values
- `timestamp` conforms to ISO 8601
- The entry count matches `manifest.total_entries`

## Programmatic Usage

```python
from generate_seed import SeedGenerator

entries = [
    {
        "timestamp": "2026-07-25T19:30:00Z",
        "gps": {"lat": -33.8568, "lng": 151.2153},
        "trigger_type": "aesthetic_gaze",
        "domain": "tourism",
        "human_label": "beautiful",
        "human_description": "Sunset light piercing through the gaps between shipping containers, forming golden beams of light.",
        "tags": ["sunset", "container terminal"],
    }
]

gen = SeedGenerator(output_dir="./seed_output")
gen.generate_seed_package(entries, "seed_my_first_batch")
```

## Specification

The Seed Package format specification is in [`specs/seed-package-schema-v1.md`](../../specs/seed-package-schema-v1.md).

## Contact

cto@goldmanglobal.com.au
