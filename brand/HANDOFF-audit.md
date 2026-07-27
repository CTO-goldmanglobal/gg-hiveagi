# Handoff Doc Audit (Opus review)

> Full audit of `HANDOFF-research-page.md` conducted before designer handoff.
> Verdict: **B+ handoff. Strategically excellent; weak on design-system specifics.**
> Recommendation: **revise before handoff (~2–3 hours, not a rewrite).**

---

## Overall verdict

A strong B+ — noticeably above average for a founder-authored brief. Copy is genuinely final, strategic "why" is well-anchored, wireframe is clear, technical claims (repo URL, AGPL-3.0 + CC-BY-NC-SA-4.0, CI badge path, "no `--skip-blur`", Obsidian plugin existence) all **verified true against the repo**.

Headline gap: **not content — it's design-system specifics.** A Webflow designer cannot build this without emailing, because §4 "Visual direction" gives adjectives ("subtle", "muted", "sparingly", "gold accent") where it needs numbers (hex codes, px/rem scales, type ramp, breakpoints, spacing tokens). Plus three concrete copy contradictions with the named source-of-truth.

---

## CRITICAL (blocks the build)

### C1. Three verbatim copy contradictions with `showcase-page-copy.md`

The handoff §11 states *"If this doc and that one differ on copy, that one wins"* — then disagrees with it in three places.

| # | Location | Handoff says | Source-of-truth says | Resolution |
|---|---|---|---|---|
| 1 | §3 Hero, secondary CTA | `Read the research` | wireframe says `Read the research brief` | **Use `Read the research`** — shorter, matches scroll target |
| 2 | §3 "How it works" intro | `One pipeline. Four stages.` | `One pipeline. Five stages.` | **Four is correct** — diagram shows 4 boxes |
| 3 | §4 comparison-table header | `Corporate AI labs` | `Corporate AGI labs` | **Use `Corporate AI labs`** — positioning brief §9 guardrail says don't call it "AGI" as if it exists today |

**Fix:** reconcile in `showcase-page-copy.md`. Then flip §11 hierarchy: *this doc's §3 wins for /research page.*

---

## HIGH (will cause rework / emails)

### H1. No actual design tokens
"Gold accent", "subtle", "muted", "deep navy" are all undefined. Every adjective is a guess.

- **Gold/amber accent** — `#D4A017`? `#F5B700`? `#E8A33D`? Designer will pick one, founder will say "too yellow/brown."
- **"Deep navy / charcoal base"** — two different colors named as one. Navy (`#0B1F3A`) ≠ charcoal (`#1A1A1A`).
- **"Muted"** (used 5×) — what hex? what opacity?
- **"Subtle" animation** — "~6s loop" is the only spec. No frame count, no easing, no transition durations.
- **"Used sparingly"** — not buildable.

**Fix:** state exact hex values + a 2-stop hover scale + specify exactly which elements get the accent.

### H2. No type scale, no spacing scale, no breakpoints, no max-width
Webflow designer needs these as numbers. Currently zero numeric specs.

### H3. No interactive-state specs
Button hover/active/disabled/focus, link hover, card hover, nav active state — none specified.

### H4. Accessibility beyond reduced-motion is essentially uncovered
For a page boasting credibility to a technical audience (many use screen readers / keyboard nav / high-contrast), this is thin. Needs: color contrast (WCAG AA), hero animation `aria-hidden`, SVG `<title>/<desc>/role="img"`, real `<table>` semantics, focus states, skip link.

### H5. OQ-3 (legal entity) is left open but copy already commits to an answer
§9.3 asks "Is Labs legally distinct?" but §3 copy already says "our open-source R&D arm" and §6 says "Sydney-based team" — both presuppose Labs is *not* separate. `about-page-copy.md` is unequivocal: "One company, two jobs."

**Fix:** close OQ-3. State Labs is a division, inherits Forge legal pages.

---

## MEDIUM (worth adding)

- **M1.** No footer legal spec; no experimental-research disclaimer (protects Goldman legally; on-brand with "honest scope" voice).
- **M2.** CLA / IP-assignment implication of contributor CTA not surfaced (real legal gap).
- **M3.** No analytics-platform specifics; no cookie-consent call for AU (GA4 needs banner; Plausible doesn't).
- **M4.** "Read the research" CTA scrolls to a pipeline diagram, not anything a visitor recognizes as "research". Relabel to "See how it works →".
- **M5.** No maintenance plan / ownership after launch (who updates when Project 2 ships, P2.5 ships, CI goes red).
- **M6.** No 404 / fallback for repo private/deleted/renamed. CI badge `<img>` would break visibly.
- **M7.** Nav-transition / brand-shift cue under-specified. Nav is shared across Forge + Labs — does active-link color shift to gold? Does logo swap? (Wireframe still shows "[GG FORGE nav]".)

---

## LOW (nice-to-have)

- **L1.** OG image + hero animation say "produce from real screenshots" with no art direction. Point designer at exact files (`seed_output/.../entry_001.md`, mock CID).
- **L2.** `Schema.org` spec is vague — paste a 15-line JSON-LD template.
- **L3.** "Honest footnote" acceptance check could add "not lazy-loaded or behind Read-more".
- **L4.** Comparison to best-in-class (Anthropic/Linear/Vercel-tier studio) — missing: Figma/Webflow share link to Forge design system; CMS collection schema for cards; Lighthouse-perf with hero video (spec `preload="none"` below fold); stakeholder sign-off row in header.
- **L5.** zh-HK README exists, About page is bilingual, /research is English-only — note this is intentional for v1.

---

## New open questions to add to §9

Existing 6 OQs are good. Missing:

- **OQ-7 (legal):** AU Privacy Act 2026 vs GDPR. Open-source will get global traffic — EU visitor + GA4 = GDPR applies. Geo-block analytics, serve consent banner, or use consent-free tool?
- **OQ-8 (legal/IP):** CLA in CONTRIBUTING.md is checkbox-on-PR, not signed agreement. Reviewed by AU lawyer? Enforceable? PRs merged before checkbox added?
- **OQ-9 (operational):** Who owns the Webflow project after launch? Founder, or agency that built Forge?
- **OQ-10 (i18n):** zh-HK /research in scope for v1 or v2? About sets bilingual precedent; /research breaks it.
- **OQ-11 (brand):** Footer legal entity name + ABN. Designer can't put "© 2026 [WHAT ENTITY]" without guessing.

---

## Ship-or-revise recommendation

**Revise before handoff — 2–3 hours, not a rewrite.** The bones are excellent. Do four things:

1. **Fix 3 copy contradictions (C1)** + flip §11 hierarchy. ~20 min.
2. **Add design tokens (H1, H2)** — hex codes, type ramp, spacing scale, breakpoints. ~45 min.
3. **Add states + a11y blocks (H3, H4)** as new subsections. ~30 min.
4. **Close OQ-3 + add 5 new OQs** so founder makes legal/analytics calls *during* build. ~15 min.

MEDIUM + LOW can ship as v1.1 or be answered in kickoff call.

One thing worth saying plainly: the *strategic* layer (positioning alignment, "what NOT to do", honest-footnote pattern, anti-hype guardrails) is genuinely better than 90% of founder-authored briefs. The weakness is purely visual-system-with-words-not-numbers. Fix that and it's an A.
