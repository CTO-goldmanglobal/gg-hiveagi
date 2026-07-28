# Project Hive.AGI

## A Distributed Knowledge Symbiosis Network for Humans

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Data License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![CI](https://github.com/CTO-goldmanglobal/gg-hiveagi/actions/workflows/ci.yml/badge.svg)](https://github.com/CTO-goldmanglobal/gg-hiveagi/actions/workflows/ci.yml)

**[English](./README.md) | [繁體中文](./docs/zh-HK/README.md)**

---

## 🎯 Vision

> Most AI systems today learn from data scraped from the internet. We are exploring a different foundation: structured human judgment — what people notice, value, and choose — as the primary signal for machine intelligence.

**Project Hive.AGI** is an open-source research initiative building a **distributed "human-perspective knowledge network."** Rather than a single centralized model trained on aggregated data, the project envisions a network of independent local nodes — each processing human input through a private LLM engine and sharing structured knowledge through content-addressed exchange.

Anyone can use their own devices (glasses, phones, computers, industrial sensors) to contribute human-perspective data from their area of expertise. Through the LLM Wiki, this data is distilled into structured knowledge that can be exchanged, verified, and synthesized across the network.

### The Living Seed

This project is best understood as a seed — not a finished product, but the
starting condition for a system designed to grow through use.

- **Local nodes** — each contributor runs a private Obsidian vault + LLM engine that processes their own input into structured tags
- **Content-addressed exchange** — Seed Packages are shared via IPFS, verifiable and tamper-resistant
- **Measurable convergence** — when independent nodes produce similar judgments for the same stimulus, that convergence is countable and traceable

This is not view counts or engagement metrics. It is **independent human
judgment agreement** — a different kind of signal, designed to reveal whether
shared human perspectives emerge organically across a distributed network.

See [`docs/THE-LIVING-SEED.md`](./docs/THE-LIVING-SEED.md) for the full
architecture.

### From the Founder

I started this project with a simple conviction: the best ideas are simple
and clean. My background is in building businesses, not academic AI research
— but I believe that human perspective, not scraped data, is the right
foundation for machine intelligence. This repository is an attempt to build
that foundation in the open, one complete loop at a time.

I'm looking for collaborators who share this direction — researchers,
engineers, and domain experts who want to explore human-perspective learning
from the ground up. If that resonates, reach out.

---

## 🚀 Quick Start (P0 — usable today)

### 1. Clone the Repo

```bash
git clone https://github.com/CTO-goldmanglobal/gg-hiveagi.git
cd gg-hiveagi
```

### 2. Install Dependencies

```bash
# P0 (seed generator + validator)
pip install -r tools/seed_generator/requirements.txt

# P1 (llm_wiki_engine)
pip install -r llm_wiki_engine/requirements.txt
```

### 3. Configure LLM Credentials (only required for P1 real mode)

The P1 LLM Wiki Engine uses mock mode by default (no key needed).
To use the real MiniMax / DeepSeek APIs, create a `.env`:

```bash
cp llm_wiki_engine/.env.example .env
# Then use an editor to fill in the real key (do not paste into chat / commit)
```

Required keys (see `specs/api-protocol-v1.md`):

| Variable | Purpose |
| :--- | :--- |
| `MINIMAX_API_KEY` | Generator (MiniMax M3) |
| `DEEPSEEK_API_KEY` | Auditor (DeepSeek V4 Flash) |

`.env` is already in `.gitignore` and will not be committed.

### 4. Generate Your First Seed Package (P0)

```bash
python tools/seed_generator/generate_seed.py
```

The output will be in `seed_output/seed_goldman_20260725/`, containing:
- `manifest.json` — contributor metadata, domain classification, data statistics
- `entries/entry_001.md` — standardized Markdown notes
- `README.md` — usage instructions

### 5. Validate the Seed Package (P0)

```bash
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/
```

### 6. LLM Wiki Engine (P1, mock mode)

```bash
python -m llm_wiki_engine process \
    --inbox llm_wiki_engine/test_samples \
    --entries /tmp/test_entries \
    --mock
```

Once `.env` is configured, remove `--mock` to use the real MiniMax + DeepSeek APIs. See [`llm_wiki_engine/README.md`](./llm_wiki_engine/README.md).

### 7. Collect RawData from Video (two paths)

```bash
# Path 1 (recommended, zero PII risk): manual curation
python tools/video_ingest/extract_frames.py video.mp4 --at 00:01:23 --out frames/
python tools/video_ingest/capture_helper.py --video video.mp4 --inbox ./00_Inbox
python -m llm_wiki_engine process --inbox ./00_Inbox --entries ./01_Entries

# Path 2 (auto-vision, mandatory PII blur)
python tools/video_ingest/extract_frames.py video.mp4 --every 30 --out frames/
python -m llm_wiki_engine process-video --frames frames/ --inbox ./00_Inbox --location Sydney
python -m llm_wiki_engine process --inbox ./00_Inbox --entries ./01_Entries
```

See [`tools/video_ingest/README.md`](./tools/video_ingest/README.md).

> 🔒 **Safety gate**: the auto-vision path **must** pass face + license plate blurring (MediaPipe + OpenCV)
> before being sent to the LLM. There is no `--skip-blur`. If blurring fails, the data is rejected from being sent to the LLM (spec §6 ironclad rule, code-enforced).

---

## 📂 Core Specification Documents

| Document | Description |
| :--- | :--- |
| `PROJECT_MASTER_PLAN.md` | Full master plan (from vision to code) |
| `specs/seed-package-schema-v1.md` | Seed Package JSON / Markdown format specification |
| `specs/vault-structure-spec.md` | Obsidian Vault directory structure and naming conventions |
| `specs/api-protocol-v1.md` | P1 LLM Wiki Engine API design (MiniMax M3 generator + DeepSeek V4 Flash auditor) |

---

## 🧩 Development Roadmap

| Phase | Component | Status |
| :--- | :--- | :--- |
| **P0** | Seed Generator + Validator + Vault Setup | ✅ Complete |
| **P0** | Specs (Schema / Vault / API) | ✅ Complete |
| **P1** | LLM Wiki Engine (MiniMax M3 + DeepSeek V4 Flash dual-LLM) | ✅ Complete (mock verified) |
| **P1** | Mobile Capture App (Basic) | 📋 Planning |
| **P2** | P2P Exchange (IPFS / content addressing) | ✅ Complete (mock verified) |
| **P2** | Obsidian Plugin | ✅ Complete (build + cross-compat verified) |

### 🏭 Commercial Modules (Goldman Forge)

These are commercial product instances built on top of the Labs research
pipeline. Each one solves a real client problem AND contributes
human-perspective data ("what is beautiful / important / worth recording")
back to the Labs knowledge network — the commercial modules fund and feed
the research, the research makes the commercial modules better.

| Module | Client | Status | What it does |
| :--- | :--- | :--- | :--- |
| **[ECH Auto-Cut](./explore_china_holiday/)** | Explore China Holiday | ✅ MVP | Turns tourism footage into short-form Reels automatically. Frame selection + English narration script + 9:16 vertical composition. PII safety gate inherited from Labs. |
| **[Clip Pool + Judge](./videogen/clip_pool/)** | Explore China Holiday | ✅ Circle #1 | Stock footage → LLM content tags → opencv metrics → human judgment → seed. First complete tagging loop. Provenance-gated. |
| **[Tour Video Finish](./.agents/skills/tour-video-finish/)** | Explore China Holiday | ✅ Draft v1 | VO (MiniMax TTS) + music mix + subtitle burn + brand end card + logo watermark. M3 vision QA audited. |

> **How the two connect:** Forge commercial modules produce client value and
> generate structured human-perspective data (what people judge as beautiful,
> important, or worth recording). Labs research explores whether this signal,
> aggregated across contributors and domains, can form the basis of a
> human-perspective knowledge network.

---

## 📄 License Overview

| Component | License | Reason |
| :--- | :--- | :--- |
| **Code** (Python Scripts, Specs, Tools) | [AGPL-3.0](./LICENSE) | Ensures open-source derivative works must share improvements, encouraging enterprise sponsorship |
| **Seed Data** (knowledge packages produced by contributors) | [CC-BY-NC-SA-4.0](./DATA_LICENSE.md) | Allows sharing and adaptation but prohibits commercial use, protecting contributors |
| **Commercial License** | [Commercial](./COMMERCIAL_LICENSE.md) | Enterprises requiring commercial use, please contact cto@goldmanglobal.com.au |

---

## 🤝 How to Contribute

1. **Star & Fork** this repo
2. **Read** [CONTRIBUTING.md](./CONTRIBUTING.md)
3. **Sign the CLA** (Contributor License Agreement)
4. **Contribute** your Seed Package or improve the code
5. **Join the discussion**: Discord (Coming Soon)

---

## 📬 Contact

- **Research collaboration & partnerships**: cto@goldmanglobal.com.au
- **Commercial licensing**: [COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md)
- **GitHub Discussions**: Open to anyone building on or with human-perspective data

---

## 🙏 Acknowledgements

Initiated by [Goldman Global Research Labs](https://goldmanglobal.com.au) — an
open-source research initiative exploring how machines can learn human
perspective through structured judgment, not centralized data scraping.

This project stands on the work of every contributor who tags, judges, and
shares their perspective. That act — a human deciding what matters and why —
is the irreducible unit this entire network is built from.

---

**In one sentence**:

> Exploring whether machines can learn human perspective through structured judgment — not by scraping data, but by earning it one decision at a time.
