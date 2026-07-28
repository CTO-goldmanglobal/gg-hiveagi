# Cursor Cold-Start Handoff — Project Hive.AGI

> **Purpose:** A single document that lets Cursor + GLM-5.2 understand the
> entire project from zero context and continue building immediately.
>
> **Read this first. Then read the specific docs it points to.**

---

## 1. What is this project?

**Project Hive.AGI** is an open-source research initiative by Goldman Global
Research Labs building "human-perspective AGI" — computers learning to
understand humans, not humans adapting to computers.

The company has two faces:
- **Goldman Forge** — commercial AI delivery (tourism videos, client work)
- **Goldman Global Research Labs** — open-source research (the AGI thesis)

Both live in one repo: `/Users/explorechina/GG-HiveAGI` (GitHub: `CTO-goldmanglobal/gg-hiveagi`).

**License:** AGPL-3.0 (code) + CC-BY-NC-SA-4.0 (data) + Commercial dual-license.

---

## 2. The architecture in one diagram

```
CAPTURE               COGNITION (Labs core)           DELIVERY (Forge)
glasses/phone    →    llm_wiki_engine/           →    tour-video-finish/
stock footage         videogen/clip_pool/              (VO, music, subs, branding)
                      ↓                                ↓
                      Obsidian Wiki ←─ KNOWLEDGE BRIDGE
                      ↓
                      Seed Packages (IPFS, provenance-gated)
```

**The provenance gate** (`videogen/provenance.py`) is the load-bearing seam:
- Stock footage → Forge only (blocked from Labs)
- Human-captured → Labs eligible
- Human judgments on stock → Labs eligible (hybrid seed, tagged)

---

## 3. Repository map (every module, what it does)

### Core cognition (Labs)
| Path | Purpose | Status |
|:---|:---|:---|
| `llm_wiki_engine/` | Dual-LLM engine: MiniMax M3 (generator) + DeepSeek V4 Flash (auditor). Converts raw data → Markdown wiki entries. | ✅ Working (1607 lines) |
| `llm_wiki_engine/vision.py` | Frame → PII blur → MiniMax M3 vision → structured analysis | ✅ Working |
| `llm_wiki_engine/llm_json.py` | Robust JSON extractor (handles `<think>` blocks, fenced code, partial JSON) | ✅ Critical utility |

### Video pipeline (Forge + Labs seam)
| Path | Purpose | Status |
|:---|:---|:---|
| `videogen/` | 7-stage pipeline: ingest → analyze → select → script → compose → finalize | ✅ Working (3368 lines) |
| `videogen/clip_pool/` | Candidate pool: fetch, pretag (LLM), metrics (opencv), adapt (crop), judge (human) | ✅ Working |
| `videogen/provenance.py` | **THE GATE** — stock blocked from Labs, code-enforced | ✅ Critical |
| `videogen/selection_log.py` | Human-override signal capture (the beauty standard seed) | ✅ Working |
| `videogen/compose.py` | ffmpeg assembly: segments, xfade, subtitles (graceful degradation) | ✅ Working |

### Finishing skill (Forge craft)
| Path | Purpose | Status |
|:---|:---|:---|
| `.agents/skills/tour-video-finish/` | ZCode skill: VO + music + subtitles + end card | ✅ Working (1577 lines) |
| `scripts/composite.py` | Single-pass overlay renderer (subs + logo + card on one frame) | ✅ The correct renderer |
| `scripts/tts_vo.py` | MiniMax speech-2.8-hd voiceover generation | ✅ Working |
| `scripts/mix_audio.py` | VO + music mix with loudnorm | ✅ Working (simple chain) |

### Infrastructure (Labs)
| Path | Purpose | Status |
|:---|:---|
| `tools/seed_generator/` | P0: Seed Package generator + validator | ✅ Working |
| `tools/pii_anonymizer/` | Face (MediaPipe) + plate (edge-based) blur, code-enforced | ✅ Working, CI-tested |
| `p2p_exchange/` | P2: IPFS/kubo Seed Package exchange (publish, verify, resolve) | ✅ Working |
| `obsidian_plugin/` | P2: Obsidian plugin for vault interaction | ✅ Scaffolded (TypeScript) |
| `tools/vault_setup/` | P0: Obsidian vault directory structure setup | ✅ Working |

### Client configs
| Path | Purpose | Status |
|:---|:---|:---|
| `explore_china_holiday/` | ECH (ExploreChina Holidays) — first Forge client | ✅ Circle #1 complete |
| `explore_china_holiday/tours/legends-of-china-warriors/` | Circle #1: scripts, keywords.yaml, cut.py, output/ | ✅ Draft v1 shipped |

### Documentation
| Path | What it is |
|:---|:---|
| `docs/LOOP-STRATEGY.md` | The "small circles" thesis — finish one loop, run the next |
| `docs/LOOP-DIAGRAMS.md` | 6 Mermaid diagrams: circle shape, provenance seam, multi-circle coverage |
| `docs/VIDEO-AUTOMATION-SETUP.md` | Cursor implementation guide: corrected pipeline, 12 modules, priorities |
| `specs/` | Schema specs: seed-package, vault-structure, api-protocol |
| `PROJECT_MASTER_PLAN.md` | Vision, roadmap, license strategy |

---

## 4. The environment

```
Repo:       /Users/explorechina/GG-HiveAGI
Python:     .venv/ (3.13, with openai, pydantic, python-dotenv, pyyaml, jsonschema, opencv-python 5.0, mediapipe 0.10.35, pillow)
APIs:       MiniMax M3 (https://api.minimax.io/v1) — generator + vision + TTS
            DeepSeek V4 Flash (https://api.deepseek.com/v1) — auditor
Keys:       .env (gitignored) — MINIMAX_API_KEY, DEEPSEEK_API_KEY
            macOS Keychain — ech-pexels-api-key (Pexels stock footage)
Media:      /Volumes/Goldman Global/HiveAGI-Media/ (external drive, 1.9TB free)
            .hiveagi-media.env — paths to external storage (gitignored)
ffmpeg:     8.1 (homebrew, NO libass/drawtext — use Pillow for text rendering)
```

---

## 5. What to build (the 5 missing modules)

From the M3 architecture review (`explore_china_holiday/.../M3-REVIEW.json`):

| # | Module | Purpose | Priority |
|:---|:---|:---|:---|
| 1 | `videogen/produce.py` | One-command orchestrator: `--tour-url URL → finished video` | 🔴 Highest |
| 2 | `videogen/ingest.py` | Scrape tour URL → structured itinerary JSON | 🔴 High |
| 3 | `videogen/timeline.py` | TTS VO → master clock → derive cut durations + subtitle timings | 🔴 High |
| 4 | `videogen/qa_gate.py` | M3 frame audit + auto-fix loop (max 2 retries) before delivery | 🔴 High |
| 5 | `videogen/preflight.py` | Asset validation: duration, codec, LUFS, license, checksum | 🟡 Medium |
| 6 | `videogen/wiki_export.py` | Export circle artifacts → Obsidian vault entries | 🟡 Medium |

### The corrected pipeline order (CRITICAL)

```
WRONG (what we did):              RIGHT (what to build):
script → cut to planned durations  script → TTS voiceover FIRST
       → finish (VO, music, subs)        → cut footage to VO durations
                                         → composite (subs + logo + card, ONE PASS)
                                         → mix audio (VO + music)
                                         → M3 QA gate (blocking)
                                         → deliver
```

**VO drives the cut. Not the other way around.**

---

## 6. The 6 bugs we hit (don't repeat)

| Bug | Root cause | Fix in code |
|:---|:---|:---|
| VO/footage 16s desync | Cut to planned durations, not VO | TTS first → cut to VO |
| Subtitles lost | Multi-pass overlay overwrote frames | `composite.py` — single pass |
| SRT parser 1/8 cues | `re.split('\n\s*\n')` on multi-line text | Split on index numbers |
| Wrong outro | Assumed media content without inspecting | Preflight + M3 audit |
| Audio mix 4 iterations | Complex sidechain chain | Simple volume + loudnorm + amix |
| No QA before delivery | Trusted the pipeline | M3 blocking gate |

---

## 7. How to run the existing pipeline

```bash
cd /Users/explorechina/GG-HiveAGI
source .venv/bin/activate

# Fetch stock pool
python -m videogen.clip_pool fetch \
  --config explore_china_holiday/tours/legends-of-china-warriors/keywords.yaml

# Pre-tag with LLM
python -m videogen.clip_pool pretag \
  --pool-dir explore_china_holiday/tours/legends-of-china-warriors/pool

# Adapt landscape → portrait
python -m videogen.clip_pool adapt \
  --pool-dir explore_china_holiday/tours/legends-of-china-warriors/pool \
  --clips pexels_36926090,pexels_2881972 --mode smart

# Judge (interactive)
python -m videogen.clip_pool judge \
  --pool-dir explore_china_holiday/tours/legends-of-china-warriors/pool

# Cut the draft
python explore_china_holiday/tours/legends-of-china-warriors/cut.py

# Finish (VO + music + subs + end card)
python .agents/skills/tour-video-finish/scripts/finish.py \
  --draft <draft.mp4> --script <selection_draft.json> \
  --music <track.mp3> --logo <logo.png> --out FINAL.mp4
```

---

## 8. The Obsidian wiki (both platforms)

Vault: `/Volumes/Goldman Global/HiveAGI-Media/obsidian-vault/`

```
00_Inbox/      ← raw data (Labs captures + Forge artifacts)
01_Entries/    ← LLM-distilled Markdown notes
02_Topics/     ← MOCs (Map of Content) — cross-linked indexes
03_SeedPackages/ ← IPFS exchange packages (provenance-gated)
04_Templates/  ← entry templates
```

Forge deposits: judgment logs, audio calibration, tour scripts, QA results.
Labs deposits: glasses/phone captures, distilled entries.
Both linked via bidirectional `[[wikilinks]]`.
Provenance gate runs before any Seed Package export.

**To build:** `videogen/wiki_export.py` — reads circle artifacts → writes vault entries.

---

## 9. Read order for Cursor

1. **This document** (you are here)
2. `docs/VIDEO-AUTOMATION-SETUP.md` — the implementation guide
3. `explore_china_holiday/tours/legends-of-china-warriors/RETROSPECTIVE.md` — what went wrong
4. `explore_china_holiday/tours/legends-of-china-warriors/M3-REVIEW.json` — M3's architecture verdict
5. `docs/LOOP-STRATEGY.md` — the thesis
6. `videogen/provenance.py` — the gate (read this before touching anything Labs-bound)

---

## 10. First task for Cursor

Build `videogen/produce.py` — the one-command orchestrator:

```bash
python -m videogen produce \
  --tour-url "https://www.explorechinaholidays.com.au/tours/legends-of-china-warriors" \
  --music /path/to/track.mp3 \
  --logo /path/to/logo.png \
  --out legends-FINAL.mp4
```

Flow: ingest URL → fetch stock → pretag → metrics → TTS VO → cut to VO → composite → mix audio → M3 QA → deliver.

Start with `produce.py` + `ingest.py` + `timeline.py`. The rest of the pipeline already exists.
