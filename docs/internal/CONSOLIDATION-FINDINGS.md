# Consolidation — Code Quality & Research Methodology Findings

**Purpose:** one place to find every finding on the two weakest dimensions of HiveAGI, so we stop re-reading 15 audit files. Grounded in live numbers, not memory.
**Date:** 2026-08-03
**Sources consolidated:** COMPREHENSIVE-REVIEW, RE-AUDIT, THESIS-VERIFICATION, EXTERNAL-AUDIT-SYNTHESIS, FINAL-AUDIT, LLM-COUNCIL, M3-REVIEW, DEEPSEEK edge/p2p/skill reviews, BIG-CIRCLE-RETROSPECTIVE, G0 results.

---

## 0. Where we actually are right now (live, not from memory)

| Signal | Value | Status |
|:---|:---|:---|
| Tests passing | **98 / 98** | ✅ green |
| **Coverage** | **24.18%** | ❌ **below the 25% gate — CI is red right now** |
| Coverage floor configured | 25% | must raise to 50 → 70 |
| `clip_pool/` (7 modules) | **0%** | the core judge/tag/metrics pipeline has zero tests |
| `g0_experiment.py` | **0%** | the experiment code is untested |
| `selection_log.py`, `videogen/cli.py`, `p2p_exchange/cli.py` | **0%** | untested |
| `provenance.py` (the gate) | **97%** | ✅ best-tested, exactly right |
| `reputation.py`, `appreciation.py` | **97%** | ✅ |
| Ruff lint installed | ✅ (in `.venv`) | 4 non-auto-fixable issues remain |
| G0 pilot run | n=1 evaluator, 90 pairs | done, not yet pre-registered |
| Overall maturity | 5 → 7 (+2) | up from baseline, still pre-commercial |

**The headline:** the gate is red *today*. Coverage 24.18% < 25%. This is the first thing to fix because a red gate trains us to ignore the gate.

---

## 1. Research methodology — the consistently weakest dimension

Every independent reviewer names the same weakness. This is the single most reliable finding in the whole audit history.

### The finding, in one line
> "We built infrastructure for collecting human-perspective data, but we haven't proven the data we're collecting *is* human perspective." — EXTERNAL-AUDIT-SYNTHESIS (OpenAI + Claude consensus)

### Scores that say the same thing
- COMPREHENSIVE-REVIEW: **research_methodology 4/10** — "more engineering than research; no empirical validation."
- RE-AUDIT (after improvements): **5/10** — up one point, still lowest dimension.
- THESIS-VERIFICATION: **both models say `thesis_valid: false`.** DeepSeek: "Human perspective is not reducible to discrete tags of attention." MiniMax: "correctly identifies the gap, falsely claims AGI already exists."

### The three concrete defects behind the low score
1. **Construct validity is unproven.** We never showed the signal we collect (tags + judgments) actually measures "human perspective." It might just measure "editorial taste on professional stock."
2. **n=1 is not a dataset.** 14 judgments (Circle F) was proof of *collection*, not evidence of a *general signal.* The G0 pilot adds 90 pairs but still from one human.
3. **Stock capture ≠ human capture.** They are different variables. Treating a Pexels clip a human picked as "human perspective" conflates two provenance types — exactly what the provenance gate exists to prevent, but the *methodology* hasn't caught up to the *code*.

### What the G0 pilot already showed (the good news)
- **Intra-rater consistency 0.80** (8/10 repeat pairs consistent) → human taste is reliable, not random.
- **Model accuracy 0.50** → the commercial_grade baseline is a coin flip; it adds zero value. Humans see things the model can't.
- Free-text notes surfaced signals no scraper gets: "left is too ai" (AI-detection), "if content is in china for ECH" (geographic fit), "people moving, content change" (motion quality).

So the thesis isn't dead — it's *unvalidated*. The pilot was step 1 of validation.

### Consolidated methodology actions (priority order)
| # | Action | Why | Effort |
|:---|:---|:---|:---|
| M1 | **Pre-register the G0 protocol** before scaling | Reviewers (OpenAI, Claude, DeepSeek) all demand it. Running the experiment then writing the protocol = p-hacking. | 1 doc |
| M2 | **Run G0 with a second (then third) evaluator** → Cohen's kappa for inter-rater reliability | n=1 can't show the signal generalizes. n=2 is the minimum for kappa. | reuse existing HTML |
| M3 | **Split provenance: stimulus_provenance vs. judgment_provenance** | Removes the stock-vs-human conflation at the data-model level, not just the code gate. | refactor |
| M4 | **Publish feature-space surrogates** (perceptual hash + metric vector + M3 tag vector), not orphan labels | Lets others reproduce without trusting our label alone. OpenAI's #2 ask. | exporter |
| M5 | **Define "Red circles"** — experiments designed to *fail* the thesis | A thesis you can't falsify isn't research. Current circles all build, none test. | design |
| M6 | **1,000+ judgments target** for a real claim | 90 pairs is a pilot; the thesis needs ~10× more to publish. | scaling |

---

## 2. Code quality — better than methodology, but the gate is red

### Scores
- COMPREHENSIVE-REVIEW: code_quality **5/10** — "AI-assisted, non-expert coding likely yields inconsistent quality."
- RE-AUDIT: **6/10** — provenance.py alone went **4/10 → 8/10** via the DeepSeek review loop. The loop works; it just hasn't been run on most modules.

### The gap is concentrated, not spread out
Coverage isn't 24% everywhere — it's **97% on the critical gate, 0% on the clip pool.** The fix is surgical:

| Module | Coverage | What it does | Risk |
|:---|:---|:---|:---|
| `clip_pool/fetch.py` | 0% | Pulls candidates, records provenance | A provenance bug here poisons the pool silently |
| `clip_pool/judge.py` | 0% | Captures human verdict → jsonl | A schema bug here corrupts preference data |
| `clip_pool/metrics.py` | 0% | opencv brightness/motion/shake | Wrong metric = wrong discard |
| `clip_pool/adapt.py` | 0% | landscape→portrait crop, provenance chain | Breaks `derived_from` chain |
| `clip_pool/llm_tags.py` | 0% | M3 vision tags | Untagged = unfilterable |
| `g0_experiment.py` | 0% | The experiment itself | Unvalidated experiment code |
| `selection_log.py` | 0% | Logs editor choices | Untested |
| `compose.py` | 10% | Renders the video | The place Circle F's 6 bugs lived |

### The engineering defects every reviewer agrees on
1. **"A DAG of hopes, not a schema-validated contract."** (M3-REVIEW) — LLM tags flow straight into the cutter; non-deterministic model output silently corrupts downstream cuts. **Contract tests between stages are missing.** This is H7 in the build plan and it's unstarted.
2. **The two-repo seam (ECH ↔ HiveAGI) has no contract tests.** DeepSeek named this the weakest link in FINAL-AUDIT. The build plan says "write contract tests FIRST, before produce.py." Not done.
3. **No observability** (latency, cost, failure logs) — can't optimize what we can't see.
4. **Human judge is an un-SLA'd synchronous bottleneck** — blocks full automation.

### Consolidated code actions (priority order)
| # | Action | Why | Effort |
|:---|:---|:---|:---|
| C1 | **Get the gate green again** — add tests until ≥26%, then raise the floor to 30 | A red gate trains us to ignore gates. This is the single most corrosive state. | hours |
| C2 | **Test `clip_pool/`** (start with metrics.py — pure functions, no API) | 0% on the provenance-bearing pool is the highest-risk gap | hours |
| C3 | **Write H7 contract tests** before any Circle G automation | Prevents the "DAG of hopes" failure mode. Reviewers say do this *first*. | days |
| C4 | **Run the DeepSeek review loop on clip_pool modules** | It took provenance 4→8. Same tool, same leverage, not yet applied. | runs |
| C5 | **Add an asset pre-flight validator + JSON schema gate** | Catches non-deterministic LLM output before it hits the cutter | days |
| C6 | **Raise coverage floor 30 → 50 → 70** as tests land | Makes the gate *enforce* quality, not just measure it | ongoing |

---

## 3. The two latent risks nobody has a fix for yet

These don't fit "methodology" or "code" cleanly, but both reviewers flagged them as potentially fatal. Consolidating so they don't get lost.

### Risk A — The discard problem (flagged 3× independently)
The Layer-1 local model discards ~95% of frames. Three reviewers (MiniMax M3, LLM-COUNCIL top risk, DEEPSEEK-EDGE-REVIEW) warn it will **"keep the visually loud and discard the visually true"** — irreversible loss of quiet but narratively pivotal frames. DEEPSEEK also says the **0.85 threshold is too high for a 1-3B model** (recommends 0.7–0.8 with calibration).

**Consensus fix (from M3):**
1. Keep a 2–3% calibration sample of "boring" discarded frames for audit.
2. Temporal coverage floor (don't discard a whole time window).
3. Human-moment / cultural-marker override tags.
4. Periodic M3 audit of the discard pile.

**Status: none built. Needs a design doc before Circle J (local LLM).**

### Risk B — Immutable IPFS privacy poisoning (LLM-COUNCIL)
Once a learned user-behavior pattern is tagged, pinned to IPFS, and shared, **the user can never retract it.** CIDs correlated across users enable deanonymization. This is a *new* class of risk the provenance gate doesn't cover (it covers pixel/frame provenance, not learned-pattern provenance).

**Status: no mitigation. Needs a design doc before Layer 5 (Learn).**

---

## 4. What's already resolved (don't redo these)

So we focus only on what's left:

- ✅ Provenance gate exists and is enforced in code (stock/AI blocked from Labs) — 97% tested.
- ✅ Share-consent gate (strict bool, commercial needs explicit consent).
- ✅ PII blur as human-controlled layer (default ON, toggle logged with reason).
- ✅ Spam filter + appreciation + contribution + improvement boards (4-layer trust).
- ✅ Ed25519 signed manifests (identity.py).
- ✅ DeepSeek code-review harness works (provenance 4→8).
- ✅ G0 pilot ran (n=1, 90 pairs, 80% consistency).
- ✅ Single-pass compositor (fixes 3 of 6 Circle F bugs).
- ✅ Calibrated audio/subtitle/logo numbers documented.

---

## 5. The one-line priority for the next loop

> **C1 then M2 then C2.** Get the coverage gate green (hours), run G0 with a second evaluator (reuses existing tooling), then backfill clip_pool tests. After that: M1 (pre-register) and C3 (contract tests) before any new automation.

Everything else is downstream of those five. The thesis lives or dies on whether the human-perspective signal generalizes beyond one person — and right now we have one person, and a red gate.
