"""
INVARIANT #2 — Runtime isolation from System A (the Labs / capture pipeline).

"No import path" is a compile-time guarantee: tools/local_bridge/ must import
NOTHING from ``videogen`` (the capture pipeline + the provenance gate) or
``p2p_exchange`` (the Labs sharing layer). This is v3 §6's isolation rule.

This test parses the package's source files and asserts none of them import
from the forbidden roots. (It checks source text rather than importing, because
importing would execute the modules and could mask a dynamic import.)
"""

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]  # tools/local_bridge/
# System A = the Labs / capture pipeline. videogen holds the capture pipeline
# AND the provenance gate; p2p_exchange is the Labs sharing layer.
FORBIDDEN_ROOTS = ("videogen", "p2p_exchange")


def _imported_top_levels(source: str) -> set[str]:
    """Return the set of top-level module names imported by ``source``."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            # absolute imports only (relative imports like `from . import x`
            # stay inside the package and cannot reach System A)
            names.add(node.module.split(".")[0])
    return names


def _package_py_files() -> list[Path]:
    return [p for p in PKG.rglob("*.py") if "__pycache__" not in str(p) and "tests" not in p.parts]


class TestNoSystemAImports:
    def test_no_imports_from_system_a(self):
        offenders: list[str] = []
        for py in _package_py_files():
            source = py.read_text(encoding="utf-8")
            imported = _imported_top_levels(source)
            bad = imported & set(FORBIDDEN_ROOTS)
            if bad:
                offenders.append(f"{py.relative_to(PKG)}: imports {sorted(bad)}")
        assert not offenders, (
            "ISOLATION VIOLATION — tools/local_bridge imports from System A:\n  "
            + "\n  ".join(offenders)
            + "\nThis breaks invariant #2 (v3 §6). The plugin must not depend on "
            "the Labs/capture pipeline at runtime."
        )

    def test_provenance_is_self_contained(self):
        """Specifically: the provenance stamping does not reach into videogen.

        We do not import videogen.provenance; we re-declare the tag locally so
        the isolation boundary holds. (Parity with videogen's gate is a Phase-2
        concern, asserted there, not here.)
        """
        ollama_src = (PKG / "ollama.py").read_text(encoding="utf-8")
        # The provenance tag is declared locally.
        assert 'AI_GENERATED = "ai_generated"' in ollama_src
        # And videogen is not imported to get it.
        assert "videogen" not in _imported_top_levels(ollama_src)

    def test_forbidden_roots_defined(self):
        # Sanity: the test itself knows what it's guarding against.
        assert "videogen" in FORBIDDEN_ROOTS
        assert "p2p_exchange" in FORBIDDEN_ROOTS
