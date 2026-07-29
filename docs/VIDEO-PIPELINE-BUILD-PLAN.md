# VIDEO-PIPELINE-BUILD-PLAN.md

> **Status:** Build plan for the HiveAGI seat. No production code written yet.
> **Companion to:** `docs/CURSOR-HANDOFF.md` (the retrospective + bug rules) and the ECH-side
> `VIDEO-AUTOMATION-AUDIT.md` v2 (the two-repo split + seam contracts).
> **Written:** 2026-07-30 by the ECH engineer seat, after verifying HiveAGI's actual state.
> **Verified state source:** the state audit at `[HiveAGI state audit](b8212dfd-45e4-4e5f-86a8-00409d1617e5)`.
>
> **Goal:** turn HiveAGI from "a human can drive it to a shipped video" into
> `python -m videogen produce --tour-url <URL> --out <mp4>` — one command, end-to-end,
> honoring the 6 Circle F bug rules and the parallel-run seam contract.

---

## 1. Where HiveAGI actually is (verified 2026-07-30)

The handoff doc says "7 of 12 skills working." Verified true. But the handoff also implies
the one-command `produce` is close. **It is not.** Confirmed missing:

- `videogen/produce.py` — the orchestrator
- `videogen/timeline.py` — the EDL generator (VO → cut)
- `videogen/qa_gate.py` — the M3 frame audit gate
- `videogen/wiki_export.py` — Obsidian export (Phase 2)
- `videogen/ingest.py` URL-scraper — the file exists but is ffprobe-only; needs rewrite
- `scenedetect` package — not installed
- EDL.json schema — designed in `CURSOR-HANDOFF.md` §3 but unimplemented

**What works today** (verified): `clip_pool/{fetch,llm_tags,metrics,adapt,judge}`,
`videogen/make` (silent draft), `tour-video-finish/finish.py` (VO+music+subs+endcard),
`selection_log.py` (override capture), `provenance.py` (Labs gate). One tour shipped:
`forge-output/legends-of-china-warriors/` (landscape + vertical MP4s).

---

## 2. The seam contract (mirror of ECH audit §3 — do not drift)

Both repos honor `schema_version`. Parser rejects unknown versions loudly.

### 2.1 Input (ECH → HiveAGI): `handoff/brief.yaml`

```yaml
schema_version: 1
tour_slug: legends-of-china-warriors
tour_url: https://www.explorechinaholidays.com.au/tours/legends-of-china-warriors/
title: "Legends of China & the Warriors"
duration_target_sec: 50
platforms: [youtube, facebook, instagram]
aspect_ratios: [16:9, 9:16]      # which cuts to produce
language: en-AU
voice: warm_calm_au
voice_model: English_expressive_narrator  # MiniMax voice_id
music_mood: cinematic_warm
cta_text: "Explore our China tours"
cta_url: https://www.explorechinaholidays.com.au/tours/
library_refs:
  - destinations/beijing-great-wall.md
  - destinations/xian.md
clip_hints:
  - scene: hook
    prompt: "dawn over the Great Wall, calm, drone shot"
    duration_sec: 5
branding:
  logo_url: <local path or URL>
  endcard_url: <local path or URL>
```

### 2.2 Output (HiveAGI → ECH): `handoff/result.json`

```json
{
  "schema_version": 1,
  "tour_slug": "legends-of-china-warriors",
  "status": "delivered",
  "video": {
    "landscape_mp4_path": "...",
    "vertical_mp4_path": "...",
    "duration_sec": 52.3
  },
  "edl": "<path to edl.json>",
  "selection_log": "<path to selection_log.jsonl>",
  "qc_report": "<path to qc_report.json>",
  "cost_usd": 1.87,
  "override_count": 3,
  "media_provenance": [
    {"shot_id": "shot1_hook", "source": "pexels", "asset_id": "35834780",
     "licence": "Pexels", "authenticity": "stock"}
  ]
}
```

### 2.3 Internal: `edl.json` (the Edit Decision List)

The HiveAGI-internal contract that `timeline.py` writes and `compose` + `finish` read:

```json
{
  "schema_version": 1,
  "tour": "legends-of-china-warriors",
  "total_duration_sec": 52.3,
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
      "human_override": null,
      "human_clip_start_sec": null,
      "human_clip_end_sec": null
    }
  ]
}
```

**Golden Rule evidence (ECH audit §1):** every `media_provenance` entry MUST carry a
`source` (`pexels` | `ai_generated` | `company_owned`), a `licence`, and an `authenticity`
tag (`stock` | `illustrative` | `documentary`). The ECH ACA gate rejects videos with
un-provenanced assets. This is non-negotiable per the spec's Golden Rule.

---

## 3. Build order (H1–H7)

Dependency-respecting. Each module lands with a test against a fixture.

### H1 — `videogen/edl.py` + `docs/edl-schema.md`

**Why first:** every downstream module reads or writes the EDL. The schema is the
keystone. Designing it first prevents rework.

**Deliverable:**
- `videogen/edl.py` — `EDL` dataclass, `load_edl(path)`, `write_edl(edl, path)`,
  `validate_edl(edl) → list[errors]`. Validates: schema_version, shot_id unique,
  durations sum to total_duration_sec (±0.5s tolerance for xfades), every shot has a
  source_path or human_override, every shot has vo_segment OR is marked silent.
- `docs/edl-schema.md` — the canonical schema doc (copy §2.3 above + field-by-field
  semantics).

**Test:** `tests/test_edl.py` — load the golden fixture, validate passes; mutate each
field, confirm the validator catches it.

**Bug rules honored:** none directly (this is the contract).

### H2 — Rename `videogen/ingest.py` → `videogen/probe.py`; build new `ingest.py`

**Why:** the current `ingest.py` is ffprobe frame-sampling. That's a probe, not an ingest.
Reclaim the name for the URL→brief converter the handoff demands.

**Deliverable:**
- `git mv videogen/ingest.py videogen/probe.py`. Update its one internal caller
  (`videogen/cli.py` stage 1 invocation).
- New `videogen/ingest.py`:
  - `fetch_tour_page(url) → html`
  - `extract_itinerary(html) → {cities, attractions, days, title}`
  - `write_script(itinerary, clip_hints) → vo_script` (the VO text, segmented by scene)
  - `build_keywords_yaml(itinerary, clip_hints) → keywords.yaml` (for `clip_pool fetch`)
  - `ingest(tour_url) → (keywords.yaml path, script.json path)`
- Reads the `library_refs` and `clip_hints` from `brief.yaml` so the script is grounded in
  ECH's verified facts, not LLM invention.

**Test:** `tests/test_ingest.py` — fetch a cached copy of a real tour page (commit a fixture
HTML), confirm extracted itinerary matches expected. No live network in unit tests.

**Bug rules honored:** none directly.

### H3 — `videogen/timeline.py` (VO is master clock — bug #1)

**Why:** the #1 bug was VO/footage desync because cuts were planned to arbitrary durations.
VO drives the cut.

**Deliverable:**
- `generate_vo(script, voice) → [(segment_text, mp3_path, duration_sec), ...]` — calls
  MiniMax `speech-2.8-hd` via the existing `tour-video-finish/scripts/tts_vo.py` logic.
  **Per-segment, not one big file**, so each shot's VO duration is measurable.
- `build_edl(script_segments, pool_manifest, ranker_selection) → EDL` — assigns each VO
  segment to a selected clip, sets `duration_sec = vo_duration_sec` (NOT the clip's native
  duration), sets `clip_start_sec`/`clip_end_sec` to the best window from `metrics.py`.
- `write_edl(edl, path)` — to `<work_dir>/edl.json`.

**Test:** `tests/test_timeline.py` — given a synthetic script + synthetic segment
durations, confirm the EDL's `sum(duration_sec) == sum(vo_duration_sec)` exactly.

**Bug rules honored:** #1 (VO drives cut).

### H4 — `videogen/produce.py` (orchestrator — bugs #2, #3, #5)

**Why:** this is the one-command entry point. It calls everything else in order.

**Deliverable:**
```python
# videogen/produce.py (sketch)
def produce(brief_yaml_path, out_mp4_path, work_dir):
    brief = load_brief(brief_yaml_path)
    # 1. ingest
    keywords, script = ingest.ingest(brief.tour_url, brief.library_refs, brief.clip_hints)
    # 2. fetch + analyze + judge (existing clip_pool)
    pool = clip_pool.fetch(keywords)
    clip_pool.pretag(pool)
    clip_pool.metrics(pool)
    clip_pool.adapt(pool, target="9:16")
    # 3. timeline (VO → EDL)
    edl = timeline.build(keywords, script, pool, brief.voice)
    # 4. compose (existing compose.py, now EDL-driven)
    draft = compose.render(edl, work_dir)
    # 5. finish (existing tour-video-finish)
    final = finish.run(draft, edl, brief.music, brief.branding, out_mp4_path)
    # 6. QA gate
    qc = qa_gate.audit(final, edl)
    if qc.decision != "PASS":
        qc = qa_gate.autofix(final, edl, qc, max_retries=2)
    # 7. write return package
    write_result_json(brief, final, edl, qc, work_dir)
```

- CLI registration: add `produce` subcommand to `videogen/cli.py:205-237`.
- **Single-pass composite only** (bug #2) — never chain overlay passes.
- **SRT split on index numbers** (bug #3) — audit `tour-video-finish/scripts/burn_subtitles.py`
  and confirm/fix the parser.
- **Simple audio mix** (bug #5) — `volume + loudnorm + amix` with the calibrated settings
  from `CURSOR-HANDOFF.md` §9 (VO_VOLUME=1.65, MUSIC_VOLUME=0.48, etc.). No sidechain.

**Test:** `tests/test_produce.py` — smoke test with mock providers (mock MiniMax, mock
Pexels, mock ffprobe). Confirms the orchestrator wires stages in the right order and writes
a valid `result.json`. The real end-to-end is a separate integration test (H7).

**Bug rules honored:** #2, #3, #5.

### H5 — `videogen/qa_gate.py` (bug #6)

**Why:** the #6 bug was shipping without QA. The M3 frame audit is the blocking gate.

**Deliverable:**
- `audit(mp4_path, edl) → QCReport`:
  - Sample N frames (every 2s) → MiniMax M3 vision: "are subtitles visible? is the logo
    visible? any black frames? any obvious AI defects?"
  - Check SRT cues vs EDL subtitle_text (every cue present and in-window).
  - Check duration matches EDL total ±0.5s.
  - Return `{overall_score, factual_accuracy, visual_relevance, readability,
    brand_consistency, audience_fit, issues[], decision}` per spec §17.
- `autofix(mp4_path, edl, qc, max_retries=2)`:
  - If subs missing → re-burn from EDL.
  - If logo missing → re-composite.
  - If audio clipped → re-mix with conservative levels.
  - Max 2 retries; then `decision = FAIL` and `result.json.status = qc_failed`.

**Test:** `tests/test_qa_gate.py` — given a known-good mp4 (from
`forge-output/legends-of-china-warriors/`) → PASS; given a mp4 with subs stripped → FAIL
with the right issue code.

**Bug rules honored:** #6.

### H6 — Install `scenedetect[opencv]`

```bash
pip install scenedetect[opencv]
```

Per `CURSOR-HANDOFF.md` §7. Reduces M3 vision calls ~75% by detecting scene boundaries
algorithmically before the expensive LLM tag step. Wire into `clip_pool/metrics.py` or
`clip_pool/llm_tags.py` as a pre-filter.

### H7 — Contract tests at the seam

**Deliverable:**
- `tests/fixtures/ech-brief.yaml` — a synthetic but realistic brief (the legends tour).
- `tests/fixtures/expected-result.json` — the expected shape of the return package.
- `tests/test_seam_contract.py`:
  - `test_brief_parses`: load `ech-brief.yaml`, confirm all required fields present.
  - `test_result_writes`: after a produce run, confirm `result.json` matches the schema.
  - `test_schema_version_rejected`: load a brief with `schema_version: 99`, confirm
    `ingest` rejects it with a clear error.

These tests are the **parallel-run guarantee**. The ECH repo will ship mirror fixtures; if
either side drifts, both sides' CI catches it.

---

## 4. Phase 1 acceptance (HiveAGI side)

Phase 1 (HiveAGI) is complete when:

1. `python -m videogen produce --tour-url <real-tour-url> --out final.mp4` works end-to-end.
2. The output `result.json` validates against the §2.2 schema.
3. `media_provenance` is populated for every shot — no un-provenanced assets.
4. `qa_gate` PASS rate on re-running the legends tour >70% (the §42 target).
5. The 6 bug rules are demonstrably honored (test coverage for each).
6. `tests/test_seam_contract.py` passes against the ECH-side fixtures.

**Not in Phase 1:** `wiki_export.py` (Phase 2), `media_analyzer` auto-tagging of uploads
(Phase 2), analytics (Phase 3), learning loop (Phase 4).

---

## 5. Parallel-run guarantees with ECH (owner directive)

| Concern | Guarantee |
|---|---|
| Shared mutable state | None. HiveAGI and ECH communicate only via files in `handoff/`. |
| Contract drift | `schema_version` on every file. Parser rejects unknown versions. |
| ECH blocked → HiveAGI still runs | HiveAGI ships `tests/fixtures/ech-brief.yaml` and runs `produce` against it without ECH existing. |
| HiveAGI blocked → ECH still runs | ECH ships `scripts/mock-hiveagi-return.sh` writing a synthetic `result.json`. ECH video-bridge, admin UI, ACA gate all exercise against the mock. |
| Credentials | HiveAGI holds MiniMax/Pexels/DeepSeek keys. ECH holds YouTube/Meta publish tokens. No key crosses the seam. |

---

## 6. What this plan does NOT do

- Does not modify `provenance.py` (the Labs gate) without understanding it — flagged as
  "THE GATE" in `CURSOR-HANDOFF.md` §5. Leave alone in Phase 1.
- Does not build `wiki_export.py` (Phase 2).
- Does not add TikTok or long-form horizontal (Phase 5+).
- Does not change the audio/subtitle/logo calibrated settings in
  `tour-video-finish/scripts/` — those are battle-tested per §9–11 of the handoff.
- Does not touch the ECH repo — that's the other seat's job per ECH audit §6.

---

## 7. First task (per CURSOR-HANDOFF.md §14, refined)

Start with H1 (the EDL schema). It's the keystone contract. Then H3 (timeline, because
VO-is-master-clock is the #1 bug rule and timeline is where it's enforced). Then H2 (ingest
rewrite), H4 (produce orchestrator), H5 (QA gate), H6 (scenedetect), H7 (contract tests).

Do NOT start with H4 (produce) — the handoff says "build produce + ingest + timeline first"
but produce is the *last* thing to wire because it depends on the others. Building it first
leads to stubs that get rewritten.

---

## 8. Contract review notes (2026-07-30)

Reviewed all three seam contracts before commit. Changes applied:

| Contract | Field added | Why |
|:---|:---|:---|
| `brief.yaml` | `aspect_ratios: [16:9, 9:16]` | ECH may only want vertical for IG — don't produce unused cuts |
| `brief.yaml` | `voice_model: English_expressive_narrator` | Maps the voice label to the actual MiniMax voice_id |
| `edl.json` | `human_clip_start_sec`, `human_clip_end_sec` | Human can override the in/out point within a clip, not just the clip choice — richer override signal for active learning |
| `result.json` | `override_count: 3` | Quick signal of how much the AI was corrected, without reading full selection_log |

No other changes. The contracts are solid. The versioned-file seam, mock-at-seam, and golden-file test pattern are all correct.

## 9. Sources

- `docs/CURSOR-HANDOFF.md` — the retrospective + bug rules + design intent.
- ECH-side `VIDEO-AUTOMATION-AUDIT.md` v2 — the two-repo split + seam contracts (mirror).
- Verified state audit: `[HiveAGI state audit](b8212dfd-45e4-4e5f-86a8-00409d1617e5)`.
