"""
Tests for p2p_exchange/appreciation.py — human appreciation board.
"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("cryptography")

from p2p_exchange.appreciation import (
    create_appreciation, sign_appreciation, verify_appreciation,
    AppreciationBoard,
)
from p2p_exchange.identity import generate_keypair, peer_id_from_public_key


class TestCreateAppreciation:
    def test_basic_creation(self):
        a = create_appreciation(
            reviewer_peer_id="hive_aaaa",
            reviewed_peer_id="hive_bbbb",
            rating=5,
            domain="tourism",
            headline="Best Warriors tags",
            body="His lighting calls are spot on.",
            interactions=12,
        )
        assert a["rating"] == 5
        assert a["reviewer_peer_id"] == "hive_aaaa"
        assert a["type"] == "appreciation"
        assert "created_at" in a

    def test_invalid_rating_high(self):
        with pytest.raises(ValueError):
            create_appreciation("hive_a", "hive_b", rating=6)

    def test_invalid_rating_low(self):
        with pytest.raises(ValueError):
            create_appreciation("hive_a", "hive_b", rating=0)

    def test_rating_boundaries(self):
        assert create_appreciation("a", "b", rating=1)["rating"] == 1
        assert create_appreciation("a", "b", rating=5)["rating"] == 5


class TestSignAndVerify:
    def test_sign_and_verify(self):
        priv, pub = generate_keypair()
        reviewer_id = peer_id_from_public_key(pub)

        a = create_appreciation(
            reviewer_peer_id=reviewer_id,
            reviewed_peer_id="hive_target",
            rating=5,
            headline="Great tags",
            body="Very accurate",
        )
        signed = sign_appreciation(a, priv)
        assert "signature" in signed

        valid, msg = verify_appreciation(signed, pub)
        assert valid is True

    def test_tamper_detection(self):
        priv, pub = generate_keypair()
        reviewer_id = peer_id_from_public_key(pub)

        a = create_appreciation(reviewer_id, "hive_target", 5, headline="Great")
        signed = sign_appreciation(a, priv)

        # Tamper: change rating from 5 to 1
        signed["rating"] = 1

        valid, msg = verify_appreciation(signed, pub)
        assert valid is False

    def test_wrong_key_fails(self):
        priv1, pub1 = generate_keypair()
        priv2, pub2 = generate_keypair()
        reviewer_id = peer_id_from_public_key(pub1)

        a = create_appreciation(reviewer_id, "hive_target", 5)
        signed = sign_appreciation(a, priv1)

        valid, msg = verify_appreciation(signed, pub2)
        assert valid is False


class TestAppreciationBoard:
    def test_add_and_retrieve(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        a = create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Great")
        board.add(a)
        assert len(board.for_peer("hive_p1")) == 1

    def test_average_rating(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5))
        board.add(create_appreciation("hive_r2", "hive_p1", 3))
        board.add(create_appreciation("hive_r3", "hive_p1", 4))
        avg = board.average_rating("hive_p1")
        assert avg == pytest.approx(4.0)

    def test_no_reviews_returns_none(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        assert board.average_rating("hive_nobody") is None

    def test_update_replaces_existing(self, tmp_path):
        """Same reviewer updating appreciation for same peer replaces, not duplicates."""
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 3, "tourism", "OK"))
        board.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Actually great"))
        assert len(board.for_peer("hive_p1")) == 1
        assert board.for_peer("hive_p1")[0]["rating"] == 5

    def test_different_domains_not_replaced(self, tmp_path):
        """Same reviewer can appreciate same peer in different domains."""
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Great travel"))
        board.add(create_appreciation("hive_r1", "hive_p1", 3, "food", "Food tags lacking"))
        entries = board.for_peer("hive_p1")
        assert len(entries) == 2

    def test_summary_card(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Excellent"))
        board.add(create_appreciation("hive_r2", "hive_p1", 4, "tourism", "Very good"))
        board.add(create_appreciation("hive_r3", "hive_p1", 5, "food", "Great food tags"))

        s = board.summary("hive_p1")
        assert s["total_reviews"] == 3
        assert s["average"] == pytest.approx(4.7, abs=0.1)
        assert s["stars"]["5"] == 2
        assert s["stars"]["4"] == 1
        assert len(s["top_domains"]) == 2

    def test_render_card(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Best ever"))
        card = board.render_card("hive_p1")
        assert "hive_p1" in card
        assert "★" in card
        assert "Best ever" in card
        assert "5★:1" in card

    def test_render_empty_card(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        card = board.render_card("hive_nobody")
        assert "No appreciations" in card

    def test_persistence(self, tmp_path):
        board1 = AppreciationBoard(tmp_path / "board.json")
        board1.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism", "Great"))

        board2 = AppreciationBoard(tmp_path / "board.json")
        assert len(board2.for_peer("hive_p1")) == 1

    def test_by_reviewer(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5))
        board.add(create_appreciation("hive_r1", "hive_p2", 4))
        board.add(create_appreciation("hive_r2", "hive_p1", 3))

        reviews = board.by_reviewer("hive_r1")
        assert len(reviews) == 2

    def test_all_summaries(self, tmp_path):
        board = AppreciationBoard(tmp_path / "board.json")
        board.add(create_appreciation("hive_r1", "hive_p1", 5, "tourism"))
        board.add(create_appreciation("hive_r2", "hive_p2", 3, "food"))

        summaries = board.all_summaries()
        assert len(summaries) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
