# Fully Automatic Video Flow — ECH to Delivered Video

> Can the whole thing run from "ECH has a tour" to "video is published" with
> zero human steps? **Yes — here's the map of what's automatic, what's manual
> today, and what closes the gap.**

---

## The fully automatic flow (the target state)

```
                    ECH ADMIN (one click)
                    "Generate video for this tour"
                           │
                           ▼
              ┌─ ECH: BUILD BRIEF ──────────────────┐
              │ scrape tour page                     │
              │ pull knowledge library refs          │
              │ write brief.yaml                     │
              │ drop into handoff/ dir               │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HANDOFF (file seam) ───────────────┐
              │ brief.yaml appears in handoff/       │
              │ (no API call, no DB — just a file)   │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: INGEST ───────────────────┐
              │ read brief.yaml                      │
              │ extract itinerary from tour URL      │
              │ write VO script (grounded in          │
              │   ECH's knowledge library, not        │
              │   LLM invention)                     │
              │ generate keywords.yaml               │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: FETCH + ANALYZE ──────────┐
              │ Pexels stock fetch (auto)            │
              │ PySceneDetect (auto — scene cuts)    │
              │ M3 content tags (auto)               │
              │ opencv metrics (auto)                │
              │ landscape→portrait adapt (auto)      │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: TTS VOICEOVER ────────────┐
              │ MiniMax speech-2.8-hd                │
              │ VO IS THE MASTER CLOCK                │
              │ each segment's duration = shot dur   │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: COMPOSE EDL ──────────────┐
              │ rank clips → select best per shot    │
              │ assign VO segments → generate EDL    │
              │ (if model confidence ≥0.85:          │
              │   auto-approve, no human needed)     │
              │ (if model confidence <0.85:          │
              │   FLAG for human review — exception) │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: RENDER ───────────────────┐
              │ composite: subs + logo + card        │
              │   (ONE pass — never chain)            │
              │ mix audio: VO + music                 │
              │ ffmpeg execute EDL                    │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: QA GATE ──────────────────┐
              │ M3 frame audit (auto)                │
              │ subs visible? logo present? errors?  │
              │ auto-fix if errors (max 2 retries)   │
              │ PASS → continue                      │
              │ FAIL → flag for human (exception)     │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HIVEAGI: WRITE RESULT ─────────────┐
              │ result.json + edl.json + mp4s        │
              │ media_provenance (every asset)       │
              │ drop into handoff/ dir               │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ HANDOFF (file seam) ───────────────┐
              │ result.json appears in handoff/      │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ ECH: ACA GATE ─────────────────────┐
              │ verify media_provenance              │
              │ (Golden Rule: no un-provenanced      │
              │  assets)                              │
              │ PASS → continue                      │
              │ FAIL → flag for human (exception)     │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ ECH: PUBLISH ──────────────────────┐
              │ YouTube (auto — API)                 │
              │ Facebook (auto — API)                │
              │ Instagram (auto — API)               │
              │ website embed (auto — CMS)           │
              └──────────────┬───────────────────────┘
                             ▼
              ┌─ ECH: ANALYTICS ────────────────────┐
              │ track views, engagement              │
              │ feed back to knowledge library       │
              │ (which clips performed best →         │
              │  future briefs prefer them)          │
              └───────────────────────────────────────┘
```

**Zero human steps in the happy path.** Humans only touch it when:
- Model confidence <0.85 (uncertain clip selection)
- QA gate fails twice (rendering problem)
- ACA gate rejects (provenance problem)

These are **exceptions**, not the default flow.

---

## What's manual TODAY vs what's automatic

| Stage | Today (Circle F) | Target (Circle G) | Gap |
|:---|:---|:---|:---|
| Create brief | ❌ Manual (write keywords.yaml by hand) | ✅ Auto (scrape tour URL → brief.yaml) | Build `ingest.py` |
| Fetch clips | ✅ Auto (`clip_pool fetch`) | ✅ Auto | Done |
| Scene detect | ❌ Not installed | ✅ Auto (PySceneDetect) | `pip install scenedetect` |
| LLM tags | ✅ Auto (`llm_tags.py`) | ✅ Auto | Done |
| Metrics | ✅ Auto (`metrics.py`) | ✅ Auto | Done |
| Adapt portrait | ✅ Auto (`adapt.py`) | ✅ Auto | Done |
| Judge clips | ❌ Manual (human reviews all) | ✅ Auto (model ≥0.85 auto-approve; <0.85 → human) | Build confidence scoring |
| TTS voiceover | ✅ Auto (`tts_vo.py`) | ✅ Auto | Done |
| Compose EDL | ❌ Manual (cut.py uses fixed plan) | ✅ Auto (timeline.py: VO durations → EDL) | Build `timeline.py` + `edl.py` |
| Render | ⚠️ Semi-auto (multi-step, manual order) | ✅ Auto (produce.py orchestrates) | Build `produce.py` |
| QA audit | ❌ Manual (human watches video) | ✅ Auto (M3 frame audit + auto-fix) | Build `qa_gate.py` |
| Write result | ❌ Manual | ✅ Auto (produce.py writes result.json) | Build in `produce.py` |
| ACA provenance | ❌ Manual | ✅ Auto (result.json has media_provenance) | Schema exists, needs wiring |
| Publish | ❌ Manual (upload by hand) | ✅ Auto (YouTube/Meta APIs) | ECH side |
| Analytics | ❌ None | ✅ Auto (views → feedback loop) | ECH side, Phase 3 |

**Score: 6 of 15 stages automatic today. Target: 15 of 15.**

---

## The three phases to fully automatic

### Phase 1: One-command pipeline (HiveAGI side — H1–H7)
The build plan in `VIDEO-PIPELINE-BUILD-PLAN.md`. After this:

```bash
python -m videogen produce --tour-url <URL> --out final.mp4
```

Works end-to-end. Human only intervenes on low-confidence clips or QA failures.

### Phase 2: ECH triggers automatically
After Phase 1, wire the ECH admin panel to:
1. Click "generate video" on a tour page
2. ECH writes brief.yaml → drops in handoff/
3. HiveAGI produce picks it up (cron or file watcher)
4. Result drops back in handoff/
5. ECH ACA gate checks provenance
6. If pass → auto-publish to YouTube/Facebook/Instagram

**No human in the loop unless an exception fires.**

### Phase 3: Learning loop (the wave)
After Phase 2, the system feeds back:
- Which clips the human overrode (override delta → preference signal)
- Which videos performed best on YouTube (analytics → knowledge library)
- Which clip choices the model got wrong (active learning → better auto-approve)

Over time, the auto-approve threshold rises (fewer human interventions).
The wave builds. The system gets more autonomous.

---

## The key automation decisions

### 1. Auto-approve threshold (the human-in-the-loop boundary)
```python
if model_confidence >= 0.85:
    auto_approve(clip)      # no human needed
else:
    flag_for_review(clip)   # human sees only the edge cases
```

Start at 0.85. As the model accumulates judgments, raise it. The system
becomes more autonomous as it earns trust.

### 2. VO drives everything (no planned durations)
The #1 bug was desync. The fix is structural: TTS generates VO first, each
segment's duration becomes the shot duration. No human plans durations.
The voice sets the pace.

### 3. EDL is the single source of truth
The AI generates edl.json. The renderer executes it. The QA gate validates
against it. The human can override it. Everything flows from the EDL.

### 4. Provenance is non-optional
Every asset in the result carries source + license + authenticity. If it
doesn't, the ACA gate rejects. No exceptions. This is the Golden Rule.

---

## What "fully automatic" does NOT mean

- **Does not mean zero human ever.** It means the human is an exception
  handler, not a step in the pipeline. The system runs itself; humans weigh
  in only when confidence is low or quality fails.
- **Does not mean the AI is always right.** The override signal (where the
  human corrects the AI) is the most valuable data the system produces.
  Full automation reduces the volume of overrides but increases their value
  (each one is a high-signal correction).
- **Does not mean no review.** The ACA gate (provenance) and QA gate (quality)
  are mandatory. They're automated, but they block delivery on failure.

---

## The one-click future

```
ECH admin clicks "Generate Video"
    → brief.yaml written
    → HiveAGI produces video (fetch, tag, TTS, cut, finish, QA)
    → result.json + mp4s returned
    → ACA gate verifies provenance
    → auto-published to YouTube + Facebook + Instagram
    → analytics tracked
    → preferences learned for next tour
```

**One click. Tour page in, published video out. Humans only see exceptions.**
