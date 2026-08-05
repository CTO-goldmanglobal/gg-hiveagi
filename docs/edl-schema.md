# EDL Schema — the Edit Decision List

> **Canonical schema for `edl.json`** — the HiveAGI-internal contract that
> `timeline.py` writes and `compose` + `finish` + `qa_gate` read. Every
> downstream module depends on this file being correct.
>
> This document incorporates three corrections from the OpenAI + DeepSeek
> audits (2026-08-04/05) that the original `VIDEO-PIPELINE-BUILD-PLAN.md` H1
> did not have. See §2–4 below.
>
> **Implementation:** `videogen/edl.py` (pydantic v2 models + validator).
> **Tests:** `videogen/test_edl.py` (25 tests, including the time-equation proof).

---

## 1. The schema

```json
{
  "schema_version": 1,
  "tour": "legends-of-china-warriors",
  "total_duration_sec": 17.5,
  "edl": [
    {
      "shot_id": "shot1_hook",
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
      "human_clip_end_sec": null,
      "provenance": {
        "source": "pexels",
        "asset_id": "35834780",
        "licence": "Pexels",
        "authenticity": "stock"
      },
      "silent": false
    }
  ]
}
```

### Field semantics

| Field | Type | Required | Meaning |
|:---|:---|:---|:---|
| `schema_version` | int | yes | Must be `1`. |
| `tour` | str | yes | Tour slug. |
| `total_duration_sec` | float | yes | **Derived from `max(timeline_start + duration)`**, not from summing. See §2. |
| `edl` | list[Shot] | yes | Non-empty. |
| `shot_id` | str | yes | Unique within the EDL. |
| `source_path` | str | conditional | Required unless `human_override` is set. |
| `clip_start_sec` / `clip_end_sec` | float | yes | Which segment of the source clip is used. `clip_end - clip_start >= duration_sec`. |
| `timeline_start_sec` | float | yes | Where the shot sits in the final video. First shot must be `0.0`. |
| `duration_sec` | float | yes | The shot's visual duration. |
| `vo_segment` | str | conditional | VO audio file. Required unless `silent: true`. |
| `vo_duration_sec` | float | optional | Must be `<= duration_sec` (VO fits in the shot). |
| `subtitle_text` | str | optional | The on-screen subtitle for this shot. |
| `transition` | object | yes (default cut) | The transition OUT of this shot. `type: xfade|cut`, `duration_sec`. |
| `purpose` | str | optional | Human-readable intent. |
| `ai_reason` | str | optional | Why the AI picked this clip (for audit/review). |
| `human_override` | str | optional | If a human replaced the AI's choice, the reason. |
| `human_clip_start_sec` / `human_clip_end_sec` | float | optional | If a human adjusted the in/out points. |
| `provenance` | object | yes (Golden Rule) | `source`, `asset_id`, `licence`, `authenticity`. See §5. |
| `silent` | bool | default false | If true, no VO required for this shot. |

---

## 2. AUDIT FIX #1 — the time equation (H1, critical)

### The bug

The original build plan said: *"durations sum to total_duration_sec."*

This is **wrong** when crossfades overlap. With transitions:

```
total = Σd_i − Σx_i          (d = shot duration, x = crossfade overlap)
```

When each shot's duration equals its VO duration, the rendered video is shorter
than the VO track by the total transition overlap → VO/footage desync. This is
the exact 16-second desync Circle F bled on.

### The fix

The validator derives total from timeline **positions**, not from summing:

```python
timeline_start[0] = 0
timeline_start[i+1] = timeline_start[i] + duration_sec[i] - transition_overlap[i]
total_duration = max(timeline_start[i] + duration_sec[i])
```

Implemented in `videogen/edl.py::compute_total_duration()` and enforced by
`validate_edl()`. A test explicitly proves that a crossfade EDL passes with
`max(start+dur)` and fails with the naive sum.

### Design rules

- Voice cue windows remain **non-overlapping** (each VO segment is within its
  shot's duration).
- Visual shots receive **transition handles** before and after the voice window.
- `timeline_start_sec` is **authoritative** — the validator derives total from it.
- Source clips must have **sufficient handle length**: `clip_end - clip_start >= duration_sec`.
- Audio and visual duration are **validated separately**: VO duration must not
  exceed shot duration.

---

## 3. AUDIT FIX #2 — three-layer QA (H5, when built)

The QA gate must not be self-referential. If the same model family runs tagging,
selection, and final QA, correlated blind spots pass through all stages.

Three layers (to be implemented in `videogen/qa_gate.py`, H5):

1. **Deterministic** (no model): duration; black-frame detection; silence and
   clipping; subtitle timing + safe-area bounds; logo presence; output
   resolution; codec and bitrate; **provenance completeness**; file readability.
2. **Model-based** (MiniMax M3): visual relevance; obvious synthetic defects;
   subtitle legibility; audience fit; visual-brand consistency.
3. **Independent sample audit** (second model or human): reviews a sample;
   factual claims checked against tour brief + verified library references;
   disagreements stored as calibration data.

> **A model score must never override a deterministic provenance failure.**

If the deterministic layer finds a missing licence, the video is rejected — no
matter how high M3 scores the visual quality. This is the same principle as the
provenance gate: honest labeling is non-negotiable; quality judgment is layered
on top.

---

## 4. AUDIT FIX #3 — brief as canonical input (H4, when built)

The stated goal `produce --tour-url <URL> --out <mp4>` cannot work alone — a URL
cannot provide aspect ratios, language, voice model, library refs, clip hints,
branding, platform list, CTA, music mood. Those live in `brief.yaml`.

**Canonical interface:**
```bash
python -m videogen produce --brief handoff/brief.yaml --out-dir forge-output/<slug>
```

A `--tour-url <URL> --preset ech-default` convenience may remain, but it must
**generate and persist an explicit brief** showing every default it selected.
"One command" means one orchestrated entry point, not an opaque black box.
Every stage remains independently replayable from the persisted brief + EDL.

The `brief.yaml` schema is defined in `VIDEO-PIPELINE-BUILD-PLAN.md §2.1`.

---

## 5. Provenance gap (Gate 1 work — not H1, but documented here)

The EDL provenance uses `source: pexels | ai_generated | company_owned | human_capture`
and `authenticity: stock | illustrative | documentary`. The project's main
provenance module (`videogen/provenance.py`) uses `source_type: stock | ai_generated
| human_capture` and `area: open | commercial`. These are **related but not
interchangeable** — the v3 architecture (§3) calls for unification to four
dimensions:

```
origin:              human_capture | company_owned | licensed_stock | ai_generated | mixed
transformation:      untouched | cropped | colour_adjusted | narrated | composited | ...
presentation_claim:  documentary | representative | illustrative | synthetic
eligibility:         labs_allowed | forge_only | private_dev_only
```

Until that unification (Gate 1), the EDL carries its own per-shot provenance
and the validator enforces the **Golden Rule**: every shot must have `source` +
`licence` + `authenticity`. This is a contract check, not a security gate — the
Labs ingestion service is the real boundary (v3 §3).

---

## 6. Validation rules (enforced by `validate_edl`)

1. `schema_version == 1`
2. `edl` is non-empty
3. All `shot_id`s unique
4. Shots sorted by `timeline_start_sec`; first shot starts at `0.0`
5. Timeline consistency: each shot's start = prev start + prev duration − prev overlap
6. **`total_duration_sec == max(timeline_start + duration)`** (the fix)
7. Each shot has `source_path` or `human_override`
8. Each shot has `vo_segment` or `silent: true`
9. Each shot has `provenance` (Golden Rule)
10. Clip handles: `clip_end - clip_start >= duration_sec`
11. VO fits: `vo_duration_sec <= duration_sec`
