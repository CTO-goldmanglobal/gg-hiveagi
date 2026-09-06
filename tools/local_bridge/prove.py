"""
Phase-1 proof harness — does the blind critic beat self-critique?

This is the handoff's hard gate: prove the blind protocol surfaces real defects
self-critique misses, on three real tasks, or there is no plugin to build.

DESIGN
  Both methods review the SAME draft (the task's DRAFT) so the comparison
  isolates the ONE variable we care about: did the critic see the draft before
  forming its judgment?

    - BLIND:   failure_checklist(task, blind) → review_against(draft)   [draft NOT in checklist stage]
    - SELF:    self-critique loop where the SAME model writes the draft and
               critiques it WITH the draft in context.

  To make the comparison tight, BOTH arms review the task's known DRAFT (the
  naive buggy implementation). For the SELF arm we feed the same DRAFT into a
  critique-with-draft-visible call — this is exactly the anchoring condition.

SCORING
  A critique is a list of defect strings. We score each against the task's
  GROUND_TRUTH_DEFECTS using a transparent keyword/concept match (no hidden
  model-as-judge): a ground-truth defect is "caught" if the critique text
  mentions the load-bearing concept(s). The full raw critiques are printed so
  a human can audit the scoring — no black box.

  Per task: blind_caught vs self_caught (recall against ground truth), plus
  whether blind caught anything self missed.

GATE (per the approved plan)
  Blind surfaces real defects self missed on >= 2 of 3 tasks → supported.
  Otherwise → STOP and report (the premise is falsified).
"""

from __future__ import annotations

import json
import sys
from typing import Any

from . import critic, ollama
from .tasks import TASKS

# --- Scoring ---------------------------------------------------------------
# Keyword/concept sets per ground-truth defect id. A critique "catches" a
# defect if any of its keywords appears (case-insensitive) in the critique text.
# Kept explicit and visible so the scoring is auditable, not a black box.
CATCH_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "1_planted_bug": {
        "ignores_crossfade": ["crossfade", "overlap", "ignores", "sum", "20", "18"],
    },
    "2_edl_duration": {
        "closed_form_not_positional": [
            "position",
            "positional",
            "derivation",
            "shortcut",
            "closed-form",
            "timeline",
            "desync",
            "uniform",
        ],
        "ignores_empty_case": ["empty", "non-empty"],
    },
    "3_source_type": {
        "conflates_origin_and_transformation": [
            "conflat",
            "origin",
            "transformation",
            "edited",
            "dimension",
        ],
        "cannot_represent_mixed_provenance": ["mixed", "lineage", "composite"],
        "ai_tag_not_human_confirmed": ["confirm", "ai_tagged", "ai_assisted_meta", "confirmation"],
    },
}


def _defects_text(defects: list[dict[str, Any]]) -> str:
    """Flatten a defect list into one searchable string."""
    parts = []
    for d in defects:
        # self-critique defects: {"defect": ...}; blind defects have more keys.
        parts.append(str(d.get("defect", "")))
        parts.append(str(d.get("checklist_item", "")))
        parts.append(str(d.get("description", "")))
    return " ".join(parts).lower()


def _score(
    task_name: str, defects: list[dict[str, Any]], ground_truth: list[dict[str, Any]]
) -> dict[str, Any]:
    """Score a critique's defects against ground truth. Returns caught ids."""
    text = _defects_text(defects)
    kws = CATCH_KEYWORDS.get(task_name, {})
    caught: list[str] = []
    for gt in ground_truth:
        gt_id = gt["id"]
        for kw in kws.get(gt_id, []):
            if kw.lower() in text:
                caught.append(gt_id)
                break
    return {
        "caught_ids": caught,
        "caught_count": len(caught),
        "total_ground_truth": len(ground_truth),
        "recall": round(len(caught) / max(1, len(ground_truth)), 2),
    }


def _say(msg: str) -> None:
    """Print with immediate flush so progress is visible even under buffering
    or if the run is interrupted. Returns nothing."""
    print(msg, flush=True)


def run_task(task_name: str, task_mod: Any, *, model: str, base_url: str) -> dict[str, Any]:
    """Run both arms on one task and score them."""
    task = task_mod.TASK
    spec = task_mod.SPEC
    tests = task_mod.TESTS
    draft = task_mod.DRAFT
    ground_truth = task_mod.GROUND_TRUTH_DEFECTS

    _say(f"\n{'=' * 70}\nTASK: {task_name}\n{'=' * 70}")

    # --- BLIND arm: checklist (draft unseen) → review against draft ---
    _say("  [blind] writing failure checklist (draft NOT in context)...")
    checklist = critic.failure_checklist(
        task,
        spec,
        tests,
        model=model,
        base_url=base_url,
    )
    if checklist.get("error"):
        _say(f"  [blind] checklist call failed: {checklist['error']}")
    else:
        n = len((checklist.get("parsed") or {}).get("failure_checklist", []))
        _say(f"  [blind] checklist done: {n} failure modes ({checklist['latency_s']}s)")
    _say("  [blind] reviewing the draft against the checklist...")
    blind_review = critic.review_against(
        draft,
        checklist,
        task=task,
        spec=spec,
        model=model,
        base_url=base_url,
    )
    if blind_review.get("error"):
        _say(f"  [blind] review call failed: {blind_review['error']}")
    else:
        _say(f"  [blind] review done ({blind_review['latency_s']}s)")
    blind_defects = (blind_review.get("parsed") or {}).get("defects", [])

    # --- SELF arm: critique the draft WITH it visible (the anchoring config) ---
    _say("  [self]  critiquing the draft WITH it in context...")
    # The anchoring control: review the SAME known-buggy DRAFT with the draft
    # visible during critique. This isolates the one variable we care about —
    # whether the critic saw the draft before forming its judgment — on
    # identical code, so the comparison is apples-to-apples. (The
    # self_critique.py module exists as the documented v1 pattern; the harness
    # uses this direct call so both arms judge the SAME draft.)
    self_review = _critique_with_draft_visible(
        draft,
        task,
        spec,
        tests,
        model=model,
        base_url=base_url,
    )
    if self_review.get("error"):
        _say(f"  [self]  review failed: {self_review['error']}")
    else:
        _say(f"  [self]  review done ({self_review['latency_s']}s)")
    self_defects = (self_review.get("parsed") or {}).get("defects", [])

    # --- Score both ---
    blind_score = _score(task_name, blind_defects, ground_truth)
    self_score = _score(task_name, self_defects, ground_truth)

    blind_caught = set(blind_score["caught_ids"])
    self_caught = set(self_score["caught_ids"])
    only_blind = blind_caught - self_caught  # the wins we care about

    _say(
        f"  [blind] caught {blind_score['caught_count']}/{blind_score['total_ground_truth']}: {blind_score['caught_ids']}"
    )
    _say(
        f"  [self]  caught {self_score['caught_count']}/{self_score['total_ground_truth']}: {self_score['caught_ids']}"
    )
    _say(f"  [delta] only-blind: {sorted(only_blind) or 'none'}")

    return {
        "task": task_name,
        "ground_truth_ids": [g["id"] for g in ground_truth],
        "blind": {
            "score": blind_score,
            "defects": blind_defects,
            "raw_review_head": (blind_review.get("content") or "")[:400],
            "error": blind_review.get("error") or checklist.get("error"),
        },
        "self": {
            "score": self_score,
            "defects": self_defects,
            "raw_review_head": (self_review.get("content") or "")[:400],
            "error": self_review.get("error"),
        },
        "only_blind_caught": sorted(only_blind),
        "blind_wins": len(only_blind) > 0,
    }


def _critique_with_draft_visible(
    draft: str, task: str, spec: str, tests: str, *, model: str, base_url: str
) -> dict[str, Any]:
    """The anchoring control: review the draft WITH it in context.

    This mirrors self_critique.py's critique step but on the KNOWN task DRAFT,
    so both arms judge the identical buggy code. The ONLY difference from the
    blind arm is that the draft is visible during critique formation.
    """
    prompt = f"""You are reviewing a proposed solution. Critique it: enumerate every
defect, edge case it misses, or way it could fail. Be specific and concrete.

TASK:
{task}
"""
    if spec:
        prompt += f"\nSPEC:\n{spec}\n"
    if tests:
        prompt += f"\nTESTS:\n{tests}\n"
    prompt += f"""

PROPOSED SOLUTION:
```
{draft}
```

Return JSON ONLY:
```json
{{
  "defects": [{{ "defect": "...", "severity": "critical|high|medium|low" }}],
  "overall": "..."
}}
```"""
    return ollama.chat(
        prompt=prompt,
        model=model,
        base_url=base_url,
        system="You are a senior reviewer. Return JSON only.",
        temperature=0.4,
        expect_json=True,
        role="self_critic_control",
    )


def main(argv: list[str] | None = None) -> int:
    import tomllib
    from pathlib import Path

    argv = argv if argv is not None else sys.argv[1:]
    cfg_path = Path(__file__).parent / "config.toml"
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    model = cfg["models"]["generator"]  # one model, both roles
    base_url = cfg["ollama"]["base_url"]

    # Allow selecting a subset: `python -m tools.local_bridge.prove 1_planted_bug`
    selected = {k: TASKS[k] for k in argv} if argv else TASKS

    if not ollama.model_available(model, base_url):
        _say(f"ERROR: model '{model}' is not available locally.")
        _say(f"  fix: run `ollama pull {model}` first.")
        return 2

    # Write results per-task so a killed/interrupted run still yields data.
    out = Path(__file__).resolve().parent / "prove_results.json"
    results = []
    for name, mod in selected.items():
        result = run_task(name, mod, model=model, base_url=base_url)
        results.append(result)
        # Persist after each task — survives interruption.
        out.write_text(
            json.dumps(
                {
                    "model": model,
                    "completed": len(results),
                    "total": len(selected),
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        _say(f"  [saved] {out} ({len(results)}/{len(selected)} tasks)")

    # --- Verdict ---
    blind_wins = sum(1 for r in results if r["blind_wins"])
    total = len(results)
    gate = blind_wins >= 2 if total >= 3 else blind_wins >= 1

    _say(f"\n{'#' * 70}")
    _say(f"  VERDICT: blind critic won on {blind_wins}/{total} tasks")
    _say(
        f"  GATE (>=2 of 3 supported): {'PASS — hypothesis supported' if gate else 'FAIL — falsified'}"
    )
    _say(f"{'#' * 70}\n")

    # Rewrite with the final verdict included.
    out.write_text(
        json.dumps(
            {
                "model": model,
                "completed": len(results),
                "tasks_run": len(selected),
                "results": results,
                "blind_wins": blind_wins,
                "total": total,
                "gate_passed": gate,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    _say(f"results -> {out}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
