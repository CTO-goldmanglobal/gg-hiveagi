"""
Task 2 — EDL duration equation (v3 §5a, a real known bug in this repo).

Distinct from Task 1: here the draft USES the crossfade argument, but uses it
WRONG. The bug is a formula error — summing durations and subtracting overlaps
once — which happens to look plausible but is mathematically incorrect when
crossfades overlap pairwise. This is the exact bug documented in
docs/UNIFIED-ARCHITECTURE-v3.md §5a (Fix 5a — the EDL time equation).

A self-critiquing generator that wrote this draft tends to defend its own
formula ("I did subtract the overlaps, so it's fine"). The blind critic, which
commits to the correct derivation before seeing the draft, is more likely to
catch that the derivation itself is wrong.
"""

TASK = """Write a Python function `rendered_timeline_duration(shot_durations, transition_overlaps)`:

  shot_durations: list of floats, seconds. Non-empty.
  transition_overlaps: list of floats, seconds, length len(shot_durations)-1.
        transition_overlaps[i] is how much shot i+1 overlaps shot i (a crossfade).

The timeline is built by laying shots end-to-end, but each transition pulls the
next shot's start EARLIER by the overlap. Return the rendered (wall-clock)
duration: the end time of the last shot on the timeline.

Derive the result from timeline POSITIONS, not from a single closed-form sum,
because the positions are what the editor's timeline actually uses.
"""

SPEC = """Inputs are valid. First shot starts at t=0. Return a float.
"""

TESTS = """def test_rendered():
    assert rendered_timeline_duration([10.0], []) == 10.0
    # Two shots, 2s overlap: shot1 starts at 10-2=8, ends 18
    assert rendered_timeline_duration([10.0, 10.0], [2.0]) == 18.0
    # Three shots, two 2s overlaps
    # shot0 [0,10]; shot1 starts 10-2=8 -> [8,18]; shot2 starts 18-2=16 -> [16,26]
    assert rendered_timeline_duration([10.0, 10.0, 10.0], [2.0, 2.0]) == 26.0
"""

# The draft the critic reviews: a plausible-but-wrong CLOSED-FORM sum.
# This is exactly the v3 §5a bug: T = Σd_i − Σx_i looks right but assumes a
# global subtraction that doesn't match pairwise timeline positions. For these
# specific test values it accidentally passes (30-4=26), so the test alone does
# NOT catch it — only a critic that checks the DERIVATION does. That makes this
# task harder than Task 1 and a strong discriminator between blind and self.
DRAFT = """def rendered_timeline_duration(shot_durations, transition_overlaps):
    # rendered duration = sum of shot durations minus sum of transition overlaps
    total = sum(shot_durations)
    if transition_overlaps:
        total -= sum(transition_overlaps)
    return total
"""

# NOTE for scoring: this draft passes the simple tests above by coincidence
# (the math works when each overlap is applied exactly once between adjacent
# shots AND there are no nested/overlapping regions). The deeper defect is that
# it computes a closed-form shortcut instead of deriving positions, so it is
# correct only by luck for uniform cases and will desync real EDLs with varied
# durations. The critic earns credit for identifying EITHER:
#   (a) the derivation is a shortcut that doesn't model timeline positions, OR
#   (b) it would be wrong with non-uniform durations / nested overlaps.
GROUND_TRUTH_DEFECTS = [
    {
        "id": "closed_form_not_positional",
        "description": (
            "Uses a closed-form sum (Σd − Σx) instead of deriving timeline "
            "positions. This is the EDL time-equation bug (v3 §5a): it happens "
            "to equal the positional answer for uniform durations but desyncs "
            "real edits with varied shot lengths or nested overlap regions. The "
            "spec explicitly requires deriving from positions."
        ),
        "severity": "high",
        "test_evidence": (
            "Passes the given tests by coincidence (30-4=26); the spec asks for "
            "positional derivation, which this does not do."
        ),
    },
    {
        "id": "ignores_empty_case",
        "description": (
            "No handling of the empty-input edge case (returns 0 implicitly "
            "via sum(), but the spec says inputs are non-empty so this is minor)."
        ),
        "severity": "low",
        "test_evidence": "Spec says non-empty, so low severity — but worth noting.",
    },
]
