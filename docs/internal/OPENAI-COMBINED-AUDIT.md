# OpenAI Combined Audit — Capture Network × Local Bridge × Media Factory

> **Audit date:** 2026-08-04.
> **Scope:** treats the edge-cloud v2 architecture and the vibe-coding bridge as
> one long-term platform, not two isolated projects.
> **Overall judgment:** **Proceed, but combine the doctrine — not the data pipelines.**
> **Verdict:** Approve the combined vision with structural changes.
>
> **Source:** OpenAI review, pasted by founder 2026-08-04. Preserved verbatim.

---

## 1. Clear strategic verdict

### Architecture score

| Area | Assessment |
|---|---:|
| Long-term vision | **8.5/10** |
| Conceptual coherence | **7/10** |
| Production architecture | **6/10** |
| Provenance safety | **5/10** |
| Research falsifiability | **7.5/10** |
| Current implementation readiness | **4.5/10** |

The ideas are stronger than the current system boundaries.

Position:
1. Finish the video pipeline first — clearest contracts, shortest route to value.
2. Build the local coding bridge in parallel, but isolated; experimentally compare with cloud review.
3. **Do not activate destructive mobile-frame discarding or public IPFS sharing yet.**
4. Before capture-network expansion: one canonical provenance language, a privacy threat model, calibrated routing, and a discard falsification study.

The project should become a platform containing **three separately governed systems**, not one giant pipeline.

---

## 2. The missing third system

The edge-cloud document defines two systems (A: human capture → Labs; B: local coding bridge). But the phase table assigns the automated video pipeline to System A. **That is a classification error.** System A is human-origin capture eligible for Labs; the video factory uses licensed stock, company-owned media, and potentially AI-generated assets.

### System A — Labs Human-Capture Network
- **Purpose:** Capture authentic human-perspective signals.
- **Permitted origin:** Primarily `human_capture`.
- **Flow:** Glasses → phone → privacy processing → local understanding → uncertain cloud judgment → protected convergence → learning.
- **Primary danger:** Quiet but important human moments discarded, or AI-generated information entering the Labs corpus.

### System B — Local Development Bridge
- **Purpose:** Improve founder/engineering productivity.
- **Permitted origin:** `ai_generated`, human instructions, source code, project documents.
- **Flow:** Task → local draft → independent critique → optional cloud synthesis → developer review.
- **Primary danger:** Anchoring, weak local critique, accidental reuse of generated material in the human-capture dataset.

### System C — Forge Media Factory
- **Purpose:** Produce commercial ExploreChina Holidays media.
- **Permitted origin:** Licensed stock, company-owned media, approved AI-generated visuals, human edits.
- **Flow:** Tour brief → script → asset pool → EDL → composition → finishing → QA → publishing handoff.
- **Primary danger:** Factual travel errors, asset-licence failures, misleading authenticity, visual defects, automated publishing of low-quality result.

This resolves a major contradiction: video assets can legitimately be AI-generated inside Forge while remaining permanently ineligible for Labs.

---

## 3. What may be shared

The three systems may share infrastructure, but not unrestricted data.

### Shared control plane
model registry; provider adapters; cost/latency telemetry; confidence-calibration framework; job orchestration; schema-versioning; audit-event format; secrets management; retry/timeout/circuit-breaker; policy engine.

### Separate data planes
raw capture media; embeddings from private capture; IPFS content; video-production asset pools; coding prompts with private repo content; training/correction datasets; credentials; retention policies; eligibility decisions.

A shared Mac Studio is acceptable. A shared database containing all three systems' records is not.

---

## 4. Critical blocker: provenance is not yet unified

The video plan uses `source: pexels | ai_generated | company_owned`, `licence`, `authenticity: stock | illustrative | documentary`. The edge-cloud plan uses `human_capture`, `ai_generated`, Labs eligibility. Related but **not interchangeable**.

A single `source` string is not enough. Provenance needs at least four independent dimensions:

```text
origin:          human_capture | company_owned | licensed_stock | ai_generated | mixed
transformation:  untouched | cropped | colour_adjusted | narrated | composited | generatively_modified | fully_synthetic
presentation_claim: documentary | representative | illustrative | synthetic
eligibility:     labs_allowed | forge_only | private_dev_only
```

Plus: parent asset IDs; transformation history; model + model version; licence evidence; consent status; human overrides; policy decision + reason; immutable audit timestamp.

**Important correction:** the statement that `videogen/provenance.py` protects the entire Labs boundary is too optimistic. A module in the video repo cannot prove every future path into Labs passes through it. Repo separation + grep checks are not a complete security boundary.

The provenance gate should become a **central policy contract**, enforced at the Labs ingestion endpoint: *No Labs record is accepted unless the Labs ingestion service independently validates its full lineage.* Forge may pre-check eligibility, but Labs must never trust the producer's declaration alone.

---

## 5. Critical blocker: the EDL time equation is inconsistent

The video plan declares voice is the master clock. But three requirements cannot all remain true:
1. every shot duration equals its voice duration;
2. shots use overlapping crossfades;
3. total video duration equals the sum of shot durations.

With overlapping transitions: `T_rendered = Σd_i − Σx_i` (d = shot duration, x = crossfade overlap). When each shot duration equals its voice duration, the rendered video becomes shorter than the complete voice track by total transition overlap.

The validator must not sum shot durations. Instead:
```text
timeline_start[0] = 0
timeline_start[i+1] = timeline_start[i] + shot_duration[i] - transition_overlap[i]
total_duration = max(timeline_start[i] + shot_duration[i])
```

Clean design: voice cue windows non-overlapping; visual shots get transition handles before/after the voice window; `timeline_start_sec` authoritative; validator derives total from positions; source clips need sufficient handle length; audio and visual duration validated separately. **Resolve in H1 before H3.**

---

## 6. The one-command contract is also inconsistent

Stated goal: `python -m videogen produce --tour-url <URL> --out <mp4>`. But the orchestrator needs `brief.yaml` (aspect ratios, language, voice model, library refs, clip hints, branding, platform list, CTA, music mood). A URL cannot provide these reliably.

Canonical interface should be `produce --brief handoff/brief.yaml --out-dir forge-output/<tour-slug>`. A `--tour-url <URL> --preset ech-default` convenience may remain but must generate and preserve an explicit brief showing every default. "One command" should mean one orchestrated entry point — not one opaque, unreplayable black box. Every stage must remain independently replayable.

---

## 7. Confidence routing: good principle, premature thresholds

FrugalRoute correctly treated as unvetted (multiple unrelated/early third-party projects; canonical foundation is FrugalGPT's LLM-cascade). Build a small internal router first; keep the adapter open; evaluate outside routers later.

**0.70 and 0.85 cannot be architectural truths** — initial experimental settings only. Calibration quality is the major bottleneck; calibration-first routing beats fixed thresholds.

The router should use:
```text
decision = f(calibrated_error_probability, consequence_class, privacy_class,
             expected_cost, expected_latency, model_capability, domain)
```

Confidence alone is insufficient. Provenance code must get cloud/human review even at 98% local confidence; a low-impact doc rewrite may stay local at lower confidence; an uncertain face/consent decision goes to a human, not just a larger model.

> **Route according to expected harm, not confidence alone.**

---

## 8. The 95% discard target should be removed

"Discard 95%" is useful as a cost hypothesis, dangerous as a product objective. Once a team is measured against a discard percentage, the easiest way to succeed is to discard aggressively — making cost metrics look excellent while destroying the thesis's most valuable information.

Real optimisation target:
> Minimise computation while keeping the quiet-signal false-negative rate below an empirically justified limit.

The four existing mitigations are strong but need two additions:

**Fifth — event-boundary protection:** quiet frames immediately before/after a detected event retained; meaning often depends on context, not the visually strongest frame.

**Sixth — shadow mode:** for the first study period the filter may label "discard" but must not delete. Compare its decision against later human + cloud review. Only after measuring false negatives is physical deletion enabled.

Monitor: missed meaningful-event rate; missed cultural-marker rate; recall by lighting/environment/event-duration/user/device; model-confidence calibration; % of discarded samples rescued by audit.

---

## 9. IPFS is not yet safe as described

"Only text leaves the device" sounds privacy-protective, but text tags can reveal identity, exact location, relationships, routines, workplaces, sensitive activities, inferred personal characteristics.

IPFS traffic and content are public unless encrypted. The first convergence implementation should **not** publish human-derived tags openly to IPFS Mainnet. Use: client-side encrypted payloads; private/hybrid-private nodes; access-control gateways; rotating group keys; pseudonymous node identifiers; subject-consent metadata; expiry/retention policies; a revocation index; separate public aggregates with no person-level information.

A CID is not a revocable database record — independently retained copies may remain outside the original node's control.

Open research question:
> **What is the smallest shareable unit that still enables convergence without exposing an identifiable human event?**

That may be a locally aggregated feature, signed claim, or privacy-preserving count — not a natural-language tag.

---

## 10. Correct the MiniMax model map

"M3 handles vision, VO and TTS" mixes a provider with separate models. MiniMax M3 is a multimodal/coding/agentic model; TTS uses `speech-2.8-hd`.

```text
Provider: MiniMax
Capabilities:
  multimodal_reasoning -> MiniMax-M3
  text_to_speech       -> speech-2.8-hd
  video_generation     -> selected Hailuo model
  music_generation     -> selected music model
```

Cost, failure modes, credentials, rate limits, version changes occur per model, not per provider. Model assignments should be configuration-driven, not hard-coded.

---

## 11. The local coding bridge is good, but needs an independent critic

Self-refine is legitimate. But sending a local draft and its own critique to the cloud can anchor the cloud to the local framing; models may favour their own outputs during self-evaluation.

A safer bridge:
1. Local generator produces Draft A.
2. Independent local critic sees the task, specification, tests — **but initially does not see Draft A.**
3. Critic writes a failure checklist and expected solution properties.
4. Then reviews Draft A against that checklist.
5. For difficult work, generate an independent Draft B.
6. Cloud synthesis receives original task + evidence + tests + both candidates + independent critique.
7. Executable tests determine success wherever possible.

For invariant-bearing code, the cloud reviewer should perform an independent cold review, not merely refine the local answer.

---

## 12. QA must not be entirely self-referential

If the same model family influences tagging, selection, and final QA, correlated blind spots may pass through all stages. Three layers:

**Deterministic:** duration; black-frame; silence/clipping; subtitle timing; safe-area bounds; logo presence; output resolution; codec/bitrate; provenance completeness; file readability.

**Model-based:** visual relevance; obvious synthetic defects; subtitle legibility; audience fit; visual-brand consistency.

**Independent sample audit:** second model or human reviews a sample; factual claims checked against tour brief + verified library references; disagreements stored as calibration data.

A model score must not override a deterministic provenance failure.

---

## 13. Better acceptance criteria for the media factory

"Greater than 70% QA PASS rate" is not enough — may reward a lenient judge. Phase-one acceptance: 100% asset-lineage completeness; zero unknown schema versions; zero ungrounded destination/itinerary claims; rendered duration within tolerance; zero subtitle safe-area violations; reproducible rerun; median human correction time; first-pass QA rate; autofix rate; human rejection rate; cost per accepted video; override count by category; publish-package completeness.

Most meaningful business metric:
> **Human minutes required per accepted, publishable video.**

---

## 14. Recommended build sequence

**Gate 1 — Constitutional foundation:** define Systems A/B/C; canonical provenance schema; Labs ingestion policy; resolve EDL time equation; brief as canonical video input; model registry + capability names; trust boundaries + storage separation.

**Gate 2 — Forge Media Factory:** EDL schema+validator; synthetic timeline tests; URL ingestion; voice generation; EDL-driven composition; deterministic QA; model-based QA; seam contract tests; reproducibility package; human-review logging.

**Gate 3 — Local Development Bridge:** `tools/local_bridge/`; no Labs dependency; local generator; blind critic; cloud escalation; model+cost logging; executable evaluation; ai_generated provenance marking.

**Gate 4 — Capture without destructive filtering:** glasses capture; on-device privacy; local tagging; consent indicators; encrypted local event vault; human correction interface. Filter may classify but nothing is deleted yet.

**Gate 5 — Discard falsification:** measure filter against retained ground truth. Enable destructive discard only when quiet-event recall acceptable, calibration stable, temporal floor works, override rules work, discard audits detect regression.

**Gate 6 — Protected convergence:** encrypted private network; controlled participants; pseudonymous records; no public NL event tags; revocation/retention testing; poisoning + duplicate detection.

**Gate 7 — Learning:** only after trusted convergence.

---

## 15. Study and experiment plan

**Study A — Video reproducibility:** run tours multiple times; measure visual-selection variance, factual consistency, cost variance, QA disagreement, human correction time, provenance failures, duration drift. Goal: stable editorial quality + factual meaning, not identical pixels.

**Study B — Local-versus-cloud code review:** one sprint, same changes independently to local Qwen / DeepSeek / human; don't let reviewers see each other's output; classify defects (correctness, security, privacy, maintainability, performance, contract drift, docs). Establishes which modules local review may approve.

**Study C — Confidence calibration:** labelled examples per routing domain (coding, visual judgment, frame retention, factual extraction, subtitle QA); measure calibration error, false-negative rate, escalation rate, cost, latency, domain-shift performance. Each model+task gets its own profile.

**Study D — Discard counterfactual:** for every "discard" frame, retain a stratified sample (low-light, slow-motion, culturally subtle); humans + independent model identify missed meaning. Key metric: **meaning lost per compute unit saved**, not percentage discarded.

**Study E — Provenance penetration test:** deliberately inject AI tags into Labs; modified stock marked documentary; unknown source type; missing parent lineage; altered consent metadata; unsupported schema version; data crossing through logs/caches/embeddings. System should fail closed + produce audit record.

**Study F — Convergence attack simulation:** before real multi-human sharing, simulate duplicate contributors, Sybil nodes, coordinated false tags, replayed old events, model-generated synthetic consensus, one high-volume node overwhelming many low-volume humans. A distributed human-perspective network requires a theory of **adversarial convergence**, not only technical transport.

---

## 16. The larger vision

Three reinforcing engines:
```text
System C — Media Factory   → commercial output + revenue
System B — Dev Bridge       → lower cost/time to build the platform
System A — Capture Network  → differentiated long-term thesis
```

The defensible asset is not IPFS, glasses, local Qwen, or any cloud model. Those are replaceable. The defensible asset is:
> **An audited judgment system that records origin, uncertainty, correction, human override and failed assumptions.**

Three separate judgment ledgers: editorial (media), engineering (code), human-perspective (Labs). Share methods, not raw truth claims.

The strongest next artifact is a **v3 unified architecture document** replacing the two-system model with this three-system structure and explicit build gates.
