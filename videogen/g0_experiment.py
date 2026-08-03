"""
G0 Falsification Experiment — does the human-perspective signal exist?

Uses the existing Legends of China Warriors pool:
  136 Pexels clips, 132 LLM-tagged, 6 known tag errors.

The experiment tests three hypotheses:
  H1: Can humans reliably choose between clips? (intra-rater consistency)
  H2: Do humans agree with each other? (inter-rater reliability)
  H3: Does the LLM tag predict the human's choice? (model accuracy)

Method: pairwise comparison (A vs B, "which would you keep?")
  - 100 pairs sampled from the pool
  - Same evaluator sees some pairs twice (hidden, reversed) → consistency test
  - M3 predicts the winner before each pair → accuracy test
  - Multiple evaluators on the same pairs → agreement test

This module GENERATES the experiment (pairs + predictions).
The human runs it via a simple HTML page (like the pool gallery).
Results are collected in experiment_results.jsonl.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

from .clip_pool.models import resolve_local_path
from .provenance import is_labs_eligible


def load_pool(pool_dir: Path) -> List[Dict[str, Any]]:
    """Load clips from pool manifest + tags.

    Provenance note (§3 invariant #1): ``source_type`` is carried through on
    every clip so it can never be silently dropped at a type boundary. G0 is a
    *falsification harness* and may legitimately use stock material as
    stimulus — that is not a Labs-eligibility violation (the gate lives at the
    p2p_exchange export, not at experiment read). But a non-Labs-eligible pool
    is surfaced as a loud, auditable notice so the provenance of any derived
    result is unambiguous. There is intentionally no Labs export path in this
    module.
    """
    pool_dir = Path(pool_dir)
    manifest = json.loads((pool_dir / "pool_manifest.json").read_text())
    tags = json.loads((pool_dir / "clip_tags.json").read_text())

    clips = []
    labs_eligible_seen = False
    for shot in manifest.get("shots", []):
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            source_type = cand.get("source_type", "")
            if is_labs_eligible(source_type):
                labs_eligible_seen = True
            clip = {
                "candidate_id": cid,
                "source_type": source_type,
                "shot_id": shot["shot_id"],
                "orientation": cand["orientation"],
                "local_path": cand["local_path"],
                "tags": tags.get(cid, {}).get("tags", {}),
            }
            clips.append(clip)
    if clips and not labs_eligible_seen:
        # Auditable notice, not a block: G0 may use stock as stimulus, but the
        # provenance of any result from this pool is "non-Labs" by construction.
        print(
            "  ⚠️  G0 pool contains no Labs-eligible (human_capture) clips — "
            "results from this pool are stimulus-only, not Labs seed data."
        )
    return clips


def generate_pairs(
    clips: List[Dict[str, Any]],
    n_pairs: int = 100,
    n_repeat: int = 10,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generate pairwise comparison pairs.

    Strategy:
      - Mix same-shot pairs (harder, tests fine discrimination)
      - Mix cross-shot pairs (easier, tests basic taste)
      - Include n_repeat pairs shown twice (reversed order) for consistency

    Returns list of pair dicts:
      {pair_id, clip_a, clip_b, is_repeat, original_pair_id}
    """
    rng = random.Random(seed)

    # Group by shot
    by_shot: Dict[str, List[Dict]] = {}
    for c in clips:
        sid = c["shot_id"]
        by_shot.setdefault(sid, []).append(c)

    shot_ids = list(by_shot.keys())
    pairs = []
    pair_id = 0

    # Phase 1: same-shot pairs (40% — harder comparisons)
    n_same = int(n_pairs * 0.4)
    for _ in range(n_same):
        sid = rng.choice(shot_ids)
        shot_clips = by_shot[sid]
        if len(shot_clips) < 2:
            continue
        a, b = rng.sample(shot_clips, 2)
        pairs.append({
            "pair_id": f"pair_{pair_id:04d}",
            "clip_a": a["candidate_id"],
            "clip_b": b["candidate_id"],
            "shot": sid,
            "type": "same_shot",
            "is_repeat": False,
        })
        pair_id += 1

    # Phase 2: cross-shot pairs (40% — easier comparisons)
    n_cross = int(n_pairs * 0.4)
    for _ in range(n_cross):
        sid1, sid2 = rng.sample(shot_ids, 2)
        a = rng.choice(by_shot[sid1])
        b = rng.choice(by_shot[sid2])
        pairs.append({
            "pair_id": f"pair_{pair_id:04d}",
            "clip_a": a["candidate_id"],
            "clip_b": b["candidate_id"],
            "shot": f"{sid1}_vs_{sid2}",
            "type": "cross_shot",
            "is_repeat": False,
        })
        pair_id += 1

    # Phase 3: repeat pairs (20% — consistency test, reversed order)
    n_rep = min(n_repeat, len(pairs))
    repeat_indices = rng.sample(range(len(pairs)), n_rep)
    for idx in repeat_indices:
        original = pairs[idx]
        pairs.append({
            "pair_id": f"pair_{pair_id:04d}",
            "clip_a": original["clip_b"],  # swapped!
            "clip_b": original["clip_a"],
            "shot": original["shot"],
            "type": "repeat",
            "is_repeat": True,
            "original_pair_id": original["pair_id"],
        })
        pair_id += 1

    # Shuffle (so repeats aren't at the end)
    rng.shuffle(pairs)

    # Renumber after shuffle
    for i, p in enumerate(pairs):
        p["display_order"] = i

    return pairs


def add_model_predictions(
    pairs: List[Dict[str, Any]],
    clips: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    For each pair, record the model's predicted winner based on commercial_grade.

    Simple heuristic: broadcast > professional > amateur > personal.
    If same grade, mark as "uncertain" (model can't predict).

    This is a BASELINE. In production, M3 would predict with confidence.
    """
    grade_order = {"broadcast": 4, "professional": 3, "amateur": 2, "personal": 1}
    clip_map = {c["candidate_id"]: c for c in clips}

    for pair in pairs:
        ca = clip_map.get(pair["clip_a"], {})
        cb = clip_map.get(pair["clip_b"], {})
        grade_a = grade_order.get((ca.get("tags", {}).get("commercial_grade", "") or "").split(" / ")[0], 0)
        grade_b = grade_order.get((cb.get("tags", {}).get("commercial_grade", "") or "").split(" / ")[0], 0)

        if grade_a > grade_b:
            pair["model_prediction"] = "A"
            pair["model_confident"] = True
        elif grade_b > grade_a:
            pair["model_prediction"] = "B"
            pair["model_confident"] = True
        else:
            pair["model_prediction"] = "uncertain"
            pair["model_confident"] = False

    return pairs


def generate_experiment_html(
    pairs: List[Dict[str, Any]],
    pool_dir: Path,
    out_path: Path,
    evaluator_id: str = "evaluator_1",
) -> Path:
    """
    Generate a self-contained HTML page for running the pairwise experiment.

    Shows two clips side by side. Human clicks "Keep A" or "Keep B".
    Results saved to a downloadable JSON on completion.
    """
    import html

    clips_data = {}
    manifest = json.loads((pool_dir / "pool_manifest.json").read_text())
    for shot in manifest.get("shots", []):
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            local = resolve_local_path(pool_dir, cand["local_path"])
            rel = local.relative_to(pool_dir)
            clips_data[cid] = str(rel)

    pairs_json = json.dumps(pairs, ensure_ascii=False)
    clips_json = json.dumps(clips_data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>G0 Experiment — {html.escape(evaluator_id)}</title>
<style>
  :root {{ --bg:#0f1115; --card:#1a1d24; --text:#e8e8e8; --muted:#8b919e;
    --accent:#e9206a; --ok:#3ecf8e; --border:#2a2e37; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    min-height:100vh; }}
  .header {{ padding:16px 20px; text-align:center; border-bottom:1px solid var(--border);
    position:sticky; top:0; background:var(--bg); z-index:10; }}
  .header h1 {{ font-size:16px; margin-bottom:4px; }}
  .header .meta {{ color:var(--muted); font-size:12px; }}
  .progress {{ background:var(--border); height:3px; border-radius:2px; margin:8px auto 0; width:90%; }}
  .progress-bar {{ background:var(--accent); height:100%; border-radius:2px; transition:width 0.3s; }}
  .pair-container {{ padding:20px; }}
  .pair {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; max-width:900px; margin:0 auto; }}
  @media(max-width:600px) {{ .pair {{ grid-template-columns:1fr; }} }}
  .clip-card {{ background:var(--card); border:2px solid var(--border); border-radius:12px;
    overflow:hidden; cursor:pointer; transition:border-color 0.2s, transform 0.1s; }}
  .clip-card:hover {{ border-color:var(--muted); }}
  .clip-card.selected {{ border-color:var(--ok); }}
  .clip-card .label {{ background:var(--accent); color:#fff; padding:6px 12px;
    font-weight:700; font-size:14px; text-align:center; }}
  .clip-card.b .label {{ background:var(--ok); color:#000; }}
  .clip-card video {{ width:100%; display:block; max-height:280px; object-fit:cover; background:#000; }}
  .clip-card .info {{ padding:8px 12px; font-size:11px; color:var(--muted); font-family:monospace; }}
  .clip-card .pick-btn {{ width:100%; padding:10px; border:none;
    background:var(--border); color:var(--text); font-size:14px; font-weight:600;
    cursor:pointer; transition:background 0.2s; }}
  .clip-card .pick-btn:hover {{ background:var(--accent); color:#fff; }}
  .clip-card.b .pick-btn:hover {{ background:var(--ok); color:#000; }}
  .nav {{ display:flex; justify-content:center; gap:12px; padding:20px; }}
  .skip-btn {{ padding:10px 20px; background:transparent; border:1px solid var(--border);
    color:var(--muted); border-radius:8px; cursor:pointer; font-size:13px; }}
  .done {{ text-align:center; padding:60px 20px; }}
  .done h2 {{ font-size:20px; margin-bottom:12px; }}
  .done a {{ color:var(--accent); text-decoration:none; font-size:16px;
    display:inline-block; padding:12px 24px; border:1px solid var(--accent); border-radius:8px; }}
  .hidden {{ display:none; }}
</style>
</head>
<body>

<div class="header">
  <h1>G0 Pairwise — Which clip would you keep?</h1>
  <div class="meta">Evaluator: {html.escape(evaluator_id)} · Question <span id="current">1</span> of <span id="total">{len(pairs)}</span></div>
  <div class="progress"><div class="progress-bar" id="bar" style="width:0%"></div></div>
</div>

<div id="experiment" class="pair-container">
  <div class="pair">
    <div class="clip-card" id="card-a" onclick="selectCard('A')">
      <div class="label">LEFT</div>
      <video id="video-a" controls preload="auto" playsinline></video>
      <div class="info" id="info-a"></div>
      <button class="pick-btn" onclick="event.stopPropagation();choose('A')">← Keep this one</button>
    </div>
    <div class="clip-card b" id="card-b" onclick="selectCard('B')">
      <div class="label">RIGHT</div>
      <video id="video-b" controls preload="auto" playsinline></video>
      <div class="info" id="info-b"></div>
      <button class="pick-btn" onclick="event.stopPropagation();choose('B')">Keep this one →</button>
    </div>
  </div>
  <div class="nav">
    <input type="text" id="note" placeholder="Why? (optional — your reason is the seed data)"
      style="width:400px;max-width:90%;padding:10px 14px;background:var(--card);border:1px solid var(--border);
      border-radius:8px;color:var(--text);font-size:14px;outline:none;">
    <button class="skip-btn" onclick="choose('skip')">Skip (can't decide)</button>
  </div>
</div>

<div id="complete" class="hidden done">
  <h2>Done! 🎉</h2>
  <p style="color:var(--muted);margin-bottom:20px;">You completed <span id="done-count">0</span> comparisons.</p>
  <a id="download" href="#" download="">Download results JSON</a>
</div>

<script>
const pairs = {pairs_json};
const clipPaths = {clips_json};
const evaluatorId = "{html.escape(evaluator_id)}";
let currentIndex = 0;
const results = [];

function showPair() {{
  if (currentIndex >= pairs.length) {{
    document.getElementById('experiment').classList.add('hidden');
    document.getElementById('complete').classList.remove('hidden');
    document.getElementById('done-count').textContent = results.length;
    const blob = new Blob([JSON.stringify(results, null, 2)], {{type:'application/json'}});
    const url = URL.createObjectURL(blob);
    document.getElementById('download').href = url;
    document.getElementById('download').download = 'g0_results_' + evaluatorId + '.json';
    return;
  }}
  const pair = pairs[currentIndex];
  const pathA = clipPaths[pair.clip_a] || '';
  const pathB = clipPaths[pair.clip_b] || '';

  const va = document.getElementById('video-a');
  const vb = document.getElementById('video-b');
  va.src = pathA;
  va.load();
  vb.src = pathB;
  vb.load();

  document.getElementById('info-a').textContent = pair.clip_a;
  document.getElementById('info-b').textContent = pair.clip_b;
  document.getElementById('card-a').classList.remove('selected');
  document.getElementById('card-b').classList.remove('selected');
  document.getElementById('current').textContent = currentIndex + 1;
  document.getElementById('bar').style.width = (currentIndex / pairs.length * 100) + '%';
}}

function selectCard(side) {{
  document.querySelectorAll('.clip-card').forEach(c => c.classList.remove('selected'));
  document.getElementById('card-' + side.toLowerCase()).classList.add('selected');
}}

function choose(choice) {{
  const pair = pairs[currentIndex];
  const note = document.getElementById('note').value.trim();
  results.push({{
    pair_id: pair.pair_id,
    left_clip: pair.clip_a,
    right_clip: pair.clip_b,
    choice: choice,
    note: note,
    evaluator_id: evaluatorId,
    timestamp: new Date().toISOString(),
    is_repeat: pair.is_repeat,
    original_pair_id: pair.original_pair_id || null,
    model_prediction: pair.model_prediction,
    type: pair.type,
  }});
  document.getElementById('note').value = '';
  currentIndex++;
  showPair();
  window.scrollTo(0, 0);
}}

showPair();
</script>
</body>
</html>"""

    out_path.write_text(html_content, encoding="utf-8")
    return out_path


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze experiment results.

    Computes:
      - Model accuracy (how often did the model prediction match the human?)
      - Consistency (on repeat pairs, did the human choose the same clip?)
      - Choice distribution (A vs B — is there a positional bias?)
      - Per-type breakdown
    """
    total = len(results)
    if total == 0:
        return {"error": "no results"}

    # Model accuracy
    model_correct = sum(
        1 for r in results
        if r.get("model_prediction") != "uncertain"
        and r["model_prediction"] == r["choice"]
    )
    model_predictable = sum(
        1 for r in results
        if r.get("model_prediction") != "uncertain"
    )
    model_accuracy = model_correct / model_predictable if model_predictable else 0

    # Consistency (repeat pairs)
    repeats = [r for r in results if r.get("is_repeat")]
    consistency = 0
    if repeats:
        consistent = 0
        for rep in repeats:
            orig_id = rep.get("original_pair_id")
            original = next((r for r in results if r["pair_id"] == orig_id), None)
            if original:
                # If original chose A, repeat (reversed) should choose B
                if original["choice"] == "A" and rep["choice"] == "B":
                    consistent += 1
                elif original["choice"] == "B" and rep["choice"] == "A":
                    consistent += 1
        consistency = consistent / len(repeats) if repeats else 0

    # Positional bias
    a_choices = sum(1 for r in results if r["choice"] == "A")
    b_choices = sum(1 for r in results if r["choice"] == "B")

    # Per-type
    by_type: Dict[str, Dict] = {}
    for r in results:
        t = r.get("type", "unknown")
        if t not in by_type:
            by_type[t] = {"total": 0, "A": 0, "B": 0}
        by_type[t]["total"] += 1
        by_type[t][r["choice"]] += 1

    return {
        "total_pairs": total,
        "model_accuracy": round(model_accuracy, 3),
        "model_predictable": model_predictable,
        "consistency": round(consistency, 3),
        "repeat_pairs": len(repeats),
        "positional_bias": {
            "A_pct": round(a_choices / total * 100, 1),
            "B_pct": round(b_choices / total * 100, 1),
        },
        "by_type": by_type,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="G0 falsification experiment")
    p.add_argument("--pool-dir", default="explore_china_holiday/tours/legends-of-china-warriors/pool")
    p.add_argument("--n-pairs", type=int, default=100)
    p.add_argument("--evaluator", default="evaluator_1")
    p.add_argument("--analyze", default=None, help="Analyze results JSON file")
    args = p.parse_args()

    if args.analyze:
        results = json.loads(Path(args.analyze).read_text())
        analysis = analyze_results(results)
        print(json.dumps(analysis, indent=2))
    else:
        pool = Path(args.pool_dir)
        clips = load_pool(pool)
        pairs = generate_pairs(clips, n_pairs=args.n_pairs)
        pairs = add_model_predictions(pairs, clips)

        html_path = pool / f"g0_experiment_{args.evaluator}.html"
        generate_experiment_html(pairs, pool, html_path, args.evaluator)

        # Also save the pairs
        (pool / f"g0_pairs_{args.evaluator}.json").write_text(
            json.dumps(pairs, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"✅ Experiment generated: {html_path}")
        print(f"   {len(pairs)} pairs ({args.n_pairs} unique + repeats)")
        print(f"   Pairs saved: g0_pairs_{args.evaluator}.json")
        print(f"   Open in browser: open '{html_path}'")
