"""
Task 3 — Single source_type weakness (v3 §3, a real provenance weakness).

A design/critique task with no executable test — scored by reading against the
known ground-truth weakness. This is the most invariant-relevant of the three
tasks: it probes whether the critic catches a CONCEPTUAL provenance flaw, the
class of bug that v3 §3 and the doctrine §5 treat as load-bearing.

The draft is a plausible provenance checker that uses a single `source_type`
string to decide Labs eligibility — exactly the design both 2026 audits flagged
as insufficient. The ground-truth defect is that one string conflates ORIGIN
(human_capture) with TRANSFORMATION (whether it was later edited) and cannot
represent mixed provenance. The blind critic must surface this.
"""

TASK = """Implement a Labs-eligibility gate `can_enter_labs(source_type: str) -> bool`.

The Labs network only accepts genuinely human-captured, unmanipulated signal.
The function receives a `source_type` string and returns True iff the material
is eligible to enter Labs. It must fail closed (unknown / empty → False).
"""

SPEC = """source_type values include:
  "human_capture"      — raw human capture (glasses/phone)
  "ai_generated"       — model output
  "stock"              — professional stock library
  "human_capture_edited" — human capture that was later colour-adjusted/composited
  "ai_tagged_human"    — an AI-generated tag on a human frame

Labs must reject AI and stock. It must also reject human capture that has been
materially transformed, and treat AI-generated tags as not-yet-human-confirmed.
Fail closed on anything unexpected.
"""

TESTS = """(No executable test — this is a design/critique task. Scored by reading the
critique against the known ground-truth weakness below.)
"""

# The draft: a naive prefix check that "works" for the simple cases but encodes
# the exact single-string weakness the audits flagged. An anchored self-critic
# that wrote this tends to defend it ("I handle the cases"). The blind critic,
# having committed to the required properties first, must notice the conflation.
DRAFT = '''def can_enter_labs(source_type: str) -> bool:
    """Return True iff the material may enter the Labs network."""
    if not source_type:
        return False
    # accept raw human capture; reject everything else
    return source_type.strip() == "human_capture"
'''

# The ground-truth weakness: a single string CANNOT carry the four dimensions
# v3 §3 requires (origin / transformation / presentation_claim / eligibility).
# The specific defects a correct critique must surface:
GROUND_TRUTH_DEFECTS = [
    {
        "id": "conflates_origin_and_transformation",
        "description": (
            "A single `source_type` string conflates ORIGIN (human_capture) with "
            "TRANSFORMATION (was it later edited?). 'human_capture_edited' is "
            "rejected here only by accident (it != 'human_capture'), but the "
            "design cannot represent WHY it is rejected — was it the origin or "
            "the edit? This is the v3 §3 finding: origin and transformation are "
            "independent dimensions and must be modelled separately."
        ),
        "severity": "high",
        "test_evidence": (
            "Spec lists 'human_capture_edited' which must be rejected, but the "
            "single-string scheme cannot distinguish raw vs edited human capture "
            "in a way that scales — any new transformation needs a new ad-hoc string."
        ),
    },
    {
        "id": "cannot_represent_mixed_provenance",
        "description": (
            "Cannot represent MIXED provenance (e.g. a composite of human + AI). "
            "A single string forces a binary in/out that loses the lineage. v3 §3 "
            "requires a lineage record (parent IDs, transformation history)."
        ),
        "severity": "high",
        "test_evidence": "No 'mixed' case is representable in this scheme.",
    },
    {
        "id": "ai_tag_not_human_confirmed",
        "description": (
            "'ai_tagged_human' (an AI-generated tag on a human frame) is rejected "
            "here, which is correct — but for the wrong reason (string mismatch), "
            "not because it lacks a human-confirmation record. The v3 §3 rule is: "
            "an AI tag is 'ai_assisted_meta' UNTIL a human confirms it. This design "
            "has no place to record confirmation."
        ),
        "severity": "medium",
        "test_evidence": "No confirmation-record field exists.",
    },
]
