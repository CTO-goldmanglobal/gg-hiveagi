"""
P2P Exchange — Project Hive.AGI P2

Seed Package content-addressed publish + verify + resolve.
Trust layer: signed manifests, spam filter, appreciation + contribution boards.
"""

from .client import P2PClient, MockP2PClient, KuboP2PClient, make_client
from .cid import compute_mock_cid
from .package import SeedPackagePackager
from .registry import load_registry, add_entry, find_by_cid
from .verify import verify_package, VerifyResult

__version__ = "2.0.0"

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

# Trust layer (optional — requires cryptography package)
try:
    from .identity import (
        generate_keypair, peer_id_from_public_key,
        sign_manifest, verify_manifest,
        init_identity, load_keypair, load_peer_id,
    )
    from .reputation import SpamFilter
    from .appreciation import AppreciationBoard, create_appreciation, sign_appreciation
    from .boards import ContributionBoard, ImprovementBoard

    __all__.extend([
        "generate_keypair", "peer_id_from_public_key",
        "sign_manifest", "verify_manifest",
        "init_identity", "load_keypair", "load_peer_id",
        "SpamFilter",
        "AppreciationBoard", "create_appreciation", "sign_appreciation",
        "ContributionBoard", "ImprovementBoard",
    ])
except ImportError:
    pass  # cryptography not installed — trust layer unavailable
