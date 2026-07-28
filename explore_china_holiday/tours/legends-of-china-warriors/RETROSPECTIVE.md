# Retrospective: Legends of China Warriors — Circle #1 Video Production

> **Date:** 2026-07-28, ~12:30 → ~00:00 (~11.5 hours)
> **What:** First complete end-to-end video production loop — from stock fetch to
> M3-audited final deliverable.
> **Result:** 80-second landscape promo video with VO, music, subtitles, logo
> watermark, semi-transparent end card, and ECH branding outro.

---

## The timeline — what actually happened

### Phase 1: Planning & Briefing (12:30–13:00)
- Fetched the tour page itinerary (12 days, Beijing→Xi'an→Suzhou→Hangzhou→Shanghai)
- Analyzed the reference YouTube video (55s "Amazing China from Australia")
- Wrote PRODUCTION-BRIEF, SCRIPT-vertical, SCRIPT-landscape, FOOTAGE-SHOT-LIST,
  MUSIC-AND-VO-DIRECTION, YOUTUBE-DESCRIPTION
- **Output:** 6 planning docs, no code yet

### Phase 2: Pool + Enrichment (12:30–15:00)
- Built `videogen/clip_pool/` — fetch, pretag, metrics, adapt, judge
- Fetched 136 candidate clips from Pexels (8 shots × landscape + portrait)
- LLM pre-tagged 132/136 clips with content dimensions (shot_type, perspective,
  mood, commercial_grade)
- Measured brightness/motion/shake on 132/136 clips
- Adapted 8 landscape→portrait crops with LLM-guided positioning + provenance
- Built provenance gate (`videogen/provenance.py`) — stock blocked from Labs
- **Output:** 10 Python modules, enriched pool, browser gallery

### Phase 3: Human Judgment (15:00–17:00)
- Founder reviewed clips via screenshots, gave detailed verdicts
- 7 founding judgments recorded (accept/reject + reason) — the seed
- Founder articulated 4 editorial rules: minus method, video needs moving
  content, reject personal-video feel, contrast/brightness continuity
- Metrics validated the rules (motion score correlated with "static" rejections)
- Founder flagged POV clips as "different category" not "reject"
- **Output:** judgment_log.jsonl, selection_draft.json (8 shots locked)

### Phase 4: Assembly (17:00–19:00)
- Built `cut.py` — assembles both landscape + portrait from locked picks
- First assembly was 13.5s (broken xfade offset math) → fixed → 51.5s
- Shot 7 was portrait-only → fixed by using landscape clip
- **Output:** legends-landscape.mp4 (51.5s silent draft)

### Phase 5: Finishing Skill (19:00–22:00)
- Built `tour-video-finish` skill (SKILL.md + 6 scripts + 3 reference docs)
- TTS voiceover via MiniMax speech-2.8-hd (8 segments)
- Audio mix (VO + music with ducking)
- Subtitle burn-in (Pillow-based — ffmpeg lacked libass)
- End card rendering (logo + price + URL overlay)
- Logo watermark (on/off at top center)
- **Multiple iterations of audio:** VO too quiet → mix fixed → music too sad →
  swapped track → VO still buried → rebuilt mix → "louder VO + stronger music"

### Phase 6: Debugging & M3 Audit (22:00–00:00)
- Captions missing → discovered add_overlays.py was overwriting frames (losing
  subtitles) → built composite.py (single-pass renderer)
- SRT parser bug: `\n\s*\n` split broke on multi-line subtitle text → only read
  1 of 8 cues → fixed by splitting on index numbers
- Outro wrong: branding .mov was a screen recording, not an animation → M3
  identified the clean ECH brand card in first 12s → re-cut
- **M3 QA audit:** sent every frame to MiniMax M3 vision for error detection
  → caught the SRT bug, the wrong outro, the missing captions → fixed all →
  re-audited → all clear
- **Output:** legends-landscape-FINAL.mp4 (80s, M3-audited)

---

## What worked well

1. **The three-layer enrichment (metrics + LLM tags + human judgment)**
   Before the founder even opened a clip, the system had already measured its
   brightness/motion/shake, tagged its content dimensions (drone/epic/morning),
   and flagged likely problems (static, amateur, brightness outlier). This
   saved enormous viewing time.

2. **LLM pre-tagging aligned with the founder's editorial eye**
   The founder called `pexels_35614363` "like AI glasses, not commercial."
   The LLM independently tagged it `first_person_pov / personal`. Same judgment,
   machine-readable. This validated the pre-tagging approach.

3. **The provenance gate as a first-class concern**
   Building `source_type` into every candidate from creation, and the gate
   (`is_labs_eligible`) before any Labs export, kept the human-perspective
   thesis honest. Stock never reaches Labs; human judgment does.

4. **Landscape→portrait adaptation**
   4K landscape clips cropped to portrait with LLM-guided subject positioning.
   No need to re-fetch weak portrait pools. The `derived_from` provenance chain
   traces every crop back to its source.

5. **M3 as QA auditor**
   The "ask MiniMax to check the video" moment was the highest-value action of
   the session. M3 caught bugs I (the builder) was blind to — the SRT parser
   only reading 1 cue, the wrong outro slice. Machine-checking machine output
   is a mandatory step, not optional.

---

## What went wrong (and the lesson)

### Problem 1: VO/footage desync (16-second drift)
**What:** TTS generated 67.6s of speech for a 51.5s video. The voice was 16
seconds ahead/behind the footage — "more than 3 seconds" of drift per shot.
**Root cause:** Shot durations were planned (6s, 8s, 10s...) but TTS at speed=0.9
produced longer speech. The plan and the reality didn't match.
**Fix:** Re-cut each shot to match its actual VO duration.
**Lesson:** **Voice drives the cut, not the other way around.** Generate VO
first, then cut footage to match. The pipeline order should be: script → TTS →
cut to VO durations → composite.

### Problem 2: Multi-pass overlay rendering losing layers
**What:** Subtitles were burned in step 3, then step 4 (logo + end card) ran a
Pillow frame rewrite that overwrote the frames — losing the subtitles.
**Root cause:** Each overlay step was a separate pass that read frames, drew,
and wrote back. Later passes didn't preserve earlier passes' work.
**Fix:** Built `composite.py` — single-pass renderer that draws subtitles +
logo + end card on each frame in one operation.
**Lesson:** **All overlays must render in one pass.** Never chain frame-level
overlay operations. Either composite in one filter graph (ffmpeg) or one Pillow
loop.

### Problem 3: SRT parser only reading 1 of 8 cues
**What:** Subtitles only appeared on shot 1. Shots 2-8 had no text.
**Root cause:** `re.split(r'\n\s*\n', content)` split on blank lines, but
multi-line subtitle text (e.g., "It begins in Beijing —\nTiananmen Square...")
contained internal `\n` that the regex treated as block boundaries.
**Fix:** Split on the SRT index number pattern (`\n(?=\d+\s*\n\d{2}:...)`)
instead of blank lines.
**Lesson:** **Test parsers on real multi-line data.** The unit test passed
because it used single-line text. Real subtitles have line breaks.

### Problem 4: Wrong outro content
**What:** The branding .mov's last 6 seconds (111-117s) was a desktop screen
recording, not a brand animation. The actual brand card was in the first 12s.
**Root cause:** I assumed the "ending" of the video was the outro. It wasn't —
the .mov was a 117s screen capture with the brand card at the start.
**Fix:** M3 identified the clean brand content at 0-12s. Re-cut from the start.
**Lesson:** **Never assume media content. Always inspect (M3 audit) before
integrating external assets.** The first 15 seconds looked clean to M3; the
last 6 didn't.

### Problem 5: Audio mix required 4 iterations
**What:** "VO can't hear" → "music too sad" → "VO still buried" → "louder VO +
stronger music."
**Root cause:** The sidechain compression + amix chain was too complex and
produced unpredictable results. Each fix addressed one symptom.
**Fix:** Simplified to volume pre-scaling + loudnorm + simple amix with explicit
weights. Final: VO at volume=1.65 (-12 LUFS), music at volume=0.48 (-22 LUFS),
amix weights 1:0.6.
**Lesson:** **Simple audio chains beat clever ones.** Volume + loudnorm + amix
is predictable. Sidechaincompress is not, for short-form content. And: the
founder's feedback IS the calibration data — each "louder/stronger" correction
is a preference pair that should be logged and learned from.

### Problem 6: No automated QA gate before delivery
**What:** Videos were sent to the founder with broken subtitles, wrong outro,
desynced audio — discovered by human viewing, not by the system.
**Root cause:** No verification step in the pipeline. "Did it render?" was
checked, but "did it render CORRECTLY?" was not.
**Fix:** M3 QA audit — send N sample frames to vision LLM, check for subtitle
visibility, logo presence, rendering errors. All-clear gate before delivery.
**Lesson:** **Machine-check machine output. Every time.** The M3 audit caught
3 bugs I was blind to as the builder. This is now a mandatory pipeline step.

---

## What we'd do differently next circle

### Pipeline order (corrected)
```
WRONG (today):                        RIGHT (next time):
script → cut to planned durations      script → TTS voiceover
       → finish (VO, music, subs)            → cut footage to VO durations
                                             → composite (subs + logo + card)
                                             → mix audio (VO + music)
                                             → M3 QA audit
                                             → deliver
```

### Mandatory QA gate
Before ANY video is delivered:
1. Extract 1 frame per shot at VO midpoint
2. Send each to M3 vision: "is subtitle visible? logo? errors?"
3. Check audio levels (volumedetect)
4. All-clear → deliver. Any ❌ → fix → re-audit.

### Audio mixing as learned calibration
Log every "louder/stronger/quieter" correction as a preference pair:
```json
{"element": "vo", "correction": "+10%", "reason": "too quiet", "from": 1.5, "to": 1.65}
```
After N circles, the system learns the founder's preferred mix without iteration.

### Logo position as learned calibration
Same pattern: "too close to edge" → log → next circle starts from safe zone.

### One composite pass, always
Never chain frame-level operations. `composite.py` is the only overlay renderer.

### External assets: inspect before integrate
Any .mov/.mp3/.png from outside the pipeline gets M3-audited before use.
