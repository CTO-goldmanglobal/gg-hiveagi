"""
Tests for the spam filter (p2p_exchange/reputation.py).

The machine's only job: move junk out of the human's way.
Like email spam: fast, automatic, imperfect, human-overridable.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("cryptography")

from p2p_exchange.reputation import SpamFilter, SPAM_THRESHOLD, FLAG_THRESHOLD
from p2p_exchange.identity import (
    generate_keypair, peer_id_from_public_key, sign_manifest, verify_manifest,
)


class TestSpamFilterBasics:
    def test_new_peer_not_spam(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        assert sf.is_spam("hive_new") is False
        assert sf.should_show_in_inbox("hive_new") is True

    def test_new_peer_score_zero(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        assert sf.get_score("hive_new") == 0.0

    def test_invalid_signature_lowers_score(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_invalid_signature("hive_attacker")
        assert sf.get_score("hive_attacker") < 0.0

    def test_two_invalid_signatures_triggers_spam(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_invalid_signature("hive_attacker")
        sf.record_invalid_signature("hive_attacker")
        assert sf.is_spam("hive_attacker") is True
        assert sf.should_show_in_inbox("hive_attacker") is False

    def test_good_tag_keeps_healthy(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        for _ in range(20):
            sf.record_good_tag("hive_healthy")
        assert sf.is_spam("hive_healthy") is False
        assert sf.should_show_in_inbox("hive_healthy") is True

    def test_spam_report_immediate(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_spam_report("hive_spammer")
        assert sf.is_spam("hive_spammer") is True

    def test_flagged_between_spam_and_healthy(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        # One bad tag = -0.3, between flag (-1.0) and spam (-3.0)
        sf.record_bad_tag("hive_questionable", "low quality tags")
        assert sf.is_flagged("hive_questionable") is True
        assert sf.is_spam("hive_questionable") is False


class TestHumanOverride:
    def test_manual_keep_overrides_spam(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_spam_report("hive_misjudged")
        assert sf.is_spam("hive_misjudged") is True

        # Human says "this is NOT spam"
        sf.manual_keep("hive_misjudged")
        assert sf.is_spam("hive_misjudged") is False
        assert sf.should_show_in_inbox("hive_misjudged") is True

    def test_manual_spam_overrides_healthy(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        # Healthy peer
        for _ in range(20):
            sf.record_good_tag("hive_trusted")
        assert sf.is_spam("hive_trusted") is False

        # Human says "this IS spam"
        sf.manual_spam("hive_trusted")
        assert sf.is_spam("hive_trusted") is True

    def test_manual_keep_persists_after_new_bad_events(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.manual_keep("hive_protected")
        sf.record_bad_tag("hive_protected", "bad tag")
        sf.record_bad_tag("hive_protected", "another bad tag")
        # Still not spam because human overrode
        assert sf.is_spam("hive_protected") is False


class TestSpamFolderOperations:
    def test_get_spam_list(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_spam_report("hive_spam1")
        sf.record_spam_report("hive_spam2")
        spam = sf.get_spam_list()
        assert "hive_spam1" in spam
        assert "hive_spam2" in spam

    def test_get_flagged_list(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_bad_tag("hive_flagged", "questionable")
        flagged = sf.get_flagged_list()
        assert "hive_flagged" in flagged

    def test_summary(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_good_tag("hive_ok")
        sf.record_spam_report("hive_bad")
        sf.record_bad_tag("hive_maybe", "questionable")
        s = sf.summary()
        assert s["total_peers_tracked"] == 3
        assert s["in_spam"] >= 1

    def test_render_spam_report(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        sf.record_good_tag("hive_ok")
        sf.record_spam_report("hive_bad")
        text = sf.render_spam_report()
        assert "Inbox" in text
        assert "Spam" in text

    def test_persistence(self, tmp_path):
        sf1 = SpamFilter(tmp_path / "spam.json")
        sf1.record_spam_report("hive_bad")
        sf2 = SpamFilter(tmp_path / "spam.json")
        assert sf2.is_spam("hive_bad") is True


class TestSignedManifestIntegration:
    """Integration: spam filter + signed manifests work together."""

    def test_valid_signed_package_not_flagged(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        priv, pub = generate_keypair()
        peer_id = peer_id_from_public_key(pub)

        manifest = {"contributor": peer_id, "entries": 5}
        signed = sign_manifest(manifest, priv)
        valid, msg = verify_manifest(signed, pub)

        assert valid
        assert sf.is_spam(peer_id) is False

    def test_tampered_package_flagged(self, tmp_path):
        sf = SpamFilter(tmp_path / "spam.json")
        priv, pub = generate_keypair()
        peer_id = peer_id_from_public_key(pub)

        manifest = {"contributor": peer_id, "entries": 5}
        signed = sign_manifest(manifest, priv)

        # Tamper
        signed["contributor"] = "attacker"
        valid, msg = verify_manifest(signed, pub)
        assert not valid

        # Record the invalid signature
        sf.record_invalid_signature(peer_id)
        assert sf.is_flagged(peer_id) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
