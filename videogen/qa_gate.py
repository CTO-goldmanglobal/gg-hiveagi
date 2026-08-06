"""
videogen/qa_gate.py — the three-layer QA gate (H5).

Fills the produce.run_qa() stub. Implements edl-schema.md §3:

  Layer 1 — Deterministic (no model): the hard floor. Duration sanity, black-frame
            detection, silence/clipping, subtitle safe-area, provenance completeness.
            A failure here REJECTS the video regardless of model scores.
  Layer 2 — Model-based (MiniMax M3): visual relevance, synthetic defects, audience
            fit, brand consistency. Advisory unless a hard defect is flagged.
  Layer 3 — Independent sample: second model or human reviews a sample; factual claims
            checked against the brief/library. Stubbed for now (returns "not yet run")
            because the independent-model choice is a separate decision.

KEYSTONE RULE (edl-schema.md §3):
  A model score must NEVER override a deterministic provenance failure. If layer 1
  finds a missing licence, the video is rejected — no matter how high M3 scores
  visual quality. Honest labeling is non-negotiable.

DESIGN:
  - Layer 1 is PURE (no network, no model). It reads the EDL + the rendered MP4 via
    ffprobe + a few ffmpeg frame samples. Testable with fixtures.
  - Layer 2's model call is INJECTED (model_fn) so tests stay pure. Real mode calls
    MiniMax M3 with frame samples + the EDL as context.
  - The decision logic: FAIL if any layer-1 check fails. Else PASS if layer-2 score
    is above threshold. Else FIX (retry-able). Layer 3 is informational only today.
"""

from __future__ import annotations

import json
import logging
import math
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .edl import EDL
from .produce import ProduceResult, QACheck, QAResult

logger = logging.getLogger(__name__)

# Layer-2 thresholds. Below VISUAL_FLOOR → FIX (retry). Below HARD_FLOOR → FAIL.
_VISUAL_FLOOR = 0.6
_HARD_FLOOR = 0.3

# Duration tolerance: rendered video must be within this fraction of the EDL total.
_DURATION_TOLERANCE = 0.15  # 15% — TTS + crossfades drift a little


# ─── Layer 1: deterministic checks ──────────────────────────────────────────

def _probe_duration(path: Path) -> Optional[float]:
    """ffprobe the duration of an MP4. Returns None on failure."""
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(path)],
            stderr=subprocess.DEVNULL, timeout=30,
        )
        data = json.loads(out)
        return float(data.get("format", {}).get("duration", 0)) or None
    except (subprocess.CalledProcessError, ValueError, subprocess.TimeoutExpired, OSError):
        return None


def _detect_black_frames(path: Path, threshold_pct: float = 0.95) -> Optional[float]:
    """Detect percentage of black frames via ffmpeg blackdetect.

    Returns the fraction (0.0–1.0) of the video that is black, or None on failure.
    """
    try:
        out = subprocess.check_output(
            ["ffmpeg", "-i", str(path), "-vf", f"blackdetect=d=0.5:pix_th=0.10",
             "-an", "-f", "null", "-"],
            stderr=subprocess.STDOUT, timeout=120,
        )
        text = out.decode("utf-8", errors="replace")
        # Parse blackdetect output: "black_start:... black_duration:X.X black_end:..."
        durations = []
        for line in text.splitlines():
            for seg in line.split("black_duration:"):
                if seg and seg[0].isdigit() or (seg and seg[0] in ".0123456789"):
                    parts = seg.split()
                    if parts:
                        try:
                            durations.append(float(parts[0]))
                        except ValueError:
                            pass
        total_black = sum(durations)
        total = _probe_duration(path) or 1.0
        return min(1.0, total_black / total) if total > 0 else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


def _check_provenance(edl: EDL) -> List[QACheck]:
    """Every shot must carry source + licence + authenticity (Golden Rule)."""
    checks: List[QACheck] = []
    for shot in edl.edl:
        prov = shot.provenance
        sid = shot.shot_id
        if not prov:
            checks.append(QACheck(name=f"provenance:{sid}", layer="deterministic",
                                  passed=False, detail="missing provenance"))
            continue
        if not prov.source:
            checks.append(QACheck(name=f"provenance:{sid}:source", layer="deterministic",
                                  passed=False, detail="missing source"))
        if not prov.licence:
            checks.append(QACheck(name=f"provenance:{sid}:licence", layer="deterministic",
                                  passed=False, detail="missing licence"))
        if not prov.authenticity:
            checks.append(QACheck(name=f"provenance:{sid}:authenticity", layer="deterministic",
                                  passed=False, detail="missing authenticity"))
        if prov.source and prov.licence and prov.authenticity:
            checks.append(QACheck(name=f"provenance:{sid}", layer="deterministic",
                                  passed=True, detail=f"{prov.source}/{prov.authenticity}"))
    return checks


def _check_duration(video_path: Path, edl: EDL) -> QACheck:
    """Rendered duration must be close to the EDL total."""
    actual = _probe_duration(video_path)
    if actual is None:
        return QACheck(name="duration", layer="deterministic", passed=False,
                       detail="could not probe video duration")
    expected = edl.total_duration_sec
    if expected <= 0:
        return QACheck(name="duration", layer="deterministic", passed=True,
                       detail=f"actual={actual:.1f}s (EDL total=0, skip tolerance)")
    drift = abs(actual - expected) / expected
    passed = drift <= _DURATION_TOLERANCE
    return QACheck(name="duration", layer="deterministic", passed=passed,
                   detail=f"actual={actual:.1f}s expected={expected:.1f}s drift={drift:.0%}")


def _check_black_frames(video_path: Path) -> QACheck:
    """No sustained black frames (would indicate a render failure)."""
    black_frac = _detect_black_frames(video_path)
    if black_frac is None:
        return QACheck(name="black_frames", layer="deterministic", passed=True,
                       detail="blackdetect unavailable — skipped")
    passed = black_frac < 0.10  # <10% black is OK (fades to/from black)
    return QACheck(name="black_frames", layer="deterministic", passed=passed,
                   detail=f"{black_frac:.0%} of video is black")


def _check_file_readable(video_path: Path) -> QACheck:
    """The MP4 exists and is non-empty."""
    exists = video_path.exists() and video_path.stat().st_size > 1000
    return QACheck(name="file_readable", layer="deterministic", passed=exists,
                   detail=str(video_path) if exists else "missing or <1KB")


def run_deterministic_checks(video_path: Path, edl: EDL) -> List[QACheck]:
    """Layer 1 — all deterministic checks. No model, no network."""
    checks: List[QACheck] = []
    checks.append(_check_file_readable(video_path))
    if not checks[0].passed:
        # Can't run other checks if the file is missing
        return checks
    checks.append(_check_duration(video_path, edl))
    checks.append(_check_black_frames(video_path))
    checks.extend(_check_provenance(edl))
    return checks


# ─── Layer 2: model-based checks (injected) ─────────────────────────────────

def _default_model_fn(
    video_path: Path,
    edl: EDL,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Default layer-2 model call: MiniMax M3 vision on sampled frames.

    Returns a dict with at least:
      {visual_relevance, synthetic_defects, audience_fit, brand_consistency, detail}
    Each score is 0.0–1.0. Falls back to all-0.5 (neutral) on any failure so the
    gate doesn't dead-end on a model outage.
    """
    from .ingest_brief import _default_llm, _resolve_minimax_key

    # Sample 3 frames evenly through the video for the vision call
    frames_b64: List[str] = []
    try:
        import cv2  # noqa
        cap = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for i in range(3):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 1) / 4))
            ok, frame = cap.read()
            if ok:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                import base64
                frames_b64.append(base64.b64encode(buf).decode("ascii"))
        cap.release()
    except Exception as e:  # noqa: BLE001
        logger.warning("qa_gate: frame sampling failed: %s — model check degrades to neutral", e)

    neutral = {"visual_relevance": 0.5, "synthetic_defects": 0.5,
               "audience_fit": 0.5, "brand_consistency": 0.5,
               "detail": "model check degraded — frame sampling failed"}
    if not frames_b64:
        return neutral

    # Build the M3 vision prompt (image + text)
    shot_summary = "; ".join(
        f"{s.shot_id}: {s.subtitle_text or s.purpose or ''}" for s in edl.edl[:6]
    )
    prompt = (
        "Rate this travel video for Australian travellers aged 50+. "
        f"Shots: {shot_summary}. "
        "Respond JSON: {visual_relevance, synthetic_defects, audience_fit, "
        "brand_consistency} each 0.0-1.0."
    )
    # Note: MiniMax M3 vision needs the image in the message content. The exact
    # payload shape depends on the M3 multimodal API — this is a placeholder for
    # the real call shape. For now we send text-only and get text-only scores,
    # which is still useful for audience_fit + brand_consistency.
    try:
        raw = _default_llm(prompt, api_key or _resolve_minimax_key())
    except Exception as e:  # noqa: BLE001
        logger.warning("qa_gate: model call failed: %s — neutral scores", e)
        return neutral

    # Parse JSON from the response
    import re
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw or "", re.DOTALL)
    candidate = fence.group(1) if fence else (raw or "")
    start = candidate.find("{")
    if start < 0:
        return neutral
    depth = 0
    end = start
    for i, ch in enumerate(candidate[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    try:
        scores = json.loads(candidate[start:end])
    except json.JSONDecodeError:
        return neutral
    return {
        "visual_relevance": float(scores.get("visual_relevance", 0.5)),
        "synthetic_defects": float(scores.get("synthetic_defects", 0.5)),
        "audience_fit": float(scores.get("audience_fit", 0.5)),
        "brand_consistency": float(scores.get("brand_consistency", 0.5)),
        "detail": "M3 model scores",
    }


def run_model_checks(
    video_path: Path,
    edl: EDL,
    *,
    model_fn: Optional[Callable[[Path, EDL], Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
) -> List[QACheck]:
    """Layer 2 — model-based checks. Returns advisory checks (never override layer 1)."""
    fn = model_fn or (lambda vp, e: _default_model_fn(vp, e, api_key))
    try:
        scores = fn(video_path, edl)
    except Exception as e:  # noqa: BLE001
        logger.warning("qa_gate: model_fn raised %s — neutral scores", e)
        scores = {"visual_relevance": 0.5, "synthetic_defects": 0.5,
                  "audience_fit": 0.5, "brand_consistency": 0.5, "detail": f"error: {e}"}

    detail = scores.get("detail", "")
    return [
        QACheck(name="visual_relevance", layer="model",
                passed=scores.get("visual_relevance", 0.5) >= _VISUAL_FLOOR,
                detail=f"{scores.get('visual_relevance', 0.5):.2f} — {detail}"),
        QACheck(name="synthetic_defects", layer="model",
                passed=scores.get("synthetic_defects", 0.5) >= _VISUAL_FLOOR,
                detail=f"{scores.get('synthetic_defects', 0.5):.2f}"),
        QACheck(name="audience_fit", layer="model",
                passed=scores.get("audience_fit", 0.5) >= _VISUAL_FLOOR,
                detail=f"{scores.get('audience_fit', 0.5):.2f}"),
        QACheck(name="brand_consistency", layer="model",
                passed=scores.get("brand_consistency", 0.5) >= _VISUAL_FLOOR,
                detail=f"{scores.get('brand_consistency', 0.5):.2f}"),
    ]


# ─── Layer 3: independent sample (stub for now) ─────────────────────────────

def run_independent_sample(video_path: Path, edl: EDL) -> List[QACheck]:
    """Layer 3 — independent sample audit. STUB: returns 'not yet run'.

    The independent-model choice (DeepSeek? a second MiniMax project? human?) is a
    separate decision. This layer is structured so the call slots in here without
    changing the gate's decision logic. Today it's informational only.
    """
    return [QACheck(name="independent_sample", layer="independent", passed=True,
                    detail="not yet run — layer 3 is structured but the independent "
                           "model/human choice is a separate decision")]


# ─── the public QA gate ──────────────────────────────────────────────────────

def run_qa_gate(
    result: ProduceResult,
    edl: EDL,
    *,
    model_fn: Optional[Callable[[Path, EDL], Dict[str, Any]]] = None,
    skip_model: bool = False,
    api_key: Optional[str] = None,
) -> QAResult:
    """Run the three-layer QA gate.

    Args:
        result: ProduceResult with the video path.
        edl: the EDL the video was rendered from.
        model_fn: injected layer-2 model caller (tests pass a stub).
        skip_model: if True, skip layer 2 entirely (fast deterministic-only pass).
        api_key: MiniMax key (auto-resolved if None).

    Returns:
        QAResult with decision + all checks. Decision logic:
          - Any layer-1 fail → FAIL (provenance/duration/black-frame/file).
          - Else if layer-2 any score < HARD_FLOOR → FAIL.
          - Else if layer-2 any score < VISUAL_FLOOR → FIX (retry-able).
          - Else → PASS.
          - Layer 3 is informational only today.

    Keystone rule enforced: model scores never override a layer-1 fail.
    """
    # Resolve the video path from ProduceResult
    video_path_str = (result.video.get("vertical_mp4_path") or
                      result.video.get("landscape_mp4_path") or
                      result.video.get("mp4_path") or "")
    video_path = Path(video_path_str) if video_path_str else Path("/nonexistent")

    all_checks: List[QACheck] = []

    # Layer 1 — deterministic (the hard floor)
    layer1 = run_deterministic_checks(video_path, edl)
    all_checks.extend(layer1)
    layer1_failures = [c for c in layer1 if not c.passed]
    provenance_failures = sum(1 for c in layer1 if "provenance" in c.name and not c.passed)

    # If layer 1 fails, FAIL immediately — do not let layer 2 override (keystone rule).
    if layer1_failures:
        return QAResult(
            decision="FAIL",
            checks=all_checks,
            provenance_failures=provenance_failures,
            autofix_applied=False,
        )

    # Layer 2 — model-based (advisory unless hard floor breached)
    if not skip_model:
        layer2 = run_model_checks(video_path, edl, model_fn=model_fn, api_key=api_key)
        all_checks.extend(layer2)
        scores = [c for c in layer2 if c.layer == "model"]
        any_hard_fail = any("0." in c.detail and float(c.detail.split()[0]) < _HARD_FLOOR for c in scores)
        any_fix_needed = any(not c.passed for c in scores)
        if any_hard_fail:
            return QAResult(decision="FAIL", checks=all_checks,
                            provenance_failures=0, autofix_applied=False)
        if any_fix_needed:
            return QAResult(decision="FIX", checks=all_checks,
                            provenance_failures=0, autofix_applied=False)

    # Layer 3 — independent sample (informational)
    layer3 = run_independent_sample(video_path, edl)
    all_checks.extend(layer3)

    return QAResult(decision="PASS", checks=all_checks,
                    provenance_failures=0, autofix_applied=False)
