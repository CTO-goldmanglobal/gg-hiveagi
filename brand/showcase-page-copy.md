# Research Showcase — Page Copy & Wireframe

> For `goldmanglobal.com.au/research`. Hand this to a Webflow/designer.
> Pair with `research-labs-positioning-brief.md` for strategy. All copy final.

---

## Page wireframe (ASCII layout)

```
┌─────────────────────────────────────────────────────────────────┐
│  [GG FORGE nav]                              Research  Contact   │  ← add "Research" to main nav
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         THE RESEARCH ENGINE BEHIND GOLDMAN FORGE                │  ← eyebrow (small, gold)
│                                                                 │
│      Building AI that learns to understand                      │  ← H1 (hero)
│      humans — not the other way around.                         │
│                                                                 │
│   Goldman Global Research Labs is our open-source R&D arm,      │  ← subhead
│   researching human-perspective, decentralized,                 │
│   audited AI. Everything we publish is AGPL.                    │
│                                                                 │
│   [★ Star on GitHub]    [Read the research brief]              │  ← CTAs
│                                                                 │
│   [subtle frame→blur→CID hero animation]                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WHAT WE'RE BUILDING                                            │  ← section H2
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │  ← 3 project cards
│  │  Hive.AGI      │  │  (future)      │  │  (future)      │       │
│  │  ★ Live        │  │  In planning   │  │  In planning   │       │
│  │                │  │                │  │                │       │
│  │  Human-        │  │                │  │                │       │
│  │  perspective   │  │                │  │                │       │
│  │  knowledge     │  │                │  │                │       │
│  │  network       │  │                │  │                │       │
│  │  [Explore →]   │  │                │  │                │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HOW IT WORKS                                                   │
│                                                                 │
│  [capture] → [LLM generate] → [audit] → [publish CID]           │  ← pipeline diagram
│     │           │                │           │                   │
│  human        MiniMax M3      DeepSeek     IPFS                 │
│  defines      writes          reviews      content-addressed    │
│  what         the entry       & corrects   exchangeable         │
│  matters                                                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  THE DIFFERENCE                                                 │
│                                                                 │
│  ┌─────────────────────┬─────────────────────┐                  │  ← comparison table
│  │  Corporate AGI      │  Research Labs       │                  │
│  ├─────────────────────┼─────────────────────┤                  │
│  │  Scraped data       │  Human-curated       │                  │
│  │  Self-evaluated     │  Dual-LLM audited    │                  │
│  │  Centralized API    │  IPFS, peer-to-peer  │                  │
│  │  Closed / restricted│  AGPL (real copyleft)│                  │
│  └─────────────────────┴─────────────────────┘                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GENUINELY OPEN                                                 │
│                                                                 │
│  Every line is AGPL-3.0. Commercial use feeds back.             │
│  Every Seed Package is CC-BY-NC-SA. Contributors keep rights.   │
│  Dual-license for enterprise.                                   │
│                                                                 │
│  [Browse the repo →]    [Contributor guide →]                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CREDIBILITY                                                    │
│                                                                 │
│  • Australian-built, Sydney-hosted                              │
│  • PII stripping enforced in code (not just policy)             │
│  • Real client signal via Goldman Forge (transport/travel/fin)  │
│  • CI-verified, reproducible builds                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WANT TO BUILD WITH US?                                         │  ← final CTA
│                                                                 │
│  Contributors: github.com/CTO-goldmanglobal/gg-hiveagi          │
│  Enterprise R&D: cto@goldmanglobal.com.au                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section-by-section copy

### Hero

**Eyebrow** (small caps, accent color):
> THE RESEARCH ENGINE BEHIND GOLDMAN FORGE

**H1**:
> Building AI that learns to understand humans — not the other way around.

**Subhead**:
> Goldman Global Research Labs is our open-source R&D arm. We research human-perspective, decentralized, dual-LLM-audited AI. Everything we publish is AGPL.

**Primary CTA**: `★ Star on GitHub` → https://github.com/CTO-goldmanglobal/gg-hiveagi
**Secondary CTA**: `Read the research` → scrolls to "How it works"

**Hero visual**: a subtle, looping animation showing a single video frame → PII-blurred frame → base64 → JSON → CID. ~6 seconds. Static fallback: a labeled still of the pipeline. No stock AI imagery.

---

### Section: What we're building

**Section H2**:
> What we're building

**Intro line** (small, under H2):
> Open-source research projects. Each ships code, not slideware.

**Card 1 — Hive.AGI** (live, primary):
- **Tag**: `● LIVE`
- **Title**: Hive.AGI
- **One-liner**: A human-perspective knowledge symbiosis network. Capture what matters → fuse into structured entries → publish as content-addressed Seed Packages.
- **Meta row**: `Python · MiniMax M3 · DeepSeek V4 Flash · IPFS`
- **CTA**: `Explore the project →` → github repo

**Card 2 — (future)**:
- **Tag**: `○ IN PLANNING`
- **Title**: [Project 2 — TBD]
- **One-liner**: Placeholder for the next research line. Don't fabricate. Leave as "Coming. Follow the repo."
- **CTA**: none (or `Follow →` linking to GitHub releases)

**Card 3 — (future)**: same as Card 2.

---

### Section: How it works

**Section H2**:
> How it works

**Intro line**:
> One pipeline. Five stages. Every step is open and inspectable.

**Pipeline diagram** (horizontal on desktop, stacked on mobile):

```
[1. CAPTURE]    →  [2. GENERATE]    →  [3. AUDIT]      →  [4. PUBLISH]
   human             MiniMax M3         DeepSeek V4       IPFS
   defines           writes the         reviews &         content-addressed
   what              wiki entry         auto-corrects     exchangeable
   matters                              hallucinations    by CID
```

**Under each stage, one line of body copy**:

1. **Capture** — A contributor (phone, glasses, sensor, or note) records a moment they judge worth keeping. *The human defines the signal.*
2. **Generate** — MiniMax M3 turns raw capture into a structured wiki entry: description, analysis, related links.
3. **Audit** — DeepSeek V4 Flash independently reviews for hallucination, schema, and bias. Auto-corrects or quarantines. *No model marks its own homework.*
4. **Publish** — The entry becomes a Seed Package, content-addressed on IPFS. Anyone can verify integrity by recomputing the hash.

**Honest footnote** (small, muted):
> P2.5 (automatic peer-to-peer sync between contributors) is in design. Today, packages are publish/verify/resolve.

---

### Section: The difference

**Section H2**:
> The difference

**Intro line**:
> We're building something corporate AI labs structurally can't.

**Comparison table**:

| | Corporate AGI labs | Goldman Global Research Labs |
| :--- | :--- | :--- |
| **Data** | Web-scraped, scale over signal | Human-curated, contributor defines value |
| **Quality** | Model evaluates itself | Independent generator + auditor (different providers) |
| **Distribution** | Centralized API, vendor lock-in | IPFS content addressing, peer-to-peer |
| **License** | Closed or "open-weight" with usage restrictions | AGPL-3.0 — genuine copyleft, SaaS-safe |
| **Sovereignty** | US/UK-centric | Australian-built, AU-hosted |
| **Privacy** | Policy-level, often bypassed in practice | Code-enforced PII stripping (no bypass exists) |

---

### Section: Genuinely open

**Section H2**:
> Genuinely open

**Body**:
> Every line of code is AGPL-3.0. If a corporation deploys our work as a service, they must share their improvements back — or buy a commercial license that funds the contributors.
>
> Every Seed Package is CC-BY-NC-SA-4.0. Contributors keep their copyright. Non-commercial sharing is free; commercial use funds the network.
>
> This isn't "open-core" theater. The full pipeline — generator, auditor, IPFS exchange, Obsidian plugin — is in the repo.

**CTAs**:
- `Browse the repo →` → GitHub
- `Contributor guide →` → CONTRIBUTING.md

---

### Section: Credibility

**Section H2**:
> Built to be trusted

**Body** (bullet list, no fluff):
- **Australian-built.** Sydney-based team, AU data hosting, ready for the 2026 Privacy Act.
- **Privacy by code.** PII stripping (faces, plates) runs *before* any LLM call. There is no `--skip-blur` flag — we checked.
- **Real-world signal.** Goldman Forge's live client deployments across transport, travel, and finance feed Labs genuine edge cases.
- **Reproducible.** Every commit runs CI. Mock mode lets anyone verify the pipeline without API keys.

---

### Final CTA

**H2**:
> Want to build with us?

**Two columns**:

**Contributors & researchers**
> Star, fork, or open a PR.
> github.com/CTO-goldmanglobal/gg-hiveagi

**Enterprise R&D & collaboration**
> Talk to us about commercial licensing, custom Seed Packages, or research partnerships.
> cto@goldmanglobal.com.au

---

## Metadata for Webflow

- **URL**: `goldmanglobal.com.au/research`
- **Nav label**: `Research` (add to main nav, between "Work" and "About")
- **Page title** (SEO): `Goldman Global Research Labs — Human-perspective, decentralized AI`
- **Meta description**: `Open-source R&D building human-perspective AI: dual-LLM audited, IPFS-published, AGPL-licensed. The research engine behind Goldman Forge.`
- **OG image**: the pipeline diagram (frame → blur → CID), branded. 1200×630.
- **Canonical**: `https://www.goldmanglobal.com.au/research`
- **Robots**: `index, follow`
- **Schema.org**: `Organization` + `SoftwareSourceCode` (the repo)

---

## Notes for the designer

1. **No purple gradients.** Every AI startup uses them. We don't. See positioning brief §10.
2. **Show real artifacts.** Use actual CIDs, actual frontmatter, actual `audit_log` comments as visual texture. They're credibility.
3. **The "Honest footnote" pattern is on-brand.** Don't hide limitations — surface them. Builds trust with the technical audience.
4. **Mono font for technical labels** (model names, CIDs, code). Sans for prose. Two-font system.
5. **Single accent color.** Gold/amber works (nod to "golden hour" + the Goldman name). Use sparingly — eyebrows, hover states, the live tag.
6. **Mobile: stack the pipeline vertically**, arrows pointing down. Keep all 4 stages visible without scrolling sideways.

---

## What this page deliberately does NOT do

- ❌ No "AI is going to change everything" hero. State what we build, not what AI will do.
- ❌ No team headshots (unless you have a real research team to show — currently Labs is small; better to show nothing than to inflate).
- ❌ No testimonials (no clients of Labs yet; Forge testimonials belong on the Forge site, not here).
- ❌ No "trusted by" logo wall. Logos of client companies from *Forge* would misattribute to *Labs*.
- ❌ No email signup form (yet — add when there's a real newsletter; a dead form erodes trust).

---

*Copy is final. Hand off to designer. Any deviation from this copy requires a brief update — don't let the page drift from the positioning.*
