# The Seed Doctrine

> **First principles.** Every architecture decision in this project — the
> three-system model, the provenance gates, the routing, the discard policy —
> traces back to the claims in this document. If a design contradicts what is
> written here, the design is wrong, not the doctrine.
>
> **Author:** Finn, founder. **Date:** 2026-08-05.

---

## 1. Imagination is the seed

The seed of this project is not data, not compute, not a model. **The seed is
imagination.**

Current machine intelligence is powerful but bounded. It interpolates within
what it has already seen. It cannot reach beyond the perimeter of its training,
because it has no lived experience of the world outside that perimeter. It
computes; it does not imagine. And without imagination, there is a hard ceiling
on what intelligence can become — a ceiling no amount of scale will lift.

**AGI requires unlimited imagination.** Imagination cannot be summoned from a
corpus. It arises only from a particular kind of being-in-the-world: a human,
at a particular time, in a particular place, attending to a particular event,
and finding it meaningful in a way no other being would. That act — a
perspective taking notice — is the only source of new imagination in any
system, machine or otherwise.

This is why the project exists. HiveAGI does not build AGI directly. It does
something more foundational: it captures the only signal from which AGI's
missing dimension can grow. The signal is human perspective. The seed is the
imagination that perspective carries.

---

## 2. Nothing is right or wrong — only situated

A machine wants every question to have a right answer and a wrong one. That is
its ontology: true or false, keep or discard.

**Human judgment does not work that way.** Nothing is right or wrong in the
abstract. Rightness is a function of three variables: **time**, **place**, and
**event**. The same frame, the same tag, the same choice can be exactly right
at this moment in this place for this event, and exactly wrong an hour later
two streets away. Rightness is *situated*. It is complex. It cannot be reduced
to a label that holds across all contexts — which is precisely why scraping
the internet for "what humans think" cannot reproduce it. The internet records
conclusions, stripped of their situation. HiveAGI records the situation
alongside the conclusion. That is the entire difference.

This single principle — that rightness is time, place, event — is the load-
bearing claim of the thesis. Every other design decision follows from taking
it seriously.

---

## 3. The first warning — locking the limit (the apple tree)

A tree's fundamental nature constrains its fruit. Whatever the soil, the
sunlight, the care, an apple tree will never bear pears. Its output is locked
by what it is.

The same danger applies to a knowledge system. **If our fundamental creativity
and guidelines lock the limit, we become an apple tree.** We will only ever
produce what the rules already permitted. The guidelines, written to protect
integrity, will quietly strangle the very imagination they were meant to serve.
The network will converge on its own priors instead of reaching beyond them.

This is the deepest risk of over-control, and it is invisible until it has
already happened. A provenance gate that says "no AI-assisted signal may ever
enter Labs, under any condition, forever" feels safe. It is not safe. It is an
apple tree. It guarantees the network can only grow what its founders already
imagined on day one — and that is the opposite of the thesis.

---

## 4. The second warning — openness without gravity (the clustering danger)

The first warning says: do not lock. It would be a mistake to read it as
"there should be no constraint at all." Unlimited imagination, left to itself,
has its own failure mode — and it is the mirror image of the apple tree.

An old Chinese proverb holds that *things of a kind gather, and people of like
nature draw together.* This is the dynamics of any open network: similarity
attracts similarity, and clusters self-reinforce. In the three-dimensional
overlap structure of this project — where circles share philosophy,
infrastructure, and signal — that dynamic cuts both ways.

**The danger is that off-thesis circles form and begin to overlap each other
more than they overlap the seed.** Because there is no hard limit, polluting
or hostile signal finds its own kind: a misleading tag attracts more
misleading tags; a synthetic consensus attracts more synthetic consensus; a
drifting sub-network attracts more drift. In three dimensions these overlaps
compound — the danger circles stick to each other, gain cohesion, and behave
as a single mass. Then one of two things happens:

- **Fragmentation.** The danger cluster drifts away from the main development,
  carrying energy, attention, and signal with it into a void where it neither
  contributes to nor is corrected by the whole.
- **Pollution.** The danger cluster grows strong enough to become a competing
  gravitational center, pulling the main development toward itself and bending
  the thesis off its axis.

Both outcomes break the project. Fragmentation starves the seed of the
perspective it needs to grow. Pollution corrupts the seed's nature until the
network optimizes for the wrong thing while still calling it human perspective.

This is not an adversarial-actor problem alone (though it includes that —
Sybil nodes, coordinated false tags, replay attacks, covered by Study F). It
is a structural problem of *any* system that permits unlimited growth: without
a gravitational center, openness does not produce a garden. It produces weeds.

---

## 5. The doctrine — protect integrity, never lock the limit, keep the seed the strongest attractor

The three claims compose into a single rule.

**Protect integrity.** Provenance, consent, honest lineage, human override.
Non-negotiable; without it the signal is noise.

**Never lock the limit.** Preserve the possibility that the network discovers
something its founders did not foresee. The guidelines must stay open to their
own revision.

**Keep the seed the strongest attractor.** This is the balance to the second
warning. Openness permits new circles; gravity ensures they orbit the seed
rather than forming competing centers. The seed must remain the most
attractive thing to gather around — through quality, through honesty, through
the clarity of the AGI north star — so that healthy circles form around it
more readily than danger circles form around each other.

The boundary, stated precisely:

> **The gate labels honestly. It does not forbid discovery. And the network
> weights influence toward circles whose overlap with the seed exceeds their
> overlap with each other.**

An insight that arrives through an AI-assisted wandering path is not banned
from the network. It enters — labeled as `ai_assisted_meta`, with its full
lineage recorded — and the network measures whether it converges with the seed
or clusters with drift. The boundary is on honesty, not on existence. Forbid
the lie (mislabeling); never forbid the discovery. But do not, in the name of
openness, grant equal gravitational weight to a circle that is drifting away.

Gravity is maintained by engineering that already exists or is planned:
**honest labeling** (provenance) so each circle's nature is visible;
**convergence measurement** so drift is detected; **the trust layer** (spam
filter, appreciation, contribution, improvement boards) so circles aligned
with the seed's DNA carry more influence than circles that merely reinforce
each other; **quarantine rather than deletion** so drift is observable and
correctable, and so a legitimate new village is not destroyed because it
looked, at first, like a weed.

---

## 6. Serendipity has a place, but it is not the justification

The doctrine must preserve room for the kind of discovery that no plan
produces. An old Chinese poem describes the experience: the traveler believes
the mountains and rivers have closed every road, when the willows darken and
the flowers brighten, and another village appears — one that could only be
found by wandering, never by aiming.

The plugin (the vibe-coding tool) exists in part to keep that freedom open:
low-cost local play, no research deliverable attached, permission to follow
the wrong path. Most wandering yields nothing measurable. Some of it yields a
village no direct plan would have reached.

The honesty matters here. You cannot engineer the appearance of the village;
you can only create the conditions for it. The plugin earns its place as a
development tool regardless. The serendipity is upside, never the
justification — and when it arrives, it enters through the same honest gate
as everything else, labeled for what it is. A village that demands to enter
unlabeled is not a village. It is the first circle of a danger cluster.

---

## 7. What this means for the architecture

The three systems are not three boxes. They are three expressions of one seed,
arranged so that the seed's gravity dominates:

- **HiveAGI is the seed.** Everything grows from it.
- **Goldman (the application) overlaps the seed.** Same DNA — routing,
  provenance discipline, the belief that human judgment is the asset.
- **The plugin overlaps the seed and Goldman.** It shares the machine, the
  model, the method. Its line to AGI is indirect — it does not aim at AGI;
  it wanders, and occasionally a village appears.
- **All three sit inside the AGI circle.** The focus never moves. What
  multiplies is the expression, not the goal.

The circles overlap at **philosophy and infrastructure** — the seed's DNA.
The **content** inside each circle (Lab tags, commercial assets, dev prompts)
never crosses. Provenance draws that line. The doctrine draws the wider one:
protect the line, but never let it become a wall around imagination — and
never let the openness become a drift toward weeds.

---

## 8. The single test for any future decision

When a future design choice is in doubt, apply this test, in order:

> **Does this protect integrity? Does it lock the limit? Does it keep the seed
> the strongest attractor?**

- Forbidding a mislabeled provenance → protects integrity. Keep it.
- Forbidding an honestly-labeled AI-assisted insight from ever entering the
  network → locks the limit. Reject it.
- Requiring human confirmation before a tag becomes Labs-eligible → protects
  integrity. Keep it.
- Mandating that only the founders' original framing of "human perspective"
  may ever define the signal → locks the limit. Reject it.
- A discard policy measured by meaning lost per compute saved → protects
  integrity and keeps the seed attractive. Keep it.
- A discard target of "95 percent gone" treated as success → locks the limit
  and starves the seed. Reject it.
- Equal weighting to a circle whose tags converge with drift as to one whose
  tags converge with the seed → surrenders gravity. Reject it.

If you cannot tell which side a decision falls on, default to **labeling over
forbidding**, and to **measuring over assuming.** Those two defaults have
never failed this project.

---

## 9. What this doctrine is not

- **Not** a license to dilute the signal. Provenance stays strict; labeling
  stays honest; consent stays human.
- **Not** a claim that anything goes. The hard blocks (no destructive discard
  until falsified; no public IPFS until encrypted) stand — they protect
  beings, not preferences.
- **Not** a prediction that serendipity will arrive. It may not.
- **Not** a static document. This doctrine is itself a seed. It must stay open
  to its own revision — by the founder, by the council, by the village the
  network one day finds that no one planned for.

---

*The v3 architecture (`UNIFIED-ARCHITECTURE-v3.md`) is the engineering
expression of this doctrine. Where they appear to conflict, the doctrine wins
— and the architecture is revised to match.*
