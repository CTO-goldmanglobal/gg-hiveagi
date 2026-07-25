"""
完整性校驗 —— recompute CID，對比預期值。

呢個係 content-addressing 嘅核心價值：
收到一個 package + 聲稱嘅 CID，可以自行驗證內容有冇俾人改過。
"""

from pathlib import Path

from .cid import compute_mock_cid, looks_like_mock_cid
from .package import SeedPackagePackager


class VerifyResult:
    def __init__(self, ok: bool, expected_cid: str, actual_cid: str, note: str = ""):
        self.ok = ok
        self.expected_cid = expected_cid
        self.actual_cid = actual_cid
        self.note = note

    def __repr__(self) -> str:
        mark = "✅" if self.ok else "❌"
        return f"{mark} expected={self.expected_cid} actual={self.actual_cid} {self.note}"


def verify_package(package_dir: Path, expected_cid: str) -> VerifyResult:
    """
    對 Seed Package 目錄 recompute mock CID，對比 expected_cid。

    Args:
        package_dir: 本地 package 目錄
        expected_cid: 聲稱嘅 CID（由 publish 時取得）

    Returns:
        VerifyResult
    """
    files = SeedPackagePackager.serialize(Path(package_dir))

    if looks_like_mock_cid(expected_cid):
        actual = compute_mock_cid(files)
        ok = (actual == expected_cid)
        note = "" if ok else "Content does not match the CID — may have been altered / corrupted"
        return VerifyResult(ok, expected_cid, actual, note)

    # 非 mock CID（真 kubo CID）—— 本地 recompute 唔適用
    # （kubo CID 取決於 UnixFS chunking / DAG 結構，唔係單純 content hash）
    return VerifyResult(
        ok=False,
        expected_cid=expected_cid,
        actual_cid="<kubo-cid:recompute-not-supported>",
        note=(
            "A real kubo CID cannot be recomputed locally (requires ipfs daemon)."
            "Use `ipfs cat <CID> | sha256sum` to verify the raw bytes yourself."
        ),
    )
