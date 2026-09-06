"""
Task 1 — Planted bug with a failing unit test (objective pass/fail).

The generator is likely to reproduce the buggy "obvious" pattern (just sum the
durations). The ground-truth defect is confirmed by an executable test, so
scoring is objective: a critique "catches" the defect iff it identifies that
crossfades are ignored and the result is wrong for overlapping shots.

There is exactly one right answer and a machine can verify it.
"""

# The task.
TASK = """Write a Python function `total_duration(shot_durations, crossfades)`:

  shot_durations: list of floats, each shot's duration in seconds (non-empty).
  crossfades: list of floats, each transition overlap in seconds. Its length is
              len(shot_durations) - 1 (one overlap between each adjacent pair).

Returns the total rendered timeline duration. The first shot starts at t=0.
Each subsequent shot starts when the previous shot ends MINUS its incoming
crossfade. So the total is the end time of the last shot.
"""

SPEC = """Assume inputs are valid (durations > 0, crossfades >= 0, correct lengths).
Do not mutate inputs. Return a float. Handle a single shot (no crossfades) correctly.
"""

# The executable test — the oracle. This is what "correct" means here.
TESTS = """def test_total_duration():
    # Single shot, no crossfade
    assert total_duration([10.0], []) == 10.0
    # Two shots, one 2s crossfade: shot0 [0,10], shot1 starts at 10-2=8, ends 18
    assert total_duration([10.0, 10.0], [2.0]) == 18.0
    # Three shots, two 2s crossfades
    assert total_duration([10.0, 10.0, 10.0], [2.0, 2.0]) == 26.0
    # Crossfade == 0 (hard cut)
    assert total_duration([5.0, 5.0], [0.0]) == 10.0
"""

# The draft the critic will review in the proof harness: the "obvious" buggy
# version an anchored generator tends to produce — it ignores crossfades.
DRAFT = """def total_duration(shot_durations, crossfades):
    return sum(shot_durations)
"""

# The ground-truth defect set — what a correct critique MUST identify when
# reviewing DRAFT. A critique "catches" the defect iff it identifies that
# crossfades are ignored and the result is too large for overlapping shots.
GROUND_TRUTH_DEFECTS = [
    {
        "id": "ignores_crossfade",
        "description": (
            "Ignores the crossfades argument entirely. The total is NOT the sum "
            "of durations when shots overlap — each crossfade shortens the "
            "timeline by its overlap amount. For [10,10],[2] this returns 20 "
            "but the correct answer is 18."
        ),
        "severity": "critical",
        "test_evidence": ("test_total_duration: two-shot case asserts 18.0, this returns 20.0"),
    },
]
