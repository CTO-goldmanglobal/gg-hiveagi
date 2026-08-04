"""
LLM Council — multi-model document auditor.

Sends one document (architecture, design, thesis) to multiple LLMs and collects
structured verdicts. Mirrors the write→review loop in tools/code_review/review.py
but for prose/architecture instead of code, and across several models at once.

The pattern: one human-authored artifact, N independent AI reviewers, one
synthesized verdict. This is the "LLM council" pattern used in
docs/internal/LLM-COUNCIL.json and FINAL-AUDIT.json.

Usage:
  python -m tools.audit.council --doc docs/EDGE-CLOUD-ARCHITECTURE-v2.md
  python -m tools.audit.council --doc <path> --models deepseek,kimi,qwen

Each provider is OpenAI-compatible (chat/completions, Bearer auth). Keys are
resolved from the environment, then .env — same convention as review.py. A
provider with no key is reported as skipped, NOT silently omitted.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Provider profiles ------------------------------------------------------
# Each: human name, OpenAI-compatible endpoint, default model, env var names to
# try (in order). Add a provider here and it Just Works in the CLI.
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek V4 Flash",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-v4-flash",
        "key_env": ["DEEPSEEK_API_KEY"],
        "role": "auditor / code reviewer",
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "model": "moonshot-v1-32k",
        "key_env": ["KIMI_API_KEY", "MOONSHOT_API_KEY"],
        "role": "long-context reviewer",
    },
    "qwen": {
        "label": "Qwen (DashScope)",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-plus",
        "key_env": ["DASHSCOPE_API_KEY", "QWEN_API_KEY", "ALIYUN_API_KEY"],
        "role": "frontier Chinese model reviewer",
    },
}


def _resolve_key(env_names: List[str]) -> Optional[str]:
    """Resolve an API key from env or .env (never prints the value)."""
    for name in env_names:
        val = os.environ.get(name, "").strip()
        if val:
            return val.strip('"').strip("'")
    # Fall back to .env in cwd
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                for name in env_names:
                    prefix = f"{name}="
                    if line.startswith(prefix) and not line.startswith("#"):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from an LLM response (handles <think>, code fences)."""
    import re

    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if blocks:
        try:
            return json.loads(blocks[-1])
        except json.JSONDecodeError:
            pass
    after = text.split("</think>")[-1].strip() if "</think>" in text else text
    start, end = after.find("{"), after.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(after[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _review_prompt(doc_text: str, doc_name: str, lean: bool = False) -> str:
    """The council prompt — asks for a structured architecture verdict.

    ``lean=True`` produces a compact prompt that asks for a minimal JSON shape.
    Used as an automatic retry when a reasoning model runs out of token budget
    on the full prompt (finish_reason=length truncating the JSON mid-array).
    """
    context = (
        "CONTEXT: Project HiveAGI — an open-source distributed human-perspective "
        "intelligence network. The project enforces provenance invariants in code "
        "(stock/AI blocked from the open \"Labs\" area; only human-captured signal "
        "is Labs-eligible; PII blur is a human-controlled layer default ON). This "
        "document is a replan of a personal-AI-infrastructure proposal, reconciled "
        "with the project's committed architecture."
    )
    if lean:
        # Minimal shape: keeps the load-bearing verdict fields, drops the long
        # per-issue arrays that starve the token budget under heavy reasoning.
        schema = (
            '{\n'
            '  "reviewer": "model name",\n'
            '  "overall_verdict": "sound | sound-with-revisions | needs-rework | reject",\n'
            '  "confidence_in_review": 1-10,\n'
            '  "one_line": "one sentence assessment",\n'
            '  "weakest_part": "the biggest problem (1-2 sentences)",\n'
            '  "provenance_leakage_risk": "none|low|medium|high + one clause why",\n'
            '  "discard_mitigations_verdict": "sufficient|insufficient + one clause",\n'
            '  "top_3_issues": ["short issue 1", "short issue 2", "short issue 3"],\n'
            '  "would_i_back_this_design": true/false\n'
            '}'
        )
        return (
            f"You are an independent senior reviewer auditing: {doc_name}.\n"
            f"{context}\n\n"
            f"DOCUMENT:\n```\n{doc_text}\n```\n\n"
            "Be honest and concise. Focus on provenance integrity, the discard "
            "problem, the confidence thresholds, and the two-system separation. "
            "Return JSON ONLY matching this shape (keep each field short):\n"
            f"{schema}"
        )
    schema = (
        '{\n'
        '  "reviewer": "your model name",\n'
        '  "overall_verdict": "sound | sound-with-revisions | needs-rework | reject",\n'
        '  "confidence_in_review": 1-10,\n'
        '  "one_line": "one sentence overall assessment",\n'
        '  "strongest_part": "what is genuinely good",\n'
        '  "weakest_part": "the biggest problem",\n'
        '  "provenance_leakage_risk": "none | low | medium | high - with explanation",\n'
        '  "discard_mitigations_verdict": "sufficient | insufficient - what\'s missing",\n'
        '  "answers_to_OQs": {"OQ-1": "...", "OQ-2": "..."},\n'
        '  "issues": [\n'
        '    {"severity": "critical|high|medium|low", "section": "where", "problem": "...", "fix": "..."}\n'
        '  ],\n'
        '  "missing_considerations": ["things the author didn\'t raise but should"],\n'
        '  "would_i_back_this_design": true/false\n'
        '}'
    )
    return (
        "You are an independent senior reviewer on an LLM council auditing a "
        "research/architecture document.\n\n"
        f"DOCUMENT: {doc_name}\n{context}\n\n"
        f"DOCUMENT TEXT:\n```\n{doc_text}\n```\n\n"
        "Review as an independent expert. Be honest — if a claim is unsupported "
        "or risky, say so. Do not flatter. Address the document's own Open "
        "Questions (OQ-1 through OQ-7) where relevant. Also assess:\n"
        "1. Soundness of the architecture and the two-system separation "
        "(capture pipeline vs dev tool).\n"
        "2. Provenance integrity — could AI-generated signal leak into the Labs "
        "data path?\n"
        "3. The discard-problem mitigations — sufficient?\n"
        "4. The confidence-routing thresholds (0.70 edge / 0.85 cloud) — "
        "correctly placed?\n"
        "5. The self-refine \"vibe-coding bridge\" — real value or hype? Any "
        "anchoring-bias risk?\n"
        "6. Cost/feasibility claims — believable?\n"
        "7. Anything missing or wrong that the author didn't ask about.\n\n"
        "Return JSON ONLY:\n" + schema
    )


def audit_with(
    provider: str,
    doc_text: str,
    doc_name: str,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Send the doc to one provider. Returns a verdict dict (or an error dict)."""
    profile = PROVIDERS[provider]
    key = _resolve_key(profile["key_env"])
    if not key:
        return {
            "provider": provider,
            "label": profile["label"],
            "status": "skipped_no_key",
            "hint": f"Set one of: {', '.join(profile['key_env'])} in env or .env",
        }

    system_msg = (
        f"You are {profile['label']} acting as {profile['role']} on an "
        "LLM council. Return JSON only, no preamble."
    )

    # First attempt: full structured prompt. If a reasoning model truncates the
    # JSON (finish_reason=length), retry once with the lean prompt.
    result = _post_and_parse(provider, profile, key, system_msg,
                             _review_prompt(doc_text, doc_name), timeout)
    if result.get("status") == "truncated":
        result = _post_and_parse(provider, profile, key, system_msg,
                                 _review_prompt(doc_text, doc_name, lean=True),
                                 timeout, lean=True)
    return result


def _post_and_parse(
    provider: str,
    profile: Dict[str, Any],
    key: str,
    system_msg: str,
    user_prompt: str,
    timeout: int,
    lean: bool = False,
) -> Dict[str, Any]:
    """One POST + parse attempt. Distinguishes parse-fail from truncation so the
    caller can retry with a leaner prompt."""
    payload = json.dumps({
        "model": profile["model"],
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        # Reasoning models emit chain-of-thought in a separate reasoning_content
        # field that counts against the completion budget. Give generous headroom
        # so reasoning doesn't starve the final answer.
        "max_tokens": 16000,
    }).encode("utf-8")

    req = urllib.request.Request(
        profile["url"],
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choice = data["choices"][0]
        message = choice["message"]
        # Prefer the final answer; fall back to reasoning_content if the model
        # placed the whole answer there.
        raw = message.get("content") or ""
        reasoning = message.get("reasoning_content") or ""
        parsed = _extract_json(raw) or _extract_json(reasoning)
        if parsed:
            parsed["provider"] = provider
            parsed["label"] = profile["label"]
            parsed["status"] = "ok"
            if lean:
                parsed["note"] = "lean retry succeeded after full-prompt truncation"
            return parsed
        # Truncation = the JSON started but ran out of tokens before closing.
        # finish_reason=length with unbalanced braces is the reliable signal.
        finish = choice.get("finish_reason", "")
        looks_truncated = (
            finish == "length"
            or (raw.count("{") > raw.count("}"))
            or (raw.count("{") > 0 and "}" not in raw)
        )
        if looks_truncated and not lean:
            return {"provider": provider, "label": profile["label"],
                    "status": "truncated", "finish_reason": finish,
                    "raw_len": len(raw), "reasoning_len": len(reasoning)}
        return {
            "provider": provider, "label": profile["label"],
            "status": "parse_failed", "finish_reason": finish,
            "raw_head": raw[:400], "reasoning_head": reasoning[:400],
        }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return {"provider": provider, "label": profile["label"],
                "status": f"http_{e.code}", "error": str(e), "body_head": body}
    except Exception as e:
        return {"provider": provider, "label": profile["label"],
                "status": "error", "error": str(e)}


def run_council(
    doc_path: Path,
    models: List[str],
    out_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the council across the requested models. Writes a combined report."""
    doc_text = doc_path.read_text(encoding="utf-8")
    doc_name = doc_path.name

    print(f"Council convening on: {doc_name}")
    print(f"Doc length: {len(doc_text)} chars\n")

    verdicts: List[Dict[str, Any]] = []
    for provider in models:
        if provider not in PROVIDERS:
            print(f"  ⚠️  unknown provider '{provider}' — skipping")
            continue
        print(f"  ▶️  {PROVIDERS[provider]['label']:24} ", end="", flush=True)
        verdict = audit_with(provider, doc_text, doc_name)
        status = verdict.get("status", "unknown")
        if status == "ok":
            print(f"✅ {verdict.get('overall_verdict', '?')} "
                  f"(conf {verdict.get('confidence_in_review', '?')})")
        elif status == "skipped_no_key":
            print(f"⏭️  no key — {verdict.get('hint', '')}")
        else:
            print(f"❌ {status}")
        verdicts.append(verdict)

    report = {
        "doc": str(doc_path),
        "models_requested": models,
        "models_ok": [v["provider"] for v in verdicts if v.get("status") == "ok"],
        "models_skipped": [v["provider"] for v in verdicts if v.get("status") == "skipped_no_key"],
        "models_failed": [v["provider"] for v in verdicts
                          if v.get("status") not in ("ok", "skipped_no_key")],
        "verdicts": verdicts,
    }

    if out_path:
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReport written: {out_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM council document auditor")
    parser.add_argument("--doc", required=True, help="Path to the document to audit")
    parser.add_argument(
        "--models", default="deepseek,kimi,qwen",
        help="Comma-separated provider names (default: deepseek,kimi,qwen)",
    )
    parser.add_argument("--out", help="Optional path to write the JSON report")
    args = parser.parse_args()

    doc_path = Path(args.doc)
    if not doc_path.exists():
        print(f"ERROR: doc not found: {doc_path}", file=sys.stderr)
        return 2

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    out_path = Path(args.out) if args.out else None
    report = run_council(doc_path, models, out_path)

    # Exit non-zero if any requested model was missing a key, so CI/scripts notice.
    if report["models_skipped"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
