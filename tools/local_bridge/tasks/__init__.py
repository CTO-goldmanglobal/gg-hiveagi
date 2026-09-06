"""The three Phase-1 proof tasks. Each exposes TASK, SPEC, TESTS, DRAFT, and
GROUND_TRUTH_DEFECTS. The DRAFT is the thing both the blind critic and the
self-critic review; GROUND_TRUTH_DEFECTS is the objective scoring key."""

from . import (
    task1_planted_bug,
    task2_edl_duration,
    task3_source_type,
)

# name -> task module
TASKS = {
    "1_planted_bug": task1_planted_bug,
    "2_edl_duration": task2_edl_duration,
    "3_source_type": task3_source_type,
}

__all__ = ["TASKS"]
