# Selection Rationale Schema (v1)

> What this IS, what it ISN'T, and the exact data format.

## What this IS

**Editor selection rationale** — the delta between the model's proposed
frame ranking and what a human editor actually shipped.

The valuable signal is **not** "the ranker picked frame X." The ranker is
an LLM; its picks are model judgments. The valuable signal is **where the
human editor overruled the model** — promoted a frame, demoted it, cut it,
or added one the model never selected. That delta is a preference pair
with a model baseline attached: precisely what preference-data buyers
want, and what no scraped video corpus contains.

## What this ISN'T (yet)

- **Not "beauty data."** The ranker isn't selecting beautiful frames; it's
  selecting frames that sell a 45-second tourism reel to a specific
  audience. That's narrower, more defensible, and more valuable than an
  abstract "beauty" label. Calling it "beauty definition AGI" invites the
  philosophical argument; calling it "what a tourism editor picks for this
  audience, and where they overrule the model" invites the interesting one.
- **Not cross-editor aggregation.** v1 captures per-run decisions. Cross-
  editor age/culture comparison (the stated long-term goal) needs multiple
  editors, each identified, across many runs. The `editor_id` field exists
  in v1 precisely so this option is preserved — every row is attributable
  from day one.
- **Not auto-published to Labs Seed Packages.** Manual for now, with PII
  review required first (see PII section below).

## The two taxonomies

Two different axes are logged per frame. Don't conflate them.

| Field | Axis | Question it answers | Values |
| :--- | :--- | :--- | :--- |
| `shot_type` | **Content** | What's in the frame? | `landscape` / `architecture` / `people` / `detail` / `food` / `action` |
| `trigger_type` | **Salience** | Why was it captured? | `aesthetic_gaze` / `anomaly_detection` / `professional_judgment` / `manual` / `other` (from Hive's RawData schema) |

`shot_type` tells you the subject; `trigger_type` tells you the capture
intent. Both matter for understanding editorial choice.

## selection_log.jsonl — one line per frame (kept AND cut)

```json
{
  "schema_version": 1,
  "run_id": "ech_20260728_143022",
  "editor_id": "founder",
  "config": "ech",

  "frame_index": 7,
  "ranker_rank": 3,
  "ranker_reason": "Strong architectural detail, golden hour light",
  "ranker_shot_type": "architecture",

  "final_rank": 1,
  "human_action": "promoted",
  "human_reason": "guide's face reads warmer than the tower",

  "trigger_type": "aesthetic_gaze",
  "frame_analysis_summary": "Forbidden City corner tower at sunset...",
  "source": {"clip": "beijing_day1.mp4", "timestamp_sec": 35.0},
  "timestamp": "2026-07-28T14:30:22Z"
}
```

### `human_action` values

| Value | Meaning | ranker_rank | final_rank |
| :--- | :--- | :--- | :--- |
| `accepted` | Editor kept the frame at the model's rank | N | N (same) |
| `promoted` | Editor moved the frame up in the order | N | < N |
| `demoted` | Editor moved the frame down in the order | N | > N |
| `rejected` | Model kept it, editor cut it | N | null |
| `added` | Model cut it, editor added it back | null | N |
| `rejected_by_both` | Neither model nor editor wanted it | null | null |

`human_action != "accepted"` is the override signal — the preference data.

### Field semantics

- `ranker_rank`: 1-based position in the model's proposed ranking. `null` if the model didn't select this frame.
- `final_rank`: 1-based position in the editor's shipped reel. `null` if the editor cut it.
- `ranker_reason` / `ranker_shot_type`: from the model's ranking output (only present for frames the model selected).
- `human_reason`: free-text, optional. Editors may skip this; the action alone (promoted/demoted/rejected/added) is the structured signal.
- `frame_analysis_summary`: truncated (≤200 char) copy of the Labs vision analysis — for human review of the log, not for model training directly.

## selection_summary.json — per-run aggregate

```json
{
  "schema_version": 1,
  "run_id": "ech_20260728_143022",
  "editor_id": "founder",
  "config": "ech",
  "total_frames": 60,
  "ranker_kept": 8,
  "final_kept": 7,
  "overrides": 3,
  "override_types": {"promoted": 1, "demoted": 1, "rejected": 1, "added": 0},
  "shot_type_distribution_final": {"architecture": 3, "landscape": 2, "people": 1, "detail": 1}
}
```

## PII — read before publishing

Selection logs inherit Hive.AGI's PII rules (see `CONTRIBUTING.md` § Privacy & PII).

- **`source.clip`** filenames can leak client identity, filming location, and
  date (`beijing_day1.mp4` tells you the city and that it's early in a trip).
- **`source.timestamp_sec`** combined with `clip` can identify a specific
  moment in footage that may contain identifiable people (even after PII
  blur, the *context* around a frame can be identifying).
- **`frame_analysis_summary`** may paraphrase content that includes signs,
  landmarks, or other location-revealing detail.

**Do not publish raw selection logs as Seed Package metadata.** Before any
publication or sharing outside Goldman Global:

1. Strip or hash `source.clip`.
2. Review `frame_analysis_summary` for location/client leaks.
3. Confirm the editor whose `editor_id` is on the row has consented to
   their decisions being shared.

Future auto-publish tooling must enforce these steps before writing to
`p2p_exchange`.

## Versioning

`schema_version: 1` is this format. When the schema changes (new fields,
renamed values, structural changes), bump the version and document the
migration in this file. Append-only logs without a version field become
migration hell the first time the format moves.

## How this feeds Labs (future)

Selection logs from Forge commercial runs are a candidate input to the
Labs human-perspective knowledge network — but only after:

1. The override signal (`human_action != "accepted"`) is the captured
   field, not the raw model pick.
2. PII review has stripped identifying source metadata.
3. The editor has consented (their aesthetic judgments are personal data).

The long-term goal: aggregate across many editors, many runs, many
domains (ECH tourism, future real-estate, future education) to detect
patterns in how different audiences and editors define "worth recording."
That's the "beauty definition AGI" thesis, made concrete — but it's a
future layer on top of this v1 capture, not v1 itself.
