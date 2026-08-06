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
    generate_script,
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

    def test_ingest_brief_runs_and_enriches(self):
        """ingest_brief is filled (H2) — it enriches the brief with keywords +
        grounded context. Fetch + LLM are injected so no network call is made."""
        brief = Brief(
            tour_slug="shanghai",
            tour_url="https://example.com/tours/shanghai",
            title="Shanghai",
            clip_hints=[
                {"scene": "hook", "prompt": "dawn skyline", "duration_sec": 5},
                {"scene": "body", "prompt": "bund waterfront", "duration_sec": 5},
            ],
        )
        # Inject stubs: a fake fetch returning minimal HTML, a fake LLM returning JSON.
        fake_html = "<html><head><title>Shanghai Tour | ExploreChina</title></head><body><h1>Shanghai</h1>Day 1: The Bund, Yu Garden. Day 2: Pudong, Maglev.</body></html>"
        fake_llm_response = '{"shot1": ["shanghai dawn skyline", "city sunrise"], "shot2": ["shanghai bund waterfront", "night skyline"]}'
        out = ingest_brief(
            brief,
            url_fetch_fn=lambda url: fake_html,
            llm_fn=lambda prompt: fake_llm_response,
        )
        # Title resolved from page
        assert out.title == "Shanghai Tour"
        # Keywords populated per shot
        assert "shot1" in out.generated_keywords
        assert "shot2" in out.generated_keywords
        assert len(out.generated_keywords["shot1"]) >= 2
        # Grounded context carries the itinerary text
        assert "Bund" in out.grounded_context or "Day 1" in out.grounded_context
        # Cities extracted
        assert "Shanghai" in out.cities

    def test_ingest_brief_degrades_when_fetch_fails(self):
        """URL fetch failure → keywords fall back to hint prompt tokens."""
        brief = Brief(
            tour_slug="t",
            tour_url="https://example.com/missing",
            clip_hints=[{"scene": "hook", "prompt": "great wall dawn", "duration_sec": 5}],
        )
        out = ingest_brief(
            brief,
            url_fetch_fn=lambda url: "",  # fetch returns empty (failure)
            llm_fn=lambda prompt: "",     # LLM also fails
        )
        # Fallback: hint prompt tokens become keywords
        assert "shot1" in out.generated_keywords
        assert any(tok in out.generated_keywords["shot1"][0] for tok in ("great", "wall", "dawn"))

    def test_ingest_brief_degrades_when_llm_returns_garbage(self):
        """LLM returning non-JSON → falls back to hint prompt tokens, no crash."""
        brief = Brief(
            tour_slug="t",
            tour_url="https://example.com/x",
            clip_hints=[{"scene": "hook", "prompt": "beijing forbidden city", "duration_sec": 5}],
        )
        out = ingest_brief(
            brief,
            url_fetch_fn=lambda url: "<html><title>Beijing</title>Day 1: Forbidden City</html>",
            llm_fn=lambda prompt: "sorry I cannot help with that",  # garbage
        )
        # Fallback applies
        assert "shot1" in out.generated_keywords
        assert len(out.generated_keywords["shot1"]) > 0

    def test_select_clips_runs_and_returns_assignments(self):
        """select_clips is filled — it returns typed ClipAssignments with
        Golden-Rule provenance, one per VO segment."""
        from videogen.timeline import VOSegment
        brief = Brief(tour_slug="t", clip_hints=[
            {"scene": "hook", "prompt": "dawn landscape", "duration_sec": 5},
        ])
        pool = {"shots": [{"shot_id": "shot1", "candidates": [
            {"candidate_id": "pexels_1", "source_type": "stock:pexels",
             "license": "Pexels License", "local_path": "pool/shot1/pexels_1.mp4",
             "duration_sec": 20.0, "keywords_matched": ["dawn"]},
        ]}]}
        tags = {"pexels_1": {"tags": {
            "shot_type": "landscape", "time_of_day": "dawn",
            "commercial_grade": "broadcast", "mood": "epic",
        }}}
        vos = [VOSegment(shot_id="shot1", text="x", mp3_path="vo/shot1.mp3",
                         duration_sec=5.0)]
        # Inject a stub measurer so no real video file is read.
        out = select_clips(brief, pool, tags, vos,
                           measure_fn=lambda c: {"motion_score": 3.0, "brightness": 120})
        assert len(out) == 1
        assert out[0].shot_id == "shot1"
        assert out[0].provenance.source == "pexels"
        assert out[0].provenance.licence == "Pexels"

    def test_generate_script_runs_and_returns_segments(self):
        """generate_script is filled — returns [{shot_id, text}] per clip_hint."""
        brief = Brief(
            tour_slug="shanghai",
            title="Shanghai",
            duration_target_sec=30,
            grounded_context="The Bund is a waterfront promenade in Shanghai.",
            clip_hints=[
                {"scene": "hook", "prompt": "dawn skyline", "duration_sec": 10},
                {"scene": "body", "prompt": "bund waterfront", "duration_sec": 10},
                {"scene": "cta", "prompt": "aerial view", "duration_sec": 10},
            ],
        )
        fake_llm = json.dumps([
            {"shot_id": "shot1", "text": "Shanghai wakes slowly, the river mist lifting off the Bund."},
            {"shot_id": "shot2", "text": "For a century, this waterfront has watched the city reinvent itself."},
            {"shot_id": "shot3", "text": "Walk it at dawn. Then explore our China tours."},
        ])
        out = generate_script(brief, {}, {}, llm_fn=lambda p: fake_llm)
        assert len(out) == 3
        assert out[0]["shot_id"] == "shot1"
        assert "Bund" in out[1]["text"] or "waterfront" in out[1]["text"]

    def test_generate_script_falls_back_for_missing_shots(self):
        """If the LLM misses a shot, the hint prompt becomes the text."""
        brief = Brief(
            tour_slug="t",
            clip_hints=[
                {"scene": "a", "prompt": "great wall", "duration_sec": 5},
                {"scene": "b", "prompt": "forbidden city", "duration_sec": 5},
            ],
        )
        # LLM returns only shot1
        out = generate_script(brief, {}, {},
                              llm_fn=lambda p: json.dumps([{"shot_id": "shot1", "text": "The Great Wall."}]))
        assert len(out) == 2
        assert out[0]["text"] == "The Great Wall."
        # shot2 fell back to its hint prompt
        assert "forbidden" in out[1]["text"].lower()

    def test_generate_script_degrades_on_llm_garbage(self):
        """LLM returning non-JSON → all shots fall back to hint prompts, no crash."""
        brief = Brief(
            tour_slug="t",
            clip_hints=[{"scene": "a", "prompt": "pandas in chengdu", "duration_sec": 5}],
        )
        out = generate_script(brief, {}, {}, llm_fn=lambda p: "I cannot help")
        assert len(out) == 1
        assert "pandas" in out[0]["text"].lower() or "chengdu" in out[0]["text"].lower()

    def test_render_video_empty_edl_raises(self):
        """render_video is now implemented; an empty EDL raises ValueError."""
        from videogen.edl import EDL
        with pytest.raises(ValueError, match="empty"):
            render_video(EDL(tour="t", total_duration_sec=0, edl=[]), Path("/tmp"))

    def test_run_qa_deterministic_layer_runs(self):
        """run_qa is filled (H5) — layer 1 runs without a model. Layer 1 fails on
        a missing video file, proving the keystone rule is enforceable."""
        from videogen.edl import EDL
        result = ProduceResult(
            tour_slug="t",
            video={"mp4_path": "/nonexistent/path.mp4"},  # missing → layer 1 fails
        )
        edl = EDL(tour="t", total_duration_sec=10.0, edl=[])
        out = run_qa(result, edl, skip_model=True)
        assert out.decision == "FAIL"  # missing file → layer 1 fail → FAIL regardless
        assert any(c.name == "file_readable" and not c.passed for c in out.checks)

    def test_run_qa_provenance_completeness_enforced(self, tmp_path):
        """A shot missing provenance fails layer 1 — model score can't override."""
        from videogen.edl import EDL, Shot, Provenance
        # Create a tiny valid mp4 so file_readable passes, then force a provenance gap
        import subprocess
        video = tmp_path / "test.mp4"
        try:
            subprocess.check_output(
                ["ffmpeg", "-f", "lavfi", "-i", "color=black:s=320x240:d=1",
                 "-c:v", "libx264", "-y", str(video)],
                stderr=subprocess.DEVNULL, timeout=30,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("ffmpeg not available")

        shot_no_prov = Shot(shot_id="shot1", source_path=str(video),
                            clip_start_sec=0, clip_end_sec=1, duration_sec=1,
                            timeline_start_sec=0, provenance=None)
        edl = EDL(tour="t", total_duration_sec=1.0, edl=[shot_no_prov])
        result = ProduceResult(tour_slug="t", video={"mp4_path": str(video)})
        out = run_qa(result, edl, skip_model=True)
        assert out.decision == "FAIL"
        assert any("provenance" in c.name and not c.passed for c in out.checks)

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
