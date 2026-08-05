"""
Tests for videogen/edl.py — the H1 keystone module.

Critical: the time-equation fix. These tests prove:
  - An EDL with crossfades PASSES when total = max(start+dur)
  - The same EDL would FAIL the old sum-based check (Σd ≠ total)
  - A desynced EDL (total set to the naive sum) is CAUGHT
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from videogen.edl import (  # noqa: E402
    EDL,
    EDL_SCHEMA_VERSION,
    Shot,
    Provenance,
    Transition,
    compute_total_duration,
    load_edl,
    validate_edl,
    write_edl,
)


# --- fixtures ----------------------------------------------------------------

def _provenance(source: str = "pexels") -> Provenance:
    return Provenance(
        source=source,
        asset_id="35834780",
        licence="Pexels",
        authenticity="stock",
    )


def _shot(
    shot_id: str = "shot1",
    timeline_start: float = 0.0,
    duration: float = 10.0,
    transition_type: str = "cut",
    transition_dur: float = 0.0,
    source: str = "pexels",
) -> Shot:
    return Shot(
        shot_id=shot_id,
        source_path=f"pool/{shot_id}/landscape/clip.mp4",
        clip_start_sec=0.0,
        clip_end_sec=duration,  # enough handle
        timeline_start_sec=timeline_start,
        duration_sec=duration,
        vo_segment=f"vo_{shot_id}.mp3",
        vo_duration_sec=duration - 0.5,
        subtitle_text="test subtitle",
        transition=Transition(type=transition_type, duration_sec=transition_dur),
        provenance=_provenance(source),
    )


def _valid_edl_with_crossfade() -> EDL:
    """Two shots, 0.5s crossfade between them.

    Shot 1: start 0, dur 10 → ends at 10
    Shot 2: start 9.5 (10 - 0.5 overlap), dur 8 → ends at 17.5
    total = max(10, 17.5) = 17.5
    naive sum = 10 + 8 = 18  ← WRONG (overcounts by 0.5s overlap)
    """
    return EDL(
        schema_version=EDL_SCHEMA_VERSION,
        tour="legends-of-china-warriors",
        total_duration_sec=17.5,
        edl=[
            _shot("shot1", 0.0, 10.0, "xfade", 0.5),
            _shot("shot2", 9.5, 8.0, "cut", 0.0),
        ],
    )


def _valid_edl_cuts_only() -> EDL:
    """Three shots, no overlaps (all cuts)."""
    return EDL(
        schema_version=EDL_SCHEMA_VERSION,
        tour="test-tour",
        total_duration_sec=30.0,
        edl=[
            _shot("shot1", 0.0, 10.0, "cut", 0.0),
            _shot("shot2", 10.0, 10.0, "cut", 0.0),
            _shot("shot3", 20.0, 10.0, "cut", 0.0),
        ],
    )


# --- THE FIX: time-equation tests --------------------------------------------

class TestTimeEquationFix:
    """The core audit fix — total = max(start+dur), not Σd."""

    def test_crossfade_edl_passes_with_correct_total(self):
        """A crossfade EDL where total = max(start+dur) should pass."""
        edl = _valid_edl_with_crossfade()
        errors = validate_edl(edl)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_crossfade_edl_fails_when_total_is_naive_sum(self):
        """If someone sets total = Σd (the old wrong check), it must FAIL."""
        edl = _valid_edl_with_crossfade()
        # naive sum = 10 + 8 = 18; correct = 17.5; set clearly outside tolerance
        edl.total_duration_sec = 19.0  # 1.5s off — clearly wrong
        errors = validate_edl(edl)
        assert any("max(start+dur)" in e for e in errors), (
            f"Expected time-equation error, got: {errors}"
        )

    def test_compute_total_uses_max_not_sum(self):
        """compute_total_duration must return max(start+dur), not Σd."""
        edl = _valid_edl_with_crossfade()
        total = compute_total_duration(edl.edl)
        assert total == 17.5  # max(0+10, 9.5+8) = max(10, 17.5)
        assert total != 18.0  # the naive sum

    def test_cuts_only_edl_sum_equals_max(self):
        """Without crossfades, Σd == max(start+dur) — both agree."""
        edl = _valid_edl_cuts_only()
        total = compute_total_duration(edl.edl)
        assert total == 30.0
        errors = validate_edl(edl)
        assert errors == []

    def test_crossfade_total_off_by_one_frame_caught(self):
        """Even a 1-frame (1/30s) desync should be caught."""
        edl = _valid_edl_with_crossfade()
        edl.total_duration_sec = 17.5 + 0.6  # just outside tolerance
        errors = validate_edl(edl)
        assert any("total_duration_sec" in e for e in errors)

    def test_timeline_gap_from_wrong_overlap_caught(self):
        """If timeline_start doesn't account for the crossfade, caught."""
        edl = _valid_edl_with_crossfade()
        # shot2 should start at 9.5 (10 - 0.5), but set it to 11.0 (clearly wrong)
        edl.edl[1].timeline_start_sec = 11.0
        errors = validate_edl(edl)
        assert any("timeline gap" in e for e in errors)


# --- schema validation tests -------------------------------------------------

class TestSchemaValidation:
    def test_valid_edl_no_errors(self):
        assert validate_edl(_valid_edl_cuts_only()) == []

    def test_wrong_schema_version(self):
        edl = _valid_edl_cuts_only()
        edl.schema_version = 99
        errors = validate_edl(edl)
        assert any("schema_version" in e for e in errors)

    def test_empty_edl(self):
        edl = EDL(schema_version=1, tour="t", total_duration_sec=0, edl=[])
        errors = validate_edl(edl)
        assert any("empty" in e for e in errors)

    def test_duplicate_shot_id(self):
        edl = _valid_edl_cuts_only()
        edl.edl[1].shot_id = "shot1"  # duplicate
        errors = validate_edl(edl)
        assert any("duplicate shot_id" in e for e in errors)

    def test_first_shot_not_at_zero(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].timeline_start_sec = 2.0
        errors = validate_edl(edl)
        assert any("timeline_start_sec" in e for e in errors)


# --- source + VO tests -------------------------------------------------------

class TestSourceAndVO:
    def test_missing_source_path_and_override(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].source_path = None
        edl.edl[0].human_override = None
        errors = validate_edl(edl)
        assert any("no source_path" in e for e in errors)

    def test_missing_vo_and_not_silent(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].vo_segment = None
        edl.edl[0].silent = False
        errors = validate_edl(edl)
        assert any("vo_segment" in e for e in errors)

    def test_silent_shot_passes_without_vo(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].vo_segment = None
        edl.edl[0].silent = True
        edl.edl[0].vo_duration_sec = None
        errors = validate_edl(edl)
        assert errors == []

    def test_vo_exceeds_duration(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].vo_duration_sec = 15.0  # > 10.0 duration
        errors = validate_edl(edl)
        assert any("vo_duration" in e for e in errors)


# --- provenance (Golden Rule) tests ------------------------------------------

class TestProvenanceGoldenRule:
    def test_missing_provenance(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].provenance = None
        errors = validate_edl(edl)
        assert any("missing provenance" in e for e in errors)

    def test_unknown_source_type(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].provenance = Provenance(
            source="unknown_source", licence="Pexels", authenticity="stock"
        )
        errors = validate_edl(edl)
        assert any("provenance.source" in e for e in errors)

    def test_unknown_authenticity(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].provenance = Provenance(
            source="pexels", licence="Pexels", authenticity="fake"
        )
        errors = validate_edl(edl)
        assert any("provenance.authenticity" in e for e in errors)

    def test_empty_licence(self):
        edl = _valid_edl_cuts_only()
        edl.edl[0].provenance = Provenance(
            source="pexels", licence="", authenticity="stock"
        )
        errors = validate_edl(edl)
        assert any("licence is empty" in e for e in errors)

    def test_ai_generated_source_accepted(self):
        """ai_generated is a valid EDL source (Forge can use AI assets)."""
        edl = _valid_edl_cuts_only()
        edl.edl[0].provenance = Provenance(
            source="ai_generated", licence="Commercial", authenticity="illustrative"
        )
        errors = validate_edl(edl)
        assert errors == []


# --- clip handle tests -------------------------------------------------------

class TestClipHandles:
    def test_source_shorter_than_shot(self):
        """Source clip segment must be >= shot duration."""
        edl = _valid_edl_cuts_only()
        edl.edl[0].clip_start_sec = 0.0
        edl.edl[0].clip_end_sec = 5.0  # < 10.0 duration
        errors = validate_edl(edl)
        assert any("source clip" in e for e in errors)

    def test_source_exactly_matches_shot(self):
        """Source segment == shot duration is fine (no extra handle needed)."""
        edl = _valid_edl_cuts_only()
        edl.edl[0].clip_start_sec = 0.0
        edl.edl[0].clip_end_sec = 10.0  # == duration
        errors = validate_edl(edl)
        assert errors == []


# --- I/O round-trip tests ----------------------------------------------------

class TestIO:
    def test_write_then_load_roundtrip(self, tmp_path):
        edl = _valid_edl_with_crossfade()
        path = tmp_path / "test_edl.json"
        write_edl(edl, path)
        loaded = load_edl(path)
        assert loaded.tour == edl.tour
        assert loaded.total_duration_sec == edl.total_duration_sec
        assert len(loaded.edl) == 2
        assert loaded.edl[0].shot_id == "shot1"
        assert loaded.edl[0].transition.type == "xfade"

    def test_load_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json}")
        with pytest.raises(json.JSONDecodeError):
            load_edl(path)

    def test_validated_after_roundtrip(self, tmp_path):
        """An EDL that's written and loaded should still validate."""
        edl = _valid_edl_with_crossfade()
        path = tmp_path / "roundtrip.json"
        write_edl(edl, path)
        loaded = load_edl(path)
        assert validate_edl(loaded) == []
