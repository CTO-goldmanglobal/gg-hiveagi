"""
P2P Exchange — Project Hive.AGI P2

Seed Package 嘅 content-addressed 發佈 + 驗證 + 解析。
Canonical real impl = kubo (local IPFS daemon) —— 真正去中心化。
Mock 令 pipeline 喺零安裝下可測。
"""

from .client import P2PClient, MockP2PClient, KuboP2PClient, make_client
from .cid import compute_mock_cid
from .package import SeedPackagePackager
from .registry import load_registry, add_entry, find_by_cid
from .verify import verify_package, VerifyResult

__version__ = "1.0.0"

__all__ = [
    "P2PClient",
    "MockP2PClient",
    "KuboP2PClient",
    "make_client",
    "compute_mock_cid",
    "SeedPackagePackager",
    "load_registry",
    "add_entry",
    "find_by_cid",
    "verify_package",
    "VerifyResult",
]
