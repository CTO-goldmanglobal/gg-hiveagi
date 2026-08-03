"""
Tests for videogen/provenance.py — the security-critical gate module.

Covers:
- Source type classification (stock vs human capture)
- Labs eligibility (stock blocked, human allowed, unknown fails closed)
- Area gate (open shares freely, commercial needs consent)
- Hard assertions (ProvenanceViolation, ShareConsentViolation)
- Unknown areas fail closed
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from videogen.provenance import (
    is_stock, is_human_capture, is_labs_eligible,
    is_judgment_labs_eligible, filter_for_labs, assert_labs_safe,
    can_share_to_labs, assert_share_consent,
    ProvenanceViolation, ShareConsentViolation,
    SOURCE_STOCK, SOURCE_HUMAN, AREA_OPEN, AREA_COMMERCIAL,
)


class TestSourceType:
    def test_stock_pexels(self):
        assert is_stock("stock:pexels") is True

    def test_stock_pixabay(self):
        assert is_stock("stock:pixabay") is True

    def test_human_glasses(self):
        assert is_human_capture("human_capture:glasses") is True

    def test_human_phone(self):
        assert is_human_capture("human_capture:phone") is True

    def test_empty_fails_closed(self):
        assert is_stock("") is False
        assert is_human_capture("") is False

    def test_unknown_fails_closed(self):
        assert is_stock("unknown") is False
        assert is_human_capture("unknown") is False


class TestLabsEligible:
    def test_stock_blocked(self):
        assert is_labs_eligible("stock:pexels") is False

    def test_human_allowed(self):
        assert is_labs_eligible("human_capture:glasses") is True

    def test_empty_blocked(self):
        assert is_labs_eligible("") is False

    def test_unknown_blocked(self):
        assert is_labs_eligible("unknown") is False


class TestJudgmentEligible:
    def test_tagged_judgment_eligible(self):
        assert is_judgment_labs_eligible({"source_type": "stock:pexels"}) is True

    def test_untagged_judgment_blocked(self):
        assert is_judgment_labs_eligible({}) is False

    def test_empty_source_blocked(self):
        assert is_judgment_labs_eligible({"source_type": ""}) is False


class TestFilterForLabs:
    def test_splits_correctly(self):
        rows = [
            {"source_type": "stock:pexels", "id": 1},
            {"source_type": "human_capture:glasses", "id": 2},
            {"source_type": "stock:pixabay", "id": 3},
            {"source_type": "human_capture:phone", "id": 4},
        ]
        elig, rej = filter_for_labs(rows)
        assert len(elig) == 2
        assert len(rej) == 2
        assert {r["id"] for r in elig} == {2, 4}
        assert {r["id"] for r in rej} == {1, 3}

    def test_empty_list(self):
        elig, rej = filter_for_labs([])
        assert len(elig) == 0
        assert len(rej) == 0

    def test_all_stock(self):
        rows = [{"source_type": "stock:pexels"}, {"source_type": "stock:pixabay"}]
        elig, rej = filter_for_labs(rows)
        assert len(elig) == 0
        assert len(rej) == 2

    def test_all_human(self):
        rows = [{"source_type": "human_capture:glasses"}]
        elig, rej = filter_for_labs(rows)
        assert len(elig) == 1
        assert len(rej) == 0


class TestAssertLabsSafe:
    def test_all_safe_passes(self):
        rows = [{"source_type": "human_capture:glasses"}]
        assert_labs_safe(rows)  # should not raise

    def test_stock_raises(self):
        rows = [{"source_type": "stock:pexels"}]
        with pytest.raises(ProvenanceViolation):
            assert_labs_safe(rows)

    def test_mixed_raises(self):
        rows = [
            {"source_type": "human_capture:glasses"},
            {"source_type": "stock:pexels"},
        ]
        with pytest.raises(ProvenanceViolation):
            assert_labs_safe(rows)


class TestAreaGate:
    def test_open_shares_by_default(self):
        assert can_share_to_labs("open") is True

    def test_commercial_without_consent_blocked(self):
        assert can_share_to_labs("commercial", share_consent=False) is False

    def test_commercial_with_consent_allowed(self):
        assert can_share_to_labs("commercial", share_consent=True) is True

    def test_unknown_area_fail_closed(self):
        assert can_share_to_labs("unknown") is False
        assert can_share_to_labs("") is False


class TestAssertShareConsent:
    def test_open_passes(self):
        assert_share_consent("open", share_consent=False)  # no raise

    def test_commercial_with_consent_passes(self):
        assert_share_consent("commercial", share_consent=True)  # no raise

    def test_commercial_without_consent_raises(self):
        with pytest.raises(ShareConsentViolation):
            assert_share_consent("commercial", share_consent=False)

    def test_commercial_without_consent_with_id(self):
        with pytest.raises(ShareConsentViolation, match="pattern_001"):
            assert_share_consent("commercial", share_consent=False, item_id="pattern_001")

    def test_unknown_area_raises(self):
        with pytest.raises(ShareConsentViolation):
            assert_share_consent("unknown", share_consent=False)

    def test_empty_area_raises(self):
        with pytest.raises(ShareConsentViolation):
            assert_share_consent("", share_consent=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
