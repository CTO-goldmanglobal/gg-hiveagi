# Explore China Holiday — Auto-Reel Generator

> **Goldman Forge commercial module.** Turns tourism footage into short-form
> Reels (Instagram / TikTok / YouTube Shorts) automatically. Builds on the
> Labs vision pipeline (`llm_wiki_engine.vision`) — the PII safety gate,
> MiniMax M3 analysis, and dual-LLM audit are inherited for free.

## What it does

```
Raw ECH footage (clips/*.mp4)
    │
    ▼  1. INGEST     ffmpeg probe + sample frames (1 per N seconds)
    │
    ▼  2. ANALYZE    Labs vision.process_frame() per frame
    │                (PII blur runs first — bystanders' faces are blurred
    │                 before MiniMax M3 ever sees them; no --skip-bypass)
    │
    ▼  3. SELECT     MiniMax M3 ranks frames by tourism appeal
    │   + SCRIPT     + writes a coherent English subtitle script
    │
    ▼  4. COMPOSE    ffmpeg: extract video segments around selected frames,
    │                concat with crossfade, burn subtitles, 9:16 vertical crop
    │
    ▼
final_reel.mp4 (≤60s, 1080×1920, English subtitles)
```

## Quick start

```bash
# 1. Install deps (Labs vision + PII anonymizer)
pip install -r llm_wiki_engine/requirements.txt
pip install -r tools/pii_anonymizer/requirements.txt

# 2. Drop your ECH clips into a folder
mkdir -p ~/ech_clips
cp /path/to/beijing_day1.mp4 ~/ech_clips/
cp /path/to/guilin_boat.mp4 ~/ech_clips/

# 3. Generate the Reel
python -m ech_videogen make \
    --clips ~/ech_clips \
    --out ~/ech_reels/beijing_reel.mp4 \
    --location "Beijing" \
    --duration 45 \
    --top-n 8
```

**Requirements:**
- `ffmpeg` installed (`brew install ffmpeg` on macOS)
- MiniMax M3 API key in `.env` (the vision calls need real mode — no mock for this)
- PII anonymizer deps installed (the safety gate needs MediaPipe + OpenCV)

## CLI reference

```
python -m ech_videogen make \
    --clips <dir>           # source clips folder
    --out <path.mp4>        # output Reel path
    [--work-dir <dir>]      # intermediate artifacts (default ./ech_output)
    [--interval 5.0]        # frame sampling interval (seconds)
    [--top-n 8]             # how many frames to select for the Reel
    [--duration 45]         # target Reel duration (seconds)
    [--location "China"]    # location hint for the LLM
    [--crossfade 0.5]       # transition duration between segments
```

## Intermediate artifacts

By default, `./ech_output/` keeps every stage's output so you can inspect
and debug:

```
ech_output/
├── frames/                 # sampled frames per clip
│   └── <clip_stem>/
│       └── frame_000001.jpg ...
├── analysis.json           # per-frame MiniMax M3 analysis
├── script.json             # the LLM-written narration script
├── subtitles.srt           # the subtitle file
├── segments/               # extracted video segments per script line
├── draft_no_subs.mp4       # concat before subtitles
└── ...                     # final .mp4 goes to --out
```

This is gitignored — it's runtime output, not source.

## How frame selection works (the actual hard part)

A 45s Reel from 5 minutes of footage = pick ~8 frames. The pipeline:

1. Sample 1 frame per 5s → ~60 candidate frames
2. Run `vision.process_frame()` on each → descriptions
3. **One** LLM call ranks all candidates by tourism appeal + visual variety + narrative coherence
4. Take top N (default 8)
5. **One** LLM call writes the script: durations + subtitle text per frame

This is 2 LLM calls per video (rank + script), not N. Keeps cost predictable.

## MVP scope (what's shipped now)

- ✅ 4-stage pipeline working end-to-end
- ✅ 9:16 vertical crop (center-crop)
- ✅ English subtitles, bottom-third, mobile-readable
- ✅ Crossfade transitions between segments
- ✅ PII safety gate inherited from Labs (faces + plates blurred before LLM)
- ✅ Per-stage intermediate artifacts for debugging

## Out of scope (future versions)

- ❌ TTS voice-over (MVP is subtitles only)
- ❌ Multi-language subtitles (English only for now)
- ❌ Music / background audio track
- ❌ Subject-aware 9:16 crop (center-crop for v1 — TODO: face/salient-region-aware crop)
- ❌ Tour-guide face allowlist (currently the PII gate blurs ALL faces, including your guide's — interesting v2 feature for `tools/pii_anonymizer/`)
- ❌ Brand watermark / lower-third logo
- ❌ Direct upload to TikTok/IG (produces .mp4; you upload manually)

## Architecture note: the Labs↔Forge seam

This module (`explore_china_holiday/ech_videogen/`) is a **Goldman Forge
commercial module**. It imports the Labs research pipeline
(`llm_wiki_engine.vision`) but does not duplicate it. Specifically:

- `ech_videogen.analyze` calls `llm_wiki_engine.vision.process_frame()`
- The PII safety gate, MiniMax call, JSON extraction — all stay inside Labs
- ECH never imports MiniMax / DeepSeek / MediaPipe / OpenCV directly

This keeps the research/commercial boundary clean. When the Labs vision
pipeline improves, ECH benefits automatically. When ECH is eventually
open-sourced or productised separately, the dependency is explicit.

## Files

```
explore_china_holiday/
├── README.md
├── requirements.txt           # refers to Labs deps
├── test_samples/              # drop your clips here
└── ech_videogen/
    ├── __init__.py
    ├── __main__.py            # python -m ech_videogen entry
    ├── cli.py                 # `make` command
    ├── ingest.py              # Stage 1: ffmpeg probe + frame sampling
    ├── analyze.py             # Stage 2: Labs vision seam
    ├── select.py              # Stage 3: LLM rank + script
    ├── compose.py             # Stage 4: ffmpeg concat + subtitles + 9:16
    ├── srt.py                 # SRT subtitle generation
    └── prompts/
        ├── frame_ranker.txt
        └── script_writer.txt
```

## License

This is a Goldman Forge commercial module. Licensing terms to be confirmed
(not automatically AGPL like the Labs code — see commercial license docs).
