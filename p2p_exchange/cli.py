"""
CLI —— publish / verify / resolve / list，配 --mock flag。
"""

import argparse
import sys
from pathlib import Path

from .client import make_client
from .package import SeedPackagePackager
from .registry import add_entry, load_registry, find_by_cid
from .verify import verify_package


def _detect_contributor(package_dir: Path) -> str:
    """由 manifest.json 拎 contributor_id（fallback 'unknown'）。"""
    manifest = package_dir / "manifest.json"
    if manifest.exists():
        try:
            import json
            data = json.loads(manifest.read_text(encoding="utf-8"))
            return data.get("contributor_id", "unknown")
        except (ValueError, OSError):
            pass
    return "unknown"


def cmd_publish(args) -> int:
    package_dir = Path(args.package)
    if not package_dir.is_dir():
        print(f"❌ Not a directory: {package_dir}", file=sys.stderr)
        return 1

    client = make_client(mock=args.mock)
    if not args.mock and not client.is_available():
        print(
            f"❌ Kubo daemon is unavailable ({client.api_url}).\n"
            "   Install kubo and run `ipfs daemon`, or test with --mock.",
            file=sys.stderr,
        )
        return 1

    files = SeedPackagePackager.serialize(package_dir)
    if not files:
        print(f"❌ Package directory is empty: {package_dir}", file=sys.stderr)
        return 1

    cid = client.publish(files)
    contributor = _detect_contributor(package_dir)
    package_name = package_dir.name

    add_entry(
        cid=cid,
        package_name=package_name,
        contributor=contributor,
        source_path=str(package_dir),
        path=Path(args.registry),
    )

    print(f"✅ Published: {package_name}")
    print(f"   CID:         {cid}")
    print(f"   Contributor: {contributor}")
    print(f"   Files:       {len(files)}")
    print(f"   Registry:    {args.registry}")
    if args.mock:
        print(f"   ⚠️  Mock mode — CID is a local simulation, not real IPFS")
    else:
        print(f"   Share with others: python -m p2p_exchange resolve --cid {cid}")
    return 0


def cmd_verify(args) -> int:
    package_dir = Path(args.package)
    if not package_dir.is_dir():
        print(f"❌ Not a directory: {package_dir}", file=sys.stderr)
        return 1

    result = verify_package(package_dir, args.cid)
    print(result)
    return 0 if result.ok else 1


def cmd_resolve(args) -> int:
    client = make_client(mock=args.mock)
    if not args.mock and not client.is_available():
        print(
            f"❌ Kubo daemon is unavailable ({client.api_url}).\n"
            "   Or use --mock to resolve from the local mock store.",
            file=sys.stderr,
        )
        return 1

    out_dir = Path(args.out)
    try:
        files = client.resolve(args.cid)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    SeedPackagePackager.deserialize(files, out_dir)
    print(f"✅ Resolved CID: {args.cid}")
    print(f"   → {out_dir}")
    print(f"   {len(files)} file(s) rebuilt")
    return 0


def cmd_list(args) -> int:
    entries = load_registry(Path(args.registry))
    if not entries:
        print(f"(registry is empty: {args.registry})")
        return 0
    print(f"📜 Registry ({args.registry}) — {len(entries)} entry/entries:\n")
    for e in entries:
        print(f"  {e['cid']}")
        print(f"    package:    {e['package_name']}")
        print(f"    contributor:{e['contributor']}")
        print(f"    published:  {e['published_at']}")
        print(f"    source:     {e['source_path']}")
        print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="p2p_exchange",
        description="P2P Seed Package exchange (IPFS / content addressing)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    common_mock = dict(action="store_true", help="Mock mode (no IPFS daemon needed)")
    common_registry = dict(default="p2p_registry.json", help="Registry file path")

    p_pub = sub.add_parser("publish", help="Publish a Seed Package → CID")
    p_pub.add_argument("--package", required=True, help="Seed Package directory")
    p_pub.add_argument("--mock", **common_mock)
    p_pub.add_argument("--registry", **common_registry)
    p_pub.set_defaults(func=cmd_publish)

    p_ver = sub.add_parser("verify", help="Verify package content matches the CID")
    p_ver.add_argument("--package", required=True, help="Seed Package directory")
    p_ver.add_argument("--cid", required=True, help="Expected CID")
    p_ver.add_argument("--mock", **common_mock)
    p_ver.add_argument("--registry", **common_registry)
    p_ver.set_defaults(func=cmd_verify)

    p_res = sub.add_parser("resolve", help="Pull a package by CID")
    p_res.add_argument("--cid", required=True, help="CID to resolve")
    p_res.add_argument("--out", required=True, help="Output directory")
    p_res.add_argument("--mock", **common_mock)
    p_res.add_argument("--registry", **common_registry)
    p_res.set_defaults(func=cmd_resolve)

    p_list = sub.add_parser("list", help="List the local registry")
    p_list.add_argument("--registry", **common_registry)
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
