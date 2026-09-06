"""
The blind critic — the core design fix over self-critique.

THE INVARIANT (the whole plugin's reason to exist):
  ``failure_checklist()`` is BLIND. Its prompt contains the task + spec + tests
  but NEVER Draft A. Only after the checklist exists does ``review_against()``
  show the critic the draft and ask it to mark defects against its own list.

  Models favor their own outputs during self-evaluation (Huang et al., ICLR
  2024, "LLMs Cannot Self-Correct Reasoning Yet"). Self-critique anchors. The
  blind protocol removes the anchor: the critic commits to what failure looks
  like before it ever sees the thing it is judging.

This is asserted mechanically by test_critic_blind.py, which checks the
checklist-stage prompt context for any substring of Draft A.

The Phase-1 design uses ONE model for generator and critic — so the blindness,
not a different model family, carries ALL the anti-anchoring weight. If blind
still beats self-critique with the same model, that is a strong result; if it
does not, it directly answers v3 OQ-C (you need a different model).
"""

from __future__ import annotations

from typing import Any

from . import ollama

# DRAFT_PLACEHOLDER is what the checklist-stage prompt uses INSTEAD of the
# actual draft. It makes the blindness explicit and machine-checkable: a test
# can confirm the real draft text is absent from the checklist context.
DRAFT_PLACEHOLDER = "<DRAFT NOT YET PROVIDED — judge from first principles>"


def _blind_checklist_prompt(task: str, spec: str, tests: str) -> str:
    """Build the checklist prompt WITHOUT the draft.

    Exposed as a standalone function (not inlined in failure_checklist) so a
    test can call it and assert it contains no draft substring — proving the
    blindness invariant at the prompt-construction layer, not just by trusting
    the call graph.
    """
    prompt = f"""You are an independent reviewer. You have NOT seen any proposed
solution. Before judging anything, write down every way a solution to this task
could fail — the failure checklist — and the properties a correct solution MUST
have.

TASK:
{task}
"""
    if spec:
        prompt += f"\nSPEC / CONSTRAINTS:\n{spec}\n"
    if tests:
        prompt += f"\nTESTS A CORRECT SOLUTION MUST PASS:\n{tests}\n"
    prompt += """

Do NOT propose a solution. Only enumerate how one could fail.

Return JSON ONLY:
```json
{
  "failure_checklist": [
    "<a concrete, specific failure mode — e.g. 'ignores the empty-list case', 'sums durations without subtracting crossfade overlap'>"
  ],
  "required_properties": [
    "<a property a correct solution must have>"
  ]
}
```"""
    return prompt


def failure_checklist(
    task: str,
    spec: str = "",
    tests: str = "",
    *,
    model: str = "qwen3.6:27b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.4,
    max_tokens: int = 4096,
    timeout: int = 180,
) -> dict[str, Any]:
    """Step 3 of the loop: write the failure checklist BLIND (no draft).

    Returns an Artifact dict. ``parsed`` holds
    ``{"failure_checklist": [...], "required_properties": [...]}``.
    """
    prompt = _blind_checklist_prompt(task, spec, tests)
    return ollama.chat(
        prompt=prompt,
        model=model,
        base_url=base_url,
        system=(
            "You are an independent, brutally honest reviewer. You have not seen "
            "the draft. Return JSON only."
        ),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        expect_json=True,
        role="critic_checklist",
    )


def review_against(
    draft: str,
    checklist_artifact: dict[str, Any],
    task: str = "",
    spec: str = "",
    *,
    model: str = "qwen3.6:27b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 180,
) -> dict[str, Any]:
    """Step 4: now show the critic the draft and mark defects against its list.

    Runs ONLY after the checklist exists. The critic is instructed to be
    specific and cite which checklist item each defect violates.

    Returns an Artifact dict. ``parsed`` holds ``{"defects": [...]}`` where each
    defect is ``{"checklist_item": "...", "defect": "...", "severity": "..."}``.
    """
    parsed = checklist_artifact.get("parsed") or {}
    checklist = parsed.get("failure_checklist", [])
    required = parsed.get("required_properties", [])

    checklist_str = "\n".join(f"  - {c}" for c in checklist) or "  (none enumerated)"
    required_str = "\n".join(f"  - {r}" for r in required) or "  (none enumerated)"

    prompt = f"""You are the same independent reviewer. You previously wrote a
failure checklist for a task (you did NOT see the draft at that time). Now you
are given a proposed draft. Review it AGAINST your checklist. For each
checklist item or required property it violates, record a specific defect.

YOUR FAILURE CHECKLIST:
{checklist_str}

REQUIRED PROPERTIES:
{required_str}
"""
    if task:
        prompt += f"\nTASK (for reference):\n{task}\n"
    if spec:
        prompt += f"\nSPEC (for reference):\n{spec}\n"
    prompt += f"""

PROPOSED DRAFT:
```
{draft}
```

Mark ONLY real defects. If the draft satisfies a checklist item, do not list it.
Be specific and concrete. Return JSON ONLY:
```json
{{
  "defects": [
    {{
      "checklist_item": "<which item it violates>",
      "defect": "<the specific problem, with the exact line/logic>",
      "severity": "critical|high|medium|low"
    }}
  ],
  "overall": "<one sentence: is the draft correct?>"
}}
```"""

    return ollama.chat(
        prompt=prompt,
        model=model,
        base_url=base_url,
        system=(
            "You are an independent reviewer applying your own failure checklist. Return JSON only."
        ),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        expect_json=True,
        role="critic_review",
    )


def run_blind_critic(
    task: str,
    draft_artifact: dict[str, Any],
    spec: str = "",
    tests: str = "",
    *,
    model: str = "qwen3.6:27b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.4,
    max_tokens: int = 4096,
    timeout: int = 180,
) -> dict[str, Any]:
    """Convenience: run the full blind-critic protocol on an existing draft.

    checklist (blind) → review (draft shown). Returns a dict with both
    artifacts and the parsed defects.
    """
    checklist = failure_checklist(
        task,
        spec,
        tests,
        model=model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    review = review_against(
        draft_artifact.get("content", ""),
        checklist,
        task=task,
        spec=spec,
        model=model,
        base_url=base_url,
        temperature=0.2,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return {
        "checklist": checklist,
        "review": review,
        "defects": (review.get("parsed") or {}).get("defects", []),
        "provenance": ollama.PROVENANCE_TAG,
    }
