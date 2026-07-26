# About Page — Copy & Layout

> For `goldmanglobal.com.au/about`. Bilingual by design:
> **English on top, Chinese on bottom. Hard separator between. Never mixed.**

---

## Layout rule (non-negotiable)

```
┌─────────────────────────────────────────────┐
│  [ENGLISH VERSION — full page]              │
│  Hero, story, two brands, values, contact   │
│  All in English.                            │
├─────────────────────────────────────────────┤  ← hard visual divider
│  ═════════════════════════════════════════  │
│  繁體中文 ↓                                  │  (or a language jump link)
│  ═════════════════════════════════════════  │
├─────────────────────────────────────────────┤
│  [繁體中文 VERSION — full page]              │
│  Same structure, same content, Cantonese    │
└─────────────────────────────────────────────┘
```

- **English section first, complete and self-contained.**
- **One hard divider** (horizontal rule + a `繁體中文 ↓` jump link that smooth-scrolls).
- **Chinese section second, complete and self-contained.**
- **No sentence contains both languages.** No inline mixing. No "Goldman Global 高盛環球".
- Brand names stay in English in both versions: "Goldman Global", "Goldman Forge", "Research Labs", "Hive.AGI" — these are proper nouns, not translated.
- A top-of-page anchor link lets Chinese-first readers jump straight down: `[English ↓](#english) | [繁體中文](#中文)` — but default landing is English.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ENGLISH VERSION (top of page)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Hero

**Eyebrow** (small, accent):
```
ABOUT GOLDMAN GLOBAL
```

**H1**:
```
An Australian AI company with two faces.
```

**Subhead**:
```
Goldman Global builds and researches artificial intelligence for the
Australian market. We ship production AI for businesses through Goldman
Forge, and publish open-source research through Goldman Global Research
Labs. One company, two jobs.
```

---

### Section: Who we are

**H2**:
```
Who we are
```

**Body**:
```
Goldman Global is a Sydney-based AI company. We don't consult, and we
don't sell slideware — we build software that runs.

We started by rebuilding foundational business systems for our own
ventures across transport, travel, and finance. Those deployments became
the proof. Today we deliver the same systems to other Australian
businesses through Goldman Forge, and we publish the underlying research
open-source through Research Labs.
```

---

### Section: Two brands, one company

**H2**:
```
Two brands, one company
```

**Two cards side-by-side**:

**Card A — Goldman Forge**
- Tag: `COMMERCIAL`
- Title: `Goldman Forge`
- Body:
  ```
  Our commercial AI delivery arm. Builds and deploys AI Front Desk
  receptionists, booking systems, and digital staff for Australian
  businesses. Fixed-price, fast delivery, hosted in Sydney.
  ```
- CTA: `See Forge →` → `/` (Forge homepage)

**Card B — Goldman Global Research Labs**
- Tag: `OPEN-SOURCE RESEARCH`
- Title: `Research Labs`
- Body:
  ```
  Our open-source R&D arm. Publishes AGPL-licensed research on
  human-perspective, decentralized, dual-LLM-audited AI. The first
  project is Hive.AGI — a human-perspective knowledge network.
  ```
- CTA: `See Labs →` → `/research`

**Under the cards, one line**:
```
The two brands share a parent, a team, and real-world signal.
Forge deployments feed Labs genuine edge cases; Labs' open protocols
give Forge a defensible foundation.
```

---

### Section: What we believe

**H2**:
```
What we believe
```

**Body** (3 short stances):

**1. AI should adapt to people, not the other way around.**
```
Most AI tools force humans to learn new interfaces, new vocabularies,
new logics. We build systems that meet people where they are — in
Cantonese, in English, in the workflows they already have.
```

**2. Real AI is built, not bought.**
```
Bolting an AI API onto a 15-year-old CRM doesn't make a business
AI-native. We rebuild the foundational software so the intelligence is
in the system, not a chatbot bolted on top.
```

**3. Open beats closed for research.**
```
Our research code is AGPL. Our data is CC-BY-NC-SA. If a corporation
wants to use our work commercially, they share improvements back or
fund the contributors. This isn't charity — it's a structural advantage.
```

---

### Section: Where we are

**H2**:
```
Where we are
```

**Body**:
```
Sydney, Australia.

All our client systems are hosted in the Sydney AWS region. Personal
data is stripped before any AI call. We're built for the 2026 Privacy
Act, not retrofit for it.
```

---

### Section: Contact

**H2**:
```
Talk to us
```

**Two columns**:

**Left — Business enquiries (Forge)**:
```
Want AI built for your business?
hello@goldmanglobal.com.au
```

**Right — Research & collaboration (Labs)**:
```
Contributing, partnering, or licensing research?
cto@goldmanglobal.com.au
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## DIVIDER
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> Designer: render as a full-width horizontal rule with the centered text `繁體中文 ↓`. Anchor target: `#中文`. Default page load shows English; the link smooth-scrolls to the Chinese section.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 繁體中文 VERSION (bottom of page)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Hero

**Eyebrow** (small, accent):
```
關於 GOLDMAN GLOBAL
```

**H1**:
```
一間澳洲 AI 公司，兩個面向。
```

**Subhead**:
```
Goldman Global 為澳洲市場建造同研究人工智能。我哋透過 Goldman Forge
為企業交付生產級 AI，透過 Goldman Global Research Labs 發表開源研究。
一間公司，兩份工。
```

---

### Section: 我哋係邊個

**H2**:
```
我哋係邊個
```

**Body**:
```
Goldman Global 係一間總部喺悉尼嘅 AI 公司。我哋唔做顧問，唔賣 PPT ——
我哋建造切實運行嘅軟件。

我哋最初係為自己喺運輸、旅遊同金融領域嘅業務，重新建造基礎業務系統。
呢啲部署成為咗證明。今日，我哋透過 Goldman Forge 將同一套系統交付俾
其他澳洲企業，並透過 Research Labs 以開源方式發表背後嘅研究。
```

---

### Section: 兩個品牌，一間公司

**H2**:
```
兩個品牌，一間公司
```

**兩張並排卡片**:

**Card A — Goldman Forge**
- Tag: `商業`
- Title: `Goldman Forge`
- Body:
  ```
  我哋嘅商業 AI 交付部門。為澳洲企業建造同部署 AI 前台接待、預約系統
  同數碼員工。固定收費、快速交付、悉尼託管。
  ```
- CTA: `睇 Forge →` → `/`

**Card B — Goldman Global Research Labs**
- Tag: `開源研究`
- Title: `Research Labs`
- Body:
  ```
  我哋嘅開源研發部門。以 AGPL 授權發表人類視角、去中心化、雙 LLM 審計
  嘅 AI 研究。第一個項目係 Hive.AGI —— 一個人類視角嘅知識網絡。
  ```
- CTA: `睇 Labs →` → `/research`

**卡片底下，一行**:
```
兩個品牌共用同一個母公司、同一個團隊、同一份真實世界訊號。
Forge 嘅部署為 Labs 提供真實嘅邊界個案；Labs 嘅開源協議為 Forge
提供一個可以防禦嘅基礎。
```

---

### Section: 我哋相信咩

**H2**:
```
我哋相信咩
```

**Body** (三個簡短立場):

**1. AI 應該遷就人，唔係人遷就 AI。**
```
大部分 AI 工具迫使人類去學新介面、新詞彙、新邏輯。我哋建造嘅系統
喺人們已經身處嘅地方迎接佢哋 —— 用廣東話、用英文、喺佢哋已經有嘅
工作流程入面。
```

**2. 真正嘅 AI 係建造出嚟嘅，唔係買返嚟嘅。**
```
將一個 AI API 𠝹落一套用咗 15 年嘅 CRM 上面，唔會令一盤生意變成
AI-native。我哋重建基礎軟件，令智能存在於系統之內，而唔係一個𠝹喺
表面嘅 chatbot。
```

**3. 研究方面，開放勝過封閉。**
```
我哋嘅研究代碼係 AGPL。我哋嘅數據係 CC-BY-NC-SA。如果一間企業想
將我哋嘅工作用喺商業用途，佢哋要分享改進，或者資助貢獻者。呢個
唔係慈善 —— 係結構性優勢。
```

---

### Section: 我哋喺邊

**H2**:
```
我哋喺邊
```

**Body**:
```
悉尼，澳洲。

我哋所有客戶系統都託管喺悉尼 AWS 區域。任何 AI 調用之前都會先剔除
個人資料。我哋係為 2026 年私隱法案而建造，唔係為佢做翻新。
```

---

### Section: 聯絡

**H2**:
```
同我哋傾
```

**兩欄**:

**左 — 商業查詢（Forge）**:
```
想你嘅業務用 AI？
hello@goldmanglobal.com.au
```

**右 — 研究及合作（Labs）**:
```
貢獻、合作，或研究授權？
cto@goldmanglobal.com.au
```

---

## Technical specs

| Field | Value |
| :--- | :--- |
| **URL** | `https://www.goldmanglobal.com.au/about` |
| **Nav label** | `About` |
| **Page title** (SEO) | `About Goldman Global — Australian AI company (Forge + Research Labs)` |
| **Meta description** | `Sydney-based AI company. Goldman Forge builds production AI for Australian business. Research Labs publishes open-source human-perspective AI research.` |
| **OG image** | Two-card composition (Forge + Labs), branded, 1200×630 |
| **Anchor IDs** | English section wrapper: `id="english"`. Chinese section wrapper: `id="中文"`. |
| **Jump link** | Top of page: `[English ↓](#english) \| [繁體中文 ↓](#中文)` (both smooth-scroll; default visible is English) |
| **Divider** | Full-width `<hr>` with centered label `繁體中文 ↓` (and a matching `English ↑` at the very top of the Chinese section linking back up) |

---

## Designer notes

1. **The two language sections are visually identical in structure** — same sections, same card layout, same CTAs. Only the language changes. This makes the page feel deliberate, not patched-on.

2. **Hard divider, not a toggle.** Both languages live on one page (good for SEO, good for sharing, good for readers who straddle both languages). Don't use JS tab-switching that hides one version — both must be present in the DOM.

3. **Default landing state: English at top.** A first-time visitor sees English. The top anchor link lets Chinese-first readers jump down without scrolling past English.

4. **No inline mixing anywhere.** If a concept needs both languages (rare), put the English in the English section and the Chinese in the Chinese section — don't parenthesize translations mid-sentence.

5. **Brand names stay English in both versions**: Goldman Global, Goldman Forge, Research Labs, Hive.AGI. These are registered trade names, not translatable terms. The Chinese section will read "Goldman Forge" and "Research Labs" in English letters — that's correct, not a translation failure.

6. **Contact emails stay as-is** in both sections (they're Latin-character email addresses regardless of language).

---

## What this page deliberately does NOT do

- ❌ **No tabbed language switcher that hides one version.** Both full versions live on the page.
- ❌ **No inline `English (英文)` or `中文 (Chinese)` parenthetical glosses.** Pick a language per section; commit to it.
- ❌ **No team photos yet** (same guardrail as the research page — Labs is small, don't inflate).
- ❌ **No "founded in YEAR by NAME" founder myth section** unless you actually want to name founders. Vague "we started by…" is fine and what the copy does.
- ❌ **No client logo wall.** Client logos belong on the Forge case-study pages, not the About.

---

*Source of truth for the About page. If this doc and `HANDOFF-research-page.md` ever disagree on the Forge/Labs relationship wording, this About page doc wins (it's the canonical statement of who-we-are).*
