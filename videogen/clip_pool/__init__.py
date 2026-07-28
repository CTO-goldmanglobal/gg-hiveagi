"""
videogen.clip_pool — the candidate pool + human-judgment loop.

Stages 1–2 of the "small circle" (see docs/LOOP-STRATEGY.md):
  fetch  — pull N candidates per keyword into a viewable pool
  judge  — human accept/reject + reason → judgment_log.jsonl

The pool is source-tagged from creation (stock:pexels, human_capture:phone,
...). The provenance gate (videogen.provenance) uses that tag to keep raw
stock material out of Labs Seed packages — while the human JUDGMENT layer
remains Labs-eligible as hybrid seed.
"""

from .fetch import fetch_pool, load_keyword_config
from .manifest import write_manifest, write_pool_index_html
from ..provenance import is_labs_eligible  # shared gate, lives at videogen/provenance.py

__all__ = [
    "fetch_pool",
    "load_keyword_config",
    "write_manifest",
    "write_pool_index_html",
    "is_labs_eligible",
]
