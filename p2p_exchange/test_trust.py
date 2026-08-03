"""
Tests for p2p_exchange/identity.py + reputation.py — the trust layer.
"""

import json
import tempfile
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Skip all tests if cryptography not installed
pytest.importorskip("cryptography")

from p2p_exchange.identity import (
    generate_keypair, peer_id_from_public_key, save_keypair, load_keypair,
    load_peer_id, init_identity, sign_manifest, verify_manifest,
    embed_public_key,
)
from p2p_exchange.reputation import (
    ReputationStore, REPUTATION_NEUTRAL, REPUTATION_TRUSTED,
    REPUTATION_UNTRUSTED, PUBLISH_GATE,
)


class TestKeypairGeneration:
    def test_generate_keypair(self):
        priv, pub = generate_keypair()
        assert b"PRIVATE KEY" in priv
        assert b"PUBLIC KEY" in pub

    def test_peer_id_format(self):
        _, pub = generate_keypair()
        peer_id = peer_id_from_public_key(pub)
        assert peer_id.startswith("hive_")
        assert len(peer_id) == 21  # hive_ + 16 chars

    def test_unique_keypairs(self):
        priv1, pub1 = generate_keypair()
        priv2, pub2 = generate_keypair()
        assert priv1 != priv2
        assert pub1 != pub2

    def test_unique_peer_ids(self):
        _, pub1 = generate_keypair()
        _, pub2 = generate_keypair()
        assert peer_id_from_public_key(pub1) != peer_id_from_public_key(pub2)


class TestIdentityStorage:
    def test_save_and_load(self, tmp_path):
        priv, pub = generate_keypair()
        save_keypair(priv, pub, tmp_path / "identity")
        loaded_priv, loaded_pub = load_keypair(tmp_path / "identity")
        assert loaded_priv == priv
        assert loaded_pub == pub

    def test_load_peer_id(self, tmp_path):
        priv, pub = generate_keypair()
        save_keypair(priv, pub, tmp_path / "identity")
        peer_id = load_peer_id(tmp_path / "identity")
        assert peer_id.startswith("hive_")

    def test_init_creates_new(self, tmp_path):
        peer_id = init_identity(tmp_path / "identity")
        assert peer_id.startswith("hive_")
        assert (tmp_path / "identity" / "private_key.pem").exists()

    def test_init_reuses_existing(self, tmp_path):
        id1 = init_identity(tmp_path / "identity")
        id2 = init_identity(tmp_path / "identity")
        assert id1 == id2  # same keypair reused


class TestSignedManifest:
    def test_sign_and_verify(self, tmp_path):
        priv, pub = generate_keypair()
        manifest = {
            "contributor_id": "test_user",
            "domain": "tourism",
            "entries": 5,
        }
        signed = sign_manifest(manifest, priv)
        assert "signature" in signed
        assert "publisher_peer_id" in signed
        assert "signed_at" in signed

        valid, msg = verify_manifest(signed, pub)
        assert valid is True
        assert "valid" in msg.lower()

    def test_tamper_detection(self, tmp_path):
        priv, pub = generate_keypair()
        manifest = {"contributor_id": "honest", "entries": 5}
        signed = sign_manifest(manifest, priv)

        # Tamper: change content after signing
        signed["contributor_id"] = "attacker"

        valid, msg = verify_manifest(signed, pub)
        assert valid is False
        assert "failed" in msg.lower()

    def test_wrong_key_fails(self, tmp_path):
        priv1, pub1 = generate_keypair()
        priv2, pub2 = generate_keypair()

        manifest = {"data": "test"}
        signed = sign_manifest(manifest, priv1)

        # Verify with wrong key
        valid, msg = verify_manifest(signed, pub2)
        assert valid is False

    def test_unsigned_manifest_fails(self):
        manifest = {"data": "no signature here"}
        valid, msg = verify_manifest(manifest, b"any_key")
        assert valid is False
        assert "no signature" in msg.lower()

    def test_embed_public_key(self):
        priv, pub = generate_keypair()
        manifest = {"data": "test"}
        # Use embed_key=True so public key is embedded during signing
        signed = sign_manifest(manifest, priv, embed_key=True)

        # Verify without providing external key (uses embedded)
        valid, msg = verify_manifest(signed)
        assert valid is True


class TestReputation:
    def test_new_peer_neutral(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        assert store.get_score("hive_newpeer") == REPUTATION_NEUTRAL
        assert store.get_status("hive_newpeer") == "neutral"

    def test_good_tag_increases(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        store.record_good_tag("hive_peer1", "accepted tag on warriors")
        assert store.get_score("hive_peer1") > REPUTATION_NEUTRAL

    def test_bad_tag_decreases(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        store.record_bad_tag("hive_peer1", "spam tag")
        assert store.get_score("hive_peer1") < REPUTATION_NEUTRAL

    def test_invalid_signature_heavy_penalty(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        store.record_invalid_signature("hive_attacker")
        assert store.get_score("hive_attacker") <= REPUTATION_UNTRUSTED

    def test_spam_makes_untrusted(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        store.record_spam("hive_spammer")
        assert store.get_status("hive_spammer") == "untrusted"

    def test_trust_threshold(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        # Build up reputation with 50 good tags
        for _ in range(50):
            store.record_good_tag("hive_reliable")
        assert store.get_status("hive_reliable") == "trusted"
        assert store.can_publish("hive_reliable") is True
        assert store.should_accept_tags("hive_reliable") is True

    def test_publish_gate_blocks_new_peers(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        # New peer with 0 reputation cannot publish
        assert store.can_publish("hive_newbie") is False

    def test_persistence(self, tmp_path):
        """Reputation survives restart."""
        store1 = ReputationStore(tmp_path / "rep.json")
        store1.record_good_tag("hive_peer1")
        score1 = store1.get_score("hive_peer1")

        # New instance loads from disk
        store2 = ReputationStore(tmp_path / "rep.json")
        assert store2.get_score("hive_peer1") == score1

    def test_summary(self, tmp_path):
        store = ReputationStore(tmp_path / "rep.json")
        # Create trusted, neutral, untrusted peers
        for _ in range(60):
            store.record_good_tag("hive_trusted")
        store.record_invalid_signature("hive_bad")
        summary = store.summary()
        assert summary["total_peers"] >= 2
        assert summary["trusted"] >= 1
        assert summary["untrusted"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
