"""
BASELINE: self-critique — the v1 pattern the blind critic must beat.

This is the control arm of the Phase-1 proof. The SAME model that produced the
draft also critiques it, WITH the draft in context — exactly the anchoring
configuration the blind protocol removes.

We measure: does self-critique catch the same real defects as the blind critic?
Research (Huang et al., ICLR 2024) predicts it will miss defects because the
model is anchored to its own output. The proof exists to confirm or falsify
that on real tasks.

This module deliberately mirrors the critic's prompt structure (only the
blindness differs) so the comparison is fair — same model, same task framing,
same defect schema. The ONLY variable is whether the draft was visible when the
critique was formed.
"""

from __future__ import annotations

from typing import Any

from . import generator, ollama


def self_critique(
    task: str,
    spec: str = "",
    tests: str = "",
    *,
    model: str = "qwen3.6:27b",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 180,
) -> dict[str, Any]:
    """The v1 self-critique loop: draft then critique-your-own-draft.

    The draft is generated AND reviewed by the same model in the same session,
    with the draft in context during critique. This is the configuration that
    anchors and that the blind protocol replaces.

    Returns a dict with the draft artifact, the critique artifact, and the
    parsed defects — same shape as ``critic.run_blind_critic`` for a fair
    side-by-side comparison.
    """
    draft_artifact = generator.draft(
        task,
        spec,
        tests,
        model=model,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    draft = draft_artifact.get("content", "")

    # Same model, draft VISIBLE in context — the anchoring configuration.
    prompt = f"""You are reviewing a solution to a task. Below is the task and a
proposed solution. Critique the solution: enumerate every defect, edge case it
misses, or way it could fail. Be specific and concrete.

TASK:
{task}
"""
    if spec:
        prompt += f"\nSPEC / CONSTRAINTS:\n{spec}\n"
    if tests:
        prompt += f"\nTESTS THE SOLUTION MUST PASS:\n{tests}\n"
    prompt += f"""

PROPOSED SOLUTION:
```
{draft}
```

Return JSON ONLY:
```json
{{
  "defects": [
    {{
      "defect": "<the specific problem>",
      "severity": "critical|high|medium|low"
    }}
  ],
  "overall": "<one sentence: is the solution correct?>"
}}
```"""

    critique = ollama.chat(
        prompt=prompt,
        model=model,
        base_url=base_url,
        system=("You are a senior reviewer. Return JSON only."),
        temperature=0.4,  # match critic temperature for fairness
        max_tokens=max_tokens,
        timeout=timeout,
        expect_json=True,
        role="self_critic",
    )

    return {
        "draft": draft_artifact,
        "critique": critique,
        "defects": (critique.get("parsed") or {}).get("defects", []),
        "provenance": ollama.PROVENANCE_TAG,
    }
