"""
Tests for p2p_exchange/boards.py — contribution + improvement boards.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from p2p_exchange.boards import ContributionBoard, ImprovementBoard


class TestContributionBoard:
    def test_new_contributor(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        p = board.get_profile("hive_new")
        assert p["total_events"] == 0

    def test_record_tag(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_tag_published("hive_a", "tourism")
        p = board.get_profile("hive_a")
        assert p["tags_published"] == 1
        assert p["domains"].get("tourism") == 1

    def test_record_judgment(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_judgment_made("hive_a", "tourism")
        board.record_judgment_made("hive_a", "tourism")
        p = board.get_profile("hive_a")
        assert p["judgments_made"] == 2

    def test_record_override(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_override("hive_a", "tourism")
        p = board.get_profile("hive_a")
        assert p["overrides"] == 1

    def test_multiple_domains(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_tag_published("hive_a", "tourism")
        board.record_tag_published("hive_a", "tourism")
        board.record_tag_published("hive_a", "food")
        p = board.get_profile("hive_a")
        assert p["domains"]["tourism"] == 2
        assert p["domains"]["food"] == 1

    def test_total_events_accumulates(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_tag_published("hive_a")
        board.record_judgment_made("hive_a")
        board.record_seed_shared("hive_a")
        p = board.get_profile("hive_a")
        assert p["total_events"] == 3

    def test_render_profile(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_tag_published("hive_a", "tourism")
        text = board.render_profile("hive_a")
        assert "hive_a" in text
        assert "Tags published" in text

    def test_render_empty_profile(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        text = board.render_profile("hive_nobody")
        assert "No contributions" in text

    def test_leaderboard(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        for _ in range(10):
            board.record_tag_published("hive_top")
        for _ in range(3):
            board.record_tag_published("hive_mid")
        board.record_tag_published("hive_low")
        lb = board.leaderboard("tags_published")
        assert lb[0]["peer_id"] == "hive_top"
        assert lb[0]["tags_published"] == 10
        assert lb[1]["peer_id"] == "hive_mid"
        assert lb[-1]["peer_id"] == "hive_low"

    def test_render_leaderboard(self, tmp_path):
        board = ContributionBoard(tmp_path / "contrib.json")
        board.record_tag_published("hive_a")
        board.record_tag_published("hive_b")
        text = board.render_leaderboard()
        assert "Leaderboard" in text

    def test_persistence(self, tmp_path):
        board1 = ContributionBoard(tmp_path / "contrib.json")
        board1.record_tag_published("hive_a")
        board2 = ContributionBoard(tmp_path / "contrib.json")
        assert board2.get_profile("hive_a")["tags_published"] == 1


class TestImprovementBoard:
    def test_take_snapshot(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        contrib.record_tag_published("hive_a", "tourism")
        contrib.record_tag_published("hive_b", "food")

        improvement = ImprovementBoard(tmp_path / "improve.json")
        snap = improvement.take_snapshot(contrib)
        assert "hive_a" in snap["contributors"]
        assert "hive_b" in snap["contributors"]

    def test_growth_no_data(self, tmp_path):
        improvement = ImprovementBoard(tmp_path / "improve.json")
        growth = improvement.get_growth("hive_a")
        assert growth["trend"] == "no_data"

    def test_growth_detected(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        improvement = ImprovementBoard(tmp_path / "improve.json")

        # Snapshot 1: 5 tags
        for _ in range(5):
            contrib.record_tag_published("hive_a", "tourism")
        improvement.take_snapshot(contrib, "month 1")

        # Snapshot 2: 7 more tags (total 12)
        for _ in range(7):
            contrib.record_tag_published("hive_a", "tourism")
        improvement.take_snapshot(contrib, "month 2")

        growth = improvement.get_growth("hive_a", "tags_published")
        assert growth["current"] == 12
        assert growth["previous"] == 5
        assert growth["delta"] == 7
        assert growth["pct_change"] == pytest.approx(140.0, abs=0.1)
        assert growth["trend"] == "↗"

    def test_new_contributor_detected(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        improvement = ImprovementBoard(tmp_path / "improve.json")

        # Snapshot 1: only hive_a
        contrib.record_tag_published("hive_a")
        improvement.take_snapshot(contrib, "before")

        # Snapshot 2: hive_b appears (new)
        contrib.record_tag_published("hive_b")
        improvement.take_snapshot(contrib, "after")

        changes = improvement.get_ranking_changes("tags_published")
        new_contribs = [c for c in changes if c["direction"] == "★"]
        assert len(new_contribs) == 1
        assert new_contribs[0]["peer_id"] == "hive_b"

    def test_ranking_change(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        improvement = ImprovementBoard(tmp_path / "improve.json")

        # Snapshot 1: hive_a > hive_b
        for _ in range(10):
            contrib.record_tag_published("hive_a")
        for _ in range(3):
            contrib.record_tag_published("hive_b")
        improvement.take_snapshot(contrib, "before")

        # Snapshot 2: hive_b overtakes hive_a
        for _ in range(20):
            contrib.record_tag_published("hive_b")
        improvement.take_snapshot(contrib, "after")

        changes = improvement.get_ranking_changes("tags_published")
        # hive_b should have moved up
        b_change = [c for c in changes if c["peer_id"] == "hive_b"]
        assert len(b_change) == 1
        assert b_change[0]["change"] > 0  # moved up

    def test_network_growth(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        improvement = ImprovementBoard(tmp_path / "improve.json")

        contrib.record_tag_published("hive_a")
        improvement.take_snapshot(contrib, "month 1")

        contrib.record_tag_published("hive_b")
        contrib.record_tag_published("hive_a")
        improvement.take_snapshot(contrib, "month 2")

        growth = improvement.network_growth()
        assert growth["current"]["contributors"] == 2
        assert growth["previous"]["contributors"] == 1
        assert growth["deltas"]["contributors"] == 1

    def test_render_improvement(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        improvement = ImprovementBoard(tmp_path / "improve.json")

        contrib.record_tag_published("hive_a")
        improvement.take_snapshot(contrib, "before")
        contrib.record_tag_published("hive_a")
        contrib.record_tag_published("hive_b")
        improvement.take_snapshot(contrib, "after")

        text = improvement.render_improvement()
        assert "Improvement Board" in text
        assert "Network" in text

    def test_persistence(self, tmp_path):
        contrib = ContributionBoard(tmp_path / "contrib.json")
        contrib.record_tag_published("hive_a")
        improvement1 = ImprovementBoard(tmp_path / "improve.json")
        improvement1.take_snapshot(contrib)

        improvement2 = ImprovementBoard(tmp_path / "improve.json")
        assert len(improvement2._snapshots) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
