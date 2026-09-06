"""
Ollama client for the Local Development Bridge.

Adapts the urllib + JSON-extraction pattern already used by
``tools/code_review/review.py`` and ``tools/audit/council.py``, pointed at the
local Ollama OpenAI-compatible endpoint (localhost, no auth). No third-party
dependencies — stdlib only, matching the rest of ``tools/``.

Every call returns an Artifact: a dict carrying the model output PLUS a
``provenance`` field stamped ``ai_generated``. This is invariant #3 in
``tools/local_bridge/__init__.py`` — no artifact leaves this package untagged.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

# Provenance tag stamped on every artifact. Self-contained — does NOT import
# videogen (isolation invariant #2). Mirrors the source_type prefix scheme in
# videogen/provenance.py so the two cannot diverge in meaning; a parity test
# (Phase 2) will assert they agree on Labs-ineligibility.
AI_GENERATED = "ai_generated"
PROVENANCE_TAG = f"{AI_GENERATED}:local_bridge"


def extract_json(text: str) -> dict[str, Any] | None:
    """Extract a JSON object from an LLM response.

    Handles fenced code blocks, ``<think>`` reasoning prefixes, and bare JSON.
    Mirrors ``tools/audit/council.py::_extract_json`` (kept local to avoid any
    cross-tool import; both tools are independently deployable).
    """
    # Fenced code blocks first
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if blocks:
        try:
            return json.loads(blocks[-1])
        except json.JSONDecodeError:
            pass

    # Strip <think>...</think> reasoning (reasoning models emit it)
    after = text.split("</think>")[-1].strip() if "</think>" in text else text

    start, end = after.find("{"), after.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(after[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _stamp(
    role: str, model: str, raw: str, parsed: dict[str, Any] | None, latency_s: float
) -> dict[str, Any]:
    """Build a provenance-stamped artifact dict. Every output is ai_generated."""
    return {
        "role": role,
        "model": model,
        "content": raw,
        "parsed": parsed,
        "provenance": PROVENANCE_TAG,  # invariant #3: always ai_generated
        "latency_s": round(latency_s, 2),
    }


def chat(
    prompt: str,
    model: str,
    base_url: str = "http://localhost:11434",
    system: str = "",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 180,
    expect_json: bool = True,
    role: str = "unknown",
) -> dict[str, Any]:
    """One chat completion against the local Ollama endpoint.

    Returns an Artifact dict (see ``_stamp``). On failure returns an artifact
    with an ``error`` field — never raises to the caller, so the proof harness
    can record a clean "model unavailable / errored" row rather than crash.

    Args:
        prompt: the user message.
        model: Ollama model tag (e.g. "qwen3.6:27b").
        base_url: Ollama host (default localhost).
        system: optional system message.
        temperature / max_tokens: sampling controls.
        expect_json: if True, attempt to parse JSON out of the response.
        role: label stamped into the artifact ("generator" / "critic" / ...).
    """
    import time

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
    ).encode("utf-8")

    # Ollama exposes an OpenAI-compatible /v1/chat/completions route.
    url = base_url.rstrip("/") + "/v1/chat/completions"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return _stamp(role, model, "", None, time.time() - t0) | {
            "error": f"connection: {e.reason}",
        }
    except Exception as e:  # pragma: no cover - defensive
        return _stamp(role, model, "", None, time.time() - t0) | {
            "error": f"{type(e).__name__}: {e}",
        }

    latency = time.time() - t0
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    # Thinking models emit chain-of-thought separately from the answer. Ollama
    # puts it under `reasoning`; OpenAI-compatible servers use `reasoning_content`.
    # Prefer the answer (`content`); fall back to the reasoning field only if the
    # model placed its whole reply there.
    raw = (
        message.get("content") or message.get("reasoning") or message.get("reasoning_content") or ""
    )
    parsed = extract_json(raw) if expect_json else None
    return _stamp(role, model, raw, parsed, latency) | {
        "finish_reason": choice.get("finish_reason", ""),
    }


def model_available(
    model: str, base_url: str = "http://localhost:11434", timeout: int = 10
) -> bool:
    """True if ``model`` is pulled locally and ready to serve."""
    try:
        with urllib.request.urlopen(
            base_url.rstrip("/") + "/v1/models",
            timeout=timeout,
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return False
    names = {m.get("id", "") for m in data.get("data", [])}
    # Ollama sometimes reports id with or without a ":latest"-style suffix.
    return model in names or any(n.split(":")[0] == model.split(":")[0] for n in names)
