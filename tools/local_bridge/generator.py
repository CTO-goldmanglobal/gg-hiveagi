"""
Draft A generator — the first half of the blind-critic loop.

Produces a draft solution to a task. Deliberately simple: one local-model call,
low temperature. The interesting work happens in ``critic.py`` — this module
exists to produce the thing the critic reviews.

Provenance: every draft is stamped ``ai_generated`` (invariant #3).
"""

from __future__ import annotations

from typing import Any

from . import ollama

SYSTEM = (
    "You are a careful senior engineer. Produce a correct, minimal solution to "
    "the task. Return ONLY the solution in a fenced code block, then a short "
    "JSON object describing your reasoning. Do not preface with chatter."
)


def draft(
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
    """Generate Draft A.

    The prompt deliberately does NOT ask for self-critique — that is the v1
    anti-pattern this plugin replaces. The generator just drafts.

    Returns an Artifact dict (provenance-stamped ai_generated) with the draft
    text in ``content``.
    """
    prompt = f"""Solve this task.

TASK:
{task}
"""
    if spec:
        prompt += f"\nSPEC / CONSTRAINTS:\n{spec}\n"
    if tests:
        prompt += f"\nTESTS THE SOLUTION MUST PASS:\n{tests}\n"
    prompt += """
Return:
```<lang>
<your solution>
```
```json
{{ "approach": "<one sentence>", "assumptions": ["..."], "confidence": "0-1" }}
```"""

    return ollama.chat(
        prompt=prompt,
        model=model,
        base_url=base_url,
        system=SYSTEM,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        expect_json=True,
        role="generator",
    )
