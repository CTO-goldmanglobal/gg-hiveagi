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


def load_pool(pool_dir: Path) -> List[Dict[str, Any]]:
    """Load clips from pool manifest + tags."""
    pool_dir = Path(pool_dir)
    manifest = json.loads((pool_dir / "pool_manifest.json").read_text())
    tags = json.loads((pool_dir / "clip_tags.json").read_text())

    clips = []
    for shot in manifest.get("shots", []):
        for cand in shot.get("candidates", []):
            cid = cand["candidate_id"]
            clip = {
                "candidate_id": cid,
                "shot_id": shot["shot_id"],
                "orientation": cand["orientation"],
                "local_path": cand["local_path"],
                "tags": tags.get(cid, {}).get("tags", {}),
            }
            clips.append(clip)
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
            # Resolve path relative to pool dir
            local = pool_dir.parent / cand["local_path"]
            if not local.exists():
                local = pool_dir / cand["local_path"].replace("pool/", "", 1)
            clips_data[cid] = str(local.relative_to(pool_dir.parent))

    pairs_json = json.dumps(pairs, ensure_ascii=False)
    clips_json = json.dumps(clips_data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>G0 Experiment — {evaluator_id}</title>
<style>
  :root {{ --bg:#0f1115; --card:#1a1d24; --text:#e8e8e8; --muted:#8b919e; --accent:#e9206a; --ok:#3ecf8e; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .header {{ padding:20px; text-align:center; border-bottom:1px solid #2a2e37; }}
  .header h1 {{ font-size:18px; margin:0 0 4px; }}
  .header .meta {{ color:var(--muted); font-size:13px; }}
  .progress {{ background:#2a2e37; height:4px; border-radius:2px; margin:12px auto; width:80%; }}
  .progress-bar {{ background:var(--accent); height:100%; border-radius:2px; transition:width 0.3s; }}
  .pair {{ display:flex; gap:20px; justify-content:center; padding:20px; flex-wrap:wrap; }}
  .clip {{ background:var(--card); border:1px solid #2a2e37; border-radius:10px; overflow:hidden; width:45%; min-width:300px; }}
  .clip video {{ width:100%; display:block; max-height:250px; object-fit:cover; background:#000; }}
  .clip .info {{ padding:8px 12px; font-size:12px; color:var(--muted); }}
  .buttons {{ display:flex; gap:20px; justify-content:center; padding:20px; }}
  .btn {{ padding:12px 32px; border:none; border-radius:8px; font-size:16px;
    font-weight:600; cursor:pointer; transition:all 0.2s; }}
  .btn-a {{ background:var(--accent); color:#fff; }}
  .btn-b {{ background:var(--ok); color:#000; }}
  .btn:hover {{ transform:scale(1.05); }}
  .done {{ text-align:center; padding:40px; }}
  .done a {{ color:var(--accent); text-decoration:none; font-size:16px; }}
  .hidden {{ display:none; }}
</style>
</head>
<body>
<div class="header">
  <h1>G0 Pairwise Experiment</h1>
  <div class="meta">Evaluator: {html.escape(evaluator_id)} · Pair <span id="current">1</span> / <span id="total">{len(pairs)}</span></div>
  <div class="progress"><div class="progress-bar" id="bar" style="width:0%"></div></div>
</div>

<div id="experiment">
  <div class="pair" id="pair-display">
    <div class="clip">
      <video id="video-a" controls preload="none"></video>
      <div class="info" id="info-a">Clip A</div>
    </div>
    <div class="clip">
      <video id="video-b" controls preload="none"></video>
      <div class="info" id="info-b">Clip B</div>
    </div>
  </div>
  <div class="buttons">
    <button class="btn btn-a" onclick="choose('A')">Keep A</button>
    <button class="btn btn-b" onclick="choose('B')">Keep B</button>
  </div>
</div>

<div id="complete" class="hidden done">
  <h2>Experiment complete! 🎉</h2>
  <p>Download your results:</p>
  <a id="download" href="#">Download results JSON</a>
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
    const blob = new Blob([JSON.stringify(results, null, 2)], {{type:'application/json'}});
    const url = URL.createObjectURL(blob);
    document.getElementById('download').href = url;
    document.getElementById('download').download = 'g0_results_' + evaluatorId + '.json';
    return;
  }}
  const pair = pairs[currentIndex];
  const va = document.getElementById('video-a');
  const vb = document.getElementById('video-b');
  va.src = clipPaths[pair.clip_a] || '';
  vb.src = clipPaths[pair.clip_b] || '';
  document.getElementById('info-a').textContent = pair.clip_a;
  document.getElementById('info-b').textContent = pair.clip_b;
  document.getElementById('current').textContent = currentIndex + 1;
  document.getElementById('bar').style.width = (currentIndex / pairs.length * 100) + '%';
}}

function choose(choice) {{
  const pair = pairs[currentIndex];
  results.push({{
    pair_id: pair.pair_id,
    clip_a: pair.clip_a,
    clip_b: pair.clip_b,
    choice: choice,
    evaluator_id: evaluatorId,
    timestamp: new Date().toISOString(),
    is_repeat: pair.is_repeat,
    original_pair_id: pair.original_pair_id || null,
    model_prediction: pair.model_prediction,
    type: pair.type,
  }});
  currentIndex++;
  showPair();
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
