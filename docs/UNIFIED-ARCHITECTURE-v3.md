# Unified Architecture v3 — Three Systems, One Platform

> **This is the canonical *engineering* document.** It is the architecture
> expression of `THE-SEED-DOCTRINE.md` — where the two appear to conflict, the
> doctrine wins and this document is revised to match.
>
> **This document** supersedes the two-system model in
> `EDGE-CLOUD-ARCHITECTURE-v2.md` and reconciles the findings of two
> independent audits (DeepSeek V4 Flash + OpenAI, 2026-08-04/05).
>
> **The core correction:** the project has **three** separately governed systems,
> not two. v2's classification error — assigning the video factory to the
> human-capture system — is fixed here. So are the EDL time-equation bug, the
> single-string provenance weakness, the premature routing thresholds, and the
> unsafe IPFS sharing assumption.
>
> **Date:** 2026-08-05. **Author:** main agent, consolidating OpenAI + DeepSeek.
> **Status:** canonical (pending Kimi/Qwen review).

---

## 0. The one-line doctrine

> **One philosophy, one control plane, three isolated data planes.**

The *philosophy* is set by `THE-SEED-DOCTRINE.md`: imagination is the seed;
rightness is situated (time, place, event); guidelines protect integrity but
must never lock the limit (the apple-tree warning). This document is the
engineering consequence of those claims. The three systems below are how the
doctrine is built — not a replacement for it.

The three systems share infrastructure (Mac Studio, local Qwen, routing logic,
provenance schema, telemetry). They **never** share data. Each owns its own
judgment ledger, its own storage namespace, and its own eligibility rules.

---

## 1. The three systems

| | System A | System B | System C |
|:---|:---|:---|:---|
| **Name** | Labs Human-Capture Network | Local Development Bridge | Forge Media Factory |
| **Purpose** | Capture human-perspective signal | Accelerate founder's coding | Produce commercial ECH media |
| **Permitted origin** | `human_capture` (primary) | `ai_generated`, code, docs | licensed_stock, company_owned, approved `ai_generated` |
| **Flow** | glasses → phone → privacy → local tag → cloud judge → convergence → learn | task → draft → **blind critic** → cloud synthesis → review | brief → script → asset pool → EDL → compose → finish → QA → publish |
| **Shares externally?** | Yes (encrypted, private IPFS only) | No — private dev loop | No — client assets |
| **Eligibility** | `labs_allowed` | `private_dev_only` | `forge_only` |
| **Primary danger** | quiet moments discarded; AI signal corrupts Labs | anchoring; weak critique; dev output leaks to Labs | factual errors; licence failures; low-quality auto-publish |

**The classification fix (v2 → v3):** the video factory is **System C**, not
System A. It uses licensed stock + company media + possibly AI assets — that is
*not* human capture. Treating it as System A was the root error that made
provenance look harder than it is. System C can be `ai_generated` internally
while remaining permanently Labs-ineligible. The tension dissolves.

---

## 2. What is shared vs. what is isolated

### Shared control plane (one set of infrastructure)
- model registry + capability names (§7)
- provider adapters (OpenAI-compatible)
- cost / latency / failure telemetry
- confidence-calibration framework
- job orchestration conventions
- schema-versioning library
- audit-event format
- secrets-management pattern
- retry / timeout / circuit-breaker
- policy engine (the provenance contract, §3)

### Separate data planes (never shared)
- raw capture media (System A)
- embeddings derived from private capture (A)
- IPFS content (A)
- video-production asset pools (C)
- coding prompts containing private repo content (B)
- training / correction datasets (all)
- credentials (all)
- retention policies (all)
- eligibility decisions (all)

**Rule:** a shared Mac Studio is acceptable. A shared database containing all
three systems' records is not.

---

## 3. Provenance — the central policy contract (critical fix)

### What was wrong
v2's `videogen/provenance.py` uses a single `source_type` string (`stock` /
`ai_generated` / `human_capture`) plus an `area` (`open` / `commercial`). Both
audits found this insufficient: it conflates origin with transformation, cannot
represent mixed provenance, and **cannot prove every future path into Labs
passes through it**. A repo-level gate is not a security boundary.

### The fix: four independent dimensions + central enforcement

```text
origin:
  human_capture | company_owned | licensed_stock | ai_generated | mixed

transformation:
  untouched | cropped | colour_adjusted | narrated | composited |
  generatively_modified | fully_synthetic

presentation_claim:
  documentary | representative | illustrative | synthetic

eligibility:
  labs_allowed | forge_only | private_dev_only
```

Plus the lineage record: parent asset IDs; transformation history; model +
model version; licence evidence; consent status; human overrides; policy
decision + reason; immutable audit timestamp.

### Where the gate lives (the load-bearing change)

The gate moves from "a function in the video repo" to a **central policy
contract enforced at the Labs ingestion endpoint**:

> **No Labs record is accepted unless the Labs ingestion service independently
> validates its full lineage.**

System C (Forge) and System B (Dev) may *pre-check* eligibility, but Labs never
trusts the producer's declaration alone. `videogen/provenance.py` remains as a
library both producers call, but it is not the boundary — the ingestion service
is.

### The human-confirmation rule (fixes DeepSeek's critical finding)

A tag written by an LLM on a human-captured frame is **not** automatically
`human_capture`. It is `ai_assisted_meta` until a human confirms it. Only on
human confirmation does it become Labs-eligible. This closes the leak DeepSeek
found (AI-generated tags entering Labs labeled as `human_capture`).

- `human_capture` + AI tag + **no** confirmation → `ai_assisted_meta` → Labs-ineligible
- `human_capture` + AI tag + **human confirms** → `human_capture` + confirmation record → Labs-eligible

This is the precise definition that was missing.

---

## 4. The hard blocks (do not cross these until the gate is passed)

Two operations are **irreversible** and therefore blocked by default:

### Block 1 — No destructive frame discarding
The local filter may *label* frames "discard," but it **must not delete** until
Gate 5 (discard falsification study, §10) passes. Shadow mode only — compare
the filter's decision against later human + cloud review. Only after false
negatives are measured is physical deletion enabled.

### Block 2 — No public IPFS sharing of human-derived tags
Text tags reveal identity, location, routines, relationships. IPFS traffic is
public unless encrypted; a CID is not revocable. The first convergence
implementation must use **encrypted private IPFS** (or private/hybrid-private
nodes), never mainnet. Blocked until Gate 6 (protected convergence + Study F
attack simulation) passes.

Everything else in the architecture is reversible. These two are not.

---

## 5. System C — Forge Media Factory (the EDL + QA fixes)

### Fix 5a — The EDL time equation (math bug)

**The bug:** the build plan declares (1) voice is master clock, (2) each shot
duration = its voice duration, (3) shots use overlapping crossfades, (4) total
= sum of shot durations. With overlap, (4) is wrong:

```
T_rendered = Σd_i − Σx_i     (d = shot duration, x = crossfade overlap)
```

When each `d_i` equals its voice duration, the rendered video is shorter than
the voice track by total transition overlap → VO/footage desync (the exact
Circle F bug).

**The fix:** the EDL already carries `timeline_start_sec` and `transition` —
use them as authoritative, and derive total from positions:

```python
timeline_start[0] = 0
timeline_start[i+1] = timeline_start[i] + shot_duration[i] - transition_overlap[i]
total_duration = max(timeline_start[i] + shot_duration[i])
```

Clean design: voice cue windows stay non-overlapping; visual shots get
transition *handles* before/after the voice window; source clips must have
sufficient handle length; audio and visual duration validated separately.
**Resolve this in H1 before H3 is implemented.**

### Fix 5b — Brief is the canonical input (not the URL black box)

The stated goal `produce --tour-url <URL> --out <mp4>` cannot work — a URL
cannot provide aspect ratios, language, voice model, library refs, clip hints,
branding, platform list, CTA, music mood. Those live in `brief.yaml`.

**Canonical interface:**
```bash
python -m videogen produce --brief handoff/brief.yaml --out-dir forge-output/<slug>
```

A `--tour-url <URL> --preset ech-default` convenience may remain, but it must
**generate and persist an explicit brief** showing every default it selected.
"One command" means one orchestrated entry point, not an opaque black box.
Every stage remains independently replayable.

### Fix 5c — Three-layer QA (no self-referential judging)

If the same model family runs tagging + selection + final QA, correlated blind
spots pass through all stages. Three layers:

1. **Deterministic** (machine, no model): duration; black-frame; silence/
   clipping; subtitle timing + safe-area; logo presence; resolution; codec/
   bitrate; **provenance completeness**; file readability.
2. **Model-based** (M3): visual relevance; obvious synthetic defects; subtitle
   legibility; audience fit; brand consistency.
3. **Independent sample audit** (second model or human): reviews a sample;
   factual claims checked against tour brief + verified library refs;
   disagreements stored as calibration data.

> A model score must never override a deterministic provenance failure.

### Fix 5d — Acceptance criteria (beyond "70% QA pass")

A 70% pass rate rewards a lenient judge. Real phase-one acceptance:
- 100% asset-lineage completeness
- zero unknown schema versions
- zero ungrounded destination/itinerary claims
- rendered duration within tolerance
- zero subtitle safe-area violations
- reproducible rerun from retained brief + EDL
- median human correction time
- first-pass QA rate; autofix rate; human rejection rate
- cost per accepted video; override count by failure category
- publish-package completeness

**The business metric that matters:**
> **Human minutes required per accepted, publishable video.**

---

## 6. System B — Local Development Bridge (the blind-critic fix)

### What was wrong
v2's vibe-coding bridge used **self-critique**: the same local model drafts,
then critiques its own draft, then sends both to the cloud. Models favor their
own outputs during self-evaluation (research-established), and the draft
*anchors* the cloud to the local framing.

### The fix: blind independent critic
1. Local generator produces **Draft A**.
2. Independent local critic sees the task, spec, and tests — **but not Draft A**.
3. Critic writes a **failure checklist** + expected solution properties.
4. Critic *then* reviews Draft A against that checklist.
5. For difficult work, generate an independent **Draft B**.
6. Cloud synthesis receives: original task + evidence + tests + both drafts +
   the independent critique.
7. **Executable tests** determine success wherever possible.

For invariant-bearing code (provenance, PII, identity, crypto), the cloud
reviewer performs an **independent cold review** — it does not merely refine
the local answer.

### Tiered review (route by harm, applied to code)
| Module class | Reviewer | Why |
|:---|:---|:---|
| Invariant-bearing (auth, provenance, PII, crypto, filesystem) | **Cloud (DeepSeek)** — always, regardless of local confidence | real bugs hide here |
| Routine (CLI, utilities, docs) | Local (Qwen-14B) | free, fast, sufficient |
| Promotion path | re-reviewed by cloud when a routine module becomes load-bearing | prevents under-review of future-critical code |

### Runtime isolation (fixes DeepSeek's "static isn't enough")
"No import path" is a compile-time guarantee only. Runtime leakage is possible
through shared processes, logs, caches, vector stores. System B and System A
run in **separate containers** with separate storage namespaces, separate
queues, separate model instances where feasible. A runtime test asserts B
cannot read A's storage or logs.

---

## 7. System A — Capture Network (the router + discard + IPFS fixes)

### Fix 7a — Route by expected harm, not confidence alone

**0.70 and 0.85 are not architectural truths** — they are initial experimental
settings, to be calibrated. Confidence alone is insufficient because it is
uncalibrated and varies by model/task/device/domain.

The router decides on multiple factors:
```text
decision = f(
  calibrated_error_probability,
  consequence_class,   # provenance? factual? privacy?
  privacy_class,       # bystanders? faces? location?
  expected_cost,
  expected_latency,
  model_capability,
  domain
)
```

- Provenance code → cloud/human review **even at 98% local confidence**.
- Low-impact doc rewrite → stays local at lower confidence.
- Uncertain face/consent decision → **human, not just a larger model**.

> **Route according to expected harm, not confidence alone.**

Calibrate on-device with held-out human-labeled samples; use separate
thresholds for discard / tag / share; monitor calibration drift. Thresholds
are versioned config with an immutable audit log.

### Fix 7b — Remove "discard 95%" as an objective

"Discard 95%" is useful as a cost hypothesis, **dangerous as a product
objective**. Once a team is measured on discard %, the easiest win is
aggressive discard — destroying the thesis's most valuable information.

**New objective:**
> Minimize computation while keeping the quiet-signal false-negative rate below
> an empirically justified limit.

### Fix 7c — Six discard mitigations (4 from M3 + 2 new)
1. Random discard sample (2–3%) for periodic audit.
2. Temporal coverage floor (never discard a whole time window).
3. Forced-retain tags (human-moment / cultural-marker).
4. Periodic cloud audit of the discard pile.
5. **Event-boundary protection** *(new, OpenAI):* quiet frames immediately
   before/after a detected event retained — meaning depends on context.
6. **Shadow mode** *(new, OpenAI):* filter labels "discard" but does not delete
   until Gate 5 passes.

Monitor: missed meaningful-event rate; missed cultural-marker rate; recall by
lighting/environment/event-duration/user/device; calibration; % of discards
rescued by audit.

### Fix 7d — IPFS privacy (the smallest-shareable-unit question)

"Only text leaves the device" is false for privacy — text tags reveal
identity, location, routines. The first convergence uses:
- client-side encrypted payloads
- private/hybrid-private IPFS nodes (never mainnet for human data)
- pseudonymous node identifiers; rotating group keys
- subject-consent metadata; expiry/retention; a revocation index
- separate public aggregates with no person-level information

**The open question that defines the share layer:**
> What is the smallest shareable unit that enables convergence without exposing
> an identifiable human event?

It may be a locally aggregated feature, a signed claim, or a privacy-preserving
count — **not a natural-language tag**.

### Fix 7e — The 7-layer brain (unchanged, reaffirmed)
Layer 0 (capture) → 0.5 (PII blur, human-gate, default ON) → 1 (filter, 1-3B)
→ 2 (understand, 3-30B) → 3 (reason, cloud) → 4 (share) → 5 (learn). The
端-边-云 tiering maps onto this; it does not replace it.

---

## 8. Model registry (provider ≠ model)

"M3 handles vision, VO, and TTS" mixes a provider with separate models. Cost,
failure modes, credentials, rate limits, and version changes occur **per
model**, not per provider. Model assignments are **configuration-driven**, not
hard-coded.

```text
Provider: MiniMax
Capabilities:
  multimodal_reasoning -> MiniMax-M3
  text_to_speech       -> speech-2.8-hd
  video_generation     -> selected Hailuo model
  music_generation     -> selected music model

Provider: DeepSeek
Capabilities:
  code_review + audit  -> deepseek-v4-flash

Provider: GLM (via Cursor)
Capabilities:
  orchestration        -> glm-5.2
```

---

## 9. Build sequence (7 gates)

**Gate 1 — Constitutional foundation** (blocks Labs path; does not block C/B):
define Systems A/B/C; canonical provenance schema (4 dims); Labs ingestion
policy; resolve EDL time equation; brief as canonical video input; model
registry; trust boundaries + storage separation.

**Gate 2 — Forge Media Factory** (System C, can proceed in parallel with Gate 1):
EDL schema + validator; synthetic timeline tests; URL ingestion; voice
generation; EDL-driven composition; deterministic QA; model-based QA; seam
contract tests; reproducibility package; human-review logging.

**Gate 3 — Local Development Bridge** (System B, can proceed in parallel):
`tools/local_bridge/`; no Labs dependency; local generator; **blind critic**;
cloud escalation; model+cost logging; executable evaluation; `ai_generated`
provenance marking; runtime isolation from System A.

**Gate 4 — Capture without destructive filtering** (System A, blocked on Gate 1):
glasses capture; on-device privacy; local tagging; consent indicators;
encrypted local event vault; human correction interface. **Filter classifies
but does not delete.**

**Gate 5 — Discard falsification** (blocked on Gate 4): measure filter against
retained ground truth. Enable destructive discard only when quiet-event recall
is acceptable, calibration stable, temporal floor works, override rules work,
discard audits detect regression.

**Gate 6 — Protected convergence** (blocked on Gate 5): encrypted private
network; controlled participants; pseudonymous records; no public NL event
tags; revocation/retention testing; poisoning + duplicate detection; **Study F
attack simulation**.

**Gate 7 — Learning** (blocked on Gate 6): local preference adaptation;
threshold calibration; reputation weighting; poisoning resistance;
privacy-preserving aggregate learning.

**Parallelization note:** Gates 2 and 3 can start **now**, in parallel with
Gate 1, because neither touches Labs. The discipline applies to the Labs path;
the commercial + dev paths should not wait on it.

---

## 10. Experiment plan (the falsification spine)

| Study | What it tests | Gate | Status |
|:---|:---|:---|:---|
| **A — Video reproducibility** | Run tours multiple times; measure selection variance, factual consistency, cost variance, QA disagreement, correction time. Goal: stable editorial quality, not identical pixels. | Gate 2 | not started |
| **B — Local vs cloud code review** | One sprint, same changes independently to local Qwen / DeepSeek / human; classify defects. Establishes which modules local review may approve. | Gate 3 | not started |
| **C — Confidence calibration** | Labelled examples per routing domain; measure calibration error, false-negative rate, escalation rate, cost, latency. Each model+task gets its own profile. | Gate 1/4 | not started |
| **D — Discard counterfactual** | Stratified sample of "discard" frames (low-light, slow-motion, culturally subtle); humans + independent model find missed meaning. Metric: **meaning lost per compute unit saved**. | Gate 5 | not started |
| **E — Provenance penetration test** | Deliberately inject AI tags into Labs; modified stock marked documentary; unknown source; missing lineage; altered consent; bad schema; data via logs/caches/embeddings. Must fail closed. | Gate 1 | not started |
| **F — Convergence attack simulation** | Duplicate contributors, Sybil nodes, coordinated false tags, replayed events, synthetic consensus, high-volume node overwhelming humans. | Gate 6 | not started |
| **G0 — Falsification (done)** | Pairwise human judgment; n=1, 90 pairs, 80% consistency. Pilot only — expand to n≥2 for inter-rater reliability (Cohen's kappa). | — | ✅ pilot done |

---

## 11. The defensible asset (the larger vision)

The three systems form a reinforcing loop:
```
System C — Media Factory   → commercial output + revenue
System B — Dev Bridge       → lowers cost/time to build the platform
System A — Capture Network  → differentiated long-term thesis
```

IPFS, glasses, local Qwen, any cloud model — all replaceable. The defensible
asset is:

> **An audited judgment system that records origin, uncertainty, correction,
> human override, and failed assumptions.**

Three separate judgment ledgers: **editorial** (media), **engineering** (code),
**human-perspective** (Labs). They share methods, not raw truth claims.

---

## 12. Audit reconciliation (what this v3 changed vs v2)

| Finding | Source | v3 fix | Section |
|:---|:---|:---|:---|
| AI tags labeled human_capture in Labs | DeepSeek (critical) | `ai_assisted_meta` until human confirms | §3 |
| provenance.py not a security boundary | OpenAI | central policy contract at Labs ingestion | §3 |
| single `source` string insufficient | OpenAI | 4 dimensions (origin/transformation/claim/eligibility) | §3 |
| video factory misclassified as System A | OpenAI | System C (Forge Media Factory) | §1 |
| EDL time equation inconsistent | OpenAI | derive from `timeline_start`, not sum | §5a |
| `--tour-url` one-command is a black box | OpenAI | `--brief` canonical, URL as preset | §5b |
| QA self-referential | OpenAI | three layers (deterministic/model/independent) | §5c |
| 0.70/0.85 thresholds premature | both | route by expected harm, calibrate | §7a |
| "discard 95%" dangerous as objective | OpenAI | replace with meaning-lost-per-compute | §7b |
| only 4 discard mitigations | both | + event-boundary + shadow mode (6 total) | §7c |
| "only text leaves device" false for IPFS | OpenAI | encrypted private IPFS, smallest-unit question | §7d |
| M3 conflated with TTS | OpenAI | model registry, config-driven | §8 |
| self-critique anchors cloud | OpenAI + DeepSeek | blind independent critic | §6 |
| static separation insufficient at runtime | DeepSeek | containers, separate storage/queues | §6 |
| L5 learning leaks via weights | DeepSeek | learned models stay `ai_generated`, weight provenance recorded | §3, §7 |
| no acceptance criteria beyond 70% | OpenAI | full criteria + "human minutes per video" | §5d |
| no attack model for convergence | OpenAI | Study F | §10 |
| destructive discard + public IPFS unsafe | OpenAI | two hard blocks | §4 |

**Both audits converge on:** the ideas are sound; the *system boundaries* and
*provenance enforcement* were not. v3 fixes both.

---

## 13. What this v3 does NOT do

- Does not delete v2 or `HYBRID-EDGE-ARCHITECTURE.md` — they remain as history.
  v3 is canonical; the older docs are reference.
- Does not relax any invariant. The human-confirmation rule (§3) *strengthens*
  invariant #4.
- Does not commit to a ship date. Gates give dependencies, not dates.
- Does not treat Kimi/Qwen review as done — they are still pending (keys
  needed). This v3 is canonical *pending* that third + fourth voice.

---

## 14. Open questions still live

- **OQ-A:** Is `ai_assisted_meta` + human confirmation the right line, or should
  Labs require *only* human-authored tags (no AI metadata at all)? This is a
  thesis-level decision for the founder.
- **OQ-B:** What *is* the smallest shareable unit for convergence (§7d)? A
  signed claim? An aggregate count? A feature vector? This needs a design doc
  before Gate 6.
- **OQ-C:** Does System B's blind critic need a *different* local model than
  the generator (to avoid same-model bias), or is task-framing isolation
  sufficient?
- **OQ-D:** For Study B (local vs cloud review), what's the statistical bar —
  is "local catches ≥80% of what cloud catches" the threshold to trust local
  review on routine modules?

These four go to Kimi + Qwen + the founder. Everything else in this doc is
settled by the two completed audits.
