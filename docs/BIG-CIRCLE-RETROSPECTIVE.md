# Big Circle Retrospective — HiveAGI Loop Development

> Where today's video work fits in the full HiveAGI project arc.
> For Fable + ChatGPT audit and outside-the-box ideation.

---

## The project arc — every loop completed

HiveAGI has been built as a series of "small circles" (per LOOP-STRATEGY.md).
Each is a complete, reviewable unit. Here's every one:

### Circle A: Foundation (P0-P2)
**What:** Seed Package system + LLM Wiki Engine + P2P exchange
**Built:**
- Seed Package generator + validator (`tools/seed_generator/`)
- Obsidian vault setup (`tools/vault_setup/`)
- Dual-LLM engine: MiniMax M3 generator + DeepSeek V4 Flash auditor (`llm_wiki_engine/`)
- Vision pipeline with PII blur gate (`llm_wiki_engine/vision.py`)
- IPFS/kubo P2P exchange: publish, verify, tamper-detect, resolve (`p2p_exchange/`)
- Obsidian plugin scaffold (`obsidian_plugin/`)
**Deliverable:** Working knowledge network — raw data → Markdown → Seed Packages → IPFS exchange
**Status:** ✅ Complete, CI-tested

### Circle B: Safety + Governance
**What:** PII enforcement + CLA + contributing framework
**Built:**
- Face blur (MediaPipe Tasks, short-range model) + plate blur (edge-based) — code-enforced, no bypass
- CI safety gate test (pixel-level assertion + dep-absence test)
- CLA with explicit license grant (dual-license compatible)
- CONTRIBUTING.md rewrite (PII rules, fork workflow, Seed Package submission)
**Deliverable:** Safe contribution framework — contributors can't leak PII, rights are clean
**Status:** ✅ Complete, CI-tested

### Circle C: Brand + Positioning
**What:** Goldman Global's two-face identity (Forge + Labs)
**Built:**
- Research Labs positioning brief (Forge=commercial, Labs=R&D)
- Website handoff docs (research page, about page, showcase)
- Brand design tokens (#C8202F, Inter, DM Serif Display)
**Deliverable:** Coherent brand story — same company, two faces, one vision
**Status:** ✅ Complete

### Circle D: Video Pipeline Core (ECH Auto-Cut)
**What:** Tourism footage → short-form Reels
**Built:**
- 4-stage pipeline: ingest → analyze → select+script → compose
- ECH-specific prompts (frame ranker, script writer)
- ffmpeg assembly with crossfade + 9:16 crop + SRT subtitles
- Refactored to config-driven core (`videogen/`) + client layer
**Deliverable:** Automated Reel generation from footage
**Status:** ✅ Complete

### Circle E: Selection Intelligence (the beauty standard)
**What:** Human-override signal capture — the real valuable data
**Built:**
- Selection rationale logging (NOT "beauty data" — editor selection rationale)
- `finalize` command: diffs model vs human selection → override signal
- Schema documenting shot_type (content) vs trigger_type (salience)
**Deliverable:** Every video edit produces preference data (the seed)
**Status:** ✅ Complete

### Circle F: TODAY — Legends of China Warriors (full loop)
**What:** First complete end-to-end video from stock to M3-audited deliverable
**Built:**
- Clip pool system: fetch (Pexels) → pretag (LLM M3) → metrics (opencv) → adapt (crop) → judge (human)
- Provenance gate: stock blocked from Labs, human judgments eligible (hybrid seed)
- Landscape→portrait adaptation with LLM-guided crop positioning + provenance chain
- Tour-video-finish skill: TTS VO + music mix + subtitle burn (Pillow) + end card + logo watermark
- Single-pass composite renderer (subtitles + logo + end card on one frame)
- M3 QA audit loop (machine-checking machine output)
- External media storage (Goldman Global drive, 1.9TB)
- Obsidian vault (both platforms — Forge + Labs knowledge bridge)
**Deliverable:** 80-second landscape promo video, M3-audited, with judgment seed
**Status:** ✅ Draft v1 complete

### Circle G: Automation (NEXT — for Cursor/GLM-5.2)
**What:** One-command pipeline: tour URL → finished video
**To build:**
- `produce.py` orchestrator
- `ingest.py` (URL → itinerary)
- `timeline.py` (VO → master clock)
- `qa_gate.py` (M3 audit, automated)
- `wiki_export.py` (circle artifacts → Obsidian)
**Goal:** `python -m videogen produce --tour-url URL → FINAL.mp4`
**Status:** ⬜ Next

---

## How the circles connect

```
Circle A (foundation) ──── Circle B (safety) ──── Circle C (brand)
       │                                              │
       └──── Circle D (video core) ──────────────────┘
                    │
              Circle E (selection intelligence)
                    │
              Circle F (today: full loop) ──── provenance gate
                    │                              │
              Circle G (automation)          Obsidian wiki
                                              (both platforms)
```

Each circle overlaps the last (reuses infrastructure) and adds new territory
(new capability). Together they cover: capture → cognition → safety → brand →
video → intelligence → automation → knowledge network.

---

## The vision check — are we on track?

**The thesis:** Let computers learn how to understand humans, rather than
humans learning how to adapt to computers.

**Today's contribution to the thesis:**
- The "beauty standard" data (human judgments on video clips) IS human
  perspective — it's what a human finds beautiful and why
- The provenance gate keeps it honest (stock pixels blocked, human judgments
  eligible)
- The Obsidian wiki accumulates it cross-domain
- Over many circles, the network learns "what humans find worth recording"

**What's still missing for the thesis:**
- Glasses/phone capture (the human_capture source_type) — currently all stock
- Cross-editor aggregation (multiple humans' judgments compared)
- The Seed Package network actually running (IPFS daemon, real exchange)
- The Obsidian plugin connecting real vaults across contributors

**The honest assessment:** Circle F proved the LOOP works end-to-end. The
loop shape (fetch → judge → cut → finish → audit → seed) is correct and
reusable. But the "human perspective" is currently editorial taste on
professional footage, not first-person capture. The inflection point (Circle M
in LOOP-DIAGRAMS.md) is when capture shifts from stock to glasses. That's when
the thesis actually starts proving itself.

---

## For Fable + ChatGPT audit

### What to ask them

1. **Is the "small circles" strategy sound?** We finish one complete loop,
   review it, run the next. Is this the right cadence, or should we parallelize?

2. **Is the provenance gate the right boundary?** Stock blocked from Labs,
   human judgments eligible. Is there a case where this is too strict or too
   loose?

3. **Is "editorial taste on stock footage" real human-perspective data?**
   Or are we fooling ourselves that beauty-standard judgments = human
   perspective? Does it only count when the human captured the footage
   themselves?

4. **The hybrid seed claim:** We say human judgments about stock ARE
   Labs-eligible because human taste IS human perspective. Is this defensible?
   Or is it a loophole that corrupts the thesis?

5. **The AGI path:** From "editor picks beautiful stock clips" to "distributed
   human-perspective AGI" — is there a credible bridge? What's the missing
   link?

### Outside-the-box ideas to explore

1. **Reverse the loop:** Instead of "stock → human judges → seed," what if
   the system PRESENTS two clips and asks the human "which is more beautiful?"
   — a pairwise preference that's faster to capture and more comparable?

2. **The wiki as training data:** The Obsidian vault, once populated across
   many circles, could be fine-tuning data for a model that learns the
   beauty standard. The vault → model → better pre-tagging → faster human
   judgment → more vault entries. A flywheel.

3. **Crowdsourced beauty:** Open the judgment interface to contributors
   (via the Obsidian plugin). Different cultures, ages, backgrounds judge
   the same clips. The seed becomes multi-perspective, not single-editor.

4. **The negative space:** We capture what humans ACCEPT. What about what
   they REJECT and WHY? The rejection reasons ("too shaky," "looks like a
   photograph," "personal video feel") might be MORE valuable than the
   accepts — they define the boundary of "good."

5. **Video as a first-class wiki type:** Currently the wiki is text
   (Markdown). What if each entry had an embedded video clip + the human's
   judgment of it? The wiki becomes a multimedia knowledge graph, not just
   text notes.

6. **The beauty standard as a filter, not a product:** Instead of making
   videos, sell the beauty-standard model. "This AI knows what an Australian
   tourist finds beautiful in China." Other travel companies license it. The
   Forge output funds the Labs research.

7. **Glasses capture → real-time judgment:** When the glasses capture is
   live, the system could ask in real-time: "you looked at this 3 seconds
   longer than average — was it beautiful?" The capture and the judgment
   happen simultaneously, not separately.

---

## The numbers

| Metric | Value |
|:---|:---|
| Total Python lines | ~8,620 |
| Total TypeScript lines (plugin) | ~500 (scaffold) |
| Circles completed | 6 (A-F) |
| Circles remaining (estimated) | ~15-20 to approach 99.9% coverage |
| Video clips processed (circle F) | 136 |
| Human judgments captured | 14 |
| LLM vision calls | ~270 (136 pretag + 8 adapt + 18 QA) |
| Final video length | 80 seconds |
| Time to build circle F | ~11.5 hours |
| External storage used | 6.5GB of 1.9TB |
| API cost (circle F, est.) | ~$2-3 (MiniMax M3 + TTS) |

---

## The one-sentence state of the project

> Circle F proved the loop works end-to-end — fetch, judge, cut, finish, audit,
> seed — and the infrastructure is reusable; the next circle (automation) turns
> an 11-hour manual process into a one-command pipeline, and the circle after
> that (glasses capture) is where the human-perspective thesis actually starts
> proving itself.
