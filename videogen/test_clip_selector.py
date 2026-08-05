"""
Tests for videogen/clip_selector.py — the pool→clip selector that fills the
produce.select_clips() stub.

Pure + hermetic: no cv2, no ffmpeg, no network. A stub measure_fn returns fixed
metric dicts so scoring is fully deterministic. The Golden-Rule proof feeds
real assignments through build_edl + validate_edl.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from videogen.clip_selector import (  # noqa: E402
    select_clips,
    hint_for_shot,
    _edl_provenance_for,
    _relevance_score,
    _quality_score,
    _hard_disqualify,
    _handle_sec,
)
from videogen.produce import Brief  # noqa: E402
from videogen.timeline import VOSegment, build_edl  # noqa: E402
from videogen.edl import validate_edl  # noqa: E402


# --- fixtures ----------------------------------------------------------------

def _brief(hints):
    """Brief with the given clip_hints (scene/prompt/duration_sec dicts)."""
    return Brief(tour_slug="t", clip_hints=hints)


def _cand(cid, *, source_type="stock:pexels", license="Pexels License",
          local_path=None, duration_sec=20.0, keywords=None):
    """A manifest candidate dict shaped like clip_pool/models.Candidate."""
    return {
        "candidate_id": cid,
        "source_type": source_type,
        "license": license,
        "local_path": local_path or f"pool/shot1/{cid}.mp4",
        "duration_sec": duration_sec,
        "keywords_matched": keywords or [],
    }


def _pool(shots):
    """Pool manifest dict: {shots: [{shot_id, candidates: [...]}]}."""
    return {"schema_version": 1, "tour": "t", "shots": shots}


def _tags(**by_cand):
    """Build a tags dict: each kwarg is candidate_id → tag fields."""
    out = {}
    for cid, fields in by_cand.items():
        out[cid] = {"tags": fields, "frames_tagged": 1}
    return out


def _vo(shot_id, dur=5.0):
    return VOSegment(shot_id=shot_id, text="x", mp3_path=f"vo/{shot_id}.mp3",
                     duration_sec=dur)


def _measure_map(**by_cand):
    """Build a measure_fn that returns a fixed metric dict per candidate_id."""
    table = dict(by_cand)

    def _fn(candidate):
        return dict(table.get(candidate["candidate_id"], {}))

    return _fn


# --- hint_for_shot -----------------------------------------------------------

class TestHintForShot:
    def test_index_aligned(self):
        brief = _brief([{"scene": "hook", "prompt": "dawn"},
                        {"scene": "body", "prompt": "city"}])
        assert hint_for_shot(brief, "shot1")["prompt"] == "dawn"
        assert hint_for_shot(brief, "shot2")["prompt"] == "city"

    def test_out_of_range_falls_back(self):
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        fb = hint_for_shot(brief, "shot9")
        assert fb["prompt"] == ""
        assert fb["scene"] == "shot9"

    def test_empty_hints(self):
        brief = _brief([])
        fb = hint_for_shot(brief, "shot1")
        assert fb["prompt"] == ""

    def test_scene_match_fallback(self):
        brief = _brief([{"scene": "cta", "prompt": "aerial"}])
        assert hint_for_shot(brief, "cta")["prompt"] == "aerial"


# --- provenance translation (Golden Rule) ------------------------------------

class TestProvenanceTranslation:
    def test_pexels_stock(self):
        p = _edl_provenance_for(_cand("pexels_5", license="Pexels License"))
        assert p.source == "pexels"
        assert p.licence == "Pexels"  # normalized
        assert p.authenticity == "stock"
        assert p.asset_id == "pexels_5"

    def test_pexels_missing_license_defaults(self):
        p = _edl_provenance_for(_cand("pexels_5", license=""))
        assert p.licence == "Pexels"

    def test_ai_generated(self):
        p = _edl_provenance_for(_cand("ai_1", source_type="ai_generated:sora"))
        assert p.source == "ai_generated"
        assert p.authenticity == "illustrative"

    def test_human_capture(self):
        p = _edl_provenance_for(_cand("cap_1", source_type="human_capture:glasses"))
        assert p.source == "human_capture"
        assert p.authenticity == "documentary"

    def test_unknown_source_is_honest(self):
        # Unknown must NOT silently become pexels/stock — that would mislabel.
        p = _edl_provenance_for(_cand("x_1", source_type="mystery:source"))
        assert p.source == "company_owned"
        assert p.authenticity == "illustrative"


# --- relevance scoring -------------------------------------------------------

class TestRelevanceScore:
    def test_matching_tags_score_higher(self):
        tags = {"shot_type": "landscape", "time_of_day": "dawn", "mood": "epic"}
        score = _relevance_score(tags, "dawn landscape epic")
        assert score == 1.0

    def test_partial_match(self):
        tags = {"shot_type": "landscape", "time_of_day": "dawn"}
        # "dawn" matches, "aerial" does not
        assert _relevance_score(tags, "dawn aerial") == 0.5

    def test_no_match_is_zero(self):
        tags = {"shot_type": "food"}
        assert _relevance_score(tags, "dawn landscape") == 0.0

    def test_empty_prompt_is_zero(self):
        assert _relevance_score({"shot_type": "landscape"}, "") == 0.0

    def test_empty_tags_is_zero(self):
        assert _relevance_score({}, "dawn landscape") == 0.0

    def test_substring_matches_compound(self):
        # "golden" should match time_of_day "golden_hour" via substring
        # ("golden_hour" contains "golden"); "light" does not, so 1 of 2 hits.
        tags = {"time_of_day": "golden_hour"}
        assert _relevance_score(tags, "golden light") == 0.5

    def test_substring_match_full(self):
        # All hint tokens appear as substrings in the flattened tag text.
        tags = {"time_of_day": "golden_hour", "mood": "epic"}
        assert _relevance_score(tags, "golden epic") == 1.0

    def test_stopwords_dont_count(self):
        # "the", "shot" are dropped before matching
        tags = {"shot_type": "landscape"}
        assert _relevance_score(tags, "the landscape shot") == 1.0


# --- quality scoring ---------------------------------------------------------

class TestQualityScore:
    def test_empty_metrics_is_zero(self):
        assert _quality_score({}) == 0.0
        assert _quality_score(None) == 0.0

    def test_missing_motion_is_zero(self):
        assert _quality_score({"brightness": 100}) == 0.0

    def test_high_motion_scores_high(self):
        s = _quality_score({"motion_score": 5.0, "brightness": 120})
        assert s == 1.0

    def test_low_motion_scores_low(self):
        s = _quality_score({"motion_score": 0.5, "brightness": 120})
        assert s == 0.0

    def test_clamped_to_unit(self):
        s = _quality_score({"motion_score": 99.0, "brightness": 120})
        assert s == 1.0

    def test_extreme_brightness_dings_score(self):
        good = _quality_score({"motion_score": 3.0, "brightness": 120})
        dark = _quality_score({"motion_score": 3.0, "brightness": 10})
        blown = _quality_score({"motion_score": 3.0, "brightness": 250})
        assert dark < good
        assert blown < good


# --- hard disqualify ---------------------------------------------------------

class TestHardDisqualify:
    def test_amateur_disqualified(self):
        dq, reasons = _hard_disqualify({"commercial_grade": "amateur"}, [])
        assert dq and any("amateur" in r for r in reasons)

    def test_personal_disqualified(self):
        dq, _ = _hard_disqualify({"commercial_grade": "personal"}, [])
        assert dq

    def test_broadcast_passes(self):
        dq, reasons = _hard_disqualify({"commercial_grade": "broadcast"}, [])
        assert not dq and reasons == []

    def test_low_motion_flag_disqualifies(self):
        dq, reasons = _hard_disqualify({}, ["low-motion (likely static)"])
        assert dq and any("static" in r for r in reasons)

    def test_shake_flag_disqualifies(self):
        dq, reasons = _hard_disqualify({}, ["possible camera shake"])
        assert dq and any("shake" in r for r in reasons)

    def test_unrelated_flag_passes(self):
        dq, _ = _hard_disqualify({}, ["brightness outlier (z=1.6)"])
        assert not dq  # brightness is a soft signal, not a hard reject


# --- handle selection --------------------------------------------------------

class TestHandleSec:
    def test_vo_plus_pad(self):
        start, end = _handle_sec(20.0, 5.0)
        assert start == 0.0
        assert end == pytest.approx(7.0)  # 5 + 2 handle

    def test_caps_at_source_length(self):
        start, end = _handle_sec(4.0, 5.0)  # source shorter than VO+pad
        assert end == 4.0

    def test_unknown_source_trusts_vo(self):
        start, end = _handle_sec(0.0, 5.0)
        assert end == pytest.approx(7.0)


# --- select_clips (integration) ----------------------------------------------

class TestSelectClips:
    def test_one_assignment_per_vo_segment(self):
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [_cand("pexels_1")]}])
        tags = _tags(pexels_1={"shot_type": "landscape", "commercial_grade": "professional"})
        vos = [_vo("shot1")]
        out = select_clips(brief, pool, tags, vos, measure_fn=_measure_map())
        assert len(out) == 1
        assert out[0].shot_id == "shot1"

    def test_picks_broadcast_relevant_over_amateur(self):
        """The selector prefers a relevant broadcast clip over an amateur one."""
        brief = _brief([{"scene": "hook", "prompt": "dawn landscape"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [
            _cand("amateur_1", keywords=["dawn"]),
            _cand("broadcast_1", keywords=["dawn"]),
        ]}])
        tags = _tags(
            amateur_1={"shot_type": "landscape", "time_of_day": "dawn",
                       "commercial_grade": "amateur"},
            broadcast_1={"shot_type": "landscape", "time_of_day": "dawn",
                         "commercial_grade": "broadcast"},
        )
        out = select_clips(brief, pool, tags, [_vo("shot1")],
                           measure_fn=_measure_map())
        assert out[0].provenance.asset_id == "broadcast_1"

    def test_all_disqualified_falls_back_least_bad(self):
        """If every candidate is disqualified, selection still returns one
        (build_edl needs a clip per VO segment)."""
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [
            _cand("amateur_a"), _cand("amateur_b"),
        ]}])
        tags = _tags(
            amateur_a={"commercial_grade": "amateur"},
            amateur_b={"commercial_grade": "personal"},
        )
        out = select_clips(brief, pool, tags, [_vo("shot1")],
                           measure_fn=_measure_map())
        assert len(out) == 1  # didn't crash; returned a fallback

    def test_keywords_tiebreak(self):
        """When relevance + quality + motion tie, more keyword matches win."""
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [
            _cand("few_kw", keywords=["dawn"]),
            _cand("many_kw", keywords=["dawn", "sunrise", "morning", "horizon"]),
        ]}])
        # Identical tags (same relevance) + identical metrics (same quality/motion)
        tags = _tags(
            few_kw={"shot_type": "landscape", "time_of_day": "dawn",
                    "commercial_grade": "broadcast"},
            many_kw={"shot_type": "landscape", "time_of_day": "dawn",
                     "commercial_grade": "broadcast"},
        )
        meas = _measure_map(few_kw={"motion_score": 3.0, "brightness": 120},
                            many_kw={"motion_score": 3.0, "brightness": 120})
        out = select_clips(brief, pool, tags, [_vo("shot1")], measure_fn=meas)
        assert out[0].provenance.asset_id == "many_kw"

    def test_empty_pool_raises(self):
        """A shot with no candidates must fail loudly, not silently mock."""
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": []}])
        with pytest.raises(ValueError, match="no candidates"):
            select_clips(brief, pool, {}, [_vo("shot1")], measure_fn=_measure_map())

    def test_missing_shot_raises(self):
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([])  # no shots at all
        with pytest.raises(ValueError, match="no candidates"):
            select_clips(brief, pool, {}, [_vo("shot1")], measure_fn=_measure_map())

    def test_provenance_is_golden_rule_valid(self):
        """Every assignment's Provenance passes the EDL validator's enum check."""
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [_cand("pexels_1")]}])
        tags = _tags(pexels_1={"shot_type": "landscape", "commercial_grade": "broadcast"})
        out = select_clips(brief, pool, tags, [_vo("shot1")], measure_fn=_measure_map())
        p = out[0].provenance
        assert p.source == "pexels"
        assert p.licence  # non-empty
        # authenticity must be in the EDL enum
        assert p.authenticity in {"stock", "illustrative", "documentary"}


class TestEndToEndValidEDL:
    """The proof: select_clips → build_edl → validate_edl passes."""

    def test_golden_rule_edl_validates(self):
        brief = _brief([
            {"scene": "hook", "prompt": "dawn landscape", "duration_sec": 5},
            {"scene": "body", "prompt": "city street", "duration_sec": 5},
        ])
        pool = _pool([
            {"shot_id": "shot1", "candidates": [
                _cand("pexels_1", duration_sec=20.0, keywords=["dawn"]),
                _cand("amateur_1", duration_sec=20.0),
            ]},
            {"shot_id": "shot2", "candidates": [
                _cand("pexels_2", duration_sec=20.0, keywords=["city"]),
            ]},
        ])
        tags = _tags(
            pexels_1={"shot_type": "landscape", "time_of_day": "dawn",
                      "commercial_grade": "broadcast", "mood": "epic"},
            amateur_1={"shot_type": "landscape", "commercial_grade": "amateur"},
            pexels_2={"shot_type": "architecture", "commercial_grade": "professional",
                      "mood": "energetic"},
        )
        vos = [_vo("shot1", 5.0), _vo("shot2", 5.0)]
        assignments = select_clips(brief, pool, tags, vos, measure_fn=_measure_map())

        # shot1 should pick the broadcast clip, not the amateur one
        assert assignments[0].provenance.asset_id == "pexels_1"

        edl = build_edl(vos, assignments, tour="t")
        errors = validate_edl(edl)
        assert errors == [], f"EDL should validate: {errors}"
        assert len(edl.edl) == 2
        assert edl.total_duration_sec == 10.0

    def test_handle_rule_holds(self):
        """clip_end - clip_start >= duration_sec for every shot (EDL rule 9)."""
        brief = _brief([{"scene": "hook", "prompt": "dawn"}])
        pool = _pool([{"shot_id": "shot1", "candidates": [
            _cand("pexels_1", duration_sec=8.0),
        ]}])
        tags = _tags(pexels_1={"commercial_grade": "broadcast"})
        vos = [_vo("shot1", 5.0)]
        assignments = select_clips(brief, pool, tags, vos, measure_fn=_measure_map())
        a = assignments[0]
        assert a.clip_end_sec - a.clip_start_sec >= 5.0
