# Unified Roadmap — From Seed to Wave

> Every circle, every phase, every dependency — in one document.
> This is the master plan. Everything else is detail.

---

## The vision

> Exploring whether machines can learn human perspective through structured
> judgment — not by scraping data, but by earning it one decision at a time.

A distributed network of local nodes, each processing human input through a
private LLM engine, sharing compact tags through content-addressed exchange,
and measuring convergence as a signal of shared human perspective.

**The wave:** many overlapping loops of development, each complete and
reviewable, building toward a system where 95% of input is processed locally
and only uncertain cases reach the cloud or the human.

---

## Circle map — the full path

```
COMPLETED                          IN PROGRESS                    PLANNED
─────────                          ───────────                    ───────

A Foundation ✅                    G One-command pipeline         H Glasses capture
B Safety ✅                        (H1-H7 build plan)             J Local LLM filter
C Brand ✅                                                        I Multi-human convergence
D Video core ✅                    G0 Falsification               K Escalation protocol
E Selection intel ✅               (pairwise, multi-human)        L Performance prediction
F Full video loop ✅                                              M Autonomous local brain
```

### Phase 1: Foundation (Circles A-F) ✅ Complete

| Circle | What | Key deliverable |
|:---|:---|:---|
| A | Seed Package system + LLM engine + IPFS exchange | Working knowledge network |
| B | PII safety gate + CLA + governance | Code-enforced privacy |
| C | Brand identity (Forge + Labs) | Two-face positioning |
| D | Video pipeline core | Auto-cut from footage |
| E | Selection intelligence | Override signal capture |
| F | Full video loop (Legends of China) | 80s M3-audited deliverable + judgment seed |

**What this proved:** the tag → judge → seed → share loop works end-to-end.
The infrastructure is reusable. Provenance gate keeps stock out of Labs.

### Phase 2: Automation + Validation (Circles G + G0) 🔄 In progress

| Circle | What | Key deliverable | Status |
|:---|:---|:---|:---|
| G | One-command pipeline | `produce --tour-url URL --out FINAL.mp4` | Build plan H1-H7 locked |
| G0 | Falsification experiment | 1,000+ pairwise judgments, 5+ humans, consistency measured | Designed, not started |

**Build plan (G):** EDL schema → timeline (VO master clock) → ingest → produce orchestrator → QA gate → scenedetect → contract tests

**Two-repo seam:** ECH (production) ↔ HiveAGI (pipeline), connected by versioned files (`brief.yaml`, `edl.json`, `result.json`), mocked independently, contract-tested in CI.

### Phase 3: Human Capture (Circles H + J)

| Circle | What | Key deliverable | Depends on |
|:---|:---|:---|:---|
| H | Glasses → phone tagging | Frame SDK app, capture → local tag | G0 |
| J | Local LLM filter on phone | 1-7B model on NPU, 95% input filtered locally | H |

**Hardware:** AI glasses (open SDK, BLE) + phone (12GB+ RAM, NPU). See `HARDWARE-SPEC.md`.

**Architecture:** Four-layer brain — glasses (capture) → mobile LLM (filter) → mobile/cloud (understand) → cloud (reason). See `HYBRID-EDGE-ARCHITECTURE.md`.

**Key principle:** J before I. The local LLM must produce reliable tags before convergence can be measured across nodes.

### Phase 4: Network + Convergence (Circles I + K)

| Circle | What | Key deliverable | Depends on |
|:---|:---|:---|:---|
| I | Multi-human convergence | Cross-node agreement measurement | J |
| K | Escalation protocol | Edge → cloud handoff for uncertain cases | J |

**The wave detector:** when N independent nodes produce similar tags for the same stimulus, convergence is measurable. This is the signal that validates the thesis.

**The escalation protocol:** local brain auto-handles confident cases (≥0.70 edge threshold), escalates uncertain ones to cloud M3. Over time, fewer escalations needed.

### Phase 5: Learning + Autonomy (Circles L + M)

| Circle | What | Key deliverable | Depends on |
|:---|:---|:---|:---|
| L | Performance prediction | Learned taste model, model improves from overrides | I, K |
| M | Autonomous local brain | Fully self-sufficient edge node | L |

**Circle M is the destination:** a mobile node that filters glasses input locally, tags confidently, escalates only genuinely uncertain cases, shares compact tags through the bridge, and contributes to the convergence wave — all privately, cheaply, continuously.

---

## Document map

### Public-facing (GitHub visitors)

| Document | What it is |
|:---|:---|
| `README.md` | Project intro, architecture diagram, quick start |
| `docs/THE-LIVING-SEED.md` | The vision — brain, bridge, flow |
| `docs/LOOP-STRATEGY.md` | The small-circles methodology |
| `docs/LOOP-DIAGRAMS.md` | 6 Mermaid diagrams (circle shape, provenance, coverage) |
| `docs/HYBRID-EDGE-ARCHITECTURE.md` | Four-layer brain, escalation protocol, cost model |
| `docs/HARDWARE-SPEC.md` | Device-agnostic requirements for edge nodes |
| `docs/UNIFIED-ROADMAP.md` | This document — the master plan |
| `PROJECT_MASTER_PLAN.md` | Original P0-P2 roadmap (foundation) |
| `specs/` | Schema, vault, API specifications |
| `CONTRIBUTING.md` | How to contribute, CLA, PII rules |

### Build plans (for Cursor / GLM-5.2)

| Document | What it is |
|:---|:---|
| `docs/CURSOR-HANDOFF.md` | Consolidated handoff: pipeline, bugs, settings, environment |
| `docs/VIDEO-PIPELINE-BUILD-PLAN.md` | H1-H7 build plan with seam contracts |
| `docs/FULLY-AUTOMATIC-FLOW.md` | Target state: one-click to published video |

### Internal (process notes, not public-facing)

| Document | What it is |
|:---|:---|
| `docs/internal/` | Retrospectives, audits, external reviews |
| `docs/internal/EXTERNAL-AUDIT-SYNTHESIS.md` | OpenAI + Claude thesis critique |
| `docs/internal/OPENAI-VIDEO-SKILL-AUDIT.md` | EDL pattern, PySceneDetect, skill landscape |
| `docs/internal/DEEPSEEK-EDGE-REVIEW.json` | Edge architecture review + corrections |

---

## Status summary

| Area | Components built | Components remaining | Phase |
|:---|:---|:---|:---|
| Foundation (Labs core) | 6/6 | 0 | ✅ Complete |
| Video pipeline (Forge) | 7/12 | 5 (ingest, timeline, produce, qa_gate, scenedetect) | 🔄 Phase 2 |
| Edge architecture (glasses + mobile) | 0/7 | 7 (capture app, local LLM, escalation, confidence, convergence, learning, distribution) | 📋 Phase 3-5 |
| Provenance + safety | 2/2 | 0 | ✅ Complete |
| Obsidian wiki | 1/3 | 2 (wiki_export, convergence measurement) | 🔄 Phase 2-4 |

**Total: 16 of 30 components built (53%).**

The next build step is Circle G (H1-H7): the EDL schema, timeline, and produce orchestrator. Both seats can start in parallel.
