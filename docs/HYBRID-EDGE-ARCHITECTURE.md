# HiveAGI Hybrid Edge Architecture

> The philosophy and design for a human-cognition-inspired system where
> cheap local filters (mobile + glasses) process most input, escalating only
> uncertain cases to expensive cloud models. The result: privacy-first,
> low-cost, always-on human-perspective capture that shares only compact tags.

---

## The philosophy

A human brain runs on 20 watts — the power of a dim lightbulb. It understands
the world not by processing every pixel, but by **filtering**: 99% of visual
input never reaches consciousness. Only what's significant gets attention.
Then language — a very compact representation — carries that significance to
memory, to other humans, to the future.

HiveAGI should work the same way:

```
THE HUMAN WAY                    THE HIVEAGI WAY
(20 watts)                       (hybrid edge-cloud)

Eyes capture everything          Glasses capture everything
       ↓                                ↓
Brain filters (99% discarded)    Mobile LLM filters (cheap, local)
       ↓                                ↓
Only significant moments         Only significant moments → tagged
reach consciousness                    ↓
       ↓                          Significant enough to need
Language (compact)               big-brain reasoning?
→ tell someone                   → YES: escalate to cloud (MiniMax M3)
→ write it down                  → NO: handle locally (done, tag it)
→ remember it                          ↓
                                 Tag flows to Obsidian vault
                                 → shared via IPFS bridge
```

The system doesn't share raw experience. It shares **tags** — compact
representations of what mattered. Like humans share language, not raw
consciousness.

---

## The four-layer brain

Each layer is cheaper than the last. Each filters for the next. The expensive
layer (cloud) only sees what the cheap layers (local) couldn't handle.

### Layer 0: Capture (glasses) — passive sensor, ~0 compute

```
Sees everything. Keeps nothing.
Continuous video/photo stream to the paired mobile device.
No processing happens here — just raw capture.
```

Hardware: AI glasses (camera + Bluetooth/WiFi to phone)

### Layer 1: Filter (mobile, tiny LLM 1-3B) — the attention layer

```
"Is anything happening?"

Receives continuous stream from glasses.
Discards 95% (sidewalk, ceiling, nothing changing).
Tags the 5% that matters: "person approaching," "interesting building,"
"sudden light change," "text on sign."

This is the ATTENTION layer — like human peripheral vision.
It decides what enters consciousness.

Cost: 1-3B params running on phone (CoreML/MLX/ONNX Runtime)
Privacy: 95% of data discarded on-device, never uploaded
Latency: instant (local processing)
```

Model candidates: Phi-3-mini (3.8B), Qwen2.5-1.5B, Llama-3.2-1B, GLM-Edge series

### Layer 2: Understand (mobile or cloud, 3-30B) — the salience layer

```
"What is this? Why does it matter?"

Takes significant moments from Layer 1.
Produces structured tags:
  shot_type: architecture
  mood: dramatic
  subject: temple entrance at golden hour
  commercial_grade: professional
  trigger: aesthetic_gaze

Confident? → tag + store to Obsidian vault (done)
Uncertain? → escalate to Layer 3

This is the SALIENCE layer — like human conscious attention.
It decides what something IS and whether it needs deeper thought.

Cost: 3-30B params (GLM-4.7-Flash 3B-active if local, or cloud API)
Privacy: 90%+ handled locally, ~10% escalated
Latency: local = instant, escalation = 1-3s
```

### Layer 3: Reason (cloud, large LLM) — the reflection layer

```
"This is significant AND complex. Deep analysis needed."

Only for the 5-10% that Layers 1+2 couldn't handle confidently.
Example: "Is this Terracotta Warrior or a replica? What era?
Is this appropriate for a tourism reel? What story does it tell?"

MiniMax M3 or equivalent large model.
Returns deep structured analysis → stored in vault.

This is the REFLECTION layer — like human deliberate thinking.
Slow, expensive, used sparingly.

Cost: MiniMax M3 API (~$0.01 per call)
Privacy: only the uncertain frame + context is uploaded
Latency: 2-5s per call
Volume: ~5-10% of significant moments
```

### Layer 4: Share (IPFS bridge) — the network layer

```
Package tags into Seed Packages.
Share with the network via content-addressed exchange.
Convergence measured across nodes.

Cost: ~0 (text tags only — compact)
Privacy: tags only, no raw media
```

---

## The cost model

```
SCENARIO: 8 hours wearing glasses, walking through Beijing

NAIVE (all cloud):
  Every frame → MiniMax M3 API
  ~28,800 frames (1fps × 8hrs)
  ~$2-3/day API cost
  28,800 frames uploaded (privacy problem)
  Latency on every decision

HYBRID (edge-first):
  Glasses → mobile processes locally
  Layer 1 (1B model on phone):
    95% of frames: "nothing" → discard (FREE)
    5% (~1,440): "something" → pass to Layer 2

  Layer 2 (3B model on phone):
    90% of significant moments: confident tag → store (FREE)
    10% (~144): uncertain → escalate to cloud

  Layer 3 (MiniMax M3 cloud):
    ~144 calls × ~$0.01 = ~$1.44 for the FULL DAY

  TOTAL: ~$1.44 vs ~$3.00 (50%+ savings)
  PRIVACY: 99.5% of frames never leave the phone
  SPEED: local decisions are instant
  BANDWIDTH: ~144 frames + ~1,440 text tags uploaded (not 28,800 frames)
```

Over a month: ~$43 vs ~$90 per contributor. Over 100 contributors: ~$4,300
vs ~$9,000. The savings scale linearly, but the privacy improvement is
absolute — 99.5% local.

---

## The escalation protocol

The key decision: **when does the local brain ask the cloud brain for help?**

```
Local model sees a frame.
  ↓
Produces tag + confidence score (0.0 - 1.0)
  ↓
confidence ≥ 0.85?
  ├── YES → tag stored, done (auto-approve)
  ├── NO, 0.50-0.85 → escalate to cloud M3 for analysis
  └── NO, <0.50 → also flag for human review (might be important)
```

This is the **same 0.85 threshold** from the video pipeline — applied at the
edge. The local brain auto-handles confident cases and escalates uncertain
ones. Over time, as the local model accumulates judgments from the vault, its
confidence rises and fewer escalations are needed.

### What gets escalated (examples)

| Situation | Local says | Confidence | Action |
|:---|:---|:---|:---|
| Temple entrance, clear daylight | "architecture, serene, professional" | 0.92 | Store locally ✓ |
| Unusual street food stall | "food, unknown, uncertain grade" | 0.61 | Escalate to M3 |
| Blurry dark alley | "unclear, low quality" | 0.30 | Discard (not worth cloud cost) |
| Famous landmark, crowded | "landscape, epic, broadcast" | 0.95 | Store locally ✓ |
| Something moving fast | "action, unclear subject" | 0.45 | Escalate + flag human |
| Duplicate of what was tagged 5 min ago | "duplicate, discard" | 0.88 | Discard ✓ |

The local brain becomes smarter over time — it learns what THIS contributor
findains significant, and stops escalating cases it's seen before.

---

## The local model choice

The mobile needs a model small enough to run on a phone but smart enough to
make reliable filter/understand decisions.

| Model | Size | Active params | Phone-ready? | Notes |
|:---|:---|:---|:---|:---|
| Llama-3.2-1B | 1B | 1B | ✅ Now | Fast, basic filtering |
| Qwen2.5-1.5B | 1.5B | 1.5B | ✅ Now | Good multilingual (Chinese) |
| Phi-3-mini | 3.8B | 3.8B | ⚠️ Tight | Better reasoning |
| GLM-4.7-Flash (MoE) | 30B | ~3B active | 🔬 Research | CompactionRL-trained, best fit |
| Mage-VL 4B | 4B | 4B | 🔬 Research | Vision-native (Microsoft) |

**Phase 1 recommendation:** Qwen2.5-1.5B for the filter layer (multilingual,
small, proven on mobile via MLX/ONNX). Upgrade to GLM-4.7-Flash when MoE
mobile inference matures.

---

## The beautiful parallel: seed to wave

```
SEED     = one human's local brain, filtering their experience
RIPPLE   = their tags shared to one other brain
WAVE     = convergence across many brains, each filtering locally,
           escalating only uncertain cases, sharing only compact tags

The wave is built from TAGS, not from raw experience.
Tags are the compact representation — like language.
Humans don't share raw consciousness. We share words.
HiveAGI nodes don't share raw video. They share tags.
```

---

## What exists vs what this needs

| Component | Role | Status |
|:---|:---|:---|
| `llm_wiki_engine/` | Layer 2-3 processing (cloud) | ✅ Working |
| Obsidian vault | Layer 4 memory | ✅ Structure built |
| `p2p_exchange/` | Layer 4 sharing | ✅ Working |
| `videogen/clip_pool/` | Tagging vehicle (video) | ✅ Working |
| Mobile capture app | Layer 0-1 (glasses + phone filter) | ❌ Not built |
| Tiny LLM on mobile | Layer 1 filter | ❌ Not built |
| Escalation protocol | Layer 2→3 switch | ❌ Not built |
| Confidence scoring | Auto-approve threshold | ❌ Not built |
| Convergence measurement | Wave detector | ❌ Not built |
| Continuous learning loop | Edge model updates from cloud | ❌ Not built |
| Model distribution pipeline | Push updated models to phones | ❌ Not built |
| Secure raw clip storage | Encrypted local retention | ❌ Not built |

**7 of 14 components exist.** The missing 7 are the edge layer — everything
between the glasses and the cloud. (Added 3 gaps per DeepSeek review:
continuous learning, model distribution, secure storage.)

---

## DeepSeek review findings (2026-07-30)

### What DeepSeek confirmed
- The four-layer cognitive model is sound
- Qwen2.5-1.5B is suitable for first mobile model (Phi-3-mini or Gemma2-2B
  as alternatives if quantization allows)
- The architecture is viable

### What DeepSeek corrected
1. **Threshold too high for edge:** 0.85 is for large cloud models. A 1-3B
   mobile model should start at **0.70-0.75**, calibrated upward.
2. **Circle order:** J (local LLM) must come BEFORE I (convergence), not
   after. The local filter must produce reliable tags before convergence can
   be measured. Reordered.
3. **Missing pieces identified:**
   - Continuous learning mechanism (edge model improves from cloud feedback)
   - Model update distribution (how to push better models to phones)
   - Secure raw clip storage (encryption at rest for retained frames)
   - UX design for the contributor experience

### The hardest engineering problem
> "Achieving low-latency, accurate on-device inference while handling
> edge-cloud handoff in the escalation protocol."

The escalation protocol is the crux — the moment where the local brain says
"I'm not sure, ask the cloud." Getting this right means:
- Fast local inference (CoreML/MLX/ONNX optimization)
- Reliable confidence estimation (the model must know when it doesn't know)
- Smooth handoff (upload frame + context, get analysis back, store)
- Graceful degradation (if cloud is unavailable, tag locally with lower
  confidence and flag for later review)

### DeepSeek's verdict
> "The architecture is viable but requires reordering of phases and heavy
> focus on mobile engineering."

---

## Circle mapping (the path from here to there)

**Reordered per DeepSeek review (2026-07-30):** J (local LLM) must precede I
(multi-human convergence) because the local LLM generates the tags that nodes
share. Without the local filter producing reliable tags, convergence
measurement has no signal to measure.

| Circle | What | Brain layer | Depends on | Status |
|:---|:---|:---|:---|:---|
| **F** ✅ | Video pipeline (clip selection) | Layer 3 (cloud only) | — | Done |
| **G** | One-command automation | Layer 3 (cloud only) | F | Building |
| **G0** | Falsification (pairwise, multi-human) | Layer 3 | F | Next |
| **H** | Glasses capture → phone tagging | Layer 0-2 | G0 | Planned |
| **J** | Local LLM filter on mobile | Layer 1-2 | H | Planned |
| **I** | Multi-human convergence | Layer 4 | J (needs local tags first) | Planned |
| **K** | Escalation protocol (edge→cloud) | Layer 2-3 switch | J | Planned |
| **L** | Performance prediction (learned taste) | Layer 2-3 | I, K | Planned |
| **M** | Fully autonomous local brain | All layers | L | Vision |

**Key reorder:** J → I (not I → J). The local LLM must produce reliable tags
before convergence can be measured across nodes. DeepSeek correctly identified
this dependency.

**Threshold correction:** 0.85 is too high for a 1-3B model. Start at
**0.70-0.75** for the edge filter, calibrate upward as the model accumulates
judgments. The 0.85 threshold stays for the cloud-side auto-approve (Circle G)
where MiniMax M3 (a much larger model) is making the call.

**Circle M is the destination:** a mobile node that runs its own tiny LLM,
filters glasses input, escalates only uncertain cases, shares compact tags,
and contributes to the convergence wave — all privately, cheaply, continuously.

---

## What full autonomy means (again, precisely)

**Not:** the system replaces human judgment.
**But:** the system handles 95% of input locally, escalates 5% to cloud,
and surfaces 0.5% to the human — only the cases where the local brain
is genuinely uncertain.

The human becomes an **exception handler** for their own perspective system.
They train it (through judgments), it learns, and over time it needs them
less — but the override signal (when the human corrects the system) becomes
MORE valuable, not less, because each correction is a high-signal event.

---

## Sources and inspirations

- **Human cognition:** attention filtering, salience, deliberate reasoning
- **CompactionRL (GLM-4.7-Flash):** small models that learn what to keep
- **Mage-VL (Microsoft):** vision-native models with streaming gates
- **Colibrì:** MoE expert-loading for running huge models on limited RAM
- **The Living Seed:** local brains share tags through a bridge
- **The founder's insight:** "seed to fruit takes sun, water, food — share the seed"
