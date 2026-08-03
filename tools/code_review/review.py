"""
Code Review Harness — GLM-5.2 writes, DeepSeek V4 Flash reviews.

Usage:
  python -m tools.code_review review --file videogen/edl.py
  python -m tools.code_review review --file videogen/edl.py --fix

Workflow:
  1. Read the target Python file
  2. Send to DeepSeek V4 Flash for review
  3. DeepSeek returns: issues found, severity, suggested fixes
  4. If --fix: apply auto-fixable issues, re-review
  5. Output: review report (JSON + human-readable)

This is the "high quality coding" loop:
  GLM writes code → DeepSeek reviews → GLM fixes → DeepSeek re-reviews → ship
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional


def _get_key() -> str:
    """Resolve DeepSeek API key."""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DEEPSEEK_API_KEY not found in env or .env")


def _get_minimax_key() -> str:
    """Resolve MiniMax API key (for secondary review if needed)."""
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""  # optional, not required


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response (handles <think>, code blocks, etc.)."""
    import re

    # Try fenced code blocks first
    blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if blocks:
        try:
            return json.loads(blocks[-1])
        except json.JSONDecodeError:
            pass

    # Try after </think>
    if "</think>" in text:
        after = text.split("</think>")[-1].strip()
    else:
        after = text

    # Find first { to last }
    start = after.find("{")
    end = after.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(after[start:end])
        except json.JSONDecodeError:
            pass

    return None


def review_code(
    file_path: Path,
    context: str = "",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a Python file to DeepSeek V4 Flash for code review.

    Args:
        file_path: path to the .py file
        context: additional context (what this module does, where it fits)
        api_key: DeepSeek key (auto-resolved if None)

    Returns:
        Review dict: {issues: [...], summary: "...", overall_score: N, ...}
    """
    key = api_key or _get_key()
    code = file_path.read_text(encoding="utf-8")

    prompt = f"""You are a senior code reviewer. Review this Python file for quality, correctness, and best practices.

FILE: {file_path.name}
CONTEXT: {context or "Part of Project HiveAGI — a distributed human-perspective intelligence system."}

CODE:
```python
{code[:6000]}
```

Review for:
1. Bugs (logic errors, edge cases, missing error handling)
2. Security (injection, path traversal, unsafe operations)
3. Type safety (missing type hints, wrong types)
4. Naming and readability
5. Architecture (does it fit a distributed, P2P, provenance-gated system?)
6. Test coverage gaps (what's NOT tested that should be?)
7. Documentation (docstrings, comments)
8. Performance (obvious bottlenecks)

Return JSON:
{{
  "overall_score": 1-10,
  "summary": "one sentence overall assessment",
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "category": "bug|security|types|readability|architecture|testing|docs|performance",
      "location": "line number or function name",
      "description": "what's wrong",
      "suggested_fix": "specific code or description of fix"
    }}
  ],
  "strengths": ["what's done well"],
  "ship_ready": true/false
}}"""

    payload = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "You are a brutally honest senior code reviewer. Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2, "max_tokens": 5000,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw = data["choices"][0]["message"]["content"]
        result = _extract_json(raw)
        if result:
            result["file"] = str(file_path)
            result["reviewed_by"] = "deepseek-v4-flash"
            return result
        return {"file": str(file_path), "error": "parse failed", "raw": raw[:300]}
    except Exception as e:
        return {"file": str(file_path), "error": str(e)}


def review_module(
    module_path: Path,
    context: str = "",
) -> List[Dict[str, Any]]:
    """
    Review all .py files in a module directory.
    """
    py_files = sorted(module_path.glob("**/*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]
    reviews = []
    for f in py_files:
        print(f"  📄 reviewing {f.relative_to(module_path.parent)}...", end="", flush=True)
        review = review_code(f, context=context)
        score = review.get("overall_score", "?")
        ship = review.get("ship_ready", False)
        issues = len(review.get("issues", []))
        icon = "✅" if ship else "⚠️"
        print(f" {icon} score={score} issues={issues}")
        reviews.append(review)
    return reviews


def format_report(reviews: List[Dict[str, Any]]) -> str:
    """Format reviews into a human-readable report."""
    lines = []
    lines.append("═" * 60)
    lines.append("  CODE REVIEW REPORT — DeepSeek V4 Flash")
    lines.append("═" * 60)
    lines.append("")

    total_score = 0
    scored = 0
    total_issues = 0
    critical = 0

    for r in reviews:
        if "error" in r:
            lines.append(f"  ❌ {r['file']}: {r['error']}")
            continue

        score = r.get("overall_score", 0)
        total_score += score
        scored += 1
        total_issues += len(r.get("issues", []))
        crit = sum(1 for i in r.get("issues", []) if i.get("severity") == "critical")
        critical += crit

        ship = r.get("ship_ready", False)
        icon = "✅" if ship else "⚠️"
        fname = Path(r.get("file", "?")).name

        lines.append(f"  {icon} {fname:<30} score={score}/10  issues={len(r.get('issues', []))}  critical={crit}")
        lines.append(f"     {r.get('summary', '')}")

        for issue in r.get("issues", []):
            sev = issue.get("severity", "?")
            cat = issue.get("category", "?")
            loc = issue.get("location", "?")
            desc = issue.get("description", "")[:70]
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
            lines.append(f"     {sev_icon} [{sev:>8}] {cat:<12} @ {loc}: {desc}")

        if r.get("strengths"):
            lines.append(f"     💪 strengths: {', '.join(r['strengths'][:2])}")
        lines.append("")

    if scored:
        avg = total_score / scored
        lines.append("─" * 60)
        lines.append(f"  AVERAGE SCORE: {avg:.1f}/10")
        lines.append(f"  TOTAL ISSUES: {total_issues} ({critical} critical)")
        lines.append(f"  FILES SHIP-READY: {sum(1 for r in reviews if r.get('ship_ready'))}/{scored}")
        lines.append("═" * 60)

    return "\n".join(lines)


def cmd_review(args) -> int:
    """Review a file or module."""
    target = Path(args.file).resolve()

    if target.is_dir():
        print(f"\n▶ Reviewing module: {target}\n")
        reviews = review_module(target, context=args.context)
    elif target.is_file():
        print(f"\n▶ Reviewing: {target}\n")
        reviews = [review_code(target, context=args.context)]
    else:
        print(f"❌ not found: {target}", file=sys.stderr)
        return 1

    report = format_report(reviews)
    print(report)

    # Save report
    report_path = target.parent / f"{target.stem}_review.json" if target.is_file() else target / "module_review.json"
    report_data = {
        "reviews": reviews,
        "report": report,
    }
    report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📁 saved to {report_path}")

    # Exit code: 0 if all ship-ready, 1 if issues
    has_critical = any(
        any(i.get("severity") == "critical" for i in r.get("issues", []))
        for r in reviews
    )
    return 1 if has_critical else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="code_review",
        description="Code review harness — DeepSeek V4 Flash reviews code",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_review = sub.add_parser("review", help="Review a file or module")
    p_review.add_argument("--file", required=True, help="Path to .py file or module directory")
    p_review.add_argument("--context", default="", help="What this module does")
    p_review.set_defaults(func=cmd_review)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
