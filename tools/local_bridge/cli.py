"""
CLI for the Local Development Bridge.

  python -m tools.local_bridge "<task>"            # run the full blind-critic loop
  python -m tools.local_bridge --prove              # run the Phase-1 proof harness
  python -m tools.local_bridge --prove 1_planted_bug  # one task

The default mode runs the loop end-to-end on one task:
  generator (Draft A) → blind critic (checklist, then review) → print result.
Every printed artifact carries an ai_generated provenance tag.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

from . import critic, generator, ollama


def _load_config() -> dict[str, Any]:
    cfg_path = Path(__file__).parent / "config.toml"
    with open(cfg_path, "rb") as f:
        return tomllib.load(f)


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _load_config()
    model = cfg["models"]["generator"]
    base_url = cfg["ollama"]["base_url"]

    if not ollama.model_available(model, base_url):
        print(f"ERROR: model '{model}' not available. Run: ollama pull {model}", file=sys.stderr)
        return 2

    print(f"▶ generator ({model}) → Draft A")
    draft = generator.draft(
        args.task,
        spec=args.spec,
        model=model,
        base_url=base_url,
        temperature=cfg["generation"]["temperature"],
        max_tokens=cfg["generation"]["max_tokens"],
        timeout=cfg["ollama"]["timeout_s"],
    )
    if draft.get("error"):
        print(f"  generator error: {draft['error']}", file=sys.stderr)
        return 1
    print(f"  done ({draft['latency_s']}s, provenance={draft['provenance']})\n")

    print(f"▶ blind critic ({model}) → failure checklist [DRAFT NOT IN CONTEXT]")
    checklist = critic.failure_checklist(
        args.task,
        spec=args.spec,
        model=model,
        base_url=base_url,
        temperature=cfg["critique"]["temperature"],
        max_tokens=cfg["critique"]["max_tokens"],
        timeout=cfg["ollama"]["timeout_s"],
    )
    if checklist.get("error"):
        print(f"  checklist error: {checklist['error']}", file=sys.stderr)
        return 1
    cl = checklist.get("parsed") or {}
    for item in cl.get("failure_checklist", []):
        print(f"  - {item}")
    print("\n▶ blind critic → review Draft A against checklist")
    review = critic.review_against(
        draft["content"],
        checklist,
        task=args.task,
        spec=args.spec,
        model=model,
        base_url=base_url,
        temperature=cfg["generation"]["temperature"],
        max_tokens=cfg["generation"]["max_tokens"],
        timeout=cfg["ollama"]["timeout_s"],
    )
    if review.get("error"):
        print(f"  review error: {review['error']}", file=sys.stderr)
        return 1
    defects = (review.get("parsed") or {}).get("defects", [])
    print(f"  {len(defects)} defect(s)\n")

    print("─" * 60)
    print("DRAFT A:")
    print(draft["content"][:1500])
    print("─" * 60)
    print("DEFECTS:")
    for d in defects:
        sev = d.get("severity", "?")
        print(f"  [{sev}] {d.get('checklist_item', '')}: {d.get('defect', '')}")
    overall = (review.get("parsed") or {}).get("overall", "")
    if overall:
        print(f"\nOVERALL: {overall}")
    print(f"\n(provenance: {draft['provenance']} / {review['provenance']})")
    return 0


def cmd_prove(args: argparse.Namespace) -> int:
    from . import prove

    return prove.main(args.tasks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="local_bridge",
        description="Local Development Bridge — blind-critic coding loop (System B).",
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Run the blind-critic loop on one task")
    p_run.add_argument("task", help="The task to solve")
    p_run.add_argument("--spec", default="", help="Optional spec/constraints")
    p_run.set_defaults(func=cmd_run)

    p_prove = sub.add_parser("prove", help="Run the Phase-1 proof harness")
    p_prove.add_argument("tasks", nargs="*", help="Optional subset of task names")
    p_prove.set_defaults(func=cmd_prove)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
