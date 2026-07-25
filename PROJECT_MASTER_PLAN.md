# Project Hive.AGI — Master Plan

> Full master plan: from vision to code.
> Initiated by Goldman Global Research Labs.
> Contact: cto@goldmanglobal.com.au

---

## 📌 One-Sentence Positioning

**Project Hive.AGI** is an open-source research project initiated by Goldman Global Research Labs, aiming to build a **knowledge symbiosis network that is contributed by humans, defined by humans, and distributed.**

Core motto:

> Let computers learn how to understand humans, rather than humans learning how to adapt to computers.

---

## 🎯 Vision

> The AGI built by big tech is computers training computers, ultimately serving the logic of computers.
> The AGI we are building has humans contributing human perspectives, ultimately serving the diverse values of humanity.

The end goal of **Project Hive.AGI** is not a centralized super-AI, but a **distributed, open-source "human-perspective knowledge symbiosis network" maintained jointly by human nodes around the world.**

Anyone can use their own devices (glasses, phones, computers, industrial sensors) to contribute "human-perspective data" from their area of expertise, and through the LLM Wiki, distill this data into structured knowledge that can be exchanged and synthesized.

---

## 🧩 Technical Core

- **Capture layer**: AI glasses / phones / industrial sensors collect "human-perspective data" (moments that a person finds important / beautiful / anomalous in the moment).
- **Wiki layer**: Obsidian Vault + bidirectional links, distilling raw data into structured Markdown knowledge.
- **LLM layer**: Dual-LLM API architecture — **MiniMax M3** (generator, primary producer of wiki entries) + **DeepSeek V4 Flash** (auditor, automated review + correction of hallucinations / schema violations). Both are OpenAI-compatible. Local Llama is not used. See `specs/api-protocol-v1.md`.
- **P2P layer**: Seed Packages (standardized knowledge packages) are exchanged between contributors via IPFS / libp2p.

---

## 📐 MVP Development Roadmap

Prioritization strategy: a minimum viable product (MVP), starting from the simplest component.

| Priority | Component | Complexity | Estimated Time | Reason |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | Seed Package Generator (Python Script) | ⭐ | 1–2 days | Convert existing data into a standardized Seed Package |
| **P0** | Obsidian Vault Setup Script | ⭐ | 1 day | Automatically build the Vault directory structure and Templates |
| **P0** | Specs (Schema / Vault / API) | ⭐ | 1 day | Lock the specifications to avoid rework |
| **P1** | LLM Wiki Engine (API-based) | ⭐⭐ | 1 week | Convert Raw Data into Markdown using OpenAI-compatible APIs |
| **P1** | Mobile Capture App (Basic) | ⭐⭐⭐ | 2–4 weeks | Replace manual pressing; achieve Passive Capture |
| **P2** | P2P Exchange (IPFS) | ⭐⭐⭐⭐ | 1–2 months | Automatic Seed Package exchange |
| **P2** | Obsidian Plugin | ⭐⭐⭐⭐ | 1–2 months | Allow other Obsidian users to participate directly |

---

## 📂 Repository Structure

```
gg-hiveagi/
├── README.md                       # Project introduction
├── LICENSE                         # AGPL-3.0
├── DATA_LICENSE.md                 # CC-BY-NC-SA-4.0 (Seed Data)
├── COMMERCIAL_LICENSE.md           # Commercial license
├── CONTRIBUTING.md                 # How to contribute + CLA
├── PROJECT_MASTER_PLAN.md          # This document
│
├── specs/                          # Specification documents (Markdown)
│   ├── seed-package-schema-v1.md
│   ├── vault-structure-spec.md
│   └── api-protocol-v1.md
│
├── tools/                          # Helper tool scripts
│   ├── seed_generator/             # P0: Seed Package Generator
│   ├── vault_setup/                # P0: Obsidian Vault Setup
│   └── pii_anonymizer/             # Privacy tooling
│
├── llm_wiki_engine/                # P1: LLM Wiki Engine (later)
├── mobile_app/                     # P1: Mobile App (later)
├── p2p_exchange/                   # P2: IPFS exchange (later)
└── obsidian_plugin/                # P2: Obsidian Plugin (later)
```

---

## 📄 License Strategy (Dual Licensing)

| Component | License | Reason |
| :--- | :--- | :--- |
| **Code** | AGPL-3.0 | Strong copyleft + closes the SaaS loophole; corporations that want SaaS deployment / commercial use must negotiate a commercial license. Ensures derivative works must share improvements. |
| **Seed Data** | CC-BY-NC-SA-4.0 | Allows sharing and adaptation but prohibits commercial use, protecting contributors. |
| **Commercial License** | Commercial | Enterprises requiring commercial use, please contact cto@goldmanglobal.com.au. Fees directly support the developers and the community. |

**Dual-license mechanism**: Goldman Global retains the copyright, so it can simultaneously offer AGPL open-source licensing to the community and commercial licensing to enterprises. All external contributors must sign a CLA (see CONTRIBUTING.md).

---

## 🚀 Take Action Now

1. **Star** our GitHub repo
2. **Join** the Discord discussion (Coming Soon)
3. **Contribute** your first Seed Package

Contact: cto@goldmanglobal.com.au

---

## 🙏 Acknowledgements

Initiated by [Goldman Global Research Labs](https://goldmanglobal.com.au), with thanks to all open-source contributors participating in the "Human-Perspective Data Contribution Program".

---

**In one sentence**:

> Let computers learn how to understand humans, rather than humans learning how to adapt to computers.
