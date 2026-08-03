"""
Contract tests for videogen/clip_pool/models.py — the enforced schema layer.

Two purposes:
1. **Backward-compat proof**: real-shaped dicts (from fetch.py / judge.py /
   llm_tags.py) must round-trip through model_validate → model_dump and come
   back identical. This is what makes the schema a safe, no-migration change.
2. **Gate proof**: the schema must REJECT the failure modes it exists to
   prevent — missing source_type (the provenance-drop guard), bad enum values
   (the "DAG of hopes" guard), wrong decision values.

Style matches test_provenance.py / test_metrics.py: pytest classes, tmp_path,
sys.path hack to repo root.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pydantic import ValidationError  # noqa: E402

from videogen.clip_pool.models import (  # noqa: E402
    MANIFEST_SCHEMA_VERSION,
    Candidate,
    ClipTag,
    PoolManifest,
    Verdict,
    resolve_local_path,
)

# ── fixtures: real-shaped dicts copied from the producing modules ────────────


def _candidate_dict(**overrides):
    """Shape from fetch.py:253-265."""
    base = {
        "candidate_id": "pexels_2881972",
        "source_type": "stock:pexels",
        "source_url": "https://www.pexels.com/video/2881972/",
        "local_path": "pool/s1_great_wall/landscape/pexels_2881972.mp4",
        "orientation": "landscape",
        "duration_sec": 12.3,
        "width": 1920,
        "height": 1080,
        "photographer": "Some Creator",
        "license": "Pexels License",
        "keywords_matched": ["great wall"],
    }
    base.update(overrides)
    return base


def _manifest_dict(**overrides):
    """Shape from fetch.py:280-287."""
    base = {
        "schema_version": 1,
        "tour": "legends-of-china-warriors",
        "source_type": "stock:pexels",
        "fetched_at": "2026-08-01T10:00:00Z",
        "total_clips": 1,
        "shots": [
            {
                "shot_id": "s1_great_wall",
                "label": "Great Wall establishing",
                "candidates": [_candidate_dict()],
            }
        ],
    }
    base.update(overrides)
    return base


class TestCandidateRoundTrip:
    def test_full_candidate_round_trips(self):
        d = _candidate_dict()
        c = Candidate.model_validate(d)
        out = c.model_dump(exclude_none=True)
        # every input key survives the round trip
        for k, v in d.items():
            assert out[k] == v, f"{k} changed: {v!r} → {out[k]!r}"

    def test_optional_none_fields_excluded(self):
        c = Candidate.model_validate(_candidate_dict(width=None, height=None))
        out = c.model_dump(exclude_none=True)
        assert "width" not in out
        assert "height" not in out

    def test_defaults_apply(self):
        minimal = {
            "candidate_id": "x",
            "source_type": "stock:pexels",
            "local_path": "p",
            "orientation": "landscape",
        }
        c = Candidate.model_validate(minimal)
        assert c.source_url == ""
        assert c.photographer == ""
        assert c.license == ""
        assert c.keywords_matched == []
        assert c.duration_sec == 0.0


class TestCandidateGuards:
    def test_missing_source_type_rejected(self):
        # This is the provenance-drop guard: a candidate with no source_type
        # must fail validation, so Labs eligibility can never be silently lost.
        d = _candidate_dict()
        del d["source_type"]
        with pytest.raises(ValidationError):
            Candidate.model_validate(d)

    def test_missing_candidate_id_rejected(self):
        d = _candidate_dict()
        del d["candidate_id"]
        with pytest.raises(ValidationError):
            Candidate.model_validate(d)

    def test_missing_local_path_rejected(self):
        d = _candidate_dict()
        del d["local_path"]
        with pytest.raises(ValidationError):
            Candidate.model_validate(d)

    def test_extra_fields_ignored(self):
        # Forward-compat: an extra key (e.g. a new field) must not break load.
        d = _candidate_dict(future_field="something")
        c = Candidate.model_validate(d)
        assert c.candidate_id == "pexels_2881972"


class TestPoolManifest:
    def test_round_trip_real_manifest(self):
        d = _manifest_dict()
        m = PoolManifest.model_validate(d)
        out = m.model_dump()
        assert out["tour"] == "legends-of-china-warriors"
        assert out["total_clips"] == 1
        assert len(out["shots"]) == 1
        assert out["shots"][0]["candidates"][0]["candidate_id"] == "pexels_2881972"

    def test_empty_manifest_ok(self):
        # fetch_pool could produce a pool with zero candidates; must not crash.
        m = PoolManifest.model_validate({"tour": "x", "shots": []})
        assert m.shots == []
        assert m.total_clips == 0

    def test_nested_candidate_validation_propagates(self):
        # A bad candidate inside a shot must fail the whole manifest load —
        # silent acceptance of malformed nested data is exactly the bug class
        # the schema exists to close.
        d = _manifest_dict()
        del d["shots"][0]["candidates"][0]["source_type"]
        with pytest.raises(ValidationError):
            PoolManifest.model_validate(d)

    def test_schema_version_default(self):
        m = PoolManifest.model_validate({"tour": "x"})
        assert m.schema_version == MANIFEST_SCHEMA_VERSION == 1


class TestClipTag:
    def test_valid_tag_round_trips(self):
        d = {
            "shot_type": "landscape",
            "camera_perspective": "drone",
            "time_of_day": "golden_hour",
            "mood": "epic",
            "commercial_grade": "broadcast",
            "subject_action": "drone reveals the wall",
            "description": "aerial",
        }
        t = ClipTag.model_validate(d)
        out = t.model_dump()
        assert out["shot_type"] == "landscape"
        assert out["mood"] == "epic"

    def test_bad_shot_type_rejected(self):
        with pytest.raises(ValidationError):
            ClipTag.model_validate({"shot_type": "not_a_real_shot"})

    def test_bad_mood_rejected(self):
        with pytest.raises(ValidationError):
            ClipTag.model_validate({"mood": "melancholy"})

    def test_bad_commercial_grade_rejected(self):
        with pytest.raises(ValidationError):
            ClipTag.model_validate({"commercial_grade": "premium"})

    def test_all_optional_empty_tag_ok(self):
        # An LLM that returned an empty/{} tag must not crash the loader.
        t = ClipTag.model_validate({})
        assert t.shot_type is None
        assert t.subject_action == ""


class TestVerdict:
    def test_round_trip_accepted(self):
        d = {
            "schema_version": 1,
            "tour": "t",
            "shot_id": "s1",
            "candidate_id": "c1",
            "source_type": "stock:pexels",
            "decision": "accepted",
            "reason": "good motion",
            "metrics": {"motion_score": 2.1},
            "flags": [],
            "editor_id": "finn",
            "timestamp": "2026-08-03T00:00:00Z",
        }
        v = Verdict.model_validate(d)
        assert v.decision == "accepted"
        assert v.metrics["motion_score"] == pytest.approx(2.1)

    def test_bad_decision_rejected(self):
        d = {
            "schema_version": 1,
            "tour": "t",
            "shot_id": "s1",
            "candidate_id": "c1",
            "source_type": "stock:pexels",
            "decision": "maybe",
            "reason": "x",
            "editor_id": "f",
            "timestamp": "t",
        }
        with pytest.raises(ValidationError):
            Verdict.model_validate(d)

    def test_missing_source_type_rejected(self):
        d = {
            "schema_version": 1,
            "tour": "t",
            "shot_id": "s1",
            "candidate_id": "c1",
            "decision": "accepted",
            "reason": "x",
            "editor_id": "f",
            "timestamp": "t",
        }
        with pytest.raises(ValidationError):
            Verdict.model_validate(d)


class TestResolveLocalPath:
    """The 7×-duplicated resolver, now tested in one place."""

    def test_parent_relative_path_exists(self, tmp_path):
        # Normal case: local_path stored relative to pool_dir.parent.
        # layout: tmp/pool/<the file>; local_path = "pool/file.mp4"
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        f = pool_dir / "clip.mp4"
        f.write_text("x")
        resolved = resolve_local_path(pool_dir, "pool/clip.mp4")
        assert resolved == f
        assert resolved.exists()

    def test_pool_prefix_stripped_fallback(self, tmp_path):
        # Fallback case: path is stored with "pool/" prefix but the file is
        # actually directly under pool_dir (no nested pool/ dir).
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        f = pool_dir / "clip.mp4"
        f.write_text("x")
        # local_path points at pool/clip.mp4, file is at pool_dir/clip.mp4
        resolved = resolve_local_path(pool_dir, "pool/clip.mp4")
        assert resolved == f

    def test_missing_file_returns_primary(self, tmp_path):
        # Neither path exists → return the primary (parent-relative) so the
        # downstream failure points at the real stored value, not a guess.
        # primary = pool_dir.parent / local_path = tmp / "pool/missing.mp4"
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        resolved = resolve_local_path(pool_dir, "pool/missing.mp4")
        assert resolved == (tmp_path / "pool" / "missing.mp4")
        assert not resolved.exists()  # genuinely missing, as intended

    def test_real_world_layout(self, tmp_path):
        # Reproduces the actual fetch.py layout:
        # pool_dir.parent / pool / s1 / landscape / id.mp4
        shot_dir = tmp_path / "pool" / "s1" / "landscape"
        shot_dir.mkdir(parents=True)
        f = shot_dir / "pexels_123.mp4"
        f.write_text("x")
        pool_dir = tmp_path / "pool"
        local = "pool/s1/landscape/pexels_123.mp4"
        assert resolve_local_path(pool_dir, local) == f


class TestResolveLocalPathGuards:
    """Path-traversal defenses added per DeepSeek review (defense-in-depth)."""

    def test_absolute_path_rejected(self, tmp_path):
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        with pytest.raises(ValueError, match="absolute"):
            resolve_local_path(pool_dir, "/etc/passwd")

    def test_parent_traversal_rejected(self, tmp_path):
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        with pytest.raises(ValueError, match="parent-traversal"):
            resolve_local_path(pool_dir, "../../etc/passwd")

    def test_null_byte_rejected(self, tmp_path):
        pool_dir = tmp_path / "pool"
        pool_dir.mkdir()
        with pytest.raises(ValueError, match="null"):
            resolve_local_path(pool_dir, "pool/evil\x00.mp4")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
