"""
Peer identity + signed manifests — the trust foundation for P2P exchange.

This module addresses DeepSeek's critical finding:
  "CIDs only prove a byte-identical package. They do not tell WHO published
   it, WHEN, or whether it supersedes an earlier one."

Solution:
  1. Each contributor generates an Ed25519 keypair (peer identity)
  2. Every Seed Package manifest is signed by the publisher's private key
  3. Receivers verify the signature against the publisher's public key
  4. A reputation system tracks trustworthiness over time

The keypair is stored locally (never shared). The public key is published
with Seed Packages. Identity = public key hash. No central registration.

Dependencies: cryptography (pip install cryptography)
"""

import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Any

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ============================================================
# Peer identity — Ed25519 keypair generation + storage
# ============================================================


def generate_keypair() -> tuple[bytes, bytes]:
    """
    Generate a new Ed25519 keypair.

    Returns:
        (private_key_pem, public_key_pem) — both as bytes.
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography package required: pip install cryptography")
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def peer_id_from_public_key(public_key_pem: bytes) -> str:
    """
    Derive a short peer ID from a public key.

    Format: "hive_" + first 16 chars of SHA256(public_key_pem)
    This is the contributor's identity on the network — derived from their
    key, not self-declared. Anyone can verify it.
    """
    digest = hashlib.sha256(public_key_pem).hexdigest()
    return f"hive_{digest[:16]}"


def save_keypair(private_key_pem: bytes, public_key_pem: bytes, path: Path) -> None:
    """Save keypair to disk (gitignored — never commit private keys)."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "private_key.pem").write_bytes(private_key_pem)
    (path / "public_key.pem").write_bytes(public_key_pem)
    # Write peer_id for convenience
    peer_id = peer_id_from_public_key(public_key_pem)
    (path / "peer_id.txt").write_text(peer_id, encoding="utf-8")


def load_keypair(path: Path) -> tuple[bytes, bytes]:
    """Load keypair from disk."""
    path = Path(path)
    priv = (path / "private_key.pem").read_bytes()
    pub = (path / "public_key.pem").read_bytes()
    return priv, pub


def load_peer_id(path: Path) -> str:
    """Load peer ID from disk."""
    path = Path(path)
    return (path / "peer_id.txt").read_text(encoding="utf-8").strip()


def init_identity(identity_dir: Path) -> str:
    """
    Initialize a new peer identity if one doesn't exist.
    Returns the peer_id.
    """
    identity_dir = Path(identity_dir)
    if (identity_dir / "private_key.pem").exists():
        _, pub = load_keypair(identity_dir)
        return peer_id_from_public_key(pub)

    priv, pub = generate_keypair()
    save_keypair(priv, pub, identity_dir)
    return peer_id_from_public_key(pub)


# ============================================================
# Signed manifests — bind Seed Package to publisher
# ============================================================


def sign_manifest(
    manifest: dict[str, Any],
    private_key_pem: bytes,
    embed_key: bool = False,
) -> dict[str, Any]:
    """
    Sign a Seed Package manifest with the publisher's private key.

    Adds fields to the manifest:
      - publisher_peer_id: hash of the signer's public key
      - signed_at: ISO timestamp
      - signature: Ed25519 signature of the canonical manifest JSON
      - publisher_public_key (if embed_key=True): base64 public key for
        verification without external key lookup

    Args:
        manifest: the manifest dict (will be modified in place + returned)
        private_key_pem: publisher's private key
        embed_key: if True, embed public key in manifest (for open networks)

    Returns:
        The signed manifest (same dict, with signature fields added).
    """
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography package required")

    # Load private key
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)

    # Get public key
    public_key = private_key.public_key()
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Add metadata BEFORE signing (so it's covered by signature)
    manifest["publisher_peer_id"] = peer_id_from_public_key(pub_pem)
    manifest["signed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if embed_key:
        manifest["publisher_public_key"] = base64.b64encode(pub_pem).decode("ascii")

    # Sign the canonical JSON (sorted keys, no whitespace)
    # Exclude signature field itself from signing
    signing_payload = {k: v for k, v in manifest.items() if k != "signature"}
    canonical = json.dumps(signing_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(canonical)
    manifest["signature"] = base64.b64encode(signature).decode("ascii")

    return manifest


def verify_manifest(
    manifest: dict[str, Any],
    public_key_pem: bytes | None = None,
) -> tuple[bool, str]:
    """
    Verify a signed manifest.

    Args:
        manifest: the manifest dict with signature fields
        public_key_pem: the publisher's public key. If None, looks for
                       publisher_public_key in the manifest (if embedded).

    Returns:
        (valid, message) — True if signature is valid, False + reason if not.
    """
    if not CRYPTO_AVAILABLE:
        return False, "cryptography package not installed"

    sig_b64 = manifest.get("signature")
    if not sig_b64:
        return False, "no signature field in manifest"

    peer_id = manifest.get("publisher_peer_id")
    if not peer_id:
        return False, "no publisher_peer_id in manifest"

    # Reconstruct signing payload (exclude signature field)
    signing_payload = {k: v for k, v in manifest.items() if k != "signature"}
    canonical = json.dumps(signing_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    try:
        signature = base64.b64decode(sig_b64)
    except Exception:
        return False, "signature is not valid base64"

    if public_key_pem is None:
        # Check if public key is embedded in manifest
        pub_b64 = manifest.get("publisher_public_key")
        if pub_b64:
            public_key_pem = base64.b64decode(pub_b64)
        else:
            return False, "no public key provided or embedded in manifest"

    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key.verify(signature, canonical)
        return True, f"signature valid (peer: {peer_id})"
    except Exception as e:
        return False, f"signature verification failed: {e}"


def embed_public_key(manifest: dict[str, Any], public_key_pem: bytes) -> dict[str, Any]:
    """
    Embed the publisher's public key in the manifest (base64).
    This allows verification without a separate key lookup — at the cost
    of larger manifest size (~200 bytes).

    For trusted networks where keys are pre-shared, don't embed.
    For open networks where anyone should verify, embed.
    """
    manifest["publisher_public_key"] = base64.b64encode(public_key_pem).decode("ascii")
    return manifest
