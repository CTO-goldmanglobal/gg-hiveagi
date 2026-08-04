# 端-边-云协同架构 v2 (Reconciled) / Edge-Cloud Architecture v2

> **This is a replan of the v1.0 personal-AI-infrastructure doc.** It keeps the
> best ideas (the 端-边-云 tier model, confidence routing, the **vibe-coding
> bridge**) and reconciles them with the project's **committed** architecture
> (`docs/HYBRID-EDGE-ARCHITECTURE.md`, `docs/HARDWARE-SPEC.md`).
>
> v1.0 had six concrete contradictions with decisions already in the repo. This
> v2 fixes them — see §2. Where v1.0 and the committed docs disagree, **the
> committed docs win**, and v2 says why.
>
> **Author:** Finn (founder). **Replan:** main agent. **Date:** 2026-08-04.
> **Status:** draft for LLM council audit (DeepSeek + Kimi + Qwen).

---

## 1. The two ideas worth keeping (and one new one)

v1.0 端-边-云协同AI系统 made three contributions. This v2 keeps all three:

1. **端-边-云三层协同** (end-edge-cloud three-tier collaboration). A clean,
   cost-driven framing: cheap local first, expensive cloud last. **This is
   already the spine of `HYBRID-EDGE-ARCHITECTURE.md`** ("cheap local filters
   process most input, escalating only uncertain cases to expensive cloud
   models"). v2 keeps it and maps it onto the committed 5-layer brain (§4).

2. **置信度路由 (confidence-based routing).** Each request carries a confidence
   score; below threshold → escalate tier. This is the **FrugalGPT / cascaded
   routing** research pattern. v2 keeps the concept but flags that the specific
   tool "FrugalRoute" is **unvetted** in this repo (§5).

3. **【新】本地LLM作为"提示词优化桥" (local LLM as a prompt-optimization bridge).**
   Local model generates a draft → self-critiques (finds 3 defects) → packages
   "question + draft + defects" → cloud does final synthesis. This is the
   **self-refine / self-critique prompting** technique. It is genuinely useful,
   and it connects directly to the project's existing code-review loop. v2 makes
   this **System B** (§3) — a dev tool that shares infrastructure with the
   capture pipeline but **must never feed the Labs data path**.

---

## 2. The six contradictions v1.0 had with the committed docs (and the fixes)

Every fix cites the committed source of truth.

### Fix 1 — Mobile RAM: 4-6GB is wrong
- **v1.0 said:** "智能手机（4-6GB RAM）".
- **Committed:** `HARDWARE-SPEC.md:44` — **≥12GB (16GB+ preferred)**, with the
  explicit reason *"7B ≈ 6-8GB + OS + app + vault"*. A 4-6GB phone cannot hold
  the 7B class model the L1 filter needs; it can only hold a 1.5B model, which
  is the *minimum* tier, not the recommended one.
- **v2:** Mobile baseline **≥12GB** (Qwen2.5-1.5B runnable, 7B tight). **16GB+**
  to run 7-13B for smarter filtering. This is arithmetic, not preference.

### Fix 2 — "Only one cloud API" is factually wrong
- **v1.0 said:** "在仅有一个云 API 的情况下" (§10).
- **Committed:** The project uses **three** cloud models — **MiniMax M3**
  (vision/VO/TTS), **DeepSeek V4 Flash** (code review + audit), **GLM**
  (this harness). The dual-LLM pattern (M3 + DeepSeek) is load-bearing
  (`docs/internal/RE-AUDIT.json`, the consolidation doc).
- **v2:** Three cloud models, with distinct roles (§4). The "one API" framing
  misdescribes the system to any reader or contributor.

### Fix 3 — FrugalRoute is unvetted
- **v1.0 said:** FrugalRoute is "路由系统" (settled).
- **Committed:** `grep -rin frugalroute docs/` → **empty**. Never referenced.
- **v2:** The **concept** (cascaded confidence routing) is sound and already in
  the architecture; the **specific tool "FrugalRoute"** is an open question for
  evaluation (§5, OQ-1). Do not name it as decided.

### Fix 4 — The IPFS share layer was missing from the flow
- **v1.0 said:** flow ends at "result returns to phone/glasses."
- **Committed:** The **entire thesis** is Layer 4 — *only the tag leaves the
  device, converges across people via IPFS*. Omitting it makes the system look
  like a personal assistant when it is a **distributed human-perspective
  network that happens to be personal-first**.
- **v2:** Layer 4 (Share) and Layer 5 (Learn) are first-class in the flow (§4).

### Fix 5 — The discard problem was unacknowledged
- **v1.0 said:** L1 discards 95% cleanly, escalate the rest. No risk noted.
- **Committed:** `LLM-COUNCIL.json` names **"local model discards quiet but
  pivotal frames"** as the **#1 risk**. Three independent reviewers flagged it.
- **v2:** §6 is dedicated to the discard problem + the four consensus
  mitigations (calibration sample, temporal floor, override tags, discard audit).

### Fix 6 — The 5-layer brain was collapsed to 3 without noting it
- **v1.0 said:** L0-L3, dropping Layer 0.5 and Layer 4.
- **Committed:** Layer 0 → **0.5 (PII blur, human-gate — invariant #3)** → 1 →
  2 → 3 → **4 (share)** → 5 (learn). Dropping 0.5 and 4 isn't simplification —
  it's **two invariants gone from the diagram**.
- **v2:** The 7-layer model is canonical (§4). 端-边-云 maps *onto* it, not
  instead of it.

---

## 3. Two systems, one infrastructure (the provenance-critical separation)

This is the most important section. v1.0 conflated two different products that
share hardware. Conflating them **pollutes the Labs data path** (invariant #4).

### System A — HiveAGI capture pipeline (the thesis)
| | |
|:---|:---|
| **Purpose 目的** | Glasses → tag → share to Labs (human-perspective signal) |
| **Local LLM role** | Filter frames (95% discard), tag the 5% that matters |
| **Cloud escalation** | M3 *judges* uncertain frames (judge, not tagger) |
| **Shares anything? 是否分享** | **Yes — tags to IPFS, convergence across people** |
| **Thesis-relevant? 是否关乎核心命题** | **This IS the thesis** |
| **Provenance** | `human_capture` (Labs-eligible) |

### System B — Vibe-coding dev tool (the new idea)
| | |
|:---|:---|
| **Purpose 目的** | Help the founder write code faster (local draft + critique → cloud synthesis) |
| **Local LLM role** | Generate draft + self-critique → package enhanced prompt |
| **Cloud escalation** | GLM / DeepSeek final-synthesizes code |
| **Shares anything?** | **No — it is a private dev loop** |
| **Thesis-relevant?** | No — productivity tooling |
| **Provenance** | `ai_generated` (**blocked from Labs** by the gate) |

**They share the Mac Studio + the local model + the confidence-routing
philosophy. They do NOT share a data path.** System B's output (AI-generated
code scaffolding, critiqued prompts) is `ai_generated` and is blocked from Labs
by `videogen/provenance.py` — exactly as today. Building System B inside the
capture pipeline would break invariant #4.

> **不变量 #4 / Invariant #4:** Don't mix AI into Labs. "Don't mix up AI. It
> will pollute HiveAGI." (Finn) — AI is fine in Forge, forbidden in Labs,
> always tagged.

---

## 4. The unified tier model (端-边-云 mapped onto the 7-layer brain)

端-边-云 is the *cost geography*. The 7-layer brain is the *cognition*. They
compose, they don't conflict:

```
端 / END (glasses + phone)          边 / EDGE (Mac Studio)        云 / CLOUD
┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────┐
│ L0  Capture (glasses)    │  │ (Mac Studio is an EDGE   │  │ L3 Reason        │
│ L0.5 PII Blur (human-gate│  │  node for System B's     │  │  - MiniMax M3    │
│      default ON)         │  │  local LLM, NOT part of  │  │    (vision/VO)   │
│ L1  Filter (phone 1-3B)  │  │  the capture L0-L2 chain)│  │  - DeepSeek V4   │
│ L2  Understand (3-30B)   │  │                          │  │    Flash (audit) │
└────────────┬─────────────┘  └────────────┬─────────────┘  │  - GLM (this     │
             │ tag (text only)              │ code/prompts     │    harness)      │
             ▼                              ▼                  │                  │
      L4 Share (IPFS)              System B dev loop          │  ← only the      │
      only text leaves device      never shares               │    uncertain 5%  │
                                   to IPFS                    │    reaches here  │
                                                                └──────────────────┘
             │
             ▼
      L5 Learn (system adapts to the user / each node's model improves)
```

### The hardware (reconciled with `HARDWARE-SPEC.md`)
| Node 节点 | Hardware 硬件 | Role 角色 |
|:---|:---|:---|
| **Glasses 眼镜** | Brilliant Labs Frame / Halo — open SDK (Python `frame-sdk`, Flutter, Lua) | L0 capture only. ~0 compute. |
| **Mobile 手机** | **≥12GB RAM** (16GB+ preferred), NPU, CoreML/MLX/ONNX | L0.5 blur + L1 filter + L2 understand. **The gateway.** |
| **Edge 边** | Mac Studio M4 Max 64GB — Ollama + Qwen2.5 14B/32B | System B (vibe-coding bridge) + optional L2 escalation for heavy local reasoning. **Zero cost, low latency.** |
| **Cloud 云** | MiniMax M3 + DeepSeek V4 Flash + GLM (via Cursor) | L3 reason. **Only the uncertain 5-10%.** Paid, last resort. |

### Three cloud models, three jobs (not "one API")
| Model 模型 | Job 职责 | When 何时调用 |
|:---|:---|:---|
| **MiniMax M3** | Vision tags, VO/TTS, **frame audit as a judge** | Capture pipeline — uncertain frames (L3) |
| **DeepSeek V4 Flash** | Code review, project audit | Dev loop (System B) + the review harness |
| **GLM** | This harness / orchestration | Everywhere — the conductor |

---

## 5. Routing & confidence (FrugalRoute evaluated, threshold reconciled)

### The concept is right; the specific tool is unvetted
The cascaded-routing pattern (cheap layer first, escalate on low confidence) is
exactly `HYBRID-EDGE-ARCHITECTURE.md`'s escalation protocol. The name
"FrugalRoute" needs evaluation before it can be named as the router — it does
not appear anywhere in the repo.

> **OQ-1 (open question for the audit):** Is FrugalRoute a real maintained
> project, or a rename of the FrugalGPT research concept? If a tool, does it
> support semantic caching + confidence scoring on-device? Until evaluated, we
> implement the routing ourselves (it is ~50 lines of confidence-threshold
> logic) and treat FrugalRoute as a research reference, not a dependency.

### The threshold reconciliation (DeepSeek already corrected this)
`HYBRID-EDGE-ARCHITECTURE.md:326` records the correction: **0.85 is for large
cloud models. A 1-3B mobile model must start at 0.70-0.75**, calibrated upward
as it accumulates judgments. v1.0's "0.8" threshold is between these — too high
for a phone-class model. v2 uses **two thresholds**:
- **Edge filter (L1, 1-3B model): 0.70 auto-approve**, escalate 0.70-0.50,
  flag human <0.50. Calibrate upward over time.
- **Cloud auto-approve (L3, M3): 0.85** stays — M3 is large enough that 0.85 is
  honest.

This is **config with an audit log**, not a constant (`FULLY-AUTOMATIC-FLOW.md`
Q2). Every threshold change is recorded.

### Semantic cache (L0 of routing)
A local semantic cache (perceptual/text hash → prior answer) catches repeats at
~1ms, $0. This is genuine and worth building. v1.0's Redis-or-LRU is a fair
implementation question.

---

## 6. The discard problem (the load-bearing risk — do not build L1 without this)

Three independent reviewers (MiniMax M3 in FINAL-AUDIT, LLM-COUNCIL #1 risk,
DEEPSEEK-EDGE-REVIEW) warn the L1 95% discard will **"keep the visually loud
and discard the visually true"** — irreversible loss of quiet-but-pivotal frames.

### The four consensus mitigations (from M3)
1. **Calibration sample:** keep a random **2-3% of discarded frames** for
   periodic M3 audit. If M3 finds signal in the discard pile, the threshold is
   wrong.
2. **Temporal coverage floor:** never discard an entire time window. If every
   frame in a 30s span is "boring," keep one — continuity matters.
3. **Override tags:** human-moment / cultural-marker tags force-retain
   regardless of confidence ("this is a tea ceremony, always keep").
4. **Periodic M3 discard audit:** a scheduled job reviews the discard sample and
   reports what was lost. This is the *falsification* of the discard policy.

**Status:** none built. This is a **design-doc prerequisite for Circle J**
(local LLM). v2 will not let L1 ship without all four.

---

## 7. The vibe-coding bridge (System B) — self-refine, placed correctly

This is the genuinely new, genuinely good idea. It connects directly to the
project's **existing dual-LLM review loop**, which today runs entirely in the
cloud (GLM writes → DeepSeek reviews → GLM fixes). System B moves the critique
step **to the local Mac Studio model** — same pattern, $0 instead of API cost.

### How it works (the generate-critique-package-synthesize loop)
```
1. Receive the dev task (raw, possibly spoken/typed casually)
2. Local Qwen-14B generates a structured DRAFT
3. Local Qwen-14B SELF-CRITIQUES: names 3 defects (logic gap, missing edge
   case, cost problem)
4. Package "task + draft + defects" as one enhanced prompt
5. IF local confidence high → use the draft, done ($0)
   IF low → send enhanced prompt to cloud (GLM/DeepSeek) for final synthesis
6. Cloud returns a high-quality answer that "stands on the shoulders" of the
   local draft — one cloud call, far better than a cold-start cloud call
```

### Tiered code review (the routing philosophy applied to review)
Not every module deserves the same review cost:
| Module class 模块类别 | Reviewer 审查者 | Why 原因 |
|:---|:---|:---|
| **Invariant-bearing** (provenance, PII, identity, reputation) | **DeepSeek cloud** | Real bugs were found here; a general 14B model misses what a specialized code model catches |
| **Routine** (CLI, utilities, docs) | **Local Qwen-14B** | Free, fast, good enough |
| **Vision/TTS output** | **M3 cloud** | Only M3 can judge vision |

This is the same **free → cheap → expensive** routing as the capture pipeline,
applied to the dev loop. It is honest about capability tiers.

### Measurement (G0-style falsification, applied to tooling)
Before trusting local critique, **measure it**: run the same diff through both
local-Qwen-critique and DeepSeek-critique for one sprint. Log which catches
which class of bug. Then we have **data** on whether local critique is good
enough — not assertion. This is the project's own discipline applied inward.

### Provenance boundary (non-negotiable)
System B's output is `ai_generated`. It is **blocked from Labs** by the
provenance gate. The local-bridge tool lives in `tools/local_bridge/` and has
**no import path** to the capture→share pipeline. Grep-verifiable, like
`--skip-blur` not existing.

---

## 8. Phased plan (reconciled with the circle map J → I)

The committed circle order is **J → I** (local LLM before convergence), per
DeepSeek's correction. v1.0's phase plan partially aligned; v2 makes it explicit.

| Phase 阶段 | Circle | Builds | System | Depends on |
|:---|:---|:---|:---|:---|
| **0** | F ✅, G, G0 | Video pipeline + one-command automation + falsification | A | — (G0 done: n=1, 90 pairs, 80% consistency) |
| **1** | **B-new** | Vibe-coding bridge (`tools/local_bridge/`) — Mac Studio Qwen-14B + self-refine | **B** | Nothing — can start now, parallel to A |
| **2** | H | Glasses capture → phone tagging (L0, L0.5 blur, L2 tag) | A | G0 |
| **3** | **J** | Local LLM filter on mobile (L1, 95% discard **+ the 4 mitigations**) | A | H — **discard design doc is a gate** |
| **4** | K | Escalation protocol (L2→L3 confidence switch, two thresholds) | A | J |
| **5** | **I** | Multi-human convergence (L4 share, IPFS) — **needs local tags first** | A | J (reordered) |
| **6** | L, M | Learned taste + autonomous local brain (L5) | A | I, K |

**Why Phase 1 (System B) can start in parallel:** it shares no data path with
System A. It is the fastest way for the founder to feel the local-LLM value
(vibe-coding productivity) while the heavier capture work proceeds. And it
exercises the Mac Studio + Qwen setup that System A's edge escalation will
later reuse.

---

## 9. Open questions for the audit

These are the questions I want DeepSeek + Kimi + Qwen to answer:

- **OQ-1:** Is FrugalRoute a real maintained project or a rename of FrugalGPT?
  Should we depend on it or implement routing ourselves?
- **OQ-2:** Is the System A / System B separation clean enough to guarantee no
  provenance leakage? Where could AI-generated signal still slip into Labs?
- **OQ-3:** Are the two thresholds (0.70 edge / 0.85 cloud) correctly placed,
  given a 1-3B mobile model and M3 cloud? Is the calibration path sound?
- **OQ-4:** Are the four discard mitigations sufficient, or is there a fifth
  failure mode (e.g., adversarial inputs that trick L1 into discarding signal)?
- **OQ-5:** Is the tiered code-review (local Qwen for routine, DeepSeek for
  invariant-bearing) honest about capability, or does it under-review routine
  code that later becomes load-bearing?
- **OQ-6:** Does the self-refine bridge (generate→critique→package→synthesize)
  introduce any risk where the local draft's blind spots propagate into the
  cloud's final answer (anchoring bias)?
- **OQ-7:** Cost model reality check — is "$1.44/day, 99.5% local" achievable
  given real mobile inference latency + the calibration-sample overhead?

---

## 10. What this v2 does NOT do

- Does not replace `HYBRID-EDGE-ARCHITECTURE.md` — it *extends* it with the
  vibe-coding bridge (System B) and the 端-边-云 framing, and reconciles v1.0.
- Does not commit to FrugalRoute as a dependency.
- Does not relax any invariant. §3 System B is provably outside the Labs path.
- Does not estimate a ship date — the circle map gives dependencies, not dates.

The next step is the **3-model audit** (DeepSeek + Kimi + Qwen) against §9's
open questions. Their findings drive v2.1.
