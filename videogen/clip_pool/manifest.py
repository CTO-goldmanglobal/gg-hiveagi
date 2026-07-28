"""
Write the pool manifest (JSON) and a browser-viewable HTML gallery.

The HTML gallery is the key deliverable of Stage 1 — it lets a human preview
every candidate inline, grouped by shot, without leaving the page. This is
"show me where they are" made concrete.
"""

import html
import json
from pathlib import Path
from typing import Dict, Any


def write_manifest(manifest: Dict[str, Any], pool_dir: Path) -> Path:
    """Write pool_manifest.json into pool_dir. Returns the path."""
    pool_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = pool_dir / "pool_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_path


def _rel(local_path: str) -> str:
    """local_path in the manifest is relative to tour_dir (pool's parent).
    From the HTML in pool_dir, the clip is at <shot>/<orient>/<file>."""
    # Strip leading "pool/" if present
    p = local_path
    if p.startswith("pool/"):
        p = p[len("pool/"):]
    return p


def write_pool_index_html(manifest: Dict[str, Any], pool_dir: Path) -> Path:
    """
    Write pool_index.html — a browser-viewable gallery with inline <video>
    players for every candidate, grouped by shot.

    If clip_metrics.json and/or judgment_log.jsonl exist in pool_dir, their
    data is rendered alongside each clip (metrics + verdict + reason).
    """
    import json

    # Load optional enrichment data
    metrics_cache = {}
    mp = pool_dir / "clip_metrics.json"
    if mp.exists():
        try:
            metrics_cache = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    tags_cache = {}  # candidate_id → {tags: {...}}
    tp = pool_dir / "clip_tags.json"
    if tp.exists():
        try:
            tags_cache = json.loads(tp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    verdicts = {}  # candidate_id → latest verdict entry
    lp = pool_dir / "judgment_log.jsonl"
    if lp.exists():
        for line in lp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                cid = e.get("candidate_id")
                if cid:
                    verdicts[cid] = e  # last wins
            except json.JSONDecodeError:
                pass

    from .metrics import flag_issues, compute_shot_stats
    tour = html.escape(manifest.get("tour", "pool"))
    source_type = html.escape(manifest.get("source_type", "unknown"))
    total = manifest.get("total_clips", 0)
    fetched_at = html.escape(manifest.get("fetched_at", ""))

    parts: list[str] = []
    parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clip Pool — {tour}</title>
<style>
  :root {{
    --bg: #0f1115; --card: #1a1d24; --text: #e8e8e8; --muted: #8b919e;
    --accent: #e9206a; --warn: #f5a623; --ok: #3ecf8e; --border: #2a2e37;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }}
  header {{
    padding: 28px 32px 20px; border-bottom: 1px solid var(--border);
    background: linear-gradient(180deg, #161a21, var(--bg));
  }}
  header h1 {{ margin: 0 0 6px; font-size: 22px; font-weight: 600; }}
  header .meta {{ color: var(--muted); font-size: 13px; }}
  header .meta b {{ color: var(--text); font-weight: 500; }}
  .badge {{
    display: inline-block; padding: 2px 9px; border-radius: 10px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.3px;
  }}
  .badge-stock {{ background: rgba(245,166,35,0.15); color: var(--warn); }}
  .badge-human {{ background: rgba(62,207,142,0.15); color: var(--ok); }}
  .provenance-warn {{
    margin: 16px 32px; padding: 12px 16px; border-radius: 8px;
    background: rgba(245,166,35,0.08); border: 1px solid rgba(245,166,35,0.3);
    color: var(--warn); font-size: 13px;
  }}
  main {{ padding: 0 32px 60px; }}
  .shot {{
    margin: 28px 0; padding: 20px 0; border-top: 1px solid var(--border);
  }}
  .shot:first-child {{ border-top: none; }}
  .shot h2 {{ font-size: 16px; margin: 0 0 4px; font-weight: 600; }}
  .shot .shot-id {{ color: var(--muted); font-size: 12px;
    font-family: ui-monospace, "SF Mono", Menlo, monospace; }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px; margin-top: 16px;
  }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; overflow: hidden;
  }}
  .card video {{ width: 100%; display: block; background: #000; max-height: 200px;
    object-fit: cover; }}
  .card .info {{ padding: 10px 12px; font-size: 12px; }}
  .card .info .id {{ font-family: ui-monospace, Menlo, monospace;
    color: var(--accent); font-weight: 600; }}
  .card .info .dim {{ color: var(--muted); margin-top: 4px; }}
  .card .info a {{ color: var(--muted); text-decoration: none; }}
  .card .info a:hover {{ color: var(--accent); }}
  .card .metrics {{ margin-top: 6px; display: flex; gap: 10px; flex-wrap: wrap;
    font-size: 11px; font-family: ui-monospace, Menlo, monospace; }}
  .card .metrics span {{ color: var(--muted); }}
  .card .metrics span b {{ color: var(--text); font-weight: 500; }}
  .card .tags {{ margin-top: 6px; display: flex; gap: 4px; flex-wrap: wrap; }}
  .card .tag {{ display: inline-block; background: rgba(99,148,235,0.12);
    color: #7aa7f7; padding: 1px 7px; border-radius: 8px; font-size: 10px;
    font-weight: 500; }}
  .card .tag.tag-action {{ background: rgba(233,32,106,0.12); color: var(--accent); }}
  .card .tag.tag-pov {{ background: rgba(168,85,247,0.15); color: #c084fc; }}
  .card .tag.tag-personal {{ background: rgba(245,166,35,0.12); color: var(--warn); }}
  .card .description {{ margin-top: 4px; color: var(--muted); font-size: 11px;
    font-style: italic; line-height: 1.4; }}
  .card .flags {{ margin-top: 4px; }}
  .card .flag {{ display: inline-block; background: rgba(245,166,35,0.12);
    color: var(--warn); padding: 1px 7px; border-radius: 8px; font-size: 10px;
    margin-right: 4px; }}
  .card .verdict {{ margin-top: 8px; padding: 6px 8px; border-radius: 6px;
    font-size: 12px; }}
  .card .verdict-accepted {{ background: rgba(62,207,142,0.1);
    border-left: 3px solid var(--ok); }}
  .card .verdict-rejected {{ background: rgba(233,32,106,0.1);
    border-left: 3px solid var(--accent); }}
  .card .verdict .v-label {{ font-weight: 600; }}
  .card .verdict-accepted .v-label {{ color: var(--ok); }}
  .card .verdict-rejected .v-label {{ color: var(--accent); }}
  .card .verdict .v-reason {{ color: var(--muted); margin-top: 2px; font-size: 11px; }}
  footer {{ padding: 20px 32px; color: var(--muted); font-size: 12px;
    border-top: 1px solid var(--border); }}
  .empty {{ color: var(--muted); font-style: italic; padding: 8px 0; }}
</style>
</head>
<body>
<header>
  <h1>Clip Pool — {tour}</h1>
  <div class="meta">
    <span class="badge {"badge-stock" if source_type.startswith("stock") else "badge-human"}">{source_type}</span>
    &nbsp; {total} candidates · fetched {fetched_at}
  </div>
</header>
""")

    # Provenance warning for stock pools
    if source_type.startswith("stock"):
        parts.append(f"""
<div class="provenance-warn">
  ⚠️ <b>Stock-sourced pool.</b> These clips are for the Forge commercial Reel only.
  Raw stock material is <b>blocked from Labs Seed packages</b> by the provenance gate
  (<code>videogen/provenance.py</code>). The human JUDGMENT layer (accept/reject + reason)
  recorded against these clips <i>is</i> Labs-eligible hybrid seed — tagged with this
  source_type so Labs can tell "taste on stock" from "human capture." See
  <code>docs/LOOP-STRATEGY.md</code> § The hybrid seed.
</div>
""")

    parts.append("<main>\n")
    for shot in manifest.get("shots", []):
        shot_id = html.escape(shot.get("shot_id", ""))
        label = html.escape(shot.get("label", shot_id))
        cands = shot.get("candidates", [])
        # Compute shot-level brightness stats for outlier flags
        shot_mets = [metrics_cache.get(c.get("candidate_id", ""), {})
                     for c in cands]
        shot_stats = compute_shot_stats(shot_mets) if shot_mets else None
        # Count verdicts for this shot
        acc = sum(1 for c in cands if verdicts.get(c.get("candidate_id", ""), {}).get("decision") == "accepted")
        rej = sum(1 for c in cands if verdicts.get(c.get("candidate_id", ""), {}).get("decision") == "rejected")
        undecided = len(cands) - acc - rej
        parts.append(f'<div class="shot">\n')
        parts.append(f'  <h2>{label}</h2>\n')
        parts.append(f'  <div class="shot-id">{shot_id} · {len(cands)} candidates'
                     + (f' · <b style="color:var(--ok)">{acc}✅</b> <b style="color:var(--accent)">{rej}❌</b> <b style="color:var(--muted)">{undecided}undecided</b>' if (acc or rej) else '')
                     + '</div>\n')
        if not cands:
            parts.append('  <div class="empty">No candidates fetched.</div>\n')
        else:
            parts.append('  <div class="grid">\n')
            for c in cands:
                cid_raw = c.get("candidate_id", "")
                cid = html.escape(cid_raw)
                src = html.escape(c.get("source_type", ""))
                vid_path = html.escape(_rel(c.get("local_path", "")))
                dur = c.get("duration_sec", 0)
                w = c.get("width") or "?"
                h = c.get("height") or "?"
                orient = html.escape(c.get("orientation", ""))
                photog = html.escape(c.get("photographer", "") or "—")
                src_url = html.escape(c.get("source_url", ""))

                # Metrics
                m = metrics_cache.get(cid_raw, {})
                flags = flag_issues(m, shot_stats) if m else []
                met_html = ""
                if m and m.get("brightness") is not None:
                    met_parts = []
                    met_parts.append(f"<span>bright<b>{m['brightness']:.0f}</b></span>")
                    if m.get("motion_score") is not None:
                        met_parts.append(f"<span>motion<b>{m['motion_score']:.1f}</b></span>")
                    if m.get("shake_score") is not None:
                        met_parts.append(f"<span>shake<b>{m['shake_score']:.2f}</b></span>")
                    met_html = f'<div class="metrics">{"".join(met_parts)}</div>'

                # Content tags (LLM)
                tag_data = tags_cache.get(cid_raw, {})
                ct = tag_data.get("tags", {}) if tag_data else {}
                tags_html = ""
                desc_html = ""
                if ct:
                    tag_parts = []
                    # Categorical tags as chips
                    for dim in ["shot_type", "camera_perspective", "time_of_day", "mood"]:
                        val = ct.get(dim, "")
                        if val and val != "unknown":
                            # Special styling for POV/action/personal
                            cls = "tag"
                            vl = val.lower()
                            if "pov" in vl or "first_person" in vl:
                                cls += " tag-pov"
                            if "action" in vl:
                                cls += " tag-action"
                            if "personal" in vl or "amateur" in vl:
                                cls += " tag-personal"
                            tag_parts.append(f'<span class="{cls}">{html.escape(val)}</span>')
                    # commercial_grade — important signal
                    grade = ct.get("commercial_grade", "")
                    if grade:
                        cls = "tag tag-personal" if grade in ("personal", "amateur") else "tag"
                        tag_parts.append(f'<span class="{cls}">{html.escape(grade)}</span>')
                    if tag_parts:
                        tags_html = '<div class="tags">' + "".join(tag_parts) + '</div>'
                    desc = ct.get("description", "")
                    if desc:
                        desc_html = f'<div class="description">{html.escape(desc)}</div>'

                flags_html = ""
                if flags:
                    flags_html = '<div class="flags">' + "".join(
                        f'<span class="flag">{html.escape(f)}</span>' for f in flags
                    ) + '</div>'

                # Verdict
                v = verdicts.get(cid_raw)
                verdict_html = ""
                if v:
                    dec = v.get("decision", "")
                    reason = html.escape(v.get("reason", ""))
                    vc = "verdict-accepted" if dec == "accepted" else "verdict-rejected"
                    icon = "✅" if dec == "accepted" else "❌"
                    verdict_html = (
                        f'<div class="verdict {vc}">'
                        f'<div class="v-label">{icon} {dec.upper()}</div>'
                        f'<div class="v-reason">{reason}</div>'
                        f'</div>'
                    )

                parts.append(f"""    <div class="card">
      <video controls preload="none" poster="">
        <source src="{vid_path}" type="video/mp4">
      </video>
      <div class="info">
        <div class="id">{cid}</div>
        <div class="dim">{w}×{h} · {dur}s · {orient} · by {photog}</div>
        <div class="dim"><a href="{src_url}" target="_blank" rel="noopener">pexels source ↗</a></div>
        {tags_html}{met_html}{flags_html}{desc_html}{verdict_html}
      </div>
    </div>
""")
            parts.append("  </div>\n")  # grid
        parts.append("</div>\n")  # shot

    parts.append("""</main>
<footer>
  Generated by <code>videogen.clip_pool</code> · Project Hive.AGI · Goldman Global
</footer>
</body>
</html>
""")

    html_path = pool_dir / "pool_index.html"
    html_path.write_text("".join(parts), encoding="utf-8")
    return html_path
