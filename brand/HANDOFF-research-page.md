# Handoff: goldmanglobal.com.au/research

| | |
| :--- | :--- |
| **Project** | Research Labs showcase page |
| **URL** | `goldmanglobal.com.au/research` |
| **Owner** | Goldman Global (you) |
| **For** | Webflow designer / developer |
| **Status** | Ready to build — copy is final |
| **Source repo** | https://github.com/CTO-goldmanglobal/gg-hiveagi |
| **Contact** | cto@goldmanglobal.com.au |

---

## TL;DR (read this first)

Build one new page at `/research` that establishes **Goldman Global Research Labs** — the open-source R&D arm of the company — as a credible, distinct entity alongside the existing **Goldman Forge** commercial brand.

The page has **7 sections**, all copy is final in this document. The visual job is to make Labs feel like serious engineering research, not another AI-marketing landing page. The whole point is anti-hype credibility.

**You already have the Forge site design system.** Extend it — don't reinvent. Labs uses the same type/spacing/grid as Forge, with one accent color (gold) that's distinct from Forge's palette so visitors can tell they've crossed into "research" territory.

---

## 1. What you're building (context)

Goldman Global runs **two brands** under one company:

- **Goldman Forge** (existing site) — commercial AI delivery. Builds and deploys AI Front Desk, automations, and digital staff for Australian businesses. Fixed-price, fast delivery.
- **Goldman Global Research Labs** (this page) — open-source research. Publishes AGPL-licensed research projects. The first project is **Hive.AGI**, a human-perspective knowledge network.

**The relationship line to internalize:**
> *Labs is the research engine behind Goldman Forge. Forge builds production AI for clients; Labs researches what production AI should be. Forge's real deployments feed Labs genuine edge cases; Labs' open protocols give Forge a defensible foundation instead of vendor lock-in.*

The page must make this relationship legible without making Labs feel like a Forge subordinate. Labs is a peer brand that happens to share a parent.

---

## 2. Page structure (7 sections)

In order, top to bottom:

1. **Hero** — positioning + 2 CTAs + subtle animation
2. **What we're building** — 3 project cards (1 live, 2 placeholders)
3. **How it works** — the pipeline diagram (capture → generate → audit → publish)
4. **The difference** — comparison table vs corporate AI labs
5. **Genuinely open** — the licensing stance + 2 CTAs
6. **Built to be trusted** — credibility bullets
7. **Want to build with us?** — final CTA (contributors + enterprise)

---

## 3. Final copy (paste-ready)

### Section 1 — Hero

**Eyebrow** (small caps, accent color):
```
THE RESEARCH ENGINE BEHIND GOLDMAN FORGE
```

**H1**:
```
Building AI that learns to understand humans — not the other way around.
```

**Subhead**:
```
Goldman Global Research Labs is our open-source R&D arm. We research
human-perspective, decentralized, dual-LLM-audited AI. Everything we
publish is AGPL.
```

**Primary CTA** (button):
```
★ Star on GitHub
```
→ `https://github.com/CTO-goldmanglobal/gg-hiveagi`

**Secondary CTA** (text link):
```
Read the research
```
→ scrolls to Section 3 (How it works)

**Hero visual**: a subtle looping animation (~6s) showing a single video frame → PII-blurred frame → base64 string → JSON → CID. Static fallback: a labeled still of the pipeline. **No stock AI imagery. No purple gradients. No glowing brains.**

---

### Section 2 — What we're building

**Section H2**:
```
What we're building
```

**Intro line** (small, muted, under H2):
```
Open-source research projects. Each ships code, not slideware.
```

**Card 1 — Hive.AGI** (primary, "live" state):
- Tag: `● LIVE` (small, accent color, pill shape)
- Title: `Hive.AGI`
- One-liner:
  ```
  A human-perspective knowledge symbiosis network. Capture what matters →
  fuse into structured entries → publish as content-addressed Seed Packages.
  ```
- Meta row (mono font): `Python · MiniMax M3 · DeepSeek V4 Flash · IPFS`
- CTA: `Explore the project →` → `https://github.com/CTO-goldmanglobal/gg-hiveagi`

**Card 2** (placeholder, muted):
- Tag: `○ IN PLANNING`
- Title: `Project 2`
- One-liner: `Coming. Follow the repo for the next research line.`
- CTA: `Follow →` → GitHub releases page

**Card 3** (placeholder, muted): identical treatment to Card 2.

---

### Section 3 — How it works

**Section H2**:
```
How it works
```

**Intro line**:
```
One pipeline. Four stages. Every step is open and inspectable.
```

**Pipeline diagram** (horizontal on desktop, stacked vertically on mobile — keep all 4 visible without sideways scroll):

```
[1. CAPTURE]   →   [2. GENERATE]   →   [3. AUDIT]      →   [4. PUBLISH]
   human            MiniMax M3          DeepSeek V4         IPFS
   defines          writes the          reviews &           content-addressed
   what             wiki entry          auto-corrects       exchangeable
   matters                              hallucinations      by CID
```

**Under each stage, one line of body copy**:

1. **Capture** — A contributor (phone, glasses, sensor, or note) records a moment they judge worth keeping. *The human defines the signal.*
2. **Generate** — MiniMax M3 turns raw capture into a structured wiki entry: description, analysis, related links.
3. **Audit** — DeepSeek V4 Flash independently reviews for hallucination, schema, and bias. Auto-corrects or quarantines. *No model marks its own homework.*
4. **Publish** — The entry becomes a Seed Package, content-addressed on IPFS. Anyone can verify integrity by recomputing the hash.

**Honest footnote** (small, muted, italic):
```
P2.5 (automatic peer-to-peer sync between contributors) is in design.
Today, packages are publish / verify / resolve.
```

> **Designer note:** The honest footnote pattern is on-brand. Do not hide limitations — surface them. It builds trust with the technical audience.

---

### Section 4 — The difference

**Section H2**:
```
The difference
```

**Intro line**:
```
We're building something corporate AI labs structurally can't.
```

**Comparison table**:

| | Corporate AI labs | Goldman Global Research Labs |
| :--- | :--- | :--- |
| **Data** | Web-scraped, scale over signal | Human-curated, contributor defines value |
| **Quality** | Model evaluates itself | Independent generator + auditor (different providers) |
| **Distribution** | Centralized API, vendor lock-in | IPFS content addressing, peer-to-peer |
| **License** | Closed or "open-weight" with usage restrictions | AGPL-3.0 — genuine copyleft, SaaS-safe |
| **Sovereignty** | US/UK-centric | Australian-built, AU-hosted |
| **Privacy** | Policy-level, often bypassed in practice | Code-enforced PII stripping (no bypass exists) |

> **Designer note:** don't frame this as "we're better than them" — frame as "we're building something they structurally can't." Factual, not rhetorical.

---

### Section 5 — Genuinely open

**Section H2**:
```
Genuinely open
```

**Body**:
```
Every line of code is AGPL-3.0. If a corporation deploys our work as a
service, they must share their improvements back — or buy a commercial
license that funds the contributors.

Every Seed Package is CC-BY-NC-SA-4.0. Contributors keep their copyright.
Non-commercial sharing is free; commercial use funds the network.

This isn't "open-core" theater. The full pipeline — generator, auditor,
IPFS exchange, Obsidian plugin — is in the repo.
```

**CTAs**:
- `Browse the repo →` → `https://github.com/CTO-goldmanglobal/gg-hiveagi`
- `Contributor guide →` → `https://github.com/CTO-goldmanglobal/gg-hiveagi/blob/main/CONTRIBUTING.md`

---

### Section 6 — Built to be trusted

**Section H2**:
```
Built to be trusted
```

**Body** (bullet list, no fluff):
- **Australian-built.** Sydney-based team, AU data hosting, ready for the 2026 Privacy Act.
- **Privacy by code.** PII stripping (faces, plates) runs *before* any LLM call. There is no `--skip-blur` flag — we checked.
- **Real-world signal.** Goldman Forge's live client deployments across transport, travel, and finance feed Labs genuine edge cases.
- **Reproducible.** Every commit runs CI. Mock mode lets anyone verify the pipeline without API keys.

---

### Section 7 — Want to build with us? (final CTA)

**H2**:
```
Want to build with us?
```

**Two columns** (side by side on desktop, stacked on mobile):

**Left column — Contributors & researchers**
```
Star, fork, or open a PR.
github.com/CTO-goldmanglobal/gg-hiveagi
```
→ make the URL a link

**Right column — Enterprise R&D & collaboration**
```
Talk to us about commercial licensing, custom Seed Packages,
or research partnerships.
cto@goldmanglobal.com.au
```
→ make the email a `mailto:` link

---

## 4. Visual direction

**You already built the Forge site.** Labs extends that system with a deliberate distinction.

| Element | Spec |
| :--- | :--- |
| **Type (prose)** | Same sans-serif as Forge site |
| **Type (technical)** | A mono font for model names, CIDs, code, the meta row on cards (e.g. JetBrains Mono, IBM Plex Mono) |
| **Base palette** | Match Forge (deep navy / charcoal base) |
| **Accent** | **Gold/amber** — distinct from Forge's accent, so visitors feel the brand shift. Used sparingly: eyebrows, hover states, the `LIVE` tag, primary CTA. |
| **What to avoid** | Purple gradients (every AI startup uses them). Glowing brains. Stock "AI" blobs. Robot hands. |
| **Imagery** | Real artifacts over stock. Show actual CIDs, actual frontmatter, actual `audit_log` comments as visual texture. They're credibility. |
| **Motion** | Minimal. Hero animation only. No scroll-triggered fade-ins on every section. |

---

## 5. Wireframe (desktop)

```
┌─────────────────────────────────────────────────────────────────┐
│  [GG FORGE nav]              Work  Research  About  Contact     │  ← add "Research" to main nav
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         THE RESEARCH ENGINE BEHIND GOLDMAN FORGE                │
│                                                                 │
│      Building AI that learns to understand                      │
│      humans — not the other way around.                         │
│                                                                 │
│   Goldman Global Research Labs is our open-source R&D arm...    │
│                                                                 │
│   [★ Star on GitHub]    [Read the research →]                  │
│                                                                 │
│   [hero animation: frame → blur → CID]                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  WHAT WE'RE BUILDING                                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                    │
│  │ Hive.AGI   │  │ Project 2 │  │ Project 3 │                    │
│  │ ● LIVE     │  │ ○ PLANNING│  │ ○ PLANNING│                    │
│  └───────────┘  └───────────┘  └───────────┘                    │
├─────────────────────────────────────────────────────────────────┤
│  HOW IT WORKS                                                   │
│  [capture] → [generate] → [audit] → [publish]                   │
├─────────────────────────────────────────────────────────────────┤
│  THE DIFFERENCE                                                 │
│  [comparison table: 2 columns × 6 rows]                         │
├─────────────────────────────────────────────────────────────────┤
│  GENUINELY OPEN                                                 │
│  [body + 2 CTAs]                                                │
├─────────────────────────────────────────────────────────────────┤
│  BUILT TO BE TRUSTED                                            │
│  [4 bullets]                                                    │
├─────────────────────────────────────────────────────────────────┤
│  WANT TO BUILD WITH US?                                         │
│  [Contributors]    [Enterprise R&D]                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Technical specs

| Field | Value |
| :--- | :--- |
| **URL** | `https://www.goldmanglobal.com.au/research` |
| **Nav label** | `Research` — add to Forge's main nav (between "Work" and "About") |
| **Page title** (SEO) | `Goldman Global Research Labs — Human-perspective, decentralized AI` |
| **Meta description** | `Open-source R&D building human-perspective AI: dual-LLM audited, IPFS-published, AGPL-licensed. The research engine behind Goldman Forge.` |
| **OG image** | Pipeline diagram (frame → blur → CID), branded. 1200×630px |
| **Canonical** | `https://www.goldmanglobal.com.au/research` |
| **Robots** | `index, follow` |
| **Schema.org** | `Organization` + `SoftwareSourceCode` (reference the GitHub repo) |

**CMS assumption**: whatever Forge uses (the site reads as Webflow/Framer-class). Extend the existing CMS with a "Research" page template — do not introduce a new stack.

**Analytics**: same tag as Forge site. Add a custom event `research_cta_click` with the CTA label, so we can measure which CTAs convert.

---

## 7. Assets you need to produce

The designer needs to create/source these. None exist yet.

| Asset | Spec | Notes |
| :--- | :--- | :--- |
| **Hero animation** | ~6s loop, MP4 + WebM, <2MB | Frame → blur → base64 → JSON → CID. Can be built from real screenshots of the pipeline running. Static fallback required for reduced-motion. |
| **OG image** | 1200×630px | Pipeline diagram, branded, with Goldman Global Research Labs wordmark |
| **Pipeline diagram** (Section 3) | SVG preferred | 4-stage horizontal flow. Must work stacked-vertical on mobile. |
| **Favicon** (if Labs gets sub-brand) | optional | Not required if page sits under the Forge domain/favicon |
| **Project card thumbnails** | 3× (for the 3 cards) | Real screenshots/artifacts preferred. Hive.AGI card: a real CID + frontmatter snippet. Placeholder cards: muted, no image needed. |

**Do NOT source from stock libraries.** The whole positioning is "real artifacts, not AI-marketing stock." If you can't produce a real screenshot, use a clean typographic treatment instead.

---

## 8. Acceptance criteria (definition of done)

The page is done when ALL of these are true:

- [ ] Live at `goldmanglobal.com.au/research`
- [ ] "Research" appears in the main nav across all Forge pages
- [ ] All 7 sections present, copy matches this doc verbatim
- [ ] Mobile layout: pipeline stacks vertically, all 4 stages visible without horizontal scroll
- [ ] Both CTAs in hero work (GitHub link opens repo; "Read the research" smooth-scrolls to Section 3)
- [ ] All outbound links use the exact URLs in this doc
- [ ] `cto@goldmanglobal.com.au` is a `mailto:` link
- [ ] Hero animation has a static fallback for `prefers-reduced-motion`
- [ ] OG image + meta description + page title set correctly (test with opengraph.xyz)
- [ ] No purple gradients, no glowing brains, no stock AI imagery
- [ ] Page loads in <3s on mobile (Lighthouse perf ≥ 90)
- [ ] Schema.org `Organization` + `SoftwareSourceCode` markup validates
- [ ] Honest footnote (Section 3) is present and visible — not hidden behind a toggle
- [ ] Analytics `research_cta_click` event fires on every CTA

---

## 9. Open questions (decisions you need to make)

These are NOT for the designer — these are for you (Goldman Global) before/during the build:

1. **Goldman Global vs Goldman Forge in the nav.** The existing site is branded "Goldman Forge" (or "Goldman Forge" / "Goldman Global Financial" in the footer). Should the parent brand be "Goldman Global" with "Forge" and "Labs" as divisions? Or is "Forge" the consumer brand and "Labs" sits under it? *Recommendation: rebrand nav to "Goldman Global" with sub-brands Forge + Labs — cleaner long-term, but it's a bigger decision than this page.*

2. **Logo / wordmark for "Research Labs".** Is there an existing Labs logo, or does the designer create one? *Recommendation: typographic wordmark for v1 — "Goldman Global Research Labs" set in the Forge typeface with the gold accent. No custom logo yet.*

3. **Is Labs a legally distinct entity?** Affects footer legal text, privacy policy, and whether the page needs its own legal pages or inherits Forge's. *Recommendation: treat as a division of Goldman Global for v1; reuse Forge legal pages with a Labs-specific contact.*

4. **Hero animation: real or illustrated?** Real screenshots of the pipeline running (most credible, takes a day to produce) vs clean illustration (faster, less credible). *Recommendation: real. The whole brand is "show the real artifacts."*

5. **What's Project 2 and 3?** The placeholder cards say "Coming." If you have even a rough direction for the next research line, name it (e.g. "On-device perception for privacy-preserving capture"). Empty placeholders feel honest now but will look abandoned in 3 months. *Recommendation: leave as "Coming" for launch; add a real direction within 90 days or remove the placeholders.*

6. **Newsletter / RSS for research updates?** The brand docs explicitly say "no dead signup form." But a real research feed (RSS from GitHub releases, or a Substack) would serve the "contributors & researchers" audience. *Recommendation: add an RSS link to GitHub releases for v1; real newsletter only when you'll commit to posting.*

---

## 10. What this page deliberately does NOT do

These were intentional decisions. Do not add them without a positioning update.

- ❌ **No team headshots.** Labs is small; inflating the team erodes credibility. Show the work, not the people (yet).
- ❌ **No testimonials.** No Labs clients exist yet. Forge testimonials belong on the Forge site, not here — would misattribute.
- ❌ **No "trusted by" logo wall.** Same reason — Forge client logos would imply Labs endorsements.
- ❌ **No email signup form.** A dead form erodes trust. Add only when there's a real newsletter.
- ❌ **No "AI is going to change everything" hero.** State what we build, not what AI will do.
- ❌ **No pricing.** Labs is open-source research, not a product. Commercial licensing is via contact, not a price table.

---

## 11. Source documents (for deeper context)

Hand this doc to the designer. The two below are for you (and anyone who wants the strategic "why"):

| Doc | Purpose | URL |
| :--- | :--- | :--- |
| **This handoff doc** | The build brief | `brand/HANDOFF-research-page.md` |
| Positioning brief (strategy) | The "why" behind every choice | `brand/research-labs-positioning-brief.md` |
| Page copy (source of truth for copy) | If this doc and that one differ on copy, that one wins | `brand/showcase-page-copy.md` |
| The actual project | Browse what you're showcasing | https://github.com/CTO-goldmanglobal/gg-hiveagi |

---

## 12. Post-launch (out of scope for this handoff)

Things to plan for after `/research` ships:

- A `/research/hive-agi` subpage (deep dive on the one live project) — only when Hive.AGI has a real milestone (e.g. first external contributor, or P2.5 peer-sync shipping)
- A blog / writeup feed for research outputs
- Cross-linking from Forge case studies to Labs research ("the tech behind this deployment")
- A Labs-branded GitHub org (currently lives under `CTO-goldmanglobal/gg-hiveagi` — consider `goldman-global-research` org when there's a second project)

---

*This handoff is the single source of truth for the `/research` build. If anything is ambiguous, the answer is probably in the positioning brief (`brand/research-labs-positioning-brief.md`). If it's still ambiguous, email cto@goldmanglobal.com.au — do not guess.*
