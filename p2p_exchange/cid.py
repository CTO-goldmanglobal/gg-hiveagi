"""
Content addressing — deterministic CIDs for Seed Packages.

同一份 Seed Package 內容，喺任何節點都會產生同一個 CID
（content-addressed，唔係 location-addressed）。
咁貢獻者可以自己 recompute hash 去驗證「我收到嘅 package 有冇俾人改過」，
唔需要任何中央權威。

⚠️  Scope 誠實說明：
    Mock CID 同 kubo 嘅真實 CID 唔會 byte-for-byte 一樣
    （kubo 用 DAG-PB / UnixFS 多層 wrapping）。
    Mock 用 "mockbafy" 前綴 + sha256(content) 去模擬 content-addressing 嘅 *邏輯*，
    令 pipeline 可測。KuboP2PClient 會用 kubo 自己計出嚟嘅真 CID。
"""

import hashlib
from pathlib import Path
from typing import List, Tuple


MOCK_CID_PREFIX = "mockbafy"
# Real IPFS CIDv1 raw codec 都係 "bafy" 開頭（dag-pb）或 "bafk"（raw）。
# 我哋用 "mockbafy" 令 mock CID 一眼可分辨，避免同真 CID 混淆。


def _base32(data: bytes) -> str:
    """RFC 4648 base32（細階，無 padding）—— 同 IPFS CIDv1 風格一致。"""
    import base64
    return base64.b32encode(data).decode("ascii").rstrip("=").lower()


def compute_mock_cid(files: List[Tuple[str, bytes]]) -> str:
    """
    由一組 (相對路徑, 內容 bytes) 計出 deterministic mock CID。

    Canonical serialization（保證順序獨立）：
        對每個 file: SHA256(相對路徑 UTF-8 + b"\\x00" + 內容)
        再 SHA256(串接所有 per-file hash，按 path 排序)
        → base32 編碼 → 加前綴

    Args:
        files: [(rel_path, content), ...] —— 順序唔影響結果

    Returns:
        str: 例如 "mockbafybeiA2K3..."
    """
    if not files:
        raise ValueError("compute_mock_cid: files 列表為空")

    # 排序保證順序獨立
    sorted_files = sorted(files, key=lambda fc: fc[0])

    h = hashlib.sha256()
    for rel_path, content in sorted_files:
        # 每個 file 嘅貢獻：path + null separator + content
        per_file = hashlib.sha256()
        per_file.update(rel_path.encode("utf-8"))
        per_file.update(b"\x00")
        per_file.update(content)
        h.update(per_file.digest())

    return MOCK_CID_PREFIX + _base32(h.digest())


def looks_like_mock_cid(cid: str) -> bool:
    """判斷一個 CID 係唔係 mock CID。"""
    return cid.startswith(MOCK_CID_PREFIX)
