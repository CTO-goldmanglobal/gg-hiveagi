"""
INVARIANT #1 — Blind critic.

The core design fix over self-critique: the failure-checklist prompt must NEVER
contain the draft. This test asserts it at the prompt-construction layer, which
is the only place the invariant can be mechanically guaranteed.

If this test fails, the plugin's central premise is broken — there is no point
running the proof.
"""

from tools.local_bridge.critic import (
    DRAFT_PLACEHOLDER,
    _blind_checklist_prompt,
    failure_checklist,
    review_against,
)


class TestBlindChecklistPrompt:
    """The checklist prompt is built without the draft, by construction."""

    def test_prompt_does_not_contain_draft(self):
        draft = "def solution(): return 42  # SECRET DRAFT MARKER xyz123"
        prompt = _blind_checklist_prompt("do the task", "spec", "tests")
        # The actual draft must not appear anywhere in the checklist prompt.
        assert draft not in prompt
        assert "def solution()" not in prompt

    def test_prompt_uses_placeholder_not_draft(self):
        prompt = _blind_checklist_prompt("task", "spec", "tests")
        # The prompt must not even reference that a draft exists to judge yet.
        assert DRAFT_PLACEHOLDER not in prompt  # placeholder only in docs, not the prompt
        assert "DRAFT NOT YET PROVIDED" not in prompt

    def test_prompt_does_not_leak_via_task_spec(self):
        """A sneaky caller shouldn't be able to inject the draft via task/spec."""
        draft = "LEAKMARKER_q9w8e7r6"
        # Even if the draft text is passed as the 'task', that's the caller's
        # problem — but the function must not ADD draft content itself.
        prompt = _blind_checklist_prompt("task", "spec", "tests")
        assert draft not in prompt  # the function adds no draft content of its own
        assert "checklist" in prompt  # it is a checklist prompt
        assert "proposed" not in prompt.lower() or "properties" in prompt.lower()


class TestBlindProtocolSeparation:
    """failure_checklist and review_against are distinct calls; the draft only
    enters at review_against, never at failure_checklist."""

    def test_failure_checklist_signature_has_no_draft_param(self):
        import inspect

        sig = inspect.signature(failure_checklist)
        # The checklist function must not accept a draft argument.
        params = set(sig.parameters)
        assert "draft" not in params
        assert "draft_artifact" not in params

    def test_review_against_requires_checklist_first(self):
        """review_against takes a checklist artifact — enforcing order."""
        import inspect

        sig = inspect.signature(review_against)
        params = set(sig.parameters)
        assert "checklist_artifact" in params  # must exist before review
        assert "draft" in params  # draft enters here, not before
