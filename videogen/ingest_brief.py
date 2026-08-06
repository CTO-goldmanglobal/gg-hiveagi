"""
videogen/ingest_brief.py — enrich a Brief from the tour URL + knowledge library.

Fills the produce.ingest_brief() stub (H2). The Brief arrives from brief.yaml with
tour_url + library_refs + clip_hints. This stage enriches it:

  1. Fetch the tour page HTML (urllib — no new deps).
  2. Extract the itinerary/title/highlights (regex + text extraction; no BeautifulSoup
     dependency to keep the module pure-testable).
  3. Ground enrichment in the library_refs markdown files when present — these are the
     fact substrate (VIDEO-AUTOMATION-AUDIT.md §1 Golden Rule). The tour page is
     marketing copy; the library is verified facts.
  4. Use MiniMax M3 to synthesize per-shot keywords from the grounded content, aligned
     to the brief's clip_hints (so fetch_pool has targeted search terms per shot).

The LLM + URL fetch are INJECTED (url_fetch_fn, llm_fn) so tests stay pure and fast.

WHY A SEPARATE MODULE (not inline in produce.py):
  ingest_brief is pure and testable: it fetches, extracts, grounds, and synthesizes.
  Keeping it isolated lets it grow (structured-data extraction, multi-language) without
  bloating the orchestrator. Mirrors the clip_selector.py isolation pattern.

DESIGN (mirrors clip_pool/llm_tags.py):
  - Fetch + extract are deterministic (no LLM). The LLM only synthesizes keywords from
    already-extracted text, so a fetch failure degrades gracefully (fall back to the
    clip_hints as keywords, same as mock mode) rather than crashing.
  - The brief is enriched IN PLACE — we return a new Brief with the same fields plus
    generated_keywords. clip_hints are preserved (they're the source of shot_id alignment).
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .produce import Brief

logger = logging.getLogger(__name__)

# Only read this many chars of HTML — tour pages are heavy with nav/footer boilerplate.
# The itinerary/title/highlights we want are in the first half of the <main>/<article>.
_MAX_HTML_CHARS = 200_000

# Cap library_ref file size too — knowledge-library entries are ~3-5KB but be defensive.
_MAX_LIBRARY_CHARS = 50_000


# --- HTML extraction (deterministic, no deps) --------------------------------

def _strip_html(html: str) -> str:
    """Crude HTML → text: drop scripts/styles/tags, collapse whitespace."""
    html = re.sub(r"<script\b[^<]*</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style\b[^<]*</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode the few entities that matter for readable text
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&lt;", "<")
                .replace("&gt;", ">"))
    return re.sub(r"\s+", " ", html).strip()


def _extract_title(html: str) -> str:
    """Pull the <title> or first <h1> — the tour name."""
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        # Site suffixes like " | ExploreChina Holidays" — strip them
        title = re.split(r"\s*[|–-]\s*Explore", title, flags=re.IGNORECASE)[0].strip()
        if title:
            return title
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return ""


def _extract_itinerary_text(body_text: str, max_chars: int = 8000) -> str:
    """Pull the itinerary-shaped section from the page body text.

    Heuristic: tour pages have a section with day-by-day content. We take the chunk
    around 'Itinerary' / 'Day 1' / 'Highlights' markers. Falls back to the first
    max_chars of body text if no marker found.
    """
    for marker in ("Itinerary", "Day 1", "Day One", "Highlights", "What You'll See"):
        idx = body_text.find(marker)
        if idx >= 0:
            return body_text[idx:idx + max_chars]
    return body_text[:max_chars]


def _extract_cities(title: str, body_text: str) -> List[str]:
    """Pull city/destination names from title + body. Curated list of ECH destinations."""
    cities = [
        "Beijing", "Shanghai", "Xi'an", "Xian", "Chengdu", "Zhangjiajie", "Guilin",
        "Yangshuo", "Lijiang", "Dali", "Kunming", "Harbin", "Suzhou", "Hangzhou",
        "Wuhan", "Chongqing", "Xianning", "Tibet", "Lhasa", "Dunhuang", "Turpan",
        "Urumqi", "Pingyao", "Luoyang", "Nanjing", "Huangshan", "Yangtze",
    ]
    haystack = f"{title} {body_text[:5000]}".lower()
    found = []
    for c in cities:
        if c.lower() in haystack and c not in found:
            found.append(c)
    return found


# --- knowledge library grounding ---------------------------------------------

def _read_library_refs(library_refs: List[str]) -> str:
    """Read the referenced knowledge-library markdown files (best-effort).

    library_refs are paths like 'destinations/shanghai.md'. They resolve relative to
    the ECH repo's content/knowledge-library/ dir. In HiveAGI we may not have that
    repo checked out, so this is best-effort: missing files degrade to empty string
    (the LLM still has the tour page text to work with).
    """
    # Candidate roots where the knowledge library might live.
    candidates = [
        Path("../explorechinaholidays_repo/explorechinaholidays/content/knowledge-library"),
        Path("../../explorechinaholidays/content/knowledge-library"),
        Path("/Users/explorechina/explorehinaholidays_repo/explorechinaholidays/content/knowledge-library"),
    ]
    root = next((p for p in candidates if p.exists()), None)
    if not root:
        logger.warning("ingest_brief: knowledge-library root not found in candidates; "
                       "enrichment will use tour-page text only")
        return ""

    chunks: List[str] = []
    for ref in library_refs:
        ref_path = root / ref
        if ref_path.exists() and ref_path.suffix == ".md":
            try:
                text = ref_path.read_text(encoding="utf-8")[:_MAX_LIBRARY_CHARS]
                chunks.append(f"### {ref}\n{text}")
            except OSError as e:
                logger.warning("ingest_brief: could not read %s: %s", ref, e)
        else:
            logger.info("ingest_brief: library ref not found: %s", ref)
    return "\n\n".join(chunks)


# --- LLM synthesis (injected; real mode calls MiniMax M3) --------------------

def _default_llm(prompt: str, api_key: Optional[str] = None) -> str:
    """Default LLM: MiniMax M3 chat completion. Returns the raw text response."""
    key = api_key or _resolve_minimax_key()
    payload = {
        "model": "MiniMax-M3",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        "https://api.minimax.io/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError) as e:
        logger.warning("ingest_brief: MiniMax call failed: %s", e)
        return ""


def _resolve_minimax_key() -> str:
    """Resolve MINIMAX_API_KEY from env or .env (mirrors clip_pool/llm_tags.py)."""
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if key:
        return key.strip('"').strip("'")
    for env_path in [Path(".env"), Path(os.getcwd()) / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MINIMAX_API_KEY not found in env or .env")


def _extract_keywords_json(raw: str) -> Dict[str, List[str]]:
    """Parse the LLM's JSON response into {shot_id: [keywords]}.

    Tolerant: strips code fences, finds the first {...} or {...: [...]} block.
    Returns {} on any parse failure (caller falls back to clip_hints prompts).
    """
    if not raw:
        return {}
    # Strip code fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    candidate = fence.group(1) if fence else raw
    # Find the first balanced {...} block
    start = candidate.find("{")
    if start < 0:
        return {}
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
        parsed = json.loads(candidate[start:end])
    except json.JSONDecodeError:
        return {}
    # Normalize: every value must be a list of strings
    out: Dict[str, List[str]] = {}
    for k, v in parsed.items():
        if isinstance(v, list):
            out[str(k)] = [str(x) for x in v][:8]  # cap at 8 keywords/shot
    return out


# --- URL fetch (injected) ----------------------------------------------------

def _default_fetch(url: str) -> str:
    """Default URL fetcher: urllib, returns decoded HTML (best-effort charset)."""
    req = urllib.request.Request(url, headers={"User-Agent": "ECH-VideoFactory/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        logger.warning("ingest_brief: fetch failed for %s: %s", url, e)
        return ""
    # Best-effort decode: utf-8 fallback
    try:
        return raw.decode("utf-8")[:_MAX_HTML_CHARS]
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")[:_MAX_HTML_CHARS]


# --- the public enricher -----------------------------------------------------

def enrich_brief(
    brief: Brief,
    *,
    url_fetch_fn: Optional[Callable[[str], str]] = None,
    llm_fn: Optional[Callable[[str], Optional[str]]] = None,
    llm_api_key: Optional[str] = None,
) -> Brief:
    """Enrich a Brief with generated keywords + a grounded context blob.

    The brief is the canonical input (audit fix #3). This stage adds two things:
      1. generated_keywords per clip_hint shot_id (used by fetch_pool for targeted search)
      2. a grounded_context field (string) carrying tour-page + library text that the
         downstream script writer consults so narration is grounded, not invented.

    Fetch + LLM are injected so tests stay pure. Real mode leaves them None.

    Graceful degradation:
      - URL fetch fails → use library_refs only; if neither, return the brief unchanged.
      - LLM fails → fall back to clip_hint prompts as keywords (same as mock mode).
      - Library refs missing → use tour-page text only.

    Never raises on content failures — only on config (missing MINIMAX_API_KEY when
    llm_fn is None and llm_api_key is None, AND we actually need the LLM).
    """
    fetch = url_fetch_fn or _default_fetch
    llm = llm_fn or (lambda p: _default_llm(p, llm_api_key))

    # 1. Fetch the tour page
    html = fetch(brief.tour_url) if brief.tour_url else ""
    page_title = _extract_title(html) if html else ""
    body_text = _strip_html(html) if html else ""
    itinerary = _extract_itinerary_text(body_text) if body_text else ""
    cities = _extract_cities(page_title or brief.title, body_text)

    # 2. Ground in the knowledge library (the fact substrate)
    library_text = _read_library_refs(brief.library_refs)

    # 3. Resolve the title: page beats brief beats slug
    resolved_title = page_title or brief.title or brief.tour_slug.replace("-", " ").title()

    # 4. Synthesize per-shot keywords via LLM, grounded in the extracted text.
    #    The prompt explicitly tells the model to use the provided content, not invent.
    shot_ids = [f"shot{i+1}" for i in range(len(brief.clip_hints))]
    hint_prompts = [str(h.get("prompt", "")) for h in brief.clip_hints]

    grounded_context = ""
    if itinerary or library_text:
        grounded_context = "\n\n".join(filter(None, [
            f"TOUR: {resolved_title}",
            f"CITIES: {', '.join(cities)}" if cities else "",
            f"ITINERARY EXCERPT:\n{itinerary}" if itinerary else "",
            f"KNOWLEDGE LIBRARY:\n{library_text}" if library_text else "",
        ]))

    # Build the LLM prompt for keyword synthesis. Keep it tight — we want search terms,
    # not prose. The model returns JSON {shot_id: [keyword, ...]}.
    keywords: Dict[str, List[str]] = {}
    if shot_ids and (grounded_context or hint_prompts):
        prompt = _build_keyword_prompt(shot_ids, hint_prompts, grounded_context, cities)
        try:
            raw = llm(prompt)
        except Exception as e:  # noqa: BLE001 — LLM failure must not kill ingest
            logger.warning("ingest_brief: llm raised %s — falling back to hint prompts", e)
            raw = ""
        keywords = _extract_keywords_json(raw or "")
        if keywords:
            logger.info("ingest_brief: synthesized keywords for %d shots", len(keywords))

    # 5. Fallback: hint prompt tokens as keywords for any shot the LLM missed
    for i, sid in enumerate(shot_ids):
        if sid not in keywords or not keywords.get(sid):
            prompt_tokens = re.findall(r"[a-z0-9]+", hint_prompts[i].lower())
            keywords[sid] = [t for t in prompt_tokens if len(t) >= 3][:5]

    # 6. Build the enriched brief. We carry the keywords + context as extra fields so
    #    generate_script can use them without re-fetching. Pydantic models allow extra
    #    fields by default (Brief has no `model_config = Extra.forbid`), so we attach
    #    them via model_copy. If that proves brittle, add explicit fields to Brief.
    enriched = brief.model_copy(update={
        "title": resolved_title,
        # Attach as private/extra attrs the downstream stages read defensively
        **({"generated_keywords": keywords} if keywords else {}),
        **({"grounded_context": grounded_context} if grounded_context else {}),
        **({"cities": cities} if cities else {}),
    })
    return enriched


def _build_keyword_prompt(
    shot_ids: List[str],
    hint_prompts: List[str],
    grounded_context: str,
    cities: List[str],
) -> str:
    """Build the LLM prompt for per-shot Pexels search-keyword synthesis.

    The model is told to produce targeted stock-footage search terms per shot,
    grounded in the real tour content. This is what fetch_pool uses to find clips.
    """
    shots_block = "\n".join(
        f'  "{sid}": hint "{hint}"' for sid, hint in zip(shot_ids, hint_prompts)
    )
    cities_str = ", ".join(cities) if cities else "(see itinerary)"
    return f"""You are generating Pexels stock-footage search keywords for a China travel video.

Use ONLY the provided tour content to ground the keywords. Do not invent destinations
or landmarks not in the content. Each shot needs 3-5 search phrases that would find
good stock footage on Pexels (e.g. "great wall dawn", "shanghai bund night",
"high speed train interior").

TOUR CITIES: {cities_str}

{grounded_context[:6000]}

SHOTS (produce keywords for each):
{shots_block}

Respond as JSON only, mapping each shot_id to a list of 3-5 lowercase search phrases:
{{"shot1": ["phrase one", "phrase two", ...], "shot2": [...]}}
"""
