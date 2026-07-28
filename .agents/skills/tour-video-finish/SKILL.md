---
name: tour-video-finish
description: Finish a tour promo video — add voiceover, music, subtitles, and brand end card to a silent draft reel. Use when the videogen cognition pipeline (fetch → pretag → metrics → adapt → judge → cut) has produced a draft video and the user wants to turn it into a shippable deliverable. Handles TTS voiceover generation, music mixing with ducking, subtitle burn-in, and branded end-card rendering. Triggered by phrases like "finish the video", "add music and voiceover", "add subtitles", "render the end card", "make the final cut", or when a draft reel exists and needs finishing layers.
---

# Tour Video Finish

> Turns a silent draft reel into a shippable tour promo video.
> Pure production craft — never touches Labs/seed data.

## What this skill does

The videogen cognition pipeline produces a **silent draft** (footage selected, cut, crossfaded — no audio, no text, no branding). This skill adds the four finishing layers:

```
Draft (silent) ──▶ ① Voiceover  ──▶ ② Music  ──▶ ③ Subtitles  ──▶ ④ End Card  ──▶ FINAL
```

Each layer is independently re-runnable. Change the music without re-rendering subtitles. Re-generate VO without touching footage.

## Architecture — the Forge seam

```
COGNITION (Labs)                    CRAFT (this skill)
videogen/                           tour-video-finish/
fetch → pretag → judge → cut        VO + music + subs + branding
                                    │
THE SEED: human judgment ◀──────────┤ never feeds back
Provenance-gated for Labs           │
                                    THE DELIVERABLE: shippable video
```

This skill does NOT read or write judgment logs, selection logs, or anything Labs-bound. It reads a draft `.mp4` + a script and produces a finished `.mp4`. The seam is one-directional: cognition → craft.

## How to use

### Prerequisites
- A draft video (from `videogen` cut step or manual assembly)
- A script with VO text + timing (JSON: `[{shot, duration, vo}, ...]`)
- A music track (MP3/WAV) — or let the skill suggest keywords
- A logo PNG for the end card

### Full finish (all 4 layers)

```bash
FINISH_SKILL_DIR="$(dirname "$(readlink -f "$0")")"  # or set manually
python3 "$FINISH_SKILL_DIR/scripts/finish.py" \
  --draft explore_china_holiday/tours/legends-of-china-warriors/output/legends-landscape.mp4 \
  --script explore_china_holiday/tours/legends-of-china-warriors/pool/selection_draft.json \
  --music /path/to/music.mp3 \
  --logo "/Users/explorechina/My Drive (finn@goldmanglobal.com.au)/ExploreChina.png" \
  --out explore_china_holiday/tours/legends-of-china-warriors/output/legends-landscape-FINAL.mp4
```

### Individual steps

```bash
# 1. Generate voiceover via MiniMax TTS
python3 "$FINISH_SKILL_DIR/scripts/tts_vo.py" \
  --script <selection_draft.json> --out vo.mp3

# 2. Mix music under VO with ducking
python3 "$FINISH_SKILL_DIR/scripts/mix_audio.py" \
  --vo vo.mp3 --music music.mp3 --out audio-mixed.mp3 \
  --vo-level -16 --music-level -25

# 3. Burn subtitles
python3 "$FINISH_SKILL_DIR/scripts/burn_subtitles.py" \
  --video draft.mp4 --script selection_draft.json --out video-subbed.mp4

# 4. Render end card (logo + price + URL)
python3 "$FINISH_SKILL_DIR/scripts/render_endcard.py" \
  --video video-subbed.mp4 --logo ExploreChina.png \
  --brand "ExploreChina Holidays" --price "From A$1,499" \
  --url "explorechinaholidays.com.au" --out FINAL.mp4
```

## Reference documents

Read these when making craft decisions:

| File | When to read |
|:---|:---|
| `references/ech-brand-guide.md` | End card design, colour, typography decisions |
| `references/music-direction.md` | Music sourcing, mix levels, guzheng/erhu brief |
| `references/vo-direction.md` | VO casting, recording spec, delivery notes per beat |

## Brand tokens (from corporate guide)

```
China Red      #C8202F    (CTA, price, accents — 3-5% of frame only)
Charcoal       #171717    (headings, body text)
Warm White     #FAF8F4    (backgrounds)
Heritage Gold  #B68A45    (premium indicators, sparingly)
Font Primary   Inter      (body, UI)
Font Editorial DM Serif Display (large headings only)
```

## File map

```
tour-video-finish/
  SKILL.md                          ← you are here
  scripts/
    finish.py                       ← orchestrator: runs all 4 steps
    tts_vo.py                       ← MiniMax TTS voiceover generation
    mix_audio.py                    ← music + VO mix with ducking
    burn_subtitles.py               ← SRT generation + ffmpeg burn-in
    render_endcard.py               ← logo + price + URL overlay on last shot
  references/
    ech-brand-guide.md              ← corporate design spec
    music-direction.md              ← music brief + levels
    vo-direction.md                 ← VO casting + recording spec
```

## Loading protocol

1. Read this SKILL.md (always)
2. Read the specific reference when a craft decision is needed (on demand)
3. Run scripts via `python3 "$FINISH_SKILL_DIR/scripts/..."` (never bare paths)
4. Never load all references at once — read what the step needs
