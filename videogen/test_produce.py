"""
Tests for videogen/produce.py — H4 skeleton orchestrator.

Focus: mock-mode end-to-end (the integration path video-bridge.mjs uses).
Stubs are tested to confirm they raise NotImplementedError with clear messages.
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from videogen.produce import (  # noqa: E402
    produce,
    load_brief,
    Brief,
    ProduceResult,
    ingest_brief,
    select_clips,
    render_video,
    run_qa,
)
from videogen.edl import load_edl, validate_edl  # noqa: E402


# --- mock-mode end-to-end ----------------------------------------------------

class TestMockEndToEnd:
    """The integration path: video-bridge.mjs calls `produce --mock` and gets
    valid result.json + edl.json."""

    def test_mock_produces_valid_result_json(self, tmp_path):
        result = produce(brief_path=None, out_dir=tmp_path, mock=True)
        assert result.status == "mock"
        result_path = tmp_path / "result.json"
        assert result_path.exists()
        data = json.loads(result_path.read_text())
        assert data["tour_slug"] == "mock-tour"
        assert data["status"] == "mock"

    def test_mock_produces_valid_edl_json(self, tmp_path):
        produce(brief_path=None, out_dir=tmp_path, mock=True)
        edl_path = tmp_path / "edl.json"
        assert edl_path.exists()
        edl = load_edl(edl_path)
        errors = validate_edl(edl)
        assert errors == [], f"Mock EDL should be valid: {errors}"

    def test_mock_edl_has_correct_total(self, tmp_path):
        """Mock EDL: 3 shots × 10s each = 30s total (compute_total_duration)."""
        produce(brief_path=None, out_dir=tmp_path, mock=True)
        edl = load_edl(tmp_path / "edl.json")
        assert edl.total_duration_sec == 30.0
        assert len(edl.edl) == 3

    def test_mock_result_has_media_provenance(self, tmp_path):
        """Golden Rule: every shot in result.json has source + licence + authenticity."""
        produce(brief_path=None, out_dir=tmp_path, mock=True)
        data = json.loads((tmp_path / "result.json").read_text())
        assert len(data["media_provenance"]) == 3
        for entry in data["media_provenance"]:
            assert entry["source"] == "pexels"
            assert entry["licence"] == "Pexels"
            assert entry["authenticity"] == "stock"

    def test_mock_qa_passes(self, tmp_path):
        result = produce(brief_path=None, out_dir=tmp_path, mock=True)
        assert result.qc_report["decision"] == "PASS"
        assert result.qc_report["provenance_failures"] == 0


# --- brief loading -----------------------------------------------------------

class TestBriefLoading:
    def test_load_real_brief(self, tmp_path):
        """A brief.yaml written to disk loads correctly."""
        brief_data = {
            "schema_version": 1,
            "tour_slug": "test-tour",
            "title": "Test Tour",
            "duration_target_sec": 45,
            "clip_hints": [
                {"scene": "hook", "prompt": "dawn", "duration_sec": 15},
                {"scene": "body", "prompt": "city", "duration_sec": 15},
                {"scene": "cta", "prompt": "aerial", "duration_sec": 15},
            ],
        }
        brief_path = tmp_path / "brief.yaml"
        brief_path.write_text(yaml.dump(brief_data))
        brief = load_brief(brief_path)
        assert brief.tour_slug == "test-tour"
        assert brief.duration_target_sec == 45
        assert len(brief.clip_hints) == 3

    def test_mock_produce_with_real_brief(self, tmp_path):
        """Mock produce with a real brief produces correct shot count."""
        brief_data = {
            "schema_version": 1,
            "tour_slug": "legends",
            "title": "Legends",
            "duration_target_sec": 40,
            "clip_hints": [
                {"scene": "a", "prompt": "x", "duration_sec": 10},
                {"scene": "b", "prompt": "y", "duration_sec": 10},
                {"scene": "c", "prompt": "z", "duration_sec": 10},
                {"scene": "d", "prompt": "w", "duration_sec": 10},
            ],
        }
        brief_path = tmp_path / "brief.yaml"
        brief_path.write_text(yaml.dump(brief_data))
        result = produce(brief_path=brief_path, out_dir=tmp_path / "out", mock=True)
        edl = load_edl(tmp_path / "out" / "edl.json")
        assert len(edl.edl) == 4
        assert edl.total_duration_sec == 40.0


# --- stubs raise NotImplementedError ----------------------------------------

class TestStubsRaise:
    """The four missing stages must raise with clear contract messages."""

    def test_ingest_brief_raises(self):
        with pytest.raises(NotImplementedError, match="H2"):
            ingest_brief(Brief(tour_slug="t"))

    def test_select_clips_raises(self):
        with pytest.raises(NotImplementedError, match="selector"):
            select_clips(Brief(tour_slug="t"), {}, {}, [])

    def test_render_video_raises(self):
        from videogen.edl import EDL
        with pytest.raises(NotImplementedError, match="EDL-driven"):
            render_video(EDL(tour="t", total_duration_sec=0, edl=[]), Path("/tmp"))

    def test_run_qa_raises(self):
        from videogen.edl import EDL
        with pytest.raises(NotImplementedError, match="H5"):
            run_qa(ProduceResult(tour_slug="t"), EDL(tour="t", total_duration_sec=0, edl=[]))

    def test_real_mode_raises_on_missing_brief(self):
        """Real mode without a brief should error, not silently mock."""
        with pytest.raises(ValueError, match="brief_path"):
            produce(mock=False)


# --- EDL + result.json integration ------------------------------------------

class TestResultPackage:
    def test_edl_path_in_result(self, tmp_path):
        result = produce(brief_path=None, out_dir=tmp_path, mock=True)
        assert "edl.json" in result.edl_path

    def test_video_duration_matches_edl(self, tmp_path):
        result = produce(brief_path=None, out_dir=tmp_path, mock=True)
        edl = load_edl(tmp_path / "edl.json")
        assert result.video["duration_sec"] == edl.total_duration_sec
