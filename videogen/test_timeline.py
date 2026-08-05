"""
Tests for videogen/timeline.py — H3 (VO is master clock).

Critical invariants tested:
  - VO drives the cut: each shot's duration_sec == vo_duration_sec
  - total_duration uses compute_total_duration (the H1 fix), not a manual sum
  - timeline_start positions are cumulative (non-overlapping VO windows)
  - The produced EDL passes validate_edl (full H1+H3 integration)
  - Missing clip assignment raises a clear error
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from videogen.edl import validate_edl, compute_total_duration  # noqa: E402
from videogen.timeline import (  # noqa: E402
    VOSegment,
    ClipAssignment,
    Provenance,
    build_edl,
)


# --- fixtures ----------------------------------------------------------------

def _provenance(source: str = "pexels") -> Provenance:
    return Provenance(source=source, asset_id="123", licence="Pexels",
                      authenticity="stock")


def _vo(shot_id: str, duration: float, text: str = "test") -> VOSegment:
    return VOSegment(shot_id=shot_id, text=text,
                     mp3_path=f"vo/{shot_id}.mp3", duration_sec=duration)


def _assign(shot_id: str, duration: float, source: str = "pexels") -> ClipAssignment:
    return ClipAssignment(shot_id=shot_id, source_path=f"pool/{shot_id}/clip.mp4",
                          clip_start_sec=0.0, clip_end_sec=duration,
                          provenance=_provenance(source))


def _synthetic_vo_and_clips():
    """3 VO segments with realistic durations."""
    vo = [
        _vo("shot1", 9.5, "China doesn't reveal itself all at once."),
        _vo("shot2", 7.2, "Beijing holds the past and the future."),
        _vo("shot3", 8.1, "The warriors stand guard in silence."),
    ]
    clips = [_assign(s.shot_id, s.duration_sec + 2) for s in vo]  # +2s handle
    return vo, clips


# --- VO drives the cut -------------------------------------------------------

class TestVODrivesCut:
    def test_duration_equals_vo_duration(self):
        """Each shot's visual duration IS its VO duration."""
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        for shot, segment in zip(edl.edl, vo):
            assert shot.duration_sec == segment.duration_sec

    def test_sum_durations_equals_sum_vo(self):
        """The build-plan H3 acceptance test: sum(duration) == sum(vo_duration)."""
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        assert sum(s.duration_sec for s in edl.edl) == sum(v.duration_sec for v in vo)

    def test_single_shot(self):
        vo = [_vo("only", 5.0)]
        clips = [_assign("only", 7.0)]
        edl = build_edl(vo, clips, tour="t")
        assert edl.edl[0].duration_sec == 5.0
        assert edl.total_duration_sec == 5.0


# --- timeline positions ------------------------------------------------------

class TestTimelinePositions:
    def test_positions_are_cumulative(self):
        """timeline_start is cumulative: 0, d0, d0+d1, ..."""
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        expected = 0.0
        for shot in edl.edl:
            assert abs(shot.timeline_start_sec - expected) < 0.001
            expected += shot.duration_sec

    def test_first_shot_starts_at_zero(self):
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        assert edl.edl[0].timeline_start_sec == 0.0

    def test_total_uses_compute_total_duration(self):
        """The H1 fix: total = max(start+dur), not a manual sum."""
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        expected = compute_total_duration(edl.edl)
        assert edl.total_duration_sec == expected


# --- H1 integration ----------------------------------------------------------

class TestEDLValidation:
    def test_produced_edl_passes_validate(self):
        """The EDL from build_edl must pass validate_edl (H1+H3 integration)."""
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="legends-of-china-warriors")
        errors = validate_edl(edl)
        assert errors == [], f"EDL validation failed: {errors}"

    def test_provenance_carried_through(self):
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        for shot in edl.edl:
            assert shot.provenance is not None
            assert shot.provenance.source == "pexels"
            assert shot.provenance.licence == "Pexels"

    def test_ai_generated_source_accepted(self):
        """Forge can use AI-generated assets (System C)."""
        vo = [_vo("s1", 5.0)]
        clips = [ClipAssignment(shot_id="s1", source_path="ai/gen.mp4",
                                clip_start_sec=0, clip_end_sec=5,
                                provenance=Provenance(
                                    source="ai_generated", licence="Commercial",
                                    authenticity="illustrative"))]
        edl = build_edl(vo, clips, tour="test")
        assert validate_edl(edl) == []

    def test_subtitle_text_set_from_vo(self):
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        for shot, segment in zip(edl.edl, vo):
            assert shot.subtitle_text == segment.text

    def test_vo_segment_filename_set(self):
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="test")
        for shot, segment in zip(edl.edl, vo):
            assert shot.vo_segment == f"{segment.shot_id}.mp3"


# --- error handling ----------------------------------------------------------

class TestErrors:
    def test_missing_clip_assignment_raises(self):
        """Every VO segment must have a matching clip assignment."""
        vo = [_vo("shot1", 5.0), _vo("shot2", 4.0)]
        clips = [_assign("shot1", 6.0)]  # shot2 missing
        with pytest.raises(ValueError, match="shot2"):
            build_edl(vo, clips, tour="test")

    def test_empty_vo_raises_on_validate(self):
        """An EDL with no shots fails validation."""
        edl = build_edl([], [], tour="empty")
        errors = validate_edl(edl)
        assert any("empty" in e for e in errors)


# --- round-trip with H1 I/O --------------------------------------------------

class TestRoundTrip:
    def test_write_validate_reload(self, tmp_path):
        """build_edl → write_edl → load_edl → validate_edl all agree."""
        from videogen.edl import write_edl, load_edl
        vo, clips = _synthetic_vo_and_clips()
        edl = build_edl(vo, clips, tour="legends")
        path = tmp_path / "edl.json"
        write_edl(edl, path)
        loaded = load_edl(path)
        assert validate_edl(loaded) == []
        assert loaded.total_duration_sec == edl.total_duration_sec
        assert len(loaded.edl) == 3
