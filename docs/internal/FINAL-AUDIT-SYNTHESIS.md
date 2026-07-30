# Final Audit Synthesis — DeepSeek + MiniMax M3

> Both LLMs reviewed the complete project state before Circle G commit.
> Captured 2026-07-30.

---

## Consensus: ready to build Circle G

**DeepSeek:** "Project is ready for Circle G but must mitigate the two-repo seam risk immediately."

**MiniMax M3:** "The architecture respects the right principles."

Both say go. But each flagged a critical risk.

---

## The two risks both flagged

### Risk 1: The two-repo seam (DeepSeek)

DeepSeek's weakest link: "version skew or mocking mismatches could break the pipeline."

**Action:** contract tests (H7) are not optional — they're the first thing to write after the EDL schema. Write the golden-file fixtures BEFORE building produce.py.

### Risk 2: The discard problem (MiniMax M3)

M3's most important warning: "A 7B local model will reliably discard visually quiet but narratively pivotal frames... It will keep the visually loud and discard the visually true."

**Specifically at risk:**
- Still hand on a temple wall (looks like "nothing" → discarded)
- Child's face turned away (no action → discarded)
- Empty courtyard at dusk (no subject → discarded)
- Daoist ritual tagged as "person in costume" → discarded as uninteresting

**M3's required mitigations (apply to Circle J when building the local filter):**
1. Confidence-weighted random sampling — keep 2-3% of "boring" frames as calibration
2. Temporal coverage floor — never discard more than N consecutive frames
3. Explicit "human-moment" and "cultural-marker" tags that override the aesthetic filter
4. Periodic audit where M3 sees a random sample of discarded frames to recalibrate

**Without these:** "technically correct but spiritually hollow output — videos that have all the right objects and none of the right feeling."

---

## M3's self-assessment: "I am being used as a tagger when I should be used as a judge"

This is the sharpest insight from either review. M3 says:

> "Right now I'm being used as a slightly smarter tagger. That's a waste. Where I genuinely earn my place: synthesis across many nodes' lived experiences, long-tail cultural interpretation, narrative-level coherence across an entire film, aesthetic judgment that requires holding the whole work in mind."

**The division of labor M3 proposes:**

| Task | Local 7B | Cloud M3 |
|:---|:---|:---|
| Tag each frame | ✅ Does this | ❌ Waste of M3 |
| Identify ambiguous landmarks | ❌ No world knowledge | ✅ This is M3's job |
| Cultural/historical fact-check | ❌ No context | ✅ This is M3's job |
| Cross-shot narrative coherence | ❌ No memory | ✅ This is M3's job |
| Aesthetic coherence (whole film) | ❌ Frame-level only | ✅ This is M3's job |
| Fact-vs-visual alignment | ❌ Can't cross-check | ✅ This is M3's job |
| Detect local model hallucinations | ❌ Can't self-audit | ✅ This is M3's job |

**For Circle G (now):** M3 should be the QA judge (whole-film coherence), not the per-frame tagger. The per-frame tagging should move to a cheaper model or the local model.

**For Circle J (edge):** M3's escalation inputs need richer tag fields (see below).

---

## M3's required escalation tag fields

When the local model escalates a frame to M3, M3 needs these fields:

```
Required:
  frame_id + timestamp (ms)
  source_node_id
  local_model_confidence (0.0-1.0)
  local_model_description (free text — even if wrong)
  escalation_reason (low_confidence | cultural_ambiguity | anomaly | 
                     context_required | human_moment | compositional_question)
  local_uncertainty_phrase (the local model's own words about what confused it)

Important:
  detected_entities (person/place/object)
  scene_type (indoor/outdoor/nature/urban/ritual)
  ocr_text (even partial)
  cultural_markers (symbolic/religious/historical flags)
  neighbor_frame_ids (last 3 + next 3 for temporal context)
  lighting_mood (bright/dim/golden/neon/natural)
  human_presence (yes/no, count, action)
  motion_estimate (static/pan/zoom/action)
```

The `local_uncertainty_phrase` is gold — M3 specifically called it out: "the local model's own words about what it wasn't sure of — gold for me."

---

## DeepSeek's start/stop guidance

**STOP:**
- Stop adding new agent skills until the pipeline is stable
- Stop manual video production — let Circle G handle it

**START:**
- Write contract tests for the two-repo seam (before building produce.py)
- Mock the ECH side thoroughly
- Design the G0 falsification dataset (to run immediately after G)

---

## Actions for the build

| Priority | Action | Source | Circle |
|:---|:---|:---|:---|
| 🔴 Now | Write seam contract tests FIRST (before produce.py) | DeepSeek | G (H7 moved up) |
| 🔴 Now | Use M3 as QA judge (whole-film), not per-frame tagger | M3 | G (qa_gate.py) |
| 🟡 G0 | Design pairwise falsification dataset | DeepSeek | G0 |
| 🟡 J | Add discard mitigations (temporal floor, random sample, human-moment override) | M3 | J |
| 🟡 J | Rich escalation tag fields (local_uncertainty_phrase etc.) | M3 | J |
| 🟡 J | Periodic M3 audit of discarded frames | M3 | J |
| 📋 L | M3 for cross-node synthesis, not tagging | M3 | L |

---

## The verdict (both)

**DeepSeek:** "Project is ready for Circle G but must mitigate the two-repo seam risk immediately."

**M3:** "The system will live or die on tag quality and escalation discipline — not on model capability. If I stay rare, I'm valuable. If everything comes to me, the local-first principle has failed."

**Combined:** Build Circle G now. Write contract tests first. Use M3 as a judge, not a tagger. Design the discard safety net before building the edge filter. The architecture is sound — the execution discipline is what matters.
