# Plugin Build — Handoff for a New Chat

> **You are starting a fresh chat to build the Plugin (vibe-coding tool).**
> This handoff is self-contained: read it, then read the two files it points to,
> and you have everything. Do not re-read the whole repo.
>
> **Date:** 2026-08-05. **From:** main agent. **To:** the chat that builds the plugin.

---

## 1. What the plugin is — in one paragraph

The plugin is a **local-first coding assistant** that runs an on-device LLM
(Qwen-14B/32B via Ollama on a Mac Studio) to do *generate → blind-critique →
package → optional cloud-escalate*. The local model drafts an answer, an
**independent critic** (which has NOT seen the draft) writes a failure
checklist, then reviews the draft against it, and the result either ships
locally ($0) or escalates to a cloud model (GLM/DeepSeek) for final synthesis.
It lives at `tools/local_bridge/`. It is **System B** in the three-system
architecture — the commercial application (Goldman) and the research network
(HiveAGI) are the other two.

## 2. The five things you must get right (the invariants)

These come from two external audits (DeepSeek + OpenAI). Violating any one
ships a known defect.

1. **Blind critic, not self-critique.** The critic sees the task + spec +
   tests, but NOT Draft A, when writing its failure checklist. Only after the
   checklist exists does it review the draft. Models favor their own outputs;
   self-critique anchors. This is the core design fix over the v1 "self-refine"
   idea. (OpenAI audit §11; doctrine §6.)

2. **Runtime isolation from System A (Labs).** "No import path" is a
   compile-time guarantee only. The plugin must run in a separate container /
   process boundary from the capture pipeline, with separate storage namespace,
   separate logs, separate config. A runtime test asserts the plugin cannot
   read System A's storage. (DeepSeek audit; v3 §6.)

3. **All output is `ai_generated`.** Every artifact the plugin produces —
   drafts, critiques, packaged prompts, code suggestions — carries
   `ai_generated` provenance. It is **hard-blocked from Labs** by
   `videogen/provenance.py::is_labs_eligible()`. The plugin never writes to the
   Labs data plane. Grep-verifiable: `tools/local_bridge/` imports nothing from
   `videogen/clip_pool/`, `p2p_exchange/`, or the Labs path. (Doctrine §5; v3 §3.)

4. **Invariant-bearing code always gets cloud review.** The plugin's own
   tiered-review routing sends any code touching auth, provenance, PII,
   crypto, or filesystem to DeepSeek cloud — regardless of local confidence.
   Local Qwen review is for routine modules only. (OpenAI audit §7, §11; v3 §6.)

5. **Route by expected harm, not confidence alone.** The escalation threshold
   is not a fixed 0.70/0.85 — it is a function of consequence class, privacy
   class, cost, and capability. A confident local answer on provenance code
   still escalates; a low-confidence local answer on a doc tweak may not.
   (OpenAI audit §7; v3 §7a.)

## 3. The loop to build

```
1. RECEIVE task (raw — typed or spoken, often casual)
2. LOCAL GENERATOR (Qwen-14B) → Draft A
3. LOCAL CRITIC (Qwen-14B, blind — no Draft A) → failure checklist
   + expected solution properties
4. CRITIC reviews Draft A against the checklist → annotated defects
5. DECIDE:
   - routine task, low harm, critic passes  → ship locally ($0)
   - difficult, or invariant-bearing, or critic fails
     → optionally generate Draft B (independent)
     → package (task + draft(s) + checklist + critique)
     → send to cloud (GLM or DeepSeek) for synthesis
6. EXECUTABLE TESTS determine success wherever possible
7. LOG: model used, cost, latency, decision reason, outcome
```

## 4. Where it lives

```
tools/local_bridge/
  __init__.py
  generator.py      # Draft A (local Qwen via Ollama)
  critic.py         # blind failure checklist + draft review
  router.py         # harm-weighted escalate-or-ship decision
  synthesizer.py    # cloud escalation (GLM/DeepSeek via existing adapter)
  provenance.py     # tags every output ai_generated (thin wrapper on videogen.provenance)
  cli.py            # `python -m tools.local_bridge <task>`
  runtime_isolation/  # container config + storage boundary
  tests/
    test_critic_blind.py    # asserts critic never sees draft before checklist
    test_provenance.py      # asserts all outputs ai_generated
    test_isolation.py       # asserts no read access to System A storage
    test_router.py          # harm-weighted routing cases
```

**Reuse, don't rebuild:** the cloud-call pattern already exists in
`tools/code_review/review.py` (urllib, OpenAI-compatible, keychain/.env
resolution) and `tools/audit/council.py` (multi-provider, truncation-handling).
The plugin's `synthesizer.py` should adapt one of these, not start fresh.

## 5. Build order (small circles)

1. **`generator.py` + `critic.py` + a CLI that runs the loop end-to-end on one
   task.** No routing, no cloud. Prove the blind-critic pattern produces better
   defects than self-critique on 3 real tasks. *(If it doesn't, stop and
   reconsider — the whole plugin depends on this.)*
2. **`router.py`** — harm-weighted escalate decision. Start simple
   (consequence_class × confidence), calibrate later.
3. **`provenance.py`** — every output tagged `ai_generated`. Wire to
   `videogen/provenance.py`.
4. **`runtime_isolation/`** — container + storage boundary. Runtime test
   asserts no System A access.
5. **`synthesizer.py`** — cloud escalation, adapter reused from
   `tools/code_review/` or `tools/audit/`.
6. **Tests for all five invariants** (§2) — these are the acceptance gate.

## 6. What to measure (Study B, from the audits)

Before trusting the plugin as a default workflow, run **Study B**: for one
sprint, send the same changes independently to local-Qwen-critique and
DeepSeek-cloud-critique (reviewers blind to each other). Classify defects
caught (correctness / security / privacy / maintainability / contract drift).
The bar for "local review is safe on routine modules" is roughly: *local
catches ≥80% of what cloud catches on routine modules; cloud always reviews
invariant-bearing modules.* Until that data exists, the plugin is experimental,
not default.

## 7. The two docs to read before coding

- **`docs/THE-SEED-DOCTRINE.md`** — §6 (serendipity's place) and §5 (label
  honestly, never forbid discovery, keep the seed the strongest attractor).
  The plugin is the doctrine's serendipity path made into a tool. Read §6.
- **`docs/UNIFIED-ARCHITECTURE-v3.md`** — §6 (System B, the blind-critic fix,
  runtime isolation) and §3 (provenance, `ai_assisted_meta`). These define the
  constraints.

Everything else (the OpenAI audit, the DeepSeek verdict, the v2) is context
you do not need to build the plugin. The doctrine and v3 §6 are the spec.

## 8. What to say when you start

Don't ask "what should I build?" — §3 and §5 above are the spec. Open with:
the five invariants are the acceptance gate; I'm starting with the blind-critic
loop (step 1) and will prove it produces better defects than self-critique on
three real tasks before building anything else. Then do it.

The plugin's value is not in existing. It is in *the blind critic producing
defects self-critique missed*. Prove that first, or there is no plugin to build.
