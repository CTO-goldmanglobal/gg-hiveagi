# The Small Circles Strategy — How Hive.AGI Gets Built

> The execution philosophy behind Project Hive.AGI.
> Status: living document. Last updated 2026-07-28.

---

## The thesis

Don't chase the big vision directly. It's too large, too abstract, and it
never finishes — so it never ships.

Instead, define **one complete, repeatable loop**. Finish it fully. Then run
the next. Each loop is a small circle:

```
        ╭──────────────╮
       ╱   complete    ╱
      │     loop      │   ← one small circle: a single domain,
      │   (reviewable │     fully finished, end to end
       ╲   repeatedly)╲
        ╰──────────────╯
```

Many completed circles cover the vision — not by drawing one big circle, but by
overlaying many small ones. Each overlaps the last (consistency, reusable
infra) and adds new territory (a new domain, a new audience, a new kind of
human perspective).

```
   ◯◯◯◯◯◯◯◯◯◯  ←  small circles, overlapping
   ░░░░░░░░░░░░   ←  coverage grows toward 99.9%
```

> "A small circle cannot cover a large circle. But repeatedly using many small
> circles — always overlapping, always including new area — finally reaches
> 99.9% covered."

The discipline is the whole point: **finish one circle completely before
starting the next.** A half-finished circle covers nothing.

---

## What makes a circle "complete"

A loop is only done when **all five stages are finished and reviewable:**

| Stage | What it produces | Reviewable? |
|:---|:---|:---|
| 1. **Capture/Source** | A pool of candidate material (stock now; glasses/phone later) | ✅ viewable |
| 2. **Judge** | Human accept/reject + *why* — the beauty standard | ✅ logged |
| 3. **Cut** | The chosen moments (which 3–4s of which clip) | ✅ recorded |
| 4. **Compose** | A finished deliverable (the Reel / the cut) | ✅ watchable |
| 5. **Seed** | The human-judgment layer extracted + gated for Labs | ✅ publishable |

If any stage is stubbed or skipped, the circle isn't complete — it's a gap that
later circles can't paper over. A circle you can't **review time and again** is
a circle that didn't run.

> **Definition of done:** a circle can be re-opened and re-reviewed at any
> time, and every decision in it is traceable to a human reason.

---

## The hybrid seed — the durable asset of every circle

Every circle produces two things. One is throwaway; one is the point.

| Output | Where it goes | Lifespan |
|:---|:---|:---|
| **The deliverable** (the cut Reel, the commercial video) | Forge — Goldman Forge, commercial delivery | Ephemeral. It sells a tour. |
| **The human judgment** (beauty standard: yes/no + why + cut point) | **Hybrid seed** — serves Forge *and* Labs | **Durable. This is the asset.** |

The hybrid seed is human perspective distilled: what a human editor found
beautiful, what they rejected, and exactly which moment they chose. That is
*exactly* the human-perspective data the Labs network exists to aggregate.

### The provenance seam — what crosses, what doesn't

This is the subtle, load-bearing distinction in the whole project. Get it
wrong and the AGI thesis silently corrupts. Get it right and one workflow feeds
both faces of the company.

| Layer | Forge (commercial) | Labs (human-perspective Seed) |
|:---|:---|:---|
| **The raw pixels** (stock .mp4, professional footage) | ✅ Use freely | ❌ **Blocked.** Professional content optimized for an audience ≠ human perspective. The thesis requires what a human *naturally noticed*, not what a production department *staged to be noticed.* |
| **The human judgment** (accept/reject + reason + cut point) | ✅ Drives the edit | ✅ **This IS the seed.** Human taste is human perspective — regardless of what it was judged against. |

So the provenance rule is **not** "block anything that ever touched stock."
It's: **block the raw stock material from Labs, but the human-judgment layer is
Labs-eligible** — tagged with what it was judged against, so Labs can always
distinguish "editor taste on professional footage" from "what a human captured
themselves." That tag is the `source_type` field; the gate is
`provenance.is_labs_eligible()`.

```
   stock footage ──▶ Forge Reel ──────────────────────▶ sells the tour
        │
        └──▶ [HUMAN JUDGES IT] ──┬──▶ drives the Forge edit
                                 └──▶ judgment_log ──▶ Labs Seed (gated)
                                                      (source_type recorded)
```

This is why the judgment tooling exists. It is not a productivity convenience.
**It is the seed harvester.** Every completed circle deposits human-perspective
beauty data into the network, whether the source pixels were stock or
glasses-captured. The stock pixels get thrown away; the judgments compound.

---

## Circle #1 — Legends of China Warriors

The first complete loop. ECH tourism. Source: stock (for now).

```
Stage 1  Pull stock candidates  →  pool/ (gitignored)         ← clip_pool fetch
Stage 2  Judge yes/no + why     →  judgment_log.jsonl         ← clip_pool judge
Stage 3  Cut chosen moments     →  cuts.json                  ← collaborative
Stage 4  Compose the Reel       →  legends-of-china.mp4       ← videogen
Stage 5  Extract hybrid seed    →  Seed Package (gated)       ← finalize + gate
```

Circle #1 proves the loop runs end to end. It is small on purpose: one tour,
eight shots, one audience. **It does not try to cover the vision.** It tries to
be *complete and reviewable*, so circle #2 has a template to copy.

### Why ECH tourism is the right first circle

- **Concrete deliverable.** A finished tour video is a real commercial asset.
  The loop produces something Goldman Forge can sell, not a research demo.
- **Beauty is the core question.** "Beauty of places" is exactly the
  human-perspective thesis in its purest form: what does a human find
  beautiful, and why? Tourism forces that question every cut.
- **Stock is available now.** We don't need to wait for glasses capture to
  prove the loop. Stock pixels are throwaway input; the judgments are the
  point, and those are human from day one.
- **Repeatable across tours.** ECH has many tours. Each is a new circle, same
  loop, overlapping infra, new domain coverage.

---

## Circle #2, #3, … — how coverage grows

The next circles reuse circle #1's infrastructure but add new territory:

| Circle | Domain | What's new | Reused from #1 |
|:---|:---|:---|:---|
| **#1** (now) | ECH — Legends of China Warriors | the loop itself, stock-sourced | — |
| **#2** | ECH — another tour (e.g. Imperial Yangtze) | a new audience/beauty profile | clip_pool, judge, finalize, gate |
| **#3** | ECH — a different region (e.g. Silk Road) | new geography, new "beauty" definition | all infra |
| **#N** | Real-estate / education / industrial | new domain entirely | the loop shape, the gate, the seed format |
| **#M** | **Glasses-captured** ECH footage | human-captured pixels → source_type flips to `human_capture` | everything — now raw pixels ARE Labs-eligible too |

The last row is the inflection point. When capture shifts from stock to
glasses/phone, the `source_type` tag changes and the raw pixels *also* become
Labs-eligible — but the loop doesn't change. The infrastructure built on stock
circles carries forward unchanged. **That's why we build the loop now, on
stock, even though stock can't seed Labs directly.** The loop is the asset;
the source type is a tag.

> The vision isn't reached by drawing one big circle. It's reached by drawing
> the *same small circle* over and over — each time in a new place, each time
> fully finished — until the overlapping coverage approaches the whole.

---

## What this strategy forbids

- **No half-circles.** A loop with a stubbed stage covers nothing. Finish or
  don't start.
- **No silent provenance mixing.** Stock pixels never reach Labs. The gate is
  code, not policy. `provenance.filter_for_labs()` runs on every export path.
- **No circle without review.** "Complete" means re-reviewable. If a stage
  can't be re-opened and re-checked, it isn't done.
- **No skipping ahead.** Circle #2 doesn't start until circle #1 is
  reviewable end to end. Otherwise we're chasing the big circle again.

---

## How to read the rest of the repo against this strategy

- `PROJECT_MASTER_PLAN.md` — the **what** (vision, components, roadmap).
- This doc — the **how** (the loop, the discipline, the hybrid seed).
- `videogen/` — the loop's compose stage (#4), generalized.
- `videogen/clip_pool/` — the loop's source + judge stages (#1, #2).
- `videogen/provenance.py` — the gate that keeps the hybrid seed honest.
- `videogen/selection_schema.md` — the judgment data format (Forge-side).
- `explore_china_holiday/tours/legends-of-china-warriors/` — circle #1, in full.

Every new tour, every new client, every new domain is another circle. The
shape never changes.
