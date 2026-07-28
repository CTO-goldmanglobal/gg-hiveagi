# Video Automation Setup — Cursor / GLM-5.2 Implementation Guide

> **Purpose:** Everything learned from circle #1 (Legends of China Warriors),
> distilled into a setup guide for Cursor + GLM-5.2 to build the automated
> one-command video pipeline.
>
> **Sources:** Human retrospective (11.5 hours of building) + MiniMax M3
> architecture review.

---

## The one-command goal

```bash
python -m videogen produce \
  --tour-url "https://www.explorechinaholidays.com.au/tours/legends-of-china-warriors" \
  --music /path/to/track.mp3 \
  --logo /path/to/logo.png \
  --out legends-FINAL.mp4
```

Input: a tour page URL. Output: a finished, M3-audited promo video.
Everything in between is automated.

---

## The corrected pipeline (VO drives the cut)

Today's pipeline was: script → cut to planned durations → finish. **This was
wrong.** It caused the 16-second VO/footage desync.

The correct order:

```
                    ┌─── ASSET PREFLIGHT (duration, codec, LUFS, license, checksum)
                    │
tour_url → INGEST ──┤
  (scrape itinerary, │
   write script)     ├── FETCH (stock clips, parallel, cache-aware)
                    │
                    ├── TTS VOICEOVER (MiniMax speech-2.8-hd)
                    │         ↓
                    │    VO IS THE MASTER CLOCK
                    │         ↓
                    ├── CUT (footage durations = VO segment durations)
                    │
                    ├── COMPOSITE (subtitles + logo + end card — ONE PASS)
                    │
                    ├── MIX AUDIO (VO + music, LUFS-normalized)
                    │
                    ├── MUX (composite video + mixed audio)
                    │
                    ├── M3 QA GATE (frame audit, auto-fix, max 2 retries)
                    │
                    └── DELIVER
```

**Key principle (from M3):** VO is the master timeline anchor. All cut
durations, subtitle timings, and music sync derive from the VO, not from a
pre-planned shot list.

---

## Architecture — 12 modules (from M3 review)

| # | Module | What it does | Exists today? |
|:---|:---|:---|:---|
| 1 | `ingest-schema-validator` | Scrape tour URL → structured itinerary JSON. Validate schema. | ❌ (manual today) |
| 2 | `asset-fetcher` | Parallel stock fetch from Pexels (cache-aware, dedupe) | ✅ `clip_pool/fetch.py` |
| 3 | `asset-preflight` | Validate duration, codec, LUFS, license, checksum BEFORE timeline | ❌ (needed — prevents wrong-asset bugs) |
| 4 | `llm-tagger` | Schema-locked LLM content tags (temperature=0, pinned model) | ✅ `clip_pool/llm_tags.py` |
| 5 | `metrics` | Brightness/motion/shake per clip | ✅ `clip_pool/metrics.py` |
| 6 | `adapt` | Landscape→portrait crop with provenance | ✅ `clip_pool/adapt.py` |
| 7 | `judge-queue` | Async human judge, confidence-threshold auto-approve | ✅ `clip_pool/judge.py` (sync, needs async) |
| 8 | `tts-vo` | MiniMax TTS voiceover generation | ✅ `tour-video-finish/scripts/tts_vo.py` |
| 9 | `timeline-anchor` | VO as master clock → derives cut durations + subtitle timings | ❌ (the missing link — was manual) |
| 10 | `single-pass-renderer` | ffmpeg/Pillow composite: VO + footage + music + subs in ONE pass | ✅ `tour-video-finish/scripts/composite.py` |
| 11 | `m3-qa-gate` | Frame audit, structured checks, auto-remediation (max 2 retries) | ❌ (manual today — must automate) |
| 12 | `orchestrator` | Durable execution, retries, cost meter, SLA tracking | ❌ (the `produce` command) |

**What exists (7/12):** fetch, tag, metrics, adapt, judge, TTS, composite.
**What's missing (5/12):** ingest, preflight, timeline-anchor, QA-gate, orchestrator.

---

## The 3 highest-impact automations (build these FIRST)

M3 ranked these by ROI. All three eliminate classes of bugs we hit today:

### Priority 1: Single-pass compositor with VO as master clock
**Eliminates:** desync, lost subtitles, audio mix churn (3 of 5 reported bugs)

```
TTS generates VO → each segment's duration becomes the shot duration →
composite renders subs + logo + card in ONE pass → mix audio separately → mux
```

No multi-pass overlay chains. No planned-vs-actual duration mismatch. One
deterministic render.

### Priority 2: Schema-locked JSON contracts between every stage
**Eliminates:** SRT parser bug (1/8 cues), wrong outro content

Every stage emits schema-validated JSON. The next stage rejects invalid input.
The SRT parser bug happened because there was no contract — the parser
silently accepted malformed input. With a schema gate, it would have failed
loudly on cue #2.

```python
# Pydantic schema example
class ShotSegment(BaseModel):
    shot_id: str
    vo_text: str
    vo_duration_sec: float  # from TTS, drives the cut
    clip_id: str
    subtitle_text: str
```

### Priority 3: M3 QA gate as blocking checkpoint with auto-fix
**Eliminates:** delivering broken videos to the founder

Before ANY delivery:
1. Extract N frames at VO midpoints
2. Send to M3 vision: "subtitle visible? logo? errors?"
3. If errors → auto-fix (re-render, swap asset) → re-audit (max 2 retries)
4. All-clear → deliver

M3 caught 3 bugs today that the builder was blind to. Make it automatic.

---

## Mistakes to NOT repeat (from retrospective + M3)

| Mistake | Root cause | Fix |
|:---|:---|:---|
| VO/footage 16s desync | Cut to planned durations, not VO durations | TTS first → cut to VO |
| Subtitles lost in overlay chain | Multi-pass frame rewrites | Single-pass composite |
| SRT parser 1/8 cues | `re.split('\n\s*\n')` on multi-line text | Schema-validated parser |
| Wrong outro content | Assumed media content without inspecting | Asset preflight + M3 audit |
| Audio mix 4 iterations | Complex sidechain chain, no calibration log | Simple volume+loudnorm+amix + log corrections |
| No QA before delivery | Trust in the pipeline | M3 blocking gate |

---

## Scale risks for 100+ tours (from M3)

1. **Stock API rate limits** — add caching + dedupe layer
2. **LLM token cost** — model-tier routing (small model for tags, large for script)
3. **Human judge bottleneck** — confidence-threshold auto-approve (≥0.85 = auto, <0.85 = human)
4. **Asset storage growth** — TTL-based cleanup policy for raw stock + intermediates
5. **Model version drift** — pin LLM/M3 versions, regression-test on known-good output
6. **No render-failure recovery** — one bad clip kills the whole tour. Needs partial-render recovery.

---

## File map for Cursor/GLM-5.2

```
videogen/
  clip_pool/                    ← EXISTS: fetch, tag, metrics, adapt, judge
    fetch.py                    ✅ Pexels multi-candidate fetcher
    llm_tags.py                 ✅ MiniMax M3 content tagger
    metrics.py                  ✅ brightness/motion/shake
    adapt.py                    ✅ landscape→portrait + provenance
    judge.py                    ✅ human verdict capture (needs async queue)
    composite.py                ✅ single-pass overlay renderer

  produce.py                    ← BUILD: the one-command orchestrator
  ingest.py                     ← BUILD: tour URL → itinerary JSON
  preflight.py                  ← BUILD: asset validation gate
  timeline.py                   ← BUILD: VO → master clock → cut/sub timings
  qa_gate.py                    ← BUILD: M3 frame audit + auto-fix loop

.agents/skills/tour-video-finish/
  scripts/
    finish.py                   ✅ orchestrator (4-step, needs VO-first reorder)
    tts_vo.py                   ✅ MiniMax TTS
    mix_audio.py                ✅ VO + music mix
    composite.py                ✅ single-pass subs + logo + card

  references/
    ech-brand-guide.md          ✅ design tokens
    music-direction.md          ✅ music brief
    vo-direction.md             ✅ VO casting + recording spec

docs/
  LOOP-STRATEGY.md              ✅ the small-circles thesis
  LOOP-DIAGRAMS.md              ✅ 6 Mermaid diagrams
  VIDEO-AUTOMATION-SETUP.md     ← you are here
```

---

## The M3 verdict

> "The pipeline is brittle because it treats stages as a DAG of hopes instead
> of a schema-validated, frame-locked, single-pass contract — fix the render
> and contracts first, everything else falls in line."

Translation for Cursor/GLM-5.2:
1. Build the schema contracts first (Pydantic models between every stage)
2. Make VO the master clock (TTS → durations → cut → subtitles all derive from VO)
3. One render pass (never chain frame-level operations)
4. M3 QA gate before delivery (always)
5. Then automate the human judge with confidence thresholds

Do those four things and the pipeline goes from "11.5 hours of debugging" to
"one command, one video, one audit, ship."
