# The Loop Diagrams — How Project Hive.AGI Actually Gets Built

> Visual map of the "small circles" strategy (see `LOOP-STRATEGY.md`).
> Each circle is a complete, reviewable loop. They overlap, they feed
> each other, and together they cover the vision.

---

## Diagram 1 — One Small Circle (the shape every loop shares)

Every circle — no matter the domain — runs the same 7 stages. Finish all 7,
or the circle isn't complete.

```mermaid
graph LR
    subgraph "COGNITION (Labs core)"
        F[① FETCH<br/>pull candidates<br/>into a pool] --> PT[② PRETAG<br/>LLM content tags<br/>shot_type, mood, grade]
        PT --> ME[③ METRICS<br/>brightness, motion,<br/>shake — opencv]
        ME --> AD[④ ADAPT<br/>landscape→portrait<br/>crop with provenance]
        AD --> JU[⑤ JUDGE<br/>human accept/reject<br/>+ reason = THE SEED]
        JU --> CU[⑥ CUT<br/>assemble the draft<br/>from locked picks]
    end

    subgraph "CRAFT (Forge skill)"
        CU --> FN[⑦ FINISH<br/>VO + music + subs<br/>+ brand end card]
    end

    FN --> DELIV[🎬 SHIPPABLE<br/>DELIVERABLE]
    JU -.->|hybrid seed| SEED[(🌱 SEED<br/>judgment_log.jsonl<br/>provenance-gated)]

    style F fill:#1a3a5c,color:#fff
    style PT fill:#1a3a5c,color:#fff
    style ME fill:#1a3a5c,color:#fff
    style AD fill:#1a3a5c,color:#fff
    style JU fill:#c8202f,color:#fff
    style CU fill:#1a3a5c,color:#fff
    style FN fill:#2d5f3f,color:#fff
    style DELIV fill:#b68a45,color:#000
    style SEED fill:#3ecf8e,color:#000
```

**The two outputs of every circle:**
- 🎬 **Deliverable** (right) — the commercial video. Ephemeral. Sells a tour.
- 🌱 **Seed** (below) — the human judgments. Durable. Feeds Labs. The asset.

---

## Diagram 2 — The Provenance Seam (what crosses, what doesn't)

This is the load-bearing boundary. Get it wrong and the AGI thesis corrupts.

```mermaid
graph TB
    subgraph SOURCES["Material Sources"]
        STOCK[📸 Stock Footage<br/>Pexels, Pixabay<br/>professional content]
        HUMAN[👁️ Human Capture<br/>AI glasses, phone<br/>first-person perspective]
    end

    subgraph FORGE["FORGE — Commercial (Goldman Forge)"]
        STOCK -->|source_type: stock:pexels<br/>✅ use freely| FREEL[Commercial Reel<br/>the deliverable]
        HUMAN -->|source_type: human_capture<br/>✅ use freely| FREEL
    end

    subgraph LABS["LABS — Human-Perspective Network"]
        STOCK -.->|🚫 BLOCKED<br/>provenance gate| GATE{is_labs_eligible?}
        HUMAN -->|✅ passes| GATE
        GATE -->|stock → reject| BLOCK[❌ blocked<br/>professional content<br/>≠ human perspective]
        GATE -->|human → accept| SEEDPKG[🌱 Seed Package<br/>CC-BY-NC-SA-4.0<br/>IPFS distributed]
    end

    JUDGE[⑤ JUDGE<br/>human judgments<br/>accept/reject + reason]
    JUDGE -->|always eligible<br/>IF source_type tagged| HYBRID[🌱 HYBRID SEED<br/>human taste = human perspective<br/>tagged: judged against stock?]
    HYBRID --> SEEDPKG

    style STOCK fill:#f5a623,color:#000
    style HUMAN fill:#3ecf8e,color:#000
    style GATE fill:#c8202f,color:#fff
    style BLOCK fill:#666,color:#fff
    style SEEDPKG fill:#3ecf8e,color:#000
    style HYBRID fill:#3ecf8e,color:#000
    style FREEL fill:#b68a45,color:#000
```

**The hybrid seed insight:** Stock *pixels* are blocked from Labs. But human
*judgments* about stock (the beauty standard) ARE Labs-eligible — tagged so
Labs can tell "editor taste on professional footage" from "human capture."

---

## Diagram 3 — Circle #1 (Legends of China Warriors) — COMPLETE

The first circle, fully run. Every stage has a concrete artifact.

```mermaid
graph TB
    KW[📋 keywords.yaml<br/>8 shots, stock:pexels] --> F

    F["① FETCH<br/>136 clips from Pexels<br/>landscape + portrait"] --> PT
    PT["② PRETAG<br/>132/136 LLM-tagged<br/>shot_type, perspective, mood, grade"] --> ME
    ME["③ METRICS<br/>132/136 measured<br/>brightness, motion, shake"] --> AD
    AD["④ ADAPT<br/>8 portrait crops<br/>LLM-guided, provenance-chained"] --> JU

    JU["⑤ JUDGE — 8 verdicts locked<br/>founder's picks + reasons<br/>+ rejected Sphinx, mislabeled"] --> CU

    CU["⑥ CUT<br/>legends-landscape.mp4 51.5s<br/>legends-vertical.mp4 51.5s<br/>8 shots, crossfaded"] --> FN

    FN["⑦ FINISH<br/>subtitles burned ✓<br/>end card rendered ✓<br/>VO + music = next pass"]

    JU -.->|14 verdicts recorded| SEED1[🌱 judgment_log.jsonl<br/>circle #1 seed]

    style F fill:#1a3a5c,color:#fff
    style JU fill:#c8202f,color:#fff
    style FN fill:#2d5f3f,color:#fff
    style SEED1 fill:#3ecf8e,color:#000
```

**Status:** Draft 1 assembled. Subtitles + end card rendered. VO + music
pending (MiniMax TTS built, music to source). The circle is *reviewable* —
every decision traceable, every clip provenance-tagged.

---

## Diagram 4 — Multiple Circles Overlapping (the coverage strategy)

Each circle is a complete loop in a new domain. They reuse infrastructure,
overlap in capability, and together approach full coverage of the vision.

```mermaid
graph TB
    subgraph CIRCLE1["◉ CIRCLE 1 — ECH Tourism (Legends of China)"]
        direction LR
        c1a[fetch] --> c1b[pretag] --> c1c[judge] --> c1d[cut] --> c1e[finish]
    end

    subgraph CIRCLE2["◉ CIRCLE 2 — ECH Tourism (Imperial Yangtze)"]
        direction LR
        c2a[fetch] --> c2b[pretag] --> c2c[judge] --> c2d[cut] --> c2e[finish]
    end

    subgraph CIRCLE3["◉ CIRCLE 3 — ECH Tourism (Silk Road)"]
        direction LR
        c3a[fetch] --> c3b[pretag] --> c3c[judge] --> c3d[cut] --> c3e[finish]
    end

    subgraph CIRCLEN["◉ CIRCLE N — New Domain (Real-estate / Education / Industrial)"]
        direction LR
        cnA[fetch] --> cnB[pretag] --> cnC[judge] --> cnD[cut] --> cnE[finish]
    end

    subgraph CIRCLEM["◉ CIRCLE M — Glasses-Captured (human perspective)"]
        direction LR
        cmA[capture] --> cmB[pretag] --> cmC[judge] --> cmD[cut] --> cmE[finish]
    end

    %% Shared infrastructure (reused across ALL circles)
    INFRA[🔧 SHARED INFRASTRUCTURE<br/>videogen/ + clip_pool/ + provenance.py<br/>+ tour-video-finish skill]
    INFRA -.->|reused by| CIRCLE1
    INFRA -.->|reused by| CIRCLE2
    INFRA -.->|reused by| CIRCLE3
    INFRA -.->|reused by| CIRCLEN
    INFRA -.->|reused by| CIRCLEM

    %% Seeds aggregate
    CIRCLE1 -.->|seed| AGG[(🌱 SEED AGGREGATE<br/>cross-domain<br/>human-perspective<br/>knowledge network)]
    CIRCLE2 -.->|seed| AGG
    CIRCLE3 -.->|seed| AGG
    CIRCLEN -.->|seed| AGG
    CIRCLEM -.->|seed| AGG

    AGG -->|when source flips to<br/>human_capture| VISION[🎯 THE VISION<br/>distributed human-perspective<br/>AGI — 99.9% coverage]

    style INFRA fill:#1a3a5c,color:#fff
    style AGG fill:#3ecf8e,color:#000
    style VISION fill:#b68a45,color:#000
```

**What each circle adds:**
- Circle 1 (done): the loop itself + tourism beauty standard
- Circle 2: new audience (over-60s), new tour geography
- Circle 3: new region (Silk Road), new "beauty" definition
- Circle N: new domain entirely (same loop shape, new content)
- Circle M: **the inflection** — source flips from stock to glasses-captured.
  Now raw pixels are ALSO Labs-eligible. The infrastructure doesn't change.

---

## Diagram 5 — How Requests, Projects, and Loops Link Together

A single request ("make a tour video") triggers a loop. A project (ECH) runs
many loops. The Labs vision aggregates seeds from all projects.

```mermaid
graph TB
    REQ1["💬 REQUEST<br/>'Make the Legends of China<br/>tour video'"]
    REQ2["💬 REQUEST<br/>'Make the Imperial Yangtze<br/>tour video'"]
    REQ3["💬 REQUEST<br/>'Analyze beauty standards<br/>across age groups'"]

    PROJ1["🏢 PROJECT: ExploreChina Holiday<br/>(Goldman Forge — commercial)"]
    PROJ2["🔬 PROJECT: Labs Research<br/>(Goldman Global Labs — open source)"]

    REQ1 -->|triggers| LOOP1[◉ LOOP: Legends of China<br/>ECH tourism · stock-sourced]
    REQ2 -->|triggers| LOOP2[◉ LOOP: Imperial Yangtze<br/>ECH tourism · stock-sourced]
    REQ3 -->|triggers| LOOP3[◉ LOOP: Cross-editor<br/>beauty aggregation<br/>Labs research · multi-editor]

    LOOP1 --> PROJ1
    LOOP2 --> PROJ1
    LOOP3 --> PROJ2

    %% Deliverables go to Forge
    PROJ1 -->|deliverables| COMMERCIAL[💰 Commercial Output<br/>tour videos, client reels<br/>revenue funds Labs]

    %% Seeds go to Labs
    LOOP1 -.->|judgment_log.jsonl| SEEDNET[🌱 SEED NETWORK<br/>human-perspective knowledge<br/>IPFS distributed · CC-BY-NC-SA]
    LOOP2 -.->|judgment_log.jsonl| SEEDNET
    LOOP3 -.->|aggregated patterns| SEEDNET

    SEEDNET -->|enriches| RESEARCH[🔬 Research Output<br/>papers, models, insights<br/>makes Forge better]
    RESEARCH -.->|better tools| PROJ1

    %% The dual-company structure
    subgraph GG["Goldman Global (the company)"]
        PROJ1
        PROJ2
        COMMERCIAL
        RESEARCH
        SEEDNET
    end

    style REQ1 fill:#2d5f3f,color:#fff
    style REQ2 fill:#2d5f3f,color:#fff
    style REQ3 fill:#1a3a5c,color:#fff
    style LOOP1 fill:#c8202f,color:#fff
    style LOOP2 fill:#c8202f,color:#fff
    style LOOP3 fill:#c8202f,color:#fff
    style COMMERCIAL fill:#b68a45,color:#000
    style SEEDNET fill:#3ecf8e,color:#000
    style RESEARCH fill:#1a3a5c,color:#fff
```

**The value loop:**
1. A request triggers a loop → produces a commercial deliverable (Forge revenue)
2. The same loop captures human judgments → deposits seed (Labs asset)
3. Labs research on aggregated seeds → better tools → better Forge deliverables
4. Better Forge output → more clients → more loops → more seed → coverage grows

**Commercial funds research. Research makes commercial better. The loop compounds.**

---

## Diagram 6 — The Full System Architecture (where everything lives)

```mermaid
graph TB
    subgraph REPO["gg-hiveagi (the repository)"]
        subgraph LABSCORE["Labs Core — Cognition"]
            VW[llm_wiki_engine/<br/>MiniMax M3 + DeepSeek V4<br/>vision, generation, audit]
            VG[videogen/<br/>the 7-stage loop engine]
            CP[videogen/clip_pool/<br/>fetch, pretag, metrics,<br/>adapt, judge]
            PV[videogen/provenance.py<br/>THE GATE<br/>stock → blocked from Labs]
            SL[videogen/selection_log.py<br/>human-override signal<br/>the seed harvester]
            P2[p2p_exchange/<br/>IPFS Seed Packages]
            SG[tools/seed_generator/<br/>P0 package builder]
            PII[tools/pii_anonymizer/<br/>face + plate blur<br/>code-enforced, no bypass]
        end

        subgraph FORGECRAFT["Forge Craft — Production"]
            ECH[explore_china_holiday/<br/>ECH configs + tours/<br/>client-specific content]
            TOUR1[tours/legends-of-china-warriors/<br/>scripts, keywords,<br/>selection_draft, output/]
            SKILL[.agents/skills/<br/>tour-video-finish/<br/>VO, music, subs, branding]
        end

        subgraph DOCS["Documentation"]
            STRAT[docs/LOOP-STRATEGY.md<br/>the small circles thesis]
            DIAG[docs/LOOP-DIAGRAMS.md<br/>you are here]
            SPEC[specs/<br/>schema, vault, API]
            CONTRIB[CONTRIBUTING.md<br/>CLA, PII rules]
        end
    end

    subgraph EXTERNAL["External"]
        PEXELS[Pexels API<br/>stock footage]
        MINIMAX[MiniMax API<br/>M3 vision + TTS]
        DEEPSEEK[DeepSeek API<br/>V4 Flash audit]
        IPFS[IPFS / kubo<br/>P2P exchange]
        OBSIDIAN[Obsidian Vault<br/>wiki layer]
    end

    PEXALS_DATA[" "] -.->|fetch| CP
    MINIMAX -.->|vision + TTS| VW
    MINIMAX -.->|vision| CP
    DEEPSEEK -.->|audit| VW
    CP --> VG
    VG --> ECH
    ECH --> TOUR1
    TOUR1 --> SKILL
    SKILL -->|finishes| TOUR1

    VW --> PII
    PII -->|blur gate| VW

    SL -.->|seed| SG
    SG -.->|publish| P2
    P2 -.->|exchange| IPFS

    style PV fill:#c8202f,color:#fff
    style PII fill:#c8202f,color:#fff
    style SKILL fill:#2d5f3f,color:#fff
    style TOUR1 fill:#b68a45,color:#000
```

---

## How to read these diagrams together

| Diagram | Answers |
|:---|:---|
| **1 — One Small Circle** | What does a complete loop look like? (the 7 stages) |
| **2 — Provenance Seam** | What crosses from Forge to Labs, and what's blocked? |
| **3 — Circle #1** | What did the Legends tour actually produce? (concrete artifacts) |
| **4 — Multiple Circles** | How do circles overlap and cover the vision? |
| **5 — Requests/Projects/Loops** | How does a request become a loop, and how do loops link? |
| **6 — System Architecture** | Where does every piece of code live in the repo? |

The thesis in one line: **finish one complete circle, review it, run the next.
Same shape every time. Overlapping coverage approaches 99.9%.**

Circle #1 is done. Circle #2 starts when you say go.
