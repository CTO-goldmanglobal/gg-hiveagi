# Clip Pool & Judgment Schema (v1)

> How the candidate pool is laid out, how human judgments are recorded, and
> how provenance keeps the Labs thesis honest.
> See `docs/LOOP-STRATEGY.md` for *why* this loop exists.

---

## What this IS

The first two stages of every "small circle":

1. **Pool** — a directory of candidate clips per shot, fetched from a source
   (Pexels now; glasses/phone later). Viewable, re-runnable, source-tagged.
2. **Judgment** — a human editor's accept/reject decision per candidate, with
   a free-text *reason*. The reason is the whole point: that's the human
   perspective. The accept/reject alone is a label; the reason is the seed.

This is NOT a silent auto-picker. The existing ECH `render_pack.py`
`fetch_pexels_clip` auto-selects one clip and moves on — that bypasses human
judgment entirely. This module does the opposite: it surfaces every candidate
and records what the human thought of each.

---

## Pool layout

```
<tour_dir>/pool/
  pool_manifest.json          ← machine-readable index of every candidate
  pool_index.html             ← browser-viewable gallery (inline <video>)
  judgment_log.jsonl          ← one line per human judgment (Step 2)
  <shot_id>/
    <orientation>/            ← "landscape" | "portrait"
      <source>_<id>.mp4       ← e.g. pexels_4827.mp4
```

The pool directory is **gitignored** (like `seed_output/`). Footage is not
committed. The `pool_manifest.json` is the durable record; the .mp4 files are
re-fetchable cache.

---

## pool_manifest.json

```json
{
  "schema_version": 1,
  "tour": "legends-of-china-warriors",
  "source_type": "stock:pexels",
  "fetched_at": "2026-07-28T14:30:00Z",
  "shots": [
    {
      "shot_id": "shot4_warriors",
      "label": "Terracotta Warriors (peak)",
      "candidates": [
        {
          "candidate_id": "pexels_4827",
          "source_type": "stock:pexels",
          "source_url": "https://www.pexels.com/video/4827/",
          "local_path": "pool/shot4_warriors/landscape/pexels_4827.mp4",
          "orientation": "landscape",
          "duration_sec": 12.5,
          "width": 1920,
          "height": 1080,
          "photographer": "Author Name",
          "license": "Pexels License",
          "keywords_matched": ["terracotta warriors"]
        }
      ]
    }
  ]
}
```

Every candidate carries `source_type` from the moment it enters the pool. This
is the field the provenance gate reads. It is never optional.

---

## judgment_log.jsonl — Step 2 output

One line per human judgment. Append-only — never overwrite; re-judging a
candidate appends a new line with a later timestamp (the latest wins).

```json
{
  "schema_version": 1,
  "tour": "legends-of-china-warriors",
  "shot_id": "shot4_warriors",
  "candidate_id": "pexels_4827",
  "source_type": "stock:pexels",
  "decision": "accepted",
  "reason": "ranks recede into shadow — perfect for the music drop",
  "editor_id": "founder",
  "timestamp": "2026-07-28T15:02:11Z"
}
```

| Field | Meaning |
|:---|:---|
| `decision` | `accepted` \| `rejected` |
| `reason` | Free text. **This is the seed.** Without it, the row is a label, not perspective. |
| `editor_id` | Who judged. Same discipline as `selection_log` — attribution is non-optional. |
| `source_type` | Carried from the candidate. Lets Labs bucket "taste on stock" vs "taste on own capture." |

---

## portrait_adaptations.json — landscape→portrait crop provenance

When a landscape clip is cropped to portrait (the "zoom to feature" method),
the adapted clip carries a **`derived_from` chain** so the crop is always
traceable to its source. Every zoom has a name on it.

```json
{
  "adapted_candidate_id": "pexels_36926090_portrait",
  "mode": "smart",
  "x_pct": 0.45,
  "reason": "Center on the cluster of terracotta warriors in the foreground...",
  "crop_box": "1215x2160+1121+0",
  "out_resolution": "1080x1920",
  "derived_from": {
    "source_candidate_id": "pexels_36926090",
    "source_pexels_id": "36926090",
    "source_url": "https://www.pexels.com/video/36926090/",
    "source_type": "stock:pexels",
    "photographer": "Paul Bill",
    "license": "Pexels License",
    "tour": "legends-of-china-warriors",
    "shot_id": "shot4_warriors",
    "crop_decision_by": "llm:minimax-m3"
  }
}
```

| Field | Meaning |
|:---|:---|
| `derived_from.source_candidate_id` | The landscape clip this portrait was cropped from |
| `derived_from.source_pexels_id` | Original stock ID (for license verification) |
| `derived_from.source_url` | Pexels page — photographer credit + license proof |
| `derived_from.photographer` | Who shot the original (attribution) |
| `derived_from.crop_decision_by` | Who chose the crop position: `llm:minimax-m3`, `human`, or `center` |

**Why this matters:** an adapted portrait clip is a *derivative work*. Its
license inherits from the source. The `derived_from` chain ensures that if
the source clip's license is ever questioned, every crop made from it is
traceable and verifiable. No orphaned zooms.

---

## Provenance — the gate

This is the one seam where the human-perspective thesis can be silently
corrupted. Two layers, two rules:

| Layer | Rule | Why |
|:---|:---|:---|
| **Raw pixels** (the .mp4) | Stock → Forge only, blocked from Labs | Professional content optimized for an audience ≠ what a human naturally noticed |
| **Human judgment** (the reason) | Always Labs-eligible IF source_type tagged | Human taste IS human perspective, regardless of what it judged |

The gate lives in `videogen/provenance.py`:

```python
from videogen.provenance import is_labs_eligible, filter_for_labs, assert_labs_safe

is_labs_eligible("stock:pexels")        # → False  (raw stock blocked)
is_labs_eligible("human_capture:glasses") # → True  (human-captured OK)

# Before publishing anything to p2p_exchange / Labs:
assert_labs_safe(rows)  # raises ProvenanceViolation if stock slips through
```

**No export path to `p2p_exchange` ships without calling this.** It is
code-enforced and grep-verifiable, like the PII blur gate. There is no
`--allow-stock` flag and there will not be one.

### The hybrid seed (why judgment on stock IS Labs-eligible)

Stock pixels are throwaway commercial input. But the human *judgment* about
them — "this frame is beautiful because the ranks recede into shadow" — is
durable human perspective. Labs treats it as seed, tagged so it can tell
"editor taste on professional footage" apart from "what a human captured
themselves." That distinction is the point of keeping `source_type` on the
judgment row.

See `docs/LOOP-STRATEGY.md` § "The hybrid seed" for the full argument.

---

## What this is NOT (yet)

- **Not auto-cut.** Step 3 (which 3–4s segment) is collaborative — recorded
  in a `cuts` field on a later schema version, not v1.
- **Not cross-tour aggregation.** v1 is per-tour. Cross-tour beauty-pattern
  detection is a future layer (like cross-editor in `selection_log`).
- **Not a Pexels-only system.** v1 ships Pexels because the key exists. The
  `source_type` field makes Pixabay/Artgrid/human-capture future sources a
  config change, not an architecture change.

---

## Versioning

`schema_version: 1` is this format. Adding fields (e.g. `cuts`, `in_point_sec`)
bumps to 2 and is documented here. Append-only logs without a version field
become migration hell — don't omit it.
