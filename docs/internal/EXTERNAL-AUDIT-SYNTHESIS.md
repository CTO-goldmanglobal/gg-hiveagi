# External Audit Synthesis — OpenAI + Claude Reviews

> Two independent audits of HiveAGI, run on the same prompt. Both arrived at
> the same core finding from different angles. This document synthesizes their
> insights and defines what changes.

---

## The auditors

| Auditor | Tone | Style |
|:---|:---|:---|
| **OpenAI (GPT)** | Generous, architectural, constructive | Reframe the thesis rather than attack it. Proposed "PerspectiveEvent" primitive, capability matrix, red circles. Scored everything 2-9/10. |
| **Claude** | Brutal, surgical, uncomfortable | Attacked the numbers. "95% machine perspective with a human garnish." "n=1." Told us to stop claiming AGI. |

Both are right. They're describing the same problem from different sides.

---

## Where they AGREE (the consensus)

### 1. Construct validity is the weakest link
**OpenAI:** "Your current implicit equation: human chose clip X → X reflects what a human finds beautiful → beauty reflects human perspective → enough perspective data leads toward AGI. The first arrow is reasonable. The next three are not established."

**Claude:** "The authors have not demonstrated that their operational variable — editor selection override on curated professional imagery — is a valid proxy for human perspective."

**Consensus:** We built infrastructure for collecting human-perspective data, but we haven't proven the data we're collecting IS human perspective. It might be "professional editing preference within an already-curated distribution."

### 2. n=1 is not a dataset
**OpenAI:** "14 judgments is proof of collection, not evidence of a general signal."

**Claude:** "'What humans find beautiful' is currently 'what Finn finds beautiful.' Any distributional claim from one editor is a personal preference model with a grand name."

**Consensus:** One editor's judgments cannot support any claim about "human" perspective. Cross-human aggregation isn't a missing feature — it's the difference between the claim and the data.

### 3. Stock vs. human-capture are DIFFERENT variables
**OpenAI:** "Choosing between professionally-shot clips measures taste within a curated distribution. Glasses capture measures attention allocation in an uncurated world. Different variables."

**Claude:** "Stop treating taste and salience as one substance... Your source_type field keeps them separable — good — but your prose pools them, and that's where you're fooling yourself."

**Consensus:** Our `source_type` tag is necessary but not sufficient. The PROSE (docs, thesis statements) conflates two different psychological constructs. The code is honest; the narrative isn't.

### 4. The next step is EVIDENCE, not more capability
**OpenAI:** "The next milestone should not be more capability. It should be evidence that the signal means what you think it means."

**Claude:** "There is not one held-out number anywhere in this retrospective showing the accumulated data improves anything."

**Consensus:** Stop building. Start measuring. Run an experiment that could FAIL.

### 5. Pairwise preference + active learning is the right experiment
**OpenAI:** "Present A vs B. Ask 'which would you keep?' ... Then ask the model: which comparison would teach me most about this human?"

**Claude:** "Before the editor judges, have M3 predict what they'll choose and log the prediction with confidence... the items where the model was confident and wrong are your gold."

**Consensus:** Move from accept/reject to pairwise comparison. Add model-prediction-before-judgment. The override delta becomes calibrated.

---

## Where they DIFFER (the disagreement is useful)

| Question | OpenAI says | Claude says |
|:---|:---|:---|
| **The hybrid seed** | Defensible if you split stimulus_provenance from judgment_provenance | The problem is mechanical: publishing a judgment without the stimulus it judged is an orphan label. Publish a feature-space surrogate instead. |
| **The AGI framing** | Reframe as "Human Perspective Learning Infrastructure" — don't call it AGI yet | "Stop claiming it." Period. The AGI framing converts a good asset into an unsupported claim. |
| **The commercial model** | "Human Override Layer" API — AI proposes, human corrects, Hive captures why | Real-estate photo culling (500→30 = 500 labeled decisions per job) or sell the "disagreement map" |
| **The wiki** | Good flywheel, but keep an immutable event store SEPARATE from the wiki (avoid synthetic feedback loop) | Didn't address wiki architecture |

---

## The 5 most actionable insights (from both)

### 1. Split the provenance into two dimensions (OpenAI)
```
stimulus_provenance: stock (blocked from Labs raw media)
judgment_provenance: human (eligible for Labs signal)
```
Don't merge them. A human judgment about stock is a "human preference event." A human judgment about their own capture is a "human preference event + human perceptual-context event." These are NOT equivalent.

### 2. Publish feature-space surrogates, not orphan labels (Claude)
When shipping preference data derived from stock clips, don't ship the judgment alone (unusable — downstream can't see what was judged). Ship the **perceptual hash + metric vector + M3 tag vector**. Downstream can reconstruct the preference pair in feature space without redistributing licensed frames. Novel, legal, defensible.

### 3. Run G0: Falsification Circle (both)
Before automating (Circle G), run an experiment that could FAIL:
- 1,000+ pairwise judgments
- Multiple humans (even 5-10)
- Same stimuli, randomized order, hidden repeat pairs
- Measure: intra-human consistency, inter-human disagreement, model prediction accuracy
- M3 predicts before human judges — log confidence
- Items where M3 was confident and wrong = gold

### 4. Model-predicts-human-first (Claude, OpenAI agrees)
Before the human judges, M3 predicts what they'll choose + confidence score. Now every judgment carries calibrated difficulty. The override signal becomes: "model was 90% confident, human chose the OTHER one." That's worth 10× a plain accept/reject.

### 5. "Red circles" — try to kill the thesis (OpenAI)
Every 2-3 build circles, run one experiment designed to DISPROVE the thesis:
- Red 1: Can the same editor reproduce their preferences?
- Red 2: Does training on stock preferences predict phone-footage preferences?
- Red 3: Does Person A's travel taste predict anything outside travel?

If the thesis survives red circles, it's real. If it doesn't, we pivoted early.

---

## What this changes about the project

### Thesis correction
**Old:** "Computers learn what humans find beautiful."
**Corrected:** "Computers learn what becomes significant to humans, in context, by observing attention, choices, corrections, actions and reflection."

Video selection is Perspective Domain #1, not the whole thesis. Beauty is one signal, not the signal.

### Naming correction
**Old:** "beauty standard"
**Better:** "perspective distribution" (per OpenAI) — because "standard" implies averaging humans together, but the disagreement IS the signal.

### Circle reordering
```
OLD:                          CORRECTED:
F (full loop) ✅              F (full loop) ✅
G (automation)                G0 (falsification — can preferences be measured?)
                              G (automation — only what G0 shows is worth collecting)
                              H (stock vs phone vs glasses — does it transfer?)
                              I (multi-human — same stimuli, different people)
                              J (generalization — can learned preferences predict?)
```

### The immediate next experiment
Not Circle G (automation). **Circle G0: Human Signal Benchmark.**

```
1,000+ pairwise judgments (A vs B, "which would you keep?")
20-50 humans if possible (even 5-10 is infinitely better than 1)
same stimuli, randomized order, hidden repeat pairs
M3 predicts before each judgment, logs confidence

measure:
  intra-human consistency (can preferences be reproduced?)
  inter-human disagreement (is there a shared signal or just personal taste?)
  model prediction accuracy (does the model add value?)
  override information gain (where was the model wrong?)
```

If this passes: the thesis has legs. Automate.
If this fails: we learned professional-editing preference ≠ human perspective, before wasting 20 more circles.

---

## The uncomfortable truth both said

**OpenAI:** "Don't prematurely call it AGI."

**Claude:** "The human-perspective system is, by volume, 95% machine perspective with a human garnish."

We have built excellent infrastructure for a claim we haven't tested. The next circle must be the test, not more infrastructure.

---

## What to tell Cursor

The automation (Circle G) is still needed — Forge needs it. But it's now a **parallel track**, not the main research path.

**Research path:** G0 (falsification) → H (POV capture) → I (multi-human)
**Commercial path:** G (automation) → more tours → revenue

Both feed the same Obsidian vault. Both produce judgment data. But the research path is where the thesis gets proven or killed.
