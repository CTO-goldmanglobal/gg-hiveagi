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
        print(f"❌ 唔係目錄：{package_dir}", file=sys.stderr)
        return 1

    client = make_client(mock=args.mock)
    if not args.mock and not client.is_available():
        print(
            f"❌ Kubo daemon 唔可用（{client.api_url}）。\n"
            "   裝 kubo 後跑 `ipfs daemon`，或用 --mock 測試。",
            file=sys.stderr,
        )
        return 1

    files = SeedPackagePackager.serialize(package_dir)
    if not files:
        print(f"❌ Package 目錄空：{package_dir}", file=sys.stderr)
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
        print(f"   ⚠️  Mock mode —— CID 係本地模擬，唔係真 IPFS")
    else:
        print(f"   分享俾其他人：python -m p2p_exchange resolve --cid {cid}")
    return 0


def cmd_verify(args) -> int:
    package_dir = Path(args.package)
    if not package_dir.is_dir():
        print(f"❌ 唔係目錄：{package_dir}", file=sys.stderr)
        return 1

    result = verify_package(package_dir, args.cid)
    print(result)
    return 0 if result.ok else 1


def cmd_resolve(args) -> int:
    client = make_client(mock=args.mock)
    if not args.mock and not client.is_available():
        print(
            f"❌ Kubo daemon 唔可用（{client.api_url}）。\n"
            "   或用 --mock 由本地 mock store resolve。",
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
    print(f"   {len(files)} 個 file 重建完成")
    return 0


def cmd_list(args) -> int:
    entries = load_registry(Path(args.registry))
    if not entries:
        print(f"（registry 空：{args.registry}）")
        return 0
    print(f"📜 Registry ({args.registry}) — {len(entries)} 筆：\n")
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

    common_mock = dict(action="store_true", help="Mock 模式（唔使 IPFS daemon）")
    common_registry = dict(default="p2p_registry.json", help="Registry 檔案路徑")

    p_pub = sub.add_parser("publish", help="發佈 Seed Package → CID")
    p_pub.add_argument("--package", required=True, help="Seed Package 目錄")
    p_pub.add_argument("--mock", **common_mock)
    p_pub.add_argument("--registry", **common_registry)
    p_pub.set_defaults(func=cmd_publish)

    p_ver = sub.add_parser("verify", help="驗證 package 內容同 CID 一致")
    p_ver.add_argument("--package", required=True, help="Seed Package 目錄")
    p_ver.add_argument("--cid", required=True, help="預期嘅 CID")
    p_ver.add_argument("--mock", **common_mock)
    p_ver.add_argument("--registry", **common_registry)
    p_ver.set_defaults(func=cmd_verify)

    p_res = sub.add_parser("resolve", help="用 CID 拉 package")
    p_res.add_argument("--cid", required=True, help="要 resolve 嘅 CID")
    p_res.add_argument("--out", required=True, help="輸出目錄")
    p_res.add_argument("--mock", **common_mock)
    p_res.add_argument("--registry", **common_registry)
    p_res.set_defaults(func=cmd_resolve)

    p_list = sub.add_parser("list", help="列本地 registry")
    p_list.add_argument("--registry", **common_registry)
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
