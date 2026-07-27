"""
ech_videogen — Explore China Holiday auto-video generator (Goldman Forge module).

Imports the Labs vision pipeline (llm_wiki_engine.vision) and adds:
  - frame selection + ranking (LLM)
  - script writing (LLM)
  - ffmpeg composition with subtitles + 9:16 crop
"""

from .ingest import ingest_clips, probe_clip
from .analyze import analyze_frames
from .select import select_and_script
from .compose import compose_reel
from .srt import script_to_srt

__version__ = "0.1.0"

__all__ = [
    "ingest_clips",
    "probe_clip",
    "analyze_frames",
    "select_and_script",
    "compose_reel",
    "script_to_srt",
]
