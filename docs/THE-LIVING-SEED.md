# The Living Seed — How HiveAGI Actually Works

> The vision that connects every piece of infrastructure.
> This is the answer to both external auditors and the internal question:
> "How does this become AGI?"

---

## The architecture in one sentence

**Local brains (Obsidian + LLM) share tags through a bridge (IPFS), creating a flow of countable human preferences that grows organically through usage.**

That's it. Everything else is implementation.

---

## The three layers

### Layer 1: The Brain (local, private, alive)

```
┌─────────────────────────────────────────┐
│           LOCAL BRAIN                    │
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
│  └── vision.py (see frames → tag them)  │
│                                         │
│  This brain CHASES:                     │
│  "Which pair teaches me most?"          │
│  "You haven't tagged today — 30sec?"    │
│                                         │
│  This brain TRACKS:                     │
│  "Your taste shifted since March"       │
│  "You disagree with 3 others on this"   │
└─────────────────────────────────────────┘
```

Each contributor has their OWN brain. Their tags. Their preferences. Their beauty standard. Locally processed, locally owned, no central server reading their data.

**The LLM engine is the brain's cortex** — it processes raw input (video frames, glasses captures, phone photos) into structured tags. Without the LLM, the brain can't think. Without Obsidian, the brain can't remember. Together: memory + cognition = a local intelligence.

### Layer 2: The Bridge (shared, content-addressed, trustless)

```
         Brain A                    Brain B                    Brain C
        (Sydney)                   (Hong Kong)                (London)
           │                           │                           │
           └───────────┬───────────────┘───────────────────────────┘
                       │
                  IPFS BRIDGE
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

The bridge doesn't store brains. It carries **seeds** — Seed Packages containing tags, judgments, and reasons. Each seed is content-addressed (CID), verifiable, tamper-detectable.

**The bridge is the seed-sharing mechanism.** You don't upload your brain. You package the tags your brain produced into a Seed Package, publish the CID, and anyone can plant it in their own brain. Their brain grows from your tags. Your brain grows from theirs.

### Layer 3: The Flow (organic, measurable, alive)

```
Seed shared ──→ planted in Brain B ──→ B adds tags ──→ B shares back
    │                                                    │
    │              popularity = countable                │
    │                                                    │
    ↓                                                    ↓
  Brain C plants ──→ C adds tags ──→ C shares ──→ flow grows
```

When multiple brains independently tag the same thing similarly — **that's popularity.** Not YouTube views. Not Instagram likes. **Independent human judgment convergence, countable, traceable.**

- 3 brains tag "Terracotta Warriors: dramatic, powerful" → emerging signal
- 50 brains tag it the same way → universal preference
- 50 brains, 30 say "dramatic," 20 say "sterile" → cultural disagreement (equally valuable)

**Popularity is the growth signal.** It tells you the seed is taking root.

---

## From seed to fruit — the organic model

```
SEED                    ── what we share (Seed Package with tags)
  ↓ sun = usage         ── more contributors = more light
  ↓ water = tags        ── more judgments per contributor = more water
  ↓ soil = diversity    ── different cultures/domains = richer soil
  ↓
SPROUT                  ── first cross-brain convergence detected
  ↓                     ── "3 independent brains agree on this tag"
  ↓
GROWING                 ── flow established, tags accumulating
  ↓                     ── popularity measurable, patterns emerging
  ↓
FRUIT                   ── a universal (or culturally-specific) perspective model
                          that can predict what a human will find significant
```

**You cannot skip from seed to fruit.** The auditors wanted proof before sharing. The organic model says: sharing IS how you get proof. The seed has to be in the ground.

---

## What flows through the system (tags, not videos)

The video pipeline was always just a **tagging vehicle.** The real product is the tags.

```
Vehicle (generates tags)          Crop (the tags themselves)
─────────────────────────         ─────────────────────────
video clip selection              shot_type: aerial
glasses capture                   mood: dramatic
phone photo culling               perspective: first_person
tour itinerary rating             preference: accepted
pairwise comparison               reason: "ranks recede into shadow"
                                  override: model picked B, human picked A
                                  confidence: model was 90% sure (wrong)
```

Every vehicle produces the same crop: **a tag + a reason + a provenance.** The crop is what gets packaged into seeds, shared across the bridge, and counted as popularity.

This is why the Obsidian wiki + LLM engine is the brain — it's the system that PROCESSES tags. And the IPFS exchange is the bridge — it's what SHARES tags. The video pipeline is just one of many vehicles that FEEDS tags into the brain.

---

## The chase and track — the brain is alive

A dead brain collects tags passively. A living brain CHASES and TRACKS.

### CHASE (the brain reaches toward the sun)

The brain actively pursues the most informative tags:

```
"You judged Great Wall clips yesterday.
 Here's a Terracotta Warriors pair where the model is 51% vs 49%.
 Your judgment here teaches the most. 30 seconds?"

"You haven't tagged in 3 days.
 Two clips on WhatsApp. Which for the brochure?"

"Three other brains disagreed on this clip.
 What do YOU see?"
```

The chase = active learning. The brain asks for the tags that would change its model the most. Not random clips — the CLOSEST calls, the edge cases, the disagreements.

### TRACK (the brain grows roots)

The brain follows the signal over time:

```
"Your taste in lighting shifted since March —
 you now prefer darker, more dramatic shots."

"You and Brain B agree on 87% of architecture tags
 but disagree on 60% of food tags. Interesting."

"The model's prediction accuracy on your tags
 improved from 62% to 78% over 200 judgments.
 It's learning you."
```

The track = longitudinal measurement. Not just "what did this human tag" but "how is this human's perspective evolving" and "how does it compare to others."

---

## This answers both auditors

### Claude: "n=1, you can't claim universality"
**Answer:** We're not claiming it. We're **sharing the seed so usage reveals it.** n=1 is the seed. The bridge carries it to n=2, n=10, n=1000. Universality is measured by popularity (convergence across brains), not asserted. The system is DESIGNED to discover whether universality exists — not to assume it.

### OpenAI: "construct validity not established"
**Answer:** Validity is established **through the flow**, not in isolation. When 50 independent local brains, each processing their own captures with their own LLM, converge on the same tag for the same stimulus — that IS construct validity. It's measured, not theorized. The bridge makes the measurement possible.

### Both: "stop building, start testing"
**Answer:** The testing IS the sharing. Build the bridge, share the seed, let the flow reveal the answer. A seed in a lab can't prove it'll grow. A seed in the ground proves itself.

---

## What already exists (we're closer than the auditors think)

| Component | Role | Status |
|:---|:---|:---|
| `llm_wiki_engine/` | The cortex — processes input → tags | ✅ Working |
| Obsidian vault | The memory — stores tags locally | ✅ Structure built |
| `p2p_exchange/` | The bridge — shares seeds via IPFS | ✅ Working |
| `tools/seed_generator/` | The seed packager | ✅ Working |
| `videogen/clip_pool/judge.py` | Tagging vehicle #1 (video selection) | ✅ Working |
| `videogen/provenance.py` | Stimulus vs judgment separation | ✅ Working |
| `obsidian_plugin/` | Local brain interface | ✅ Scaffolded |

**What's missing:**
- The CHASE (active learning — "ask the most informative question")
- The TRACK (longitudinal measurement — "how is this brain evolving?")
- The FLOW counter (popularity measurement — "how many brains converged?")
- More vehicles (WhatsApp pairwise, glasses capture, photo culling)

But the brain + bridge + seed infrastructure is **already built.** The flow just needs to start.

---

## The one command that starts the flow

```bash
# Package your brain's tags into a seed
python tools/seed_generator/generate_seed.py

# Share the seed through the bridge
python -m p2p_exchange publish --package seed_output/seed_goldman_20260729/

# Another brain plants it
python -m p2p_exchange resolve --cid <CID>

# Their brain grows from your tags
# Their tags flow back
# The flow begins
```

The seed is in the repo. The bridge is built. The brain is alive. 
**Plant it.**
