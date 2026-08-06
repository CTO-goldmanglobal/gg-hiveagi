"""
videogen/produce.py — the one-command video orchestrator (H4 skeleton).

This is the entry point: `python -m videogen produce --brief brief.yaml --out dir/`

The full chain: ingest → fetch → tag → select → TTS → timeline → compose →
render → QA → result.json + edl.json.

STATUS: skeleton with typed stub contracts. Four stages don't exist yet and
raise NotImplementedError with documented input/output contracts. Three stages
exist but need network (fetch/tag/TTS) — in --mock mode they use synthetic data.
Two stages are pure and always work (load_brief, build_timeline via H1+H3).

Even in mock mode, produce() writes a valid result.json (mock values) and a
valid edl.json (passes validate_edl). This lets video-bridge.mjs call produce
end-to-end immediately, with the stubs filled in subsequent PRs.

STUB CONTRACTS (4 stages to fill):
  - ingest_brief():  brief_path → Brief with keywords + script generated from URL
    FILLED → videogen/ingest_brief.py (H2: URL→keywords, grounded in library_refs)
  - select_clips():  Brief + pool manifest → list[ClipAssignment]
    FILLED → videogen/clip_selector.py (relevance + quality scoring,
               minus-method disqualify, Golden-Rule provenance translation).
  - render_video():  EDL + clips + audio → RenderResult (the actual MP4)
    FILLED → videogen/render.py (EDL-driven renderer: extract → concat → mux).
  - run_qa():        ProduceResult + EDL → QAResult (deterministic + model QA)
    Filled by: H5 (videogen/qa_gate.py)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml
from pydantic import BaseModel

from .edl import EDL, validate_edl, write_edl
from .timeline import VOSegment, ClipAssignment, Provenance, build_edl

logger = logging.getLogger(__name__)

PRODUCE_SCHEMA_VERSION = 1


# --- models ------------------------------------------------------------------

class Brief(BaseModel):
    """The canonical input — from brief.yaml (source of truth per audit fix #3)."""
    schema_version: int = 1
    tour_slug: str
    tour_url: str = ""
    title: str = ""
    duration_target_sec: int = 50
    platforms: List[str] = ["youtube"]
    aspect_ratios: List[str] = ["16:9"]
    language: str = "en-AU"
    voice: str = "warm_calm_au"
    voice_model: str = "English_expressive_narrator"
    music_mood: str = "cinematic_warm"
    cta_text: str = ""
    cta_url: str = ""
    library_refs: List[str] = []
    clip_hints: List[Dict[str, Any]] = []
    branding: Dict[str, Any] = {}
    # Enriched by ingest_brief (H2). Empty when loaded from yaml; populated after the
    # URL→brief enrichment stage so generate_script reads typed/serializable fields
    # instead of untyped extras that model_dump() would drop.
    generated_keywords: Dict[str, List[str]] = {}  # {shot_id: [pexels search phrases]}
    grounded_context: str = ""                      # tour-page + library text for the script writer
    cities: List[str] = []                          # resolved destination names


class RenderResult(BaseModel):
    """Output of the render stage — the actual video file."""
    video_path: str
    duration_sec: float
    codec: str = "h264"
    resolution: str = "1920x1080"


class QACheck(BaseModel):
    """One QA check result."""
    name: str
    layer: str  # deterministic | model | independent
    passed: bool
    detail: str = ""


class QAResult(BaseModel):
    """Output of the QA gate — three-layer audit per edl-schema.md §3."""
    decision: str  # PASS | FAIL | FIX
    checks: List[QACheck] = []
    provenance_failures: int = 0  # must be 0 — model score never overrides this
    autofix_applied: bool = False


class ProduceResult(BaseModel):
    """The return package written to result.json (build plan §2.2)."""
    schema_version: int = PRODUCE_SCHEMA_VERSION
    tour_slug: str
    status: str = "pending"  # delivered | mock | failed | pending
    video: Dict[str, Any] = {}
    edl_path: str = ""
    selection_log_path: Optional[str] = None
    qc_report: Dict[str, Any] = {}
    cost_usd: float = 0.0
    override_count: int = 0
    media_provenance: List[Dict[str, Any]] = []


# --- stage 1: load brief (always works) -------------------------------------

def load_brief(brief_path: Path | str) -> Brief:
    """Load and validate a brief.yaml file.

    The brief is the canonical input (audit fix #3): URL becomes a preset,
    brief.yaml is the source of truth. This function always works — it's pure
    file I/O + pydantic validation.
    """
    data = yaml.safe_load(Path(brief_path).read_text(encoding="utf-8"))
    return Brief.model_validate(data)


def _mock_brief(tour_slug: str = "mock-tour") -> Brief:
    """Create a synthetic brief for mock mode."""
    return Brief(
        tour_slug=tour_slug,
        title="Mock Tour",
        duration_target_sec=30,
        clip_hints=[
            {"scene": "hook", "prompt": "dawn landscape", "duration_sec": 10},
            {"scene": "body", "prompt": "city street", "duration_sec": 10},
            {"scene": "cta", "prompt": "aerial view", "duration_sec": 10},
        ],
    )


# --- stage 2: ingest (STUB — H2) --------------------------------------------

def ingest_brief(
    brief: Brief,
    *,
    url_fetch_fn: Optional[Callable[[str], str]] = None,
    llm_fn: Optional[Callable[[str], Optional[str]]] = None,
    llm_api_key: Optional[str] = None,
) -> Brief:
    """Enrich the brief with keywords + grounded context from the tour URL.

    Contract:
      Input:  Brief (with tour_url + library_refs + clip_hints)
      Output: Brief (enriched: title resolved, generated_keywords + grounded_context
                     + cities populated for the downstream script writer)

    FILLED → videogen/ingest_brief.py (H2). Fetches the tour page, grounds in the
    knowledge-library refs, synthesizes per-shot Pexels search keywords via MiniMax M3.
    Fetch + LLM are injected so tests stay pure; real mode leaves them None.

    Graceful degradation: URL fetch failure → library-only; LLM failure → hint prompts
    as keywords (same as mock). Never raises on content failures.

    In mock mode: produce() bypasses this stage entirely (_mock_brief is used).
    """
    from .ingest_brief import enrich_brief
    return enrich_brief(
        brief,
        url_fetch_fn=url_fetch_fn,
        llm_fn=llm_fn,
        llm_api_key=llm_api_key,
    )


# --- stage 3: fetch (EXISTS — clip_pool.fetch, needs network) ---------------

def fetch_pool_stage(brief: Brief, work_dir: Path, mock: bool = False) -> Dict[str, Any]:
    """Fetch Pexels candidates per shot.

    Real mode: calls clip_pool.fetch.fetch_pool() (fully implemented).
    Mock mode: returns a synthetic pool manifest.
    """
    if mock:
        return _mock_pool_manifest(brief)
    from .clip_pool.fetch import fetch_pool
    # Build a keywords config from the brief's clip_hints
    # (H2 will formalize this mapping)
    raise NotImplementedError(
        "Real fetch_pool_stage needs a keywords.yaml built from brief.clip_hints. "
        "This wiring is part of H2. Use --mock for now, or call "
        "clip_pool.fetch.fetch_pool() directly with a keywords config."
    )


def _mock_pool_manifest(brief: Brief) -> Dict[str, Any]:
    """Synthetic pool manifest for mock mode."""
    return {
        "schema_version": 1,
        "tour": brief.tour_slug,
        "source_type": "stock:pexels",
        "shots": [
            {
                "shot_id": f"shot{i+1}",
                "candidates": [
                    {"candidate_id": f"pexels_{1000+i}", "local_path": f"pool/shot{i+1}/clip.mp4"}
                ],
            }
            for i, hint in enumerate(brief.clip_hints)
        ],
    }


# --- stage 4: tag (EXISTS — clip_pool.llm_tags, needs network) --------------

def tag_pool_stage(pool: Dict[str, Any], work_dir: Path, mock: bool = False) -> Dict[str, Any]:
    """Tag all candidates in the pool via MiniMax M3 vision.

    Real mode: calls clip_pool.llm_tags.pretag_pool() (fully implemented).
    Mock mode: returns synthetic tags.
    """
    if mock:
        return _mock_tags(pool)
    from .clip_pool.llm_tags import pretag_pool
    return pretag_pool(pool, work_dir)


def _mock_tags(pool: Dict[str, Any]) -> Dict[str, Any]:
    """Synthetic tags for mock mode."""
    tags = {}
    for shot in pool.get("shots", []):
        for cand in shot.get("candidates", []):
            tags[cand["candidate_id"]] = {
                "tags": {
                    "shot_type": "landscape",
                    "commercial_grade": "professional",
                    "mood": "cinematic",
                }
            }
    return tags


# --- stage 5: generate script (STUB — needs selector) -----------------------

def generate_script(brief: Brief, pool: Dict[str, Any], tags: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate a narration script from the brief + tagged pool.

    Contract:
      Input:  Brief + pool manifest + tags dict
      Output: [{shot_id, text}, ...] — one entry per shot
      Filled by: a new script generator (pool→narration).

    In mock mode: produce() calls _mock_script() directly.
    """
    raise NotImplementedError(
        "generate_script() not yet built. Needs an LLM-driven narration writer "
        "that reads the tagged pool + brief and produces per-shot VO text. "
        "The old select.py:write_script() is frame-based and doesn't fit the "
        "clip-pool paradigm. In mock mode, produce() uses a synthetic script."
    )


def _mock_script(brief: Brief) -> List[Dict[str, str]]:
    """Synthetic script for mock mode — one segment per clip hint."""
    return [
        {"shot_id": f"shot{i+1}", "text": hint.get("prompt", f"Scene {i+1}")}
        for i, hint in enumerate(brief.clip_hints)
    ] or [{"shot_id": "shot1", "text": "Mock narration."}]


# --- stage 6: select clips (STUB — needs selector) --------------------------

def select_clips(
    brief: Brief,
    pool: Dict[str, Any],
    tags: Dict[str, Any],
    vo_segments: List[VOSegment],
    measure_fn: Optional[Any] = None,
) -> List[ClipAssignment]:
    """Select the best candidate per shot from the tagged pool.

    Delegates to videogen.clip_selector.select_clips — the pool→clip selector
    that scores candidates by tag relevance (vs the brief's clip_hints) + measured
    quality, applies the minus-method hard filter (amateur/personal, low-motion),
    and emits one ClipAssignment per VO segment with Golden-Rule Provenance.

    Contract:
      Input:  Brief + pool manifest + tags + VO segments (one per shot)
      Output: list[ClipAssignment] — one per shot, with source_path + provenance

    measure_fn is forwarded to the selector when provided (tests inject a stub
    so no real video file is read); real mode leaves it None to use the default
    on-disk measurer.

    In mock mode: produce() calls _mock_clip_assignments() directly.
    """
    from .clip_selector import select_clips as _select
    if measure_fn is not None:
        return _select(brief, pool, tags, vo_segments, measure_fn=measure_fn)
    return _select(brief, pool, tags, vo_segments)


def _mock_clip_assignments(
    pool: Dict[str, Any], vo_segments: List[VOSegment]
) -> List[ClipAssignment]:
    """Synthetic clip assignments — first candidate per shot, mock provenance."""
    shot_map = {}
    for shot in pool.get("shots", []):
        cands = shot.get("candidates", [])
        if cands:
            shot_map[shot["shot_id"]] = cands[0]

    assignments = []
    for vo in vo_segments:
        cand = shot_map.get(vo.shot_id, {"local_path": f"pool/{vo.shot_id}/clip.mp4"})
        assignments.append(ClipAssignment(
            shot_id=vo.shot_id,
            source_path=cand.get("local_path", f"pool/{vo.shot_id}/clip.mp4"),
            clip_start_sec=0.0,
            clip_end_sec=vo.duration_sec + 2.0,  # +2s handle
            provenance=Provenance(
                source="pexels",
                asset_id=cand.get("candidate_id", "mock"),
                licence="Pexels",
                authenticity="stock",
            ),
        ))
    return assignments


# --- stage 7: TTS (EXISTS — timeline.generate_vo_segments, needs network) ---

def tts_stage(
    script: List[Dict[str, str]],
    work_dir: Path,
    brief: Brief,
    mock: bool = False,
) -> List[VOSegment]:
    """Generate VO segments via MiniMax speech-2.8-hd.

    Real mode: calls timeline.generate_vo_segments() (fully implemented in H3).
    Mock mode: returns synthetic segments with even durations.
    """
    if mock:
        return _mock_vo_segments(script, brief)
    from .timeline import generate_vo_segments
    return generate_vo_segments(
        script, work_dir,
        voice_id=brief.voice_model,
    )


def _mock_vo_segments(script: List[Dict[str, str]], brief: Brief) -> List[VOSegment]:
    """Synthetic VO segments — even-split durations across target."""
    n = len(script)
    per_shot = brief.duration_target_sec / n if n else 10.0
    return [
        VOSegment(
            shot_id=item["shot_id"],
            text=item["text"],
            mp3_path=f"vo/{item['shot_id']}.mp3",
            duration_sec=per_shot,
        )
        for item in script
    ]


# --- stage 8: build timeline (EXISTS — H3, pure) ----------------------------

def build_timeline_stage(
    vo_segments: List[VOSegment],
    clip_assignments: List[ClipAssignment],
    brief: Brief,
) -> EDL:
    """Build the EDL from VO segments + clip assignments.

    Pure function — no network. Uses timeline.build_edl() (H3) which calls
    compute_total_duration() from edl.py (the H1 time-equation fix).
    """
    return build_edl(vo_segments, clip_assignments, tour=brief.tour_slug)


# --- stage 9: render (STUB — needs EDL-driven compose) ----------------------

def render_video(
    edl: EDL,
    work_dir: Path,
    audio_path: Optional[str] = None,
) -> RenderResult:
    """Render the EDL into a final video file.

    Calls videogen/render.py::render_video() — the EDL-driven renderer.
    Three phases: extract segments → concat → mux audio.
    Produces a BASE video (no branding overlays; those are a separate finish step).

    Contract:
      Input:  EDL (validated) + work_dir + optional mixed audio path
      Output: RenderResult (video_path, duration, codec, resolution)
    """
    from .render import render_video as _render
    return _render(edl, work_dir, audio_path=audio_path)


# --- stage 10: QA (STUB — H5) -----------------------------------------------

def run_qa(result: ProduceResult, edl: EDL) -> QAResult:
    """STUB: run the three-layer QA gate.

    Contract:
      Input:  ProduceResult (with video path) + EDL
      Output: QAResult (decision: PASS|FAIL|FIX, checks per layer)
      Filled by: H5 — videogen/qa_gate.py.

    Three layers (edl-schema.md §3):
      1. Deterministic: duration, black-frame, silence, subtitle timing,
         safe-area, provenance completeness.
      2. Model-based (M3): visual relevance, synthetic defects, brand fit.
      3. Independent sample: second model or human reviews a sample.

    Rule: a model score must NEVER override a deterministic provenance failure.
    """
    raise NotImplementedError(
        "run_qa() not yet built — this is H5 (videogen/qa_gate.py). "
        "Three-layer QA: deterministic > model-based > independent. "
        "A model score must never override a deterministic provenance failure."
    )


def _mock_qa(edl: EDL) -> QAResult:
    """Mock QA — always passes, notes it's a mock."""
    return QAResult(
        decision="PASS",
        checks=[QACheck(name="mock_mode", layer="deterministic", passed=True,
                        detail="Mock QA — no real checks run.")],
        provenance_failures=0,
    )


# --- result.json writer ------------------------------------------------------

def write_result_json(
    result: ProduceResult,
    edl: EDL,
    out_dir: Path,
) -> Path:
    """Write result.json with media_provenance extracted from the EDL."""
    result.edl_path = str(out_dir / "edl.json")
    result.media_provenance = [
        {
            "shot_id": s.shot_id,
            "source": s.provenance.source if s.provenance else "unknown",
            "asset_id": s.provenance.asset_id if s.provenance else "",
            "licence": s.provenance.licence if s.provenance else "",
            "authenticity": s.provenance.authenticity if s.provenance else "",
        }
        for s in edl.edl
    ]
    path = out_dir / "result.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path


# --- the orchestrator --------------------------------------------------------

def produce(
    brief_path: Optional[Path | str] = None,
    out_dir: Path | str = "forge-output",
    mock: bool = False,
) -> ProduceResult:
    """Run the full video production pipeline.

    Args:
        brief_path: path to brief.yaml (canonical input). If None + mock, uses a mock brief.
        out_dir: output directory for result.json + edl.json.
        mock: if True, skip all network calls and stubs; use synthetic data.
              Produces valid result.json + edl.json for integration testing.

    Returns:
        ProduceResult — also written to out_dir/result.json.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("produce() mode=%s brief=%s out=%s", "mock" if mock else "real", brief_path, out_dir)

    # 1. Load brief (always works)
    if brief_path:
        brief = load_brief(brief_path)
    elif mock:
        brief = _mock_brief()
    else:
        raise ValueError("brief_path is required in real mode (or use mock=True)")

    # 2. Ingest (H2 stub — skipped in mock)
    if not mock:
        brief = ingest_brief(brief)  # H2: URL→keywords, grounded in library_refs

    # 3. Fetch pool
    pool = fetch_pool_stage(brief, out_dir, mock=mock)

    # 4. Tag pool
    tags = tag_pool_stage(pool, out_dir, mock=mock)

    # 5. Generate script
    if mock:
        script = _mock_script(brief)
    else:
        script = generate_script(brief, pool, tags)  # NotImplementedError until built

    # 6. TTS
    vo_segments = tts_stage(script, out_dir, brief, mock=mock)

    # 7. Select clips
    if mock:
        clip_assignments = _mock_clip_assignments(pool, vo_segments)
    else:
        clip_assignments = select_clips(brief, pool, tags, vo_segments)  # stub

    # 8. Build timeline (H3 — pure, always works)
    edl = build_timeline_stage(vo_segments, clip_assignments, brief)

    # 9. Validate EDL (H1 — the gate)
    errors = validate_edl(edl)
    if errors:
        raise ValueError(f"EDL validation failed: {errors}")
    write_edl(edl, out_dir / "edl.json")
    logger.info("EDL written + validated: %d shots, %.1fs", len(edl.edl), edl.total_duration_sec)

    # 10. Render (stub — skipped in mock)
    if mock:
        render = RenderResult(
            video_path=str(out_dir / "mock_video.mp4"),
            duration_sec=edl.total_duration_sec,
        )
    else:
        render = render_video(edl, out_dir)  # NotImplementedError until built

    # 11. QA (H5 stub — mock passes)
    result = ProduceResult(
        tour_slug=brief.tour_slug,
        status="mock" if mock else "delivered",
        video={"landscape_mp4_path": render.video_path,
               "duration_sec": render.duration_sec},
        cost_usd=0.0 if mock else 0.0,  # TODO: real cost tracking
    )
    if mock:
        qa = _mock_qa(edl)
    else:
        qa = run_qa(result, edl)  # NotImplementedError until H5

    result.qc_report = qa.model_dump()

    # 12. Write result.json (Golden Rule: media_provenance from EDL)
    result_path = write_result_json(result, edl, out_dir)
    logger.info("result.json written: %s (status=%s)", result_path, result.status)

    return result
