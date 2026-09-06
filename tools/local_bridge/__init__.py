"""
Local Development Bridge — System B of the three-system architecture.

A local-first coding assistant that runs an on-device LLM (via Ollama) to do
generate → blind-critique → package. The critic sees the task + spec + tests
but NOT the draft when writing its failure checklist; only after the checklist
exists does it review the draft against it.

INVARIANTS (the acceptance gate — enforced in tests/):
  1. Blind critic — the checklist-stage context never contains Draft A.
  2. Runtime isolation from System A — this package imports NOTHING from
     ``videogen`` or ``p2p_exchange`` (the Labs / capture pipeline). That is a
     compile-time guarantee, asserted by test_no_system_a_imports.py.
  3. ai_generated provenance — every artifact this package produces carries an
     ``ai_generated`` tag. The plugin never writes to the Labs data plane.

See docs/UNIFIED-ARCHITECTURE-v3.md §6 and docs/THE-SEED-DOCTRINE.md §6.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
