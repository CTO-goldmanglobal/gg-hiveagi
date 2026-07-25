# Goldman Global Research Labs — Positioning Brief

> Strategic foundation for the research showcase at `goldmanglobal.com.au/research`.
> Pair with `showcase-page-copy.md` for execution.

---

## 1. One-sentence positioning

**Goldman Global Research Labs is the open-source R&D arm building human-perspective AI — systems that learn to understand people, rather than training people to adapt to systems.**

---

## 2. Relationship to Goldman Forge

The same company. Two faces.

| | **Goldman Forge** | **Research Labs** |
| :--- | :--- | :--- |
| **Role** | Commercial product delivery | Open-source research |
| **Output** | Deployed AI systems for paying clients (AI Front Desk, automations) | Published research, open-source tools, public protocols |
| **Audience** | Australian businesses buying AI | Developers, researchers, contributors, enterprise R&D scouts |
| **License** | Proprietary / client-owned | AGPL-3.0 (code) + CC-BY-NC-SA-4.0 (data) |
| **KPI** | Client deployments, revenue | Contributions, citations, package adoption |

**The narrative bridge**: Forge builds *production* AI for Australian business; Labs researches *what production AI should be* in the first place. Forge's real client deployments (transport, travel, finance) feed Labs real-world signal; Labs' open protocols give Forge a defensible foundation instead of vendor lock-in.

Showcase line: *"The research engine behind Goldman Forge."*

---

## 3. Mission narrative — "Human-perspective AGI"

### The problem (what's broken)

Corporate AGI labs (DeepMind, FAIR, OpenAI) build AI trained on scraped internet data. The resulting systems optimize for the logic of the data — not the values of the humans who produce it. People then adapt to the system. This is backwards.

### The thesis

Intelligence should be defined bottom-up, by the humans contributing their perspective — what they find beautiful, anomalous, worth remembering — not top-down by whoever owns the compute. A globally distributed network of human-perspective data, fused into shared knowledge via open protocols, produces AI that serves plural human values rather than a single corporate one.

### What we're building toward

Not a central superintelligence. A **decentralized, open, human-maintained knowledge symbiosis network** — where anyone with a phone, glasses, or sensor can contribute human-perspective data, and where LLMs fuse that data into structured, exchangeable knowledge (Seed Packages) verified by content addressing.

### The line that captures it (use sparingly, don't overuse)

> *Let computers learn to understand humans, rather than humans learning to adapt to computers.*

---

## 4. Audiences (three, in priority order)

### Primary: Contributors & researchers
- **Who**: Open-source devs, ML researchers, PhD students, AI-curious engineers
- **What they want**: A credible project to contribute to; interesting technical problems; their name on something real
- **How we reach them**: GitHub, technical writeups, the dual-LLM audit design, AGPL stance

### Secondary: Enterprise R&D scouts & collaborators
- **Who**: Innovation leads at AU enterprises, govtech, universities
- **What they want**: Evidence of depth, IP cleanliness (AGPL is a flag here — be ready), AU sovereignty
- **How we reach them**: The showcase page, case studies via Forge, speaking/writing

### Tertiary: General tech-curious public
- **Who**: People who read Hacker News, follow AI on social
- **What they want**: A clear story, no hype, something they can star/fork
- **How we reach them**: Concise README, the "human vs corporate AGI" framing

---

## 5. Key messages — 5 pillars

Use 1–3 per context. Don't dump all five.

1. **Human-perspective by design.** Data is curated by humans defining what matters, not scraped from the web. The contributor's judgment is the signal.
2. **Decentralized & content-addressed.** Seed Packages are IPFS-published, hash-verified, exchangeable peer-to-peer. No central authority owns the knowledge.
3. **Quality via dual-LLM audit.** A generator (MiniMax M3) writes, an independent auditor (DeepSeek V4 Flash) reviews and auto-corrects. No model marks its own homework.
4. **Genuinely open.** AGPL-3.0 code (closes the SaaS loophole — corporate use feeds back), CC-BY-NC-SA data (protects contributors), dual-license for commercial. Not "open-core" theater.
5. **Australian-built & privacy-first.** Sydney-based, AU-hosted, PII stripping enforced in code (not just policy) before any LLM call. Compliance-ready for the 2026 Privacy Act.

---

## 6. Tone of voice

- **Rigorous, not hypey.** Cite numbers, name models, show the architecture. No "revolutionary" / "game-changing" / "10x".
- **Confident, not arrogant.** State what works, what doesn't, what's stubbed. The "Honest scope" sections in our docs are a brand asset — keep that voice.
- **Accessible, not dumbed down.** A smart non-ML engineer should follow the showcase. An ML researcher should respect the depth.
- **Direct.** Short sentences. Active voice. No hedging.
- **Anti-hype is a position.** Call out what corporate AGI labs do that we disagree with — factually, not rhetorically.

**Voice reference**: closer to Anthropic's engineering blog than to OpenAI's marketing. Closer to Plausible Analytics than to Salesforce.

---

## 7. SEO keywords (primary → secondary)

Tier 1 (own these):
- human-perspective AI
- decentralized knowledge network
- AGPL AI research Australia
- human-curated AI training data

Tier 2 (compete on these):
- open source AGI
- multimodal AGI research
- content-addressed knowledge
- dual-LLM audit

Tier 3 (appear for these):
- AI research lab Sydney
- Goldman Global AI
- MiniMax M3 research
- DeepSeek V4 Flash

---

## 8. Differentiators vs corporate labs (DeepMind / FAIR / OpenAI)

| Dimension | **Corporate labs** | **Research Labs** |
| :--- | :--- | :--- |
| **Data sourcing** | Web scrape, scale at all costs | Human curation, the contributor defines signal |
| **Quality control** | Single model self-evaluates | Independent generator + auditor (different providers) |
| **Distribution** | Centralized API, vendor lock-in | IPFS content addressing, peer-to-peer |
| **License** | Closed / "open-weight" (usage-restricted) | AGPL-3.0 (genuine copyleft, SaaS-safe) |
| **Geography** | US/UK-centric | Australian-built, AU data sovereignty |
| **Privacy** | Policy-level, often bypassed | Code-enforced PII stripping (no `--skip-blur` exists) |

Don't frame this as "we're better than them" — frame as "we're building something they structurally can't."

---

## 9. What NOT to claim (honesty guardrails)

- ❌ Don't call it "AGI" as if it exists today. It's *research toward* human-perspective AGI.
- ❌ Don't claim the network is decentralized *yet* — P2 part 1 delivers content addressing; peer discovery (libp2p pubsub) is documented as P2.5, not shipped.
- ❌ Don't claim "millions of contributors" or similar — be exact about current state.
- ❌ Don't claim the auditor catches all hallucinations — it catches *some*, with a documented retry→quarantine policy.
- ❌ Don't imply MiniMax/DeepSeek are "our" models — we're API clients, they're providers.

---

## 10. Visual direction (for designer)

- **Palette**: serious engineering. Deep navy / charcoal base, single accent (consider a warm gold — nods to "golden hour" sample data + the Goldman name). Avoid the "every AI startup uses purple gradient" trap.
- **Type**: a technical grotesk (e.g. Inter, IBM Plex Sans) for body; consider a mono (JetBrains Mono, IBM Plex Mono) for code/CIDs/architecture labels.
- **Imagery**: real pipeline diagrams over stock AI blobs. Show actual CIDs, actual frontmatter, actual audit_log comments. The artifacts ARE the credibility.
- **Motion**: minimal. Maybe a subtle "frame → blur → CID" animation in the hero. Nothing flashy.

---

## 11. Contact & legal anchor

- **Repo**: https://github.com/CTO-goldmanglobal/gg-hiveagi
- **Contact**: cto@goldmanglobal.com.au
- **Legal entity**: Goldman Global (parent of Goldman Forge)
- **Licenses**: AGPL-3.0 (code) · CC-BY-NC-SA-4.0 (data) · Commercial available

---

*This brief is the source of truth for all Research Labs communication. Update it when positioning shifts; don't let the website drift from it.*
