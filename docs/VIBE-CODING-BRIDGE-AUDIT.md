# Vibe-Coding Bridge — For LLM Review

> **Self-contained proposal for Kimi / Qwen / any reviewer.** No repo access
> needed. Return the verdict in §7. Date: 2026-08-04. Author: Finn.

## 1. The one idea

A local LLM (Qwen-14B on a Mac Studio, free + private) **optimizes prompts
before they reach the cloud**: it drafts an answer, self-critiques (names 3
defects), then packages "task + draft + defects" as one enhanced prompt for the
paid cloud model. The cloud call is made **only when local confidence is low**.

This is the **self-refine** pattern, placed on a free local model so each paid
cloud call "stands on the shoulders" of a local draft instead of starting cold.

## 2. The loop

```
1. Raw dev task (often casual / incomplete)
2. Local Qwen-14B → structured DRAFT (free, ~3s)
3. Local Qwen-14B → SELF-CRITIQUE: "name 3 defects
   (logic gap, missing edge case, cost/risk)" (free)
4. Package: "task + draft + 3 defects → fix them"
5. confidence HIGH → ship draft ($0)
   confidence LOW  → send package to cloud (1 paid call)
6. Cloud returns an answer that closes the named gaps
   — far better than a cold-start call
```

**Example.** Task: "海外AI客服，担心隐私和延迟". Local draft: basic
microservices + DB. Self-critique finds: (1) no GDPR, (2) no edge distribution,
(3) no cost estimate. Enhanced prompt → cloud → complete plan closing all 3
gaps, in **one** call.

## 3. Why it may beat a single good cloud call

- The local model names defects the human author missed.
- It compresses a 3–5-turn cloud conversation into 1 paid call.
- The raw task stays private; sensitive detail can be redacted locally before
  the cloud sees the enhanced prompt.

## 4. Co-existence with a separate "capture" system (slight overlap)

The same Mac Studio + Qwen also serves a **different** system — a glasses-based
human-perspective capture network (cloud-filtered frames → shared tags). The two
**slightly overlap** and must co-exist:

| | Vibe-coding bridge (this doc) | Capture system |
|:---|:---|:---|
| Purpose | Help the author code faster | Capture human perspective → share |
| Local LLM role | Draft + critique + package | Filter camera frames (95% discard) |
| Cloud role | Final code synthesis | Judge uncertain frames |
| Shares externally? | **No — private dev loop** | **Yes — tags via IPFS** |
| Provenance label | `ai_generated` | `human_capture` |

**The overlap is only infrastructure** (same machine, same model, same routing
philosophy). The data paths do **not** touch. Dev output is `ai_generated` and
is hard-blocked from the research network.

## 5. The boundary (non-negotiable)

The bridge's output (`ai_generated`) is **forbidden from the research network**.
Enforced by separate code paths + provenance labels + a hard gate
(`is_labs_eligible()` returns false for `ai_generated`).

**Open question for reviewers:** is this *static* separation enough, given both
systems share one machine + one model? Or is runtime isolation (separate
containers, storage, model instances) required to truly prevent leakage? Shared
processes, logs, caches, or vector stores can leak across a "no import" boundary.

## 6. Questions for reviewers (answer honestly; do not flatter)

- **VQ-1 (value):** Is draft→critique→package genuinely better than one
  well-crafted cloud call, or just a more elaborate way to write a prompt?
  Where is the real delta — quality, cost, privacy, or speed?
- **VQ-2 (anchoring):** When the draft has a blind spot, does "task + draft +
  defects" *frame-lock* the cloud model, making it less likely to find a
  fundamentally different (better) answer? How would you test this?
- **VQ-3 (capability):** Is Qwen-14B/32B capable of *useful* self-critique on
  real engineering tasks, or will its critiques be shallow/sycophantic? At what
  complexity does local critique stop adding value?
- **VQ-4 (cost):** Is an ~80% local / ~15% edge / ~5% cloud split believable
  for a solo developer's daily coding?
- **VQ-5 (boundary):** Is the static separation enough to keep AI dev output
  out of the human-perspective network? What runtime guarantees are missing?
- **VQ-6 (worst failure):** What is the single most likely failure mode? (e.g.
  local model confidently wrong → critique reinforces error → cloud
  rubber-stamps it.)
- **VQ-7 (overlap):** Is the co-existence framing sound, or papering over a
  real conflict — e.g. the shared model learning patterns from dev tasks that
  bias its capture-pipeline filtering?

## 7. Verdict template

```
{
  "overall_verdict": "valuable | valuable-with-caveats | marginal | not-worth-it",
  "confidence": 1-10,
  "one_line": "...",
  "real_delta": "where it beats a single cloud call (or 'nowhere')",
  "biggest_risk": "...",
  "answers_to_VQs": {"VQ-1": "...", "VQ-2": "...", ...},
  "conditions_for_it_to_be_worth_building": ["..."],
  "would_you_build_this": true/false
}
```

## 8. What this is NOT

Not novel research (self-refine is known). Not part of the thesis (the capture
network is the thesis; this is productivity tooling). Not asking to relax any
provenance invariant. Not committed — a proposal awaiting review.
