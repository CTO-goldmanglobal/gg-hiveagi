"""
videogen — generic auto-video pipeline core (Goldman Forge).

4-stage pipeline: ingest → analyze → select+script → compose.
Config-driven: each commercial client (ECH, future real-estate, etc.)
supplies a VideoGenConfig pointing at its own prompts + settings.

Imports the Labs vision pipeline (llm_wiki_engine.vision) and adds:
  - frame selection + ranking (LLM)
  - script writing (LLM)
  - ffmpeg composition with subtitles + aspect-ratio crop
  - selection-rationale logging (the human-override signal)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .ingest import ingest_clips, probe_clip
from .analyze import analyze_frames
from .select import select_and_script
from .compose import compose_reel
from .srt import script_to_srt

__version__ = "0.2.0"


@dataclass
class VideoGenConfig:
    """Per-client configuration for the videogen pipeline."""
    name: str
    frame_ranker_prompt: str  # path to ranker prompt .txt
    script_writer_prompt: str  # path to script-writer prompt .txt
    target_aspect: str = "9:16"  # "9:16" or "16:9"
    target_duration_sec: int = 45
    language: str = "en"
    domain: str = "tourism"
    location_default: str = "China"
    subtitle_placement: str = "bottom_third"
    crossfade_sec: float = 0.5


def load_config(name: str) -> VideoGenConfig:
    """
    Load a named config from the registry.
    Built-in: 'ech'. Future configs drop in as files in configs/.
    """
    name = name.lower().strip()
    if name == "ech":
        # Lazy import to avoid circular dep at module load
        import os
        import sys
        _repo_root = Path(os.environ.get(
            "VIDEOGEN_REPO_ROOT",
            Path(__file__).resolve().parents[1],
        ))
        ech_dir = _repo_root / "explore_china_holiday"
        return VideoGenConfig(
            name="ech",
            frame_ranker_prompt=str(ech_dir / "prompts" / "ech_frame_ranker.txt"),
            script_writer_prompt=str(ech_dir / "prompts" / "ech_script_writer.txt"),
            target_aspect="9:16",
            target_duration_sec=45,
            language="en",
            domain="tourism",
            location_default="China",
            subtitle_placement="bottom_third",
            crossfade_sec=0.5,
        )
    raise ValueError(
        f"Unknown config '{name}'. Available: ech. "
        f"To add configs, see VideoGenConfig in videogen/__init__.py."
    )


__all__ = [
    "ingest_clips",
    "probe_clip",
    "analyze_frames",
    "select_and_script",
    "compose_reel",
    "script_to_srt",
    "VideoGenConfig",
    "load_config",
]
