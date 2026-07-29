# Cursor Handoff — Video Automation Pipeline

> **The single document for Cursor + GLM-5.2 to build the one-command video
> pipeline.** Everything from the cold-start overview, the retrospectives, the
> three external audits (OpenAI, Claude, DeepSeek), and the skill research —
> consolidated into one actionable blueprint.
>
> **Read this first. Then read the code it points to.**

---

## 1. The goal

```bash
python -m videogen produce \
  --tour-url "https://www.explorechinaholidays.com.au/tours/legends-of-china-warriors" \
  --music /Volumes/Goldman\ Global/HiveAGI-Media/branding-assets/track.mp3 \
  --logo /Volumes/Goldman\ Global/HiveAGI-Media/branding-assets/ExploreChina.png \
  --out legends-FINAL.mp4
```

**Input:** a tour page URL. **Output:** a finished, M3-audited promo video.
**Constraint:** the human's override signal (where they change the AI's
decisions) is the most valuable output — more valuable than the video itself.

---

## 2. The corrected pipeline (from retrospective — do NOT repeat the bugs)

### The wrong order (what Circle F did):
```
script → cut to planned durations → finish (VO, music, subs)
```
This caused a 16-second VO/footage desync. Don't do this.

### The right order:
```
                TOUR URL
                   │
                   ▼
           ┌─ INGEST ─────────────────────┐
           │ scrape itinerary              │
           │ write script (VO text)        │
           └───────────────┬───────────────┘
                           ▼
           ┌─ FETCH ──────────────────────┐
           │ Pexels stock clips            │
           │ (parallel, cache-aware)       │
           └───────────────┬───────────────┘
                           ▼
           ┌─ ASSET PREFLIGHT ────────────┐
           │ validate duration, codec,     │  ← prevents wrong-asset bugs
           │ resolution, license           │
           └───────────────┬───────────────┘
                           ▼
           ┌─ SHOT INTELLIGENCE ──────────┐
           │ PySceneDetect (scene cuts)   │  ← NEW: install scenedetect
           │ opencv metrics (bright/motion)│  ← EXISTS: clip_pool/metrics.py
           └───────────────┬───────────────┘
                           ▼
           ┌─ M3 VISUAL JUDGE ────────────┐
           │ content tags + quality grade  │  ← EXISTS: clip_pool/llm_tags.py
           │ predict human's choice + conf │  ← NEW: active learning
           └───────────────┬───────────────┘
                           ▼
           ┌─ HUMAN JUDGE ────────────────┐
           │ uncertain cases only          │  ← EXISTS: clip_pool/judge.py
           │ (model auto-approves ≥0.85)   │
           └───────────────┬───────────────┘
                           ▼
           ┌─ TTS VOICEOVER ──────────────┐
           │ MiniMax speech-2.8-hd         │  ← EXISTS: tts_vo.py
           │ VO IS THE MASTER CLOCK        │
           └───────────────┬───────────────┘
                           ▼
           ┌─ COMPOSE EDL ────────────────┐
           │ Edit Decision List (JSON)     │  ← NEW: the key missing piece
           │ shot durations = VO durations │
           └───────────────┬───────────────┘
                           ▼
           ┌─ RENDER ─────────────────────┐
           │ composite: subs+logo+card     │  ← EXISTS: composite.py (ONE PASS)
           │ mix audio: VO + music         │  ← EXISTS: mix_audio.py
           │ ffmpeg execution              │
           └───────────────┬───────────────┘
                           ▼
           ┌─ M3 QA GATE ─────────────────┐
           │ frame audit (subs? logo?)     │  ← EXISTS (manual): automate
           │ auto-fix if errors (max 2)    │
           └───────────────┬───────────────┘
                           ▼
                      FINAL.mp4
                           │
                           ▼
           ┌─ WIKI EXPORT ────────────────┐
           │ judgments → Obsidian vault    │  ← NEW: wiki_export.py
           │ audio corrections → vault     │
           │ override delta → seed data    │
           └───────────────────────────────┘
```

**Key principle:** VO drives the cut. All shot durations derive from TTS
segment durations. Not the other way around.

---

## 3. The EDL — the most important new component

From OpenAI's audit of [browser-use/video-use](https://github.com/browser-use/video-use):

The LLM should NOT directly edit video. It should produce an **Edit Decision
List (EDL)** — a JSON description of every cut — then a deterministic renderer
executes it.

### EDL schema (design this first)

```json
{
  "schema_version": 1,
  "tour": "legends-of-china-warriors",
  "total_duration_sec": 68.2,
  "edl": [
    {
      "shot_id": "shot1_hook",
      "source": "pexels_35834780.mp4",
      "source_path": "pool/shot1_hook/landscape/pexels_35834780.mp4",
      "clip_start_sec": 0,
      "clip_end_sec": 10.0,
      "timeline_start_sec": 0,
      "duration_sec": 10.0,
      "vo_segment": "vo_00.mp3",
      "vo_duration_sec": 9.5,
      "subtitle_text": "China doesn't reveal itself all at once.",
      "transition": {"type": "xfade", "duration_sec": 0.5},
      "purpose": "opening hook — dawn Great Wall",
      "ai_reason": "broadcast grade, drone, dawn colour, calm motion",
      "human_override": null
    }
  ]
}
```

### Why EDL matters for HiveAGI

The override signal becomes structured:

```
AI proposed EDL:   shot_41 @ 12.5–16.2  "looks dramatic"
Human final EDL:   shot_73 @ 12.5–15.6  "feels more authentic, shows older travellers"
→ override delta: {from: shot_41, to: shot_73, reason: "authentic, shows target demographic"}
```

This is the richest preference data the system can capture — far more valuable
than binary accept/reject.

---

## 4. The 6 bugs from Circle F (do NOT repeat)

| Bug | Root cause | Fix |
|:---|:---|:---|
| VO/footage 16s desync | Cut to planned durations, not VO | TTS first → cut to VO |
| Subtitles lost in overlay | Multi-pass frame rewrites overwrite prior overlays | Single-pass `composite.py` — never chain |
| SRT parser 1/8 cues | `re.split('\n\s*\n')` breaks on multi-line subtitle text | Split on SRT index numbers |
| Wrong outro | Assumed media content without inspecting | Asset preflight + M3 audit before use |
| Audio mix 4 iterations | Complex sidechain compression unpredictable | Simple `volume + loudnorm + amix` with explicit weights |
| No QA before delivery | Trusted pipeline output | M3 frame audit as blocking gate, max 2 auto-fix retries |

---

## 5. What exists (7 of 12 skills)

| Module | Path | Status |
|:---|:---|:---|
| Fetch stock clips | `videogen/clip_pool/fetch.py` | ✅ Working |
| LLM content tags | `videogen/clip_pool/llm_tags.py` | ✅ Working |
| opencv metrics | `videogen/clip_pool/metrics.py` | ✅ Working |
| Landscape→portrait adapt | `videogen/clip_pool/adapt.py` | ✅ Working |
| Human judgment capture | `videogen/clip_pool/judge.py` | ✅ Working |
| Provenance gate | `videogen/provenance.py` | ✅ Working |
| TTS voiceover | `.agents/skills/tour-video-finish/scripts/tts_vo.py` | ✅ Working |
| Subtitle burn (Pillow) | `.agents/skills/tour-video-finish/scripts/burn_subtitles.py` | ✅ Working |
| Composite (subs+logo+card) | `.agents/skills/tour-video-finish/scripts/composite.py` | ✅ Working |
| Audio mix | `.agents/skills/tour-video-finish/scripts/mix_audio.py` | ✅ Working |
| Draft cut assembly | `explore_china_holiday/tours/.../cut.py` | ✅ Working (needs EDL integration) |
| Selection override log | `videogen/selection_log.py` | ✅ Working |

## 6. What to BUILD (5 modules)

| # | Module | Priority | What it does |
|:---|:---|:---|:---|
| 1 | `videogen/ingest.py` | 🔴 | Scrape tour URL → itinerary JSON → script VO text |
| 2 | `videogen/timeline.py` | 🔴 | TTS VO → master clock → generate EDL with shot durations |
| 3 | `videogen/produce.py` | 🔴 | One-command orchestrator (the `produce` subcommand) |
| 4 | `videogen/qa_gate.py` | 🔴 | Automated M3 frame audit + auto-fix loop (max 2 retries) |
| 5 | `videogen/wiki_export.py` | 🟡 | Circle artifacts → Obsidian vault entries |

## 7. What to INSTALL

```bash
pip install scenedetect[opencv]    # PySceneDetect — scene boundary detection
                                    # Reduces M3 vision calls ~75%
```

---

## 8. Lessons from external audits

### From OpenAI + Claude (the thesis attack):
- **Construct validity** is the weakest link: "editor taste on curated stock ≠ human perspective"
- **n=1** is not a dataset — need multi-human, pairwise comparison
- **Stock vs. glasses-capture are different variables** — keep them separate in provenance
- Next experiment should **test the signal**, not build more capability
- **Pairwise preference** (A vs B, "which?") is better than accept/reject
- **Model predicts first, logs confidence** — items where model was confident and wrong = gold

### From DeepSeek (skill architecture):
- Formalize quality checks into **deterministic detector rules** (like impeccable's 60 rules)
- Convert binary accept/reject into **tunable preference dials** (like taste-skill's 3 dials)
- Detectors = algorithmic (cheap). Dials = learned (human-fed). Keep separate.

### From OpenAI (video skill landscape):
- **EDL pattern** from video-use: LLM generates edit decisions, renderer executes
- **PySceneDetect**: cheap scene detection before expensive M3 vision calls
- **Skill primitives**: each editing operation = one skill (SKILL.md + script + schema + tests)
- GLM-5.2 acts as **director**, not video engineer

---

## 9. Audio mix settings (learned from 4 iterations)

```python
# The CORRECT settings (from Circle F calibration):
VO_VOLUME = 1.65      # VO pre-scale
MUSIC_VOLUME = 0.48   # Music pre-scale (music is 20% of VO)
VO_LUFS = -14         # VO target (dramatic narration level)
MUSIC_LUFS = -22      # Music target (8dB below VO — industry standard)
MIX_WEIGHTS = "1 0.6" # amix weights (VO dominant)

# Mix chain (SIMPLE — do not use sidechaincompress):
filter = f"[0:a]volume={VO_VOLUME},loudnorm=I={VO_LUFS}:TP=-1.5:LRA=11[vo];"
         f"[1:a]volume={MUSIC_VOLUME},atrim=duration={{dur}},loudnorm=I={MUSIC_LUFS}:TP=-1.5:LRA=11[music];"
         f"[vo][music]amix=inputs=2:duration=first:weights={MIX_WEIGHTS}[out]"
```

## 10. Subtitle settings (learned from SRT parser bug + visibility issues)

```python
# Font: Arial Bold (available on macOS, renders in Pillow)
# Size: max(36, h * 0.038) — at least 3.8% of frame height
# Position: bottom, 12% from bottom (mobile safe zone)
# Box: semi-transparent black (0,0,0,160) rounded rectangle
# Text: white (255,255,255,255)

# CRITICAL: SRT parser must split on index numbers, NOT blank lines:
# WRONG: re.split(r'\n\s*\n', content)  ← breaks on multi-line subtitle text
# RIGHT: re.split(r'\n(?=\d+\s*\n\d{2}:\d{2})', content)
```

## 11. Logo watermark settings (learned from "too close to edge")

```python
LOGO_WIDTH_PCT = 0.12    # 12% of frame width
LOGO_Y_PCT = 0.07        # 7% from top (inside title-safe area)
LOGO_ALPHA = 180         # slightly transparent
LOGO_CYCLE = 10.0        # visible 4s, hidden 6s, repeat
LOGO_FADE = 0.5          # fade in/out duration
```

---

## 12. Environment

```
Repo:       /Users/explorechina/GG-HiveAGI
Python:     .venv/ (3.13)
APIs:       MiniMax M3 (https://api.minimax.io/v1) — vision + TTS
            DeepSeek V4 Flash (https://api.deepseek.com/v1) — audit
            Pexels (keychain: ech-pexels-api-key)
Keys:       .env (gitignored)
Media:      /Volumes/Goldman Global/HiveAGI-Media/ (external, 1.9TB)
            .hiveagi-media.env — paths (gitignored)
ffmpeg:     8.1 homebrew (NO libass/drawtext — use Pillow for ALL text)
Installed:  impeccable + taste-skill (15 skills in .agents/skills/)
            PySceneDetect (install: pip install scenedetect[opencv])
```

---

## 13. File map for Cursor

```
BUILD THESE:
videogen/produce.py          ← one-command orchestrator
videogen/ingest.py           ← tour URL → itinerary → script
videogen/timeline.py         ← TTS VO → EDL with durations
videogen/qa_gate.py          ← automated M3 audit + auto-fix
videogen/wiki_export.py      ← artifacts → Obsidian vault

INSTALL THIS:
scenedetect[opencv]          ← scene detection (pip install)

THESE EXIST (read before modifying):
videogen/clip_pool/          ← fetch, llm_tags, metrics, adapt, judge
videogen/provenance.py       ← THE GATE (don't touch without understanding)
videogen/selection_log.py    ← override signal capture
.agents/skills/tour-video-finish/scripts/
  composite.py               ← single-pass overlay renderer (the correct one)
  tts_vo.py                  ← MiniMax TTS
  mix_audio.py               ← VO + music mix
  burn_subtitles.py          ← Pillow subtitle burn

REFERENCE (read for context):
docs/THE-LIVING-SEED.md      ← the vision
docs/LOOP-STRATEGY.md        ← the methodology
docs/internal/OPENAI-VIDEO-SKILL-AUDIT.md  ← EDL + PySceneDetect insights
docs/internal/EXTERNAL-AUDIT-SYNTHESIS.md  ← thesis critique
docs/internal/DEEPSEEK-SKILL-REVIEW.json   ← detector + dial architecture
```

---

## 14. First task

Build `videogen/produce.py` + `videogen/ingest.py` + `videogen/timeline.py`.

1. `ingest.py`: fetch tour page → extract itinerary (cities, attractions, days) → write VO script
2. `timeline.py`: send script to MiniMax TTS → get VO segment durations → generate EDL.json
3. `produce.py`: call existing fetch → pretag → metrics → judge → cut to EDL → composite → mix → QA → deliver

Start with these three. The rest of the pipeline already works.
