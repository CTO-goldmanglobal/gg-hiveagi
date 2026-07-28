"""
CLI entry: `python -m videogen.clip_pool fetch --config <keywords.yaml>`

Stage 1 of the small-circle loop: fetch candidates into a viewable pool.
"""

import argparse
import sys
from pathlib import Path

from .fetch import fetch_pool, load_keyword_config
from .manifest import write_manifest, write_pool_index_html
from .judge import run_judge
from .llm_tags import pretag_pool
from .adapt import crop_to_portrait, adapt_pool_clips


def _default_pool_dir(config_path: Path) -> Path:
    """Pool lives in a `pool/` dir next to the keywords.yaml config."""
    return config_path.parent / "pool"


def cmd_fetch(args) -> int:
    config_path = Path(args.config).resolve()
    if not config_path.is_file():
        print(f"❌ config not found: {config_path}", file=sys.stderr)
        return 1

    pool_dir = Path(args.pool_dir).resolve() if args.pool_dir else _default_pool_dir(config_path)

    orientations = args.orientations.split(",") if args.orientations else None

    manifest = fetch_pool(
        config_path=config_path,
        pool_dir=pool_dir,
        orientations=orientations,
    )

    manifest_path = write_manifest(manifest, pool_dir)
    html_path = write_pool_index_html(manifest, pool_dir)

    print()
    print(f"  📋 manifest: {manifest_path}")
    print(f"  🌐 gallery:  {html_path}")
    print()
    print("  Next: open the gallery in a browser to review candidates:")
    if sys.platform == "darwin":
        print(f"    open \"{html_path}\"")
    else:
        print(f"    xdg-open \"{html_path}\"")
    return 0


def cmd_judge(args) -> int:
    """Step 2: walk each candidate, capture accept/reject + reason as seed."""
    pool_dir = Path(args.pool_dir).resolve()
    if not pool_dir.is_dir():
        print(f"❌ pool dir not found: {pool_dir}", file=sys.stderr)
        return 1
    return run_judge(
        pool_dir=pool_dir,
        editor_id=args.editor_id,
        shot_filter=args.shot,
        only_undecided=args.only_undecided,
    )


def cmd_pretag(args) -> int:
    """Step 1.5: LLM pre-tag every clip with content dimensions."""
    import json
    pool_dir = Path(args.pool_dir).resolve()
    manifest_path = pool_dir / "pool_manifest.json"
    if not manifest_path.exists():
        print(f"❌ pool_manifest.json not found in {pool_dir}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print("═" * 60)
    print(f"  Clip Pool — PRETAG (MiniMax M3 vision) · tour: {manifest.get('tour')}")
    print("═" * 60)
    pretag_pool(manifest, pool_dir, n_frames=args.frames, force=args.force)
    print("\n  Next: regenerate gallery to see content tags:")
    print(f"    python -m videogen.clip_pool gallery --pool-dir {pool_dir}")
    return 0


def cmd_gallery(args) -> int:
    """Regenerate the pool_index.html gallery (picks up new metrics/tags/verdicts)."""
    import json
    pool_dir = Path(args.pool_dir).resolve()
    manifest_path = pool_dir / "pool_manifest.json"
    if not manifest_path.exists():
        print(f"❌ pool_manifest.json not found in {pool_dir}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    html_path = write_pool_index_html(manifest, pool_dir)
    print(f"✅ gallery regenerated: {html_path}")
    if sys.platform == "darwin":
        import subprocess
        subprocess.Popen(["open", str(html_path)])
    return 0


def cmd_adapt(args) -> int:
    """Crop landscape clips to portrait (9:16)."""
    import json
    pool_dir = Path(args.pool_dir).resolve()
    manifest_path = pool_dir / "pool_manifest.json"
    if not manifest_path.exists():
        print(f"❌ pool_manifest.json not found in {pool_dir}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clip_ids = [c.strip() for c in args.clips.split(",") if c.strip()]
    if not clip_ids:
        print("❌ no clip IDs provided", file=sys.stderr)
        return 1

    print("═" * 60)
    print(f"  Clip Pool — ADAPT (landscape→portrait, {args.mode})")
    print("═" * 60)
    results = adapt_pool_clips(pool_dir, manifest, clip_ids, mode=args.mode)
    print(f"\n  ✅ adapted {len(results)} clips → portrait_adapted/ subdirs")

    # Write an adaptation manifest so the gallery can show them
    adapt_path = pool_dir / "portrait_adaptations.json"
    adapt_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  📋 {adapt_path}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="videogen.clip_pool",
        description="Clip pool fetcher + judgment loop (Goldman Forge / Labs)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Fetch stock candidates into a viewable pool")
    p_fetch.add_argument("--config", required=True,
                         help="Path to keywords.yaml")
    p_fetch.add_argument("--pool-dir", default=None,
                         help="Pool output dir (default: <config_dir>/pool)")
    p_fetch.add_argument("--orientations", default=None,
                         help="Comma-separated: landscape,portrait (default: from config)")
    p_fetch.set_defaults(func=cmd_fetch)

    # judge subcommand — Step 2: human verdict + reason → judgment_log.jsonl
    p_judge = sub.add_parser("judge",
                             help="Judge candidates (accept/reject + reason) — Step 2")
    p_judge.add_argument("--pool-dir", required=True,
                         help="Pool directory (contains pool_manifest.json)")
    p_judge.add_argument("--editor-id", default="founder",
                         help="Who is judging (default: founder)")
    p_judge.add_argument("--shot", default=None,
                         help="Only judge this shot_id (default: all)")
    p_judge.add_argument("--only-undecided", action="store_true",
                         help="Skip clips already judged")
    p_judge.set_defaults(func=cmd_judge)

    # pretag subcommand — Step 1.5: LLM content dimension tagging
    p_pretag = sub.add_parser("pretag",
                              help="LLM pre-tag clips with content dimensions (shot_type, perspective, mood, ...)")
    p_pretag.add_argument("--pool-dir", required=True,
                          help="Pool directory (contains pool_manifest.json)")
    p_pretag.add_argument("--frames", type=int, default=2,
                          help="Frames to sample per clip (default 2)")
    p_pretag.add_argument("--force", action="store_true",
                          help="Re-tag even if cached")
    p_pretag.set_defaults(func=cmd_pretag)

    # gallery subcommand — regenerate pool_index.html
    p_gallery = sub.add_parser("gallery",
                               help="Regenerate the pool_index.html gallery")
    p_gallery.add_argument("--pool-dir", required=True,
                           help="Pool directory")
    p_gallery.set_defaults(func=cmd_gallery)

    # adapt subcommand — landscape→portrait crop
    p_adapt = sub.add_parser("adapt",
                             help="Crop landscape clips to portrait (9:16)")
    p_adapt.add_argument("--pool-dir", required=True,
                         help="Pool directory")
    p_adapt.add_argument("--clips", required=True,
                         help="Comma-separated candidate IDs to adapt")
    p_adapt.add_argument("--mode", default="smart",
                         choices=["center", "smart", "feature"],
                         help="Crop mode: center (blind), smart (LLM-guided), feature (manual)")
    p_adapt.set_defaults(func=cmd_adapt)

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
