# The Living Seed — Architecture Overview

> The design vision that connects every component of Project Hive.AGI.
> This document describes the intended architecture and research direction.

---

## The architecture in one sentence

**Local nodes (Obsidian vault + LLM engine) process human input into structured tags. These tags are shared through content-addressed exchange (IPFS), creating a measurable flow of human preference signals across a distributed network.**

---

## The three layers

### Layer 1: Local Node (private, independently operated)

```
┌─────────────────────────────────────────┐
│           LOCAL NODE                     │
│                                         │
│  Obsidian Vault                         │
│  ├── 00_Inbox/ (raw captures)           │
│  ├── 01_Entries/ (LLM-distilled tags)   │
│  ├── 02_Topics/ (MOCs — cross-links)    │
│  └── 03_SeedPackages/ (ready to share)  │
│                                         │
│  Powered by: llm_wiki_engine            │
│  ├── MiniMax M3 (generate tags)         │
│  ├── DeepSeek V4 Flash (audit tags)     │
│  └── vision.py (frame analysis → tags)  │
│                                         │
│  Active learning (planned):             │
│  "Which comparison teaches the most?"   │
│                                         │
│  Longitudinal tracking (planned):       │
│  "How has this contributor's            │
│   perspective evolved?"                 │
└─────────────────────────────────────────┘
```

Each contributor operates their own node. Their tags, their judgments, their
preferences — processed locally, owned locally. No central server processes
their raw data.

The LLM engine serves as the node's processing layer — it converts raw input
(video frames, glasses captures, phone photos) into structured tags. The
Obsidian vault serves as the node's memory layer, storing and cross-linking
the distilled knowledge.

### Layer 2: Content-Addressed Exchange (shared, verifiable, trustless)

```
         Node A                     Node B                     Node C
        (Sydney)                   (Hong Kong)                (London)
           │                           │                           │
           └───────────┬───────────────┘───────────────────────────┘
                       │
                  IPFS EXCHANGE
              (p2p_exchange/)
                       │
              Seed Packages flow:
              ┌────────────────────┐
              │ seed_yu_20260729/  │
              │  ├── manifest.json │
              │  ├── entries/      │
              │  │  ├── tags       │
              │  │  ├── judgments  │
              │  │  └── reasons    │
              │  └── provenance    │
              └────────────────────┘
```

The exchange layer does not store nodes or raw data. It carries **Seed
Packages** — structured bundles of tags, judgments, and reasons. Each package
is content-addressed (CID), verifiable, and tamper-detectable.

Contributors package their node's structured output into a Seed Package,
publish the CID, and other nodes can import it. No raw media is shared — only
the structured judgments derived from it.

### Layer 3: Convergence Flow (measurable, organic, growing)

```
Seed shared ──→ imported by Node B ──→ B adds tags ──→ B shares back
    │                                                    │
    │         convergence = countable signal             │
    │                                                    │
    ↓                                                    ↓
  Node C imports ──→ C adds tags ──→ C shares ──→ network grows
```

When multiple independent nodes produce similar judgments for the same
stimulus, that convergence is measurable. It is not view counts or engagement
metrics — it is **independent human judgment agreement**, countable and
traceable across the network.

- 3 nodes independently tag "Terracotta Warriors: dramatic, powerful" → emerging signal
- 50 nodes converge on the same judgment → strong preference signal
- 50 nodes, 30 say "dramatic," 20 say "sterile" → measurable disagreement (equally valuable)

**Convergence is the growth signal.** It indicates whether shared human
perspectives are emerging across the network — or whether perspectives
diverge in culturally or individually meaningful ways.

---

## From seed to wave — the organic model

No single loop produces AGI. What we are looking for is a **wave** — a pattern
that emerges from many overlapping loops of development, each one complete
and reviewable, each one adding new signal. One loop is a ripple. Many loops,
shared across many nodes, build toward a wave that pushes the system closer
to genuine human-perspective intelligence.

```
SEED                    ── what we share (Seed Package with tags)
  ↓ usage = energy      ── more contributors = more signal
  ↓ tags = substance    ── more judgments per contributor = richer data
  ↓ diversity = depth   ── different cultures/domains = broader coverage
  ↓
RIPPLE                  ── first cross-node convergence detected
  ↓                     ── "3 independent nodes agree on this judgment"
  ↓
WAVE BUILDING           ── flow established, tags accumulating
  ↓                     ── convergence measurable, patterns emerging
  ↓
WAVE                    ── a distributed human-perspective signal strong enough
                          to predict what a person will find significant,
                          in context, across domains
```

This cannot be rushed or theorized into existence. It has to be grown — one
loop at a time, shared, measured, repeated. The wave is the cumulative effect
of many complete loops, not the output of any single one.

---

## What flows through the system (tags, not videos)

The video pipeline is one of several **input vehicles** — systems that
generate structured human judgments. The real output of every vehicle is the
same: a tag + a reason + a provenance.

```
Input vehicle                    Structured output (what gets shared)
───────────────────              ───────────────────────────────────
video clip selection             shot_type: aerial
glasses capture                  mood: dramatic
phone photo culling              perspective: first_person
tour itinerary rating            preference: accepted
pairwise comparison              reason: "ranks recede into shadow"
                                 override: model picked B, human picked A
                                 confidence: model was 90% sure (wrong)
```

Every vehicle produces structured judgment data. That data is what gets
packaged into Seed Packages, shared across the exchange, and measured for
convergence. The Obsidian vault + LLM engine is the processing layer; the
IPFS exchange is the sharing layer; the video pipeline (and future vehicles)
are input layers.

---

## The chase and track — the brain is alive

A dead brain collects tags passively. A living brain CHASES and TRACKS.

### CHASE (the brain reaches toward the sun)

The node actively surfaces the most informative comparisons:

```
"You judged Great Wall clips yesterday.
 Here's a Terracotta Warriors pair where the model is 51% vs 49%.
 Your judgment here teaches the most. 30 seconds?"

"Three other nodes disagreed on this clip.
 What do you see?"
```

Active learning means the system requests the judgments that would most
improve its model — not random prompts, but the closest calls, the edge
cases, the disagreements.

### TRACK (longitudinal measurement)

The node follows the signal over time:

```
"Your lighting preference has shifted since March —
 you now favor darker, more dramatic shots."

"You and Node B agree on 87% of architecture tags
 but disagree on 60% of food tags."

"The model's prediction accuracy on your judgments
 improved from 62% to 78% over 200 comparisons."
```

Longitudinal tracking measures not just what a contributor judged, but how
their perspective evolves and how it relates to other nodes in the network.

---

## Research direction — not claims

This project is at an early research stage. We are not claiming to have
demonstrated universal human perspective, construct validity, or AGI. What we
have built is **infrastructure designed to test whether distributed human
judgment convergence produces a meaningful signal.**

The questions we are exploring:
- Can human preferences be measured reliably through structured judgment capture?
- Do independent nodes converge on similar judgments for the same stimuli?
- Does the signal transfer across domains (e.g., travel → food → architecture)?
- Where do humans disagree, and is that disagreement predictable by culture,
  age, or context?

These questions can only be answered through deployment and measurement —
not through isolated analysis. The infrastructure exists to run the
experiment. The experiment requires contributors.

---

## What already exists

| Component | Role | Status |
|:---|:---|:---|
| `llm_wiki_engine/` | Processing layer — converts input to structured tags | ✅ Working |
| Obsidian vault | Memory layer — stores and cross-links tags locally | ✅ Structure built |
| `p2p_exchange/` | Exchange layer — shares Seed Packages via IPFS | ✅ Working |
| `tools/seed_generator/` | Packaging — bundles tags into shareable seeds | ✅ Working |
| `videogen/clip_pool/judge.py` | Input vehicle #1 — video clip judgment capture | ✅ Working |
| `videogen/provenance.py` | Provenance gate — separates stimulus from judgment | ✅ Working |
| `obsidian_plugin/` | Local brain interface | ✅ Scaffolded |

**What's in development:**
- Active learning (surface the most informative comparisons)
- Longitudinal tracking (measure how perspectives evolve over time)
- Convergence measurement (count cross-node agreement)
- Additional input vehicles (pairwise comparison, glasses capture, photo culling)

The core infrastructure — processing, memory, exchange, packaging, provenance — is operational. The next phase is deployment: getting the system into contributors' hands and measuring what emerges.

---

## The one command that starts the flow

```bash
# Package your node's structured tags into a seed
python tools/seed_generator/generate_seed.py

# Share the seed through content-addressed exchange
python -m p2p_exchange publish --package seed_output/seed_goldman_20260729/

# Another node imports it
python -m p2p_exchange resolve --cid <CID>

# Their node processes your tags alongside their own
# Their tags flow back through the exchange
# Convergence becomes measurable
```

The infrastructure is built. The exchange is operational. What comes next is
deployment — and the wave of signal that emerges from many independent loops,
shared, measured, and accumulated over time.
