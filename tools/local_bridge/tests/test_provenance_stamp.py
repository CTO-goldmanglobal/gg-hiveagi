"""
INVARIANT #3 — ai_generated provenance.

Every artifact the plugin produces carries an ``ai_generated`` tag. The plugin
is hard-blocked from Labs by videogen/provenance.py::is_labs_eligible() — but
this package must do its part: stamp every output so the downstream gate has
something honest to read.

This test asserts the stamping at the ``ollama.chat`` layer (where every artifact
is built) and that the tag is Labs-ineligible by construction (matches the
``ai_generated`` prefix that is_labs_eligible rejects).

No model required — this is a structural test of the stamping machinery.
"""

from tools.local_bridge import ollama
from tools.local_bridge.ollama import AI_GENERATED, PROVENANCE_TAG


class TestProvenanceStamp:
    def test_tag_is_ai_generated(self):
        assert PROVENANCE_TAG.startswith(AI_GENERATED)
        assert "local_bridge" in PROVENANCE_TAG

    def test_tag_is_labs_ineligible_prefix(self):
        """The tag's prefix is exactly 'ai_generated' — the prefix
        videogen.provenance.is_labs_eligible rejects. We re-declare the literal
        here (not import videogen — isolation) to assert the match.

        If this literal ever drifts from videogen's SOURCE_AI, a Phase-2 parity
        test will catch it; here we only assert self-consistency.
        """
        prefix = PROVENANCE_TAG.split(":", 1)[0]
        assert prefix == "ai_generated"

    def test_stamp_attaches_provenance(self):
        """_stamp must put the provenance tag on every artifact."""
        art = ollama._stamp(
            role="test",
            model="m",
            raw="r",
            parsed=None,
            latency_s=0.1,
        )
        assert art["provenance"] == PROVENANCE_TAG
        assert art["provenance"].startswith("ai_generated")

    def test_failed_call_is_still_stamped(self):
        """Even an error artifact must carry provenance — no untagged output
        leaves the package, success or failure. We simulate by calling chat
        against a dead port."""
        art = ollama.chat(
            prompt="x",
            model="qwen3.6:27b",
            base_url="http://127.0.0.1:1",
            timeout=1,
            role="test_should_fail",
        )
        assert "error" in art  # the call failed as expected
        assert art["provenance"] == PROVENANCE_TAG  # but it's still tagged
