# Local Development Bridge (System B)

A local-first coding assistant that runs an on-device LLM (via Ollama) to do
**generate → blind-critique**. It is System B of the three-system architecture
(`docs/UNIFIED-ARCHITECTURE-v3.md` §6). The commercial app (Goldman) and the
research network (HiveAGI) are the other two.

## The one idea

The critic is **blind**. It sees the task + spec + tests but **not Draft A**
when writing its failure checklist; only after the checklist exists does it
review the draft against it. Models favor their own outputs during
self-evaluation (Huang et al., ICLR 2024); self-critique anchors. The blind
protocol removes the anchor.

## Status: Phase 1 — proof

Per the build plan, the plugin exists only to **prove** the blind critic beats
self-critique on real tasks. If it doesn't, there is no plugin to build. The
router, cloud synthesizer, and runtime-isolation container are deferred until
the proof passes.

## The three invariants (the acceptance gate)

Enforced as tests in `tests/`, runnable with no model:

1. **Blind critic** — `test_critic_blind.py` asserts the checklist-stage prompt
   never contains the draft.
2. **Runtime isolation** — `test_no_system_a_imports.py` asserts this package
   imports nothing from `videogen` or `p2p_exchange` (System A).
3. **ai_generated provenance** — `test_provenance_stamp.py` asserts every
   artifact is stamped `ai_generated` (the plugin never writes to Labs).

## Usage

```bash
# Run the blind-critic loop on one task
python -m tools.local_bridge run "Write a function that ..."

# Run the Phase-1 proof harness (blind vs self-critique on 3 tasks)
python -m tools.local_bridge prove
```

## Layout

```
tools/local_bridge/
  ollama.py        # urllib client (OpenAI-compatible, localhost no-auth); provenance stamping
  generator.py     # Draft A
  critic.py        # failure_checklist() [BLIND] → review_against()
  self_critique.py # BASELINE: the v1 self-critique pattern to beat
  prove.py         # the proof harness (blind vs self, scored vs ground truth)
  cli.py           # run / prove commands
  config.toml      # model + endpoint config (one-line model swaps)
  tasks/           # 3 real tasks with known ground-truth defects
  tests/           # the 3 invariants (no model required)
```

## Config

Models are one-line swaps in `config.toml`. Phase 1 uses **one model**
(`qwen3.6:27b`) for both roles — the critic's blindness carries the
anti-anchoring weight, not a different model family. See
`docs/internal/local-bridge-model-audit.md` for the selection rationale.

## What this does NOT do (yet)

No router (harm-weighted escalation), no cloud synthesizer, no container
isolation, no Labs writes — ever. These return from the build plan once the
proof earns them.
