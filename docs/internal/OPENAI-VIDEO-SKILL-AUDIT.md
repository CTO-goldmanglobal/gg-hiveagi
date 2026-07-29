# OpenAI Video Skill Audit — Research Findings

> OpenAI's review of the GitHub landscape for AI-agent video editing skills
> that could strengthen the HiveAGI pipeline. Captured 2026-07-29.

---

## Summary: what to steal, what to install, what to ignore

| Repo | Stars | License | Action |
|:---|:---|:---|:---|
| **[browser-use/video-use](https://github.com/browser-use/video-use)** | 8.5k | MIT | 🎯 **Steal architecture** — EDL pattern, compact transcript → visual timeline |
| **[AKMessi/vex](https://github.com/AKMessi/vex)** | — | PolyForm NC | 📖 **Study only** — Director pattern, but commercial license required |
| **[6missedcalls/video-editing-skill](https://github.com/6missedcalls/video-editing-skill)** | — | MIT | ✅ **Model for our skills** — simple bash+ffmpeg+whisper primitives |
| **[PySceneDetect](https://github.com/Breakthrough/PySceneDetect)** | 5k | BSD-3 | 📦 **Install** — cheap scene detection before M3 vision calls |
| **[Auto-Editor](https://github.com/WyattBlue/auto-editor)** | 4.3k | GPL | 📋 **Later** — silence/dead-region detection for glasses capture |
| **[remotion-dev/skills](https://github.com/remotion-dev/skills)** | 3.3k | MIT | 📋 **Later** — brand/text/graphic composition layer |
| **[HKUDS/VideoAgent](https://github.com/HKUDS/VideoAgent)** | 748 | MIT | 📖 **Labs study** — video understanding representation |
| ShortGPT | — | — | ❌ **Ignore** — we're already structurally more advanced |

---

## The key insight: EDL (Edit Decision List)

From **video-use**: the LLM should NOT directly edit video. It should produce
an **EDL (Edit Decision List)** — a JSON description of what goes where —
then a deterministic renderer executes it.

```json
{
  "source": "great_wall_07.mp4",
  "start": 4.7,
  "end": 8.1,
  "purpose": "opening reveal",
  "reason": "wide establishing shot with clear subject"
}
```

**Why this matters for HiveAGI:** the override signal becomes much richer:

```
AI proposed EDL:    shot_41 @ 12.5–16.2
Human final EDL:   shot_73 @ 12.5–15.6
WHY:               "41 looks dramatic, but 73 feels more authentic
                    and shows older travellers."
```

That delta — AI's edit decision vs human's edit decision + reason — is the
most valuable preference data the system can capture.

---

## PySceneDetect — the cheap intelligence multiplier

Instead of feeding whole clips to M3 vision:

```
CURRENT (expensive):
38-second clip → M3 sees many frames → 270 vision calls for 136 clips

WITH PySceneDetect (cheap):
38-second clip
     ↓
PySceneDetect (free, local)
     ↓
shot 1: 0–4.8s    → sample 1 frame → M3
shot 2: 4.8–11.1s → sample 1 frame → M3
shot 3: 11.1–17.4s→ sample 1 frame → M3
     ↓
M3 only sees the RIGHT frames, not every frame
     ↓
~70 vision calls instead of ~270 (75% reduction)
```

---

## The recommended HiveAGI skill architecture

From OpenAI's synthesis:

```
                 TOUR URL
                    │
                    ▼
              STORY DIRECTOR
                    │
                    ▼
        ┌──── SHOT INTELLIGENCE ────┐
        │                            │
 PySceneDetect                cheap CV metrics
 (scene boundaries)           (brightness/motion/shake)
        │                            │
        └───────────┬────────────────┘
                    ▼
               M3 VISUAL JUDGE
                    │
                    ▼
              SHOT SCORE GRAPH
                    │
            ┌───────┴─────────┐
            ▼                 ▼
        accepted           uncertain
                              │
                              ▼
                         human judge
                              │
                    preference signal
            └───────────┬───────────┘
                        ▼
                   EDIT DIRECTOR
                        │
                        ▼
                     EDL.json
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
           FFmpeg               Remotion
        footage/audio          graphics/UI
             └──────────┬──────────┘
                        ▼
                      render
                        │
                        ▼
                    QA AGENT
                  ↙           ↘
               PASS           FAIL
                 │              │
                 ▼              └── repair
             FINAL.mp4
```

### Reusable skill primitives (from 6missedcalls pattern)

```
.agents/skills/
├── video-inventory/     ← probe, list, hash all source clips
├── scene-detect/        ← PySceneDetect wrapper
├── visual-rank/         ← M3 content tagger (exists: llm_tags.py)
├── beauty-rank/         ← metrics + flags (exists: metrics.py)
├── clip-select/         ← human judge (exists: judge.py)
├── crop-portrait/       ← adapt (exists: adapt.py)
├── compose-timeline/    ← EDL generator (NEW — the Edit Director)
├── music-fit/           ← music selection + mix
├── voiceover/           ← TTS (exists: tts_vo.py)
├── subtitle/            ← SRT + burn (exists: burn_subtitles.py)
├── branding/            ← logo + end card (exists: composite.py)
├── render/              ← EDL → ffmpeg execution
└── video-qa/            ← M3 frame audit (exists: manual today)
```

Each skill: SKILL.md + script + input schema + output schema + tests.

GLM-5.2 acts as **director**, not video engineer. It calls skills; skills
execute deterministically.

---

## What exists vs. what to build

| Skill | Exists? | Where |
|:---|:---|:---|
| scene-detect | ❌ | Install PySceneDetect |
| visual-rank | ✅ | `clip_pool/llm_tags.py` |
| beauty-rank | ✅ | `clip_pool/metrics.py` |
| clip-select | ✅ | `clip_pool/judge.py` |
| crop-portrait | ✅ | `clip_pool/adapt.py` |
| compose-timeline (EDL) | ❌ | **The key missing piece** |
| voiceover | ✅ | `tour-video-finish/scripts/tts_vo.py` |
| subtitle | ✅ | `tour-video-finish/scripts/burn_subtitles.py` |
| branding | ✅ | `tour-video-finish/scripts/composite.py` |
| render | ✅ (partial) | `cut.py` + `composite.py` |
| video-qa | ✅ (manual) | M3 audit loop (needs automation) |

**7 of 12 skills exist.** The key gap: the **EDL layer** (compose-timeline)
that sits between judgment and rendering. That's what makes the override
signal structured.

---

## Immediate actions

1. **Install PySceneDetect** — `pip install scenedetect[opencv]` — cheap scene detection, reduces M3 vision calls ~75%
2. **Design the EDL format** — the JSON schema for edit decisions (source, start, end, purpose, reason)
3. **Study video-use's EDL + QA pattern** — how it generates edl.json before rendering, then self-checks
4. **Build compose-timeline skill** — the Edit Director that produces EDL from ranked shots
5. **Keep FFmpeg for footage, consider Remotion for graphics** — logo, map, day cards, price cards render better in a graphics layer than ffmpeg drawtext

Document the EDL override signal as the richest preference data the system can capture.
