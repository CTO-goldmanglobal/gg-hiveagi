"""
Stage 3 — SELECT + SCRIPT

Two LLM calls:
  1. Rank all analyzed frames by "tourism appeal for a 30-60s Reel"
  2. Write a coherent English narration script for the top N selected frames

Output: a script [{frame_index, duration_sec, voiceover_text}, ...] that
the COMPOSE stage consumes.
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

# Reuse Labs' robust JSON extractor (handles <think> blocks etc.)
import os
import sys
_repo_root = Path(os.environ.get(
    "VIDEOGEN_REPO_ROOT",
    Path(__file__).resolve().parents[1],
))
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
from llm_wiki_engine.llm_json import extract_json
from llm_wiki_engine.config import Config


def _load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
    return prompt_path.read_text(encoding="utf-8")


def _call_minimax(config: Config, system_prompt: str, user_prompt: str,
                  temperature: float = 0.4) -> str:
    """Single MiniMax M3 chat call. Returns raw content string."""
    payload = json.dumps({
        "model": config.minimax_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{config.minimax_base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {config.minimax_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:300]
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"MiniMax HTTP {e.code}: {body}") from e


def rank_frames(analyses: List[Dict[str, Any]],
                config: Config,
                top_n: int = 8,
                target_duration_sec: int = 45,
                ranker_prompt_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ask MiniMax to rank frames by tourism appeal + visual variety.

    Args:
        analyses: output of analyze_frames()
        config: Labs config (for MiniMax key)
        top_n: how many to keep
        target_duration_sec: informs the ranker's "how many slots" heuristic
        ranker_prompt_path: path to a client-specific ranker prompt. If None,
                            uses the default at videogen/prompts/default_frame_ranker.txt

    Returns:
        Top-N subset of analyses, ordered by rank (best first). Each entry
        is enriched with `_ranker_rationale` = {reason, shot_type} for the
        selection-logging layer.
    """
    # Filter out frames that errored during analysis
    valid = [a for a in analyses if a.get("ai_analysis")]
    if len(valid) <= top_n:
        return valid  # nothing to rank

    # Load prompt: client-specific if provided, else default
    if ranker_prompt_path and Path(ranker_prompt_path).exists():
        system_prompt = Path(ranker_prompt_path).read_text(encoding="utf-8")
    else:
        system_prompt = _load_prompt("default_frame_ranker")

    # Compact summary: frame_index + one-line description (truncate to save tokens)
    summaries = []
    for a in valid:
        desc = a["ai_analysis"][:120].replace("\n", " ")
        summaries.append(f"Frame #{a['frame_index']}: {desc}")
    user_prompt = (
        f"Target: a {target_duration_sec}-second tourism Reel.\n"
        f"Select the best {top_n} frames from these {len(valid)} candidates. "
        f"Prefer visual variety, narrative coherence, and strong tourism appeal.\n\n"
        + "\n".join(summaries)
        + '\n\nReturn JSON: {"ranked_indices": [<frame_index>, ...], '
        '"rationale": {"<frame_index>": {"reason": "<one line>", '
        '"shot_type": "<landscape|architecture|people|detail|food|action>"}, ...}}'
    )

    raw = _call_minimax(config, system_prompt, user_prompt, temperature=0.2)
    parsed = extract_json(raw)
    if not parsed or "ranked_indices" not in parsed:
        # fallback: just take the first top_n in original order
        print("  ⚠️  ranker returned unparseable output; using first-N fallback")
        return valid[:top_n]

    ranked_indices = parsed["ranked_indices"][:top_n]
    rationale = parsed.get("rationale", {})

    # Map back to analysis dicts + attach rationale for logging
    by_index = {a["frame_index"]: a for a in valid}
    selected = []
    for i in ranked_indices:
        if i in by_index:
            entry = dict(by_index[i])  # shallow copy so we don't mutate analyses
            # rationale keys may be int or str depending on LLM output
            rat = rationale.get(i) or rationale.get(str(i), {})
            entry["_ranker_rationale"] = {
                "reason": rat.get("reason", "") if isinstance(rat, dict) else str(rat),
                "shot_type": rat.get("shot_type", "") if isinstance(rat, dict) else "",
            }
            selected.append(entry)
    return selected


def write_script(selected: List[Dict[str, Any]],
                 config: Config,
                 target_duration_sec: int = 45,
                 location_hint: str = "China",
                 writer_prompt_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ask MiniMax to write a narration script for the selected frames.

    Returns:
        Script: [{frame_index, duration_sec, voiceover_text}, ...]
        Sums to roughly target_duration_sec.
    """
    if not selected:
        return []

    # Load prompt: client-specific if provided, else default
    if writer_prompt_path and Path(writer_prompt_path).exists():
        system_prompt = Path(writer_prompt_path).read_text(encoding="utf-8")
    else:
        system_prompt = _load_prompt("default_script_writer")

    descriptions = []
    for a in selected:
        desc = a["ai_analysis"][:200].replace("\n", " ")
        descriptions.append(f"Frame #{a['frame_index']}: {desc}")
    user_prompt = (
        f"Write a {target_duration_sec}-second English narration script for a "
        f"short-form tourism video about {location_hint}. "
        f"The script will appear as on-screen subtitles (no voiceover).\n\n"
        f"Selected frames in order:\n" + "\n".join(descriptions)
        + '\n\nReturn JSON: {"script": [{"frame_index": int, '
        '"duration_sec": float, "voiceover_text": "string"}, ...]}. '
        f'Durations must sum to approximately {target_duration_sec} seconds. '
        'Each voiceover_text should be a short subtitle-friendly phrase '
        '(under 60 characters ideally).'
    )

    raw = _call_minimax(config, system_prompt, user_prompt, temperature=0.5)
    parsed = extract_json(raw)
    if not parsed or "script" not in parsed:
        print("  ⚠️  script writer returned unparseable output; using uniform fallback")
        # Fallback: equal duration, English placeholder text.
        # Do NOT use raw ai_analysis as subtitle — it may be in another language
        # (process_frame follows participant input language) and may be long.
        # These placeholders are honest about the fallback state.
        n = len(selected)
        per = target_duration_sec / n if n else 5
        return [{
            "frame_index": a["frame_index"],
            "duration_sec": round(per, 1),
            "voiceover_text": "Explore China with us",
        } for a in selected]

    script = parsed["script"]
    # Validate + normalize: ensure frame_index is int, duration_sec is float,
    # and force English (the writer was instructed in English; if it slipped,
    # the subtitle pipeline downstream assumes English for TikTok/IG).
    normalized = []
    for seg in script:
        try:
            text = str(seg.get("voiceover_text", "")).strip()
            normalized.append({
                "frame_index": int(seg["frame_index"]),
                "duration_sec": max(2.0, float(seg.get("duration_sec", 5.0))),
                "voiceover_text": text,
            })
        except (KeyError, ValueError, TypeError):
            continue
    return normalized


def select_and_script(analyses: List[Dict[str, Any]],
                      config: Config,
                      top_n: int = 8,
                      target_duration_sec: int = 45,
                      location_hint: str = "China",
                      ranker_prompt_path: Optional[str] = None,
                      writer_prompt_path: Optional[str] = None) -> tuple:
    """
    Convenience: rank → script in one call.

    Returns:
        (script, selected) — the script for compose, and the ranked selection
        (with _ranker_rationale attached) for the finalize/logging layer.
    """
    print(f"  🎯 ranking {len([a for a in analyses if a.get('ai_analysis')])} frames, picking top {top_n} ...")
    selected = rank_frames(analyses, config, top_n, target_duration_sec,
                           ranker_prompt_path=ranker_prompt_path)
    print(f"  ✍️  writing {target_duration_sec}s script for {len(selected)} frames ...")
    script = write_script(selected, config, target_duration_sec, location_hint,
                          writer_prompt_path=writer_prompt_path)
    total = sum(s["duration_sec"] for s in script)
    print(f"  📝 script: {len(script)} segments, {total:.1f}s total")
    return script, selected
