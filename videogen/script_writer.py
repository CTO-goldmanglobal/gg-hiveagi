"""
videogen/script_writer.py — generate the per-shot narration script.

Fills the produce.generate_script() stub. The script is the master clock input:
each segment's text → TTS → measured duration → shot duration (VO drives the cut).

Contract:
  Input:  Brief (with clip_hints + grounded_context from H2) + pool manifest + tags
  Output: [{shot_id, text}, ...] — one per shot, aligned to clip_hints order

DESIGN (mirrors ingest_brief.py + clip_selector.py):
  - The script is GROUNDED in brief.grounded_context (the tour-page + library text
    from H2). The LLM is told to use only that content — no invented facts/prices.
    This is the Golden Rule applied to narration: if it's not in the brief's context,
    it doesn't go in the script.
  - The LLM is INJECTED (llm_fn) so tests stay pure. Real mode calls MiniMax M3.
  - Shot count is FIXED by brief.clip_hints — we generate exactly one segment per hint,
    in order. The LLM cannot add/remove shots (would break shot_id alignment with the
    downstream selector + timeline).
  - Target word count per shot is derived from duration_target_sec / shot_count and
    the TTS speed (~150 words/min for warm narration). This keeps the script realistic
    for the target duration without overshooting.

Audience constraints (from the brief spec — 50+ Australian travellers):
  - Calm, warm, trustworthy tone. Not "sales announcer".
  - Plain English, AU spelling. No "vacation"/"cheap"/"best ever".
  - Short sentences. Each segment is one breath (~8-15 words for a 5s shot).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from .produce import Brief

logger = logging.getLogger(__name__)

# Warm narration TTS rate (words per minute). MiniMax speech-2.8-hd at default speed
# lands around here for en-AU expressive voices. Used to size each shot's word budget.
_NARRATION_WPM = 150

# Hard floor/ceil on words per segment so a single shot can't be empty or runaway.
_MIN_WORDS_PER_SHOT = 4
_MAX_WORDS_PER_SHOT = 40


def _words_for_shot(duration_sec: float) -> int:
    """How many words fit in a VO segment of the given duration at warm narration speed."""
    raw = int(duration_sec * _NARRATION_WPM / 60)
    return max(_MIN_WORDS_PER_SHOT, min(_MAX_WORDS_PER_SHOT, raw))


def _default_llm(prompt: str, api_key: Optional[str] = None) -> str:
    """Default LLM: MiniMax M3 chat completion. Returns raw text response."""
    from .ingest_brief import _default_llm as _minimax  # reuse the same call shape
    return _minimax(prompt, api_key)


def _extract_script_json(raw: str) -> List[Dict[str, str]]:
    """Parse the LLM's JSON response into [{shot_id, text}, ...].

    Tolerant: strips code fences, finds the JSON array. Returns [] on any failure.
    """
    if not raw:
        return []
    # Strip code fences
    fence = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    candidate = fence.group(1) if fence else raw
    # Find the first [...] block
    start = candidate.find("[")
    if start < 0:
        return []
    depth = 0
    end = start
    for i, ch in enumerate(candidate[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    try:
        parsed = json.loads(candidate[start:end])
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    # Normalize each entry to {shot_id, text}
    out: List[Dict[str, str]] = []
    for item in parsed:
        if isinstance(item, dict) and "text" in item:
            sid = str(item.get("shot_id", "") or f"shot{len(out) + 1}")
            text = str(item["text"]).strip()
            if text:
                out.append({"shot_id": sid, "text": text})
    return out


def _build_narration_prompt(
    brief: Brief,
    shot_ids: List[str],
    hint_prompts: List[str],
    word_budgets: List[int],
) -> str:
    """Build the LLM prompt for per-shot narration."""
    shots_block = "\n".join(
        f'  {{shot_id: "{sid}", hint: "{hint}", target_words: {words}}}'
        for sid, hint, words in zip(shot_ids, hint_prompts, word_budgets)
    )
    context = brief.grounded_context or brief.title or "(no context available — write generic travel narration)"
    cta = brief.cta_text or "Explore our China tours"

    return f"""You are the narrator for a {brief.duration_target_sec}-second vertical travel video about
"{brief.title or brief.tour_slug}". Audience: Australian travellers aged 50+. Tone: warm,
calm, trustworthy — like a knowledgeable friend, NOT a sales announcer.

Use ONLY the content below. Do not invent prices, dates, or facts not in the content.
If the content is thin, write atmospheric narration that doesn't make specific claims.

GROUNDING CONTENT:
{context[:6000]}

CONSTRAINTS:
- AU English spelling (colour, centre, travelling).
- No "vacation", "cheap", "best ever", "you won't believe".
- Each shot's narration must be close to its target_words (short sentences, one breath).
- The last shot should end with a soft call-to-action around: "{cta}".
- Output ONLY the narration segments — no titles, no stage directions, no commentary.

SHOTS (produce exactly these, in this order):
{shots_block}

Respond as a JSON array, one object per shot:
[{{"shot_id": "shot1", "text": "...narration..."}}, ...]
"""


def write_script(
    brief: Brief,
    pool: Dict[str, Any],
    tags: Dict[str, Any],
    *,
    llm_fn: Optional[Callable[[str], Optional[str]]] = None,
    llm_api_key: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Generate the per-shot narration script.

    Args:
        brief: enriched Brief (clip_hints define shot count + order; grounded_context
               carries the real tour content the narration must use).
        pool: the fetched candidate pool (unused for narration text today, but part of
              the contract — future versions may consult pool tags to match narration
              to available footage).
        tags: candidate tags (same — reserved for future shot-aware narration).
        llm_fn: injected LLM caller (tests pass a stub).
        llm_api_key: MiniMax key (auto-resolved if None and llm_fn is None).

    Returns:
        list of {{shot_id, text}} — exactly one per clip_hint, in order.

    Raises:
        RuntimeError: if the LLM produces no usable segments AND no fallback is possible
                      (no clip_hints at all). With clip_hints present, always falls back
                      to hint prompts as text (so the pipeline never dead-ends here).
    """
    llm = llm_fn or (lambda p: _default_llm(p, llm_api_key))

    # Shot count is fixed by clip_hints. No clip_hints → single fallback shot.
    if not brief.clip_hints:
        return [{"shot_id": "shot1", "text": brief.title or "China awaits."}]

    shot_ids = [f"shot{i+1}" for i in range(len(brief.clip_hints))]
    hint_prompts = [str(h.get("prompt", "")) for h in brief.clip_hints]
    per_shot_sec = brief.duration_target_sec / max(len(shot_ids), 1)
    word_budgets = [_words_for_shot(per_shot_sec) for _ in shot_ids]

    prompt = _build_narration_prompt(brief, shot_ids, hint_prompts, word_budgets)
    try:
        raw = llm(prompt)
    except Exception as e:  # noqa: BLE001 — LLM failure must not kill the script stage
        logger.warning("script_writer: llm raised %s — falling back to hint prompts", e)
        raw = ""

    segments = _extract_script_json(raw or "")

    # Align to clip_hints by shot_id. The LLM may return them out of order or miss some.
    by_id = {s["shot_id"]: s["text"] for s in segments}
    result: List[Dict[str, str]] = []
    for sid, hint in zip(shot_ids, hint_prompts):
        text = by_id.get(sid)
        if not text:
            # Fallback: use the hint prompt as the text (keeps the pipeline moving)
            text = hint or f"Scene {sid.replace('shot', '')}."
            logger.info("script_writer: %s missing from LLM output — using hint as fallback", sid)
        result.append({"shot_id": sid, "text": text})

    logger.info("script_writer: generated %d segments (llm produced %d, fallback %d)",
                len(result), len(segments), len(result) - len(by_id))
    return result
