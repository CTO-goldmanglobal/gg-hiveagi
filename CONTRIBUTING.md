# Contributing to Project Hive.AGI

Thank you for your interest in participating in this project! This document explains how to contribute, the rules to follow, and how we work together to build the "human-perspective knowledge symbiosis network".

**New here?** Read the [README](./README.md) first for the vision and Quick Start, then come back.

---

## 🧭 Ways to Contribute

| Type | Description | Skills Required | Where it goes |
| :--- | :--- | :--- | :--- |
| **Seed Package Contribution** | Share your human-perspective data (travel, legal, industrial, etc.) | Anyone with an Obsidian Vault | Published via P2P CID — see [§ Contributing a Seed Package](#-contributing-a-seed-package) |
| **Code Contribution** | Improve Python tools, the LLM Wiki Engine, P2P exchange, Obsidian plugin | Python, TypeScript, Git | Pull Request |
| **Documentation Contribution** | Improve README, specs, tutorials, `docs/zh-HK/` translations | Writing, technical documentation | Pull Request |
| **Community Contribution** | Testing, feedback, bug reports, promotion | Communication, testing | Issues / Discussions |

> ⚠️ **Seed Packages are not contributed by Pull Request.** `seed_output/` is in `.gitignore` — data does not live in this repo. See the dedicated section below.

---

## 🔒 Privacy & PII — Read Before Contributing Any Data

Hive.AGI collects **human-perspective data**, which means contributions can carry real privacy risk. These rules are non-negotiable and apply to Seed Packages, test samples, screenshots in issues, and example data in PRs.

**Never contribute:**

- Identifiable faces or license plates in any image or frame
- Names, phone numbers, emails, ID numbers, or addresses of other people — in `human_description`, `tags`, filenames, or anywhere else
- Anything recorded where the people present had a reasonable expectation of privacy
- Data you do not have the right to share (employer-confidential, client work, copyrighted footage)

**Location data:** Seed Package entries carry `gps_lat` / `gps_lng`. Do not publish packages containing your home, your children's school, or any location that reveals a private routine. Coarsen or drop the coordinates for anything near a sensitive location — an approximate suburb is usually enough for the knowledge to be useful.

**Anonymisation:** Both capture paths enforce face + plate blurring.
- The **auto-vision path** (`python -m llm_wiki_engine process-video`) runs real MediaPipe face detection + OpenCV edge-based plate detection, with no `--skip-blur` bypass (spec §6, code-enforced).
- The **manual curation path** (`tools/video_ingest/capture_helper.py`) keeps PII risk at zero — you choose each frame and write only text.
For still images you handle yourself, run `python tools/pii_anonymizer/anonymize.py <image>` before any upload or LLM call.

**Legal note:** Australian Privacy Act obligations and equivalent laws in your own jurisdiction apply to you as the contributor. When in doubt, leave it out or ask at <cto@goldmanglobal.com.au> before publishing.

---

## 📄 Contributor License Agreement (CLA)

Because Project Hive.AGI uses **dual licensing (AGPL-3.0 + CC-BY-NC-SA-4.0 + Commercial)**, all contributors must agree to the CLA.

**CLA Terms** (you confirm these in every Pull Request):

1. You retain the copyright to the content you contribute.
2. You grant Goldman Global Research Labs a perpetual, worldwide, irrevocable, royalty-free licence to use, reproduce, modify, sublicense and distribute your contribution — **including under commercial licence terms**.
3. Code you contribute is released to the public under **AGPL-3.0** ([LICENSE](./LICENSE)).
4. Seed Data you contribute is released to the public under **CC-BY-NC-SA-4.0** ([DATA_LICENSE.md](./DATA_LICENSE.md)).
5. You confirm the contribution is your own work, that you have the right to grant this licence, and that it complies with the Privacy & PII rules above.

> ℹ️ **Why term 2 is a grant, not a "retention".** Dual licensing only works if contributors explicitly licence Goldman Global the right to re-license commercially. Without an explicit grant, Goldman Global has nothing to "retain". This wording was corrected after legal review flagged the earlier "retains the right" phrasing as a nullity. **Contributors: if you have questions about this grant, email <cto@goldmanglobal.com.au> before opening a PR — do not tick the box blindly.**

**How to sign**: tick the CLA confirmation checkbox in the [Pull Request template](./.github/PULL_REQUEST_TEMPLATE.md). Seed Package contributors confirm the same terms in the submission issue.

Questions about licensing, or need a commercial licence? → <cto@goldmanglobal.com.au> ([COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md))

---

## 🛠️ Development Environment

| Requirement | Version | Needed for |
| :--- | :--- | :--- |
| Python | **3.13** (matches CI) | Everything except the Obsidian plugin |
| Node.js | 20+ (matches `@types/node` in `obsidian_plugin/package.json`) | `obsidian_plugin/` only |
| kubo (IPFS daemon) | latest | P2 real mode only — `--mock` needs nothing |

```bash
# 1. Fork the repo on GitHub, then clone YOUR fork
git clone https://github.com/<your-username>/gg-hiveagi.git
cd gg-hiveagi
git remote add upstream https://github.com/CTO-goldmanglobal/gg-hiveagi.git

# 2. Virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Dependencies
pip install -r tools/seed_generator/requirements.txt
pip install -r llm_wiki_engine/requirements.txt
pip install -r p2p_exchange/requirements.txt
```

**Credentials**: P1 runs in mock mode by default and needs no API keys. For real mode, `cp llm_wiki_engine/.env.example .env` and fill it in locally. `.env` is gitignored — **never commit a key, and never paste one into an issue, PR, or chat window.**

---

## 🚀 Contribution Workflow (Code & Docs)

### 1. Create a branch

```bash
git checkout -b feature/your-feature-name
```

Branch prefixes: `feature/`, `fix/`, `docs/`, `chore/`, `spec/`.

### 2. Write code and run the full test suite locally

Run everything CI runs — a red PR will not be reviewed. See [§ Testing Requirements](#-testing-requirements) for the commands.

### 3. Commit

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add plate-blur strength option to PII anonymizer"
```

Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `spec`. Scope is optional and follows the CI/Dependabot convention — `feat(p1):`, `fix(p2):`, `docs(zh-HK):`.

### 4. Sync and push

```bash
git fetch upstream && git rebase upstream/main
git push origin feature/your-feature-name
```

### 5. Open a Pull Request against `main`

- Title clearly describes the change (Conventional Commit style is ideal)
- Fill in the PR template: change type, description, test results
- Explain **why**, not just what
- Tick the CLA confirmation checkbox
- Link the related issue (`Closes #123`)
- Wait for CI to go green; push fixes to the same branch if it doesn't

One logical change per PR. If you're planning something large or structural, **open an issue first** so we can agree on the approach before you spend the effort.

---

## 🌱 Contributing a Seed Package

Seed data is content-addressed and exchanged peer-to-peer — it is not committed to this repository.

```bash
# 1. Set up a Vault (if you don't have one)
python tools/vault_setup/setup_vault.py --target ~/HiveAGI

# 2. Capture Raw Data into 00_Inbox/, then distil it
python -m llm_wiki_engine process --inbox ~/HiveAGI/00_Inbox --entries ~/HiveAGI/01_Entries

# 3. Generate and validate the package
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/<your_package>/

# 4. Re-read the Privacy & PII section above, then publish
python -m p2p_exchange publish --package seed_output/<your_package> --mock
```

Then **open an issue** using the Seed Package label containing: the CID, the domain (`tourism` / `industrial` / `legal` / …), the entry count, a one-paragraph description of what the knowledge covers, and your confirmation of the CLA and PII rules. Maintainers verify the CID and add it to the network registry.

Drop `--mock` once you have a local kubo daemon running to publish a real IPFS CID.

---

## 🧪 Testing Requirements

| Type | Requirement |
| :--- | :--- |
| **Python** | Must pass the full CI smoke suite below (P0 + P1 mock + P2 mock + cross-compat) |
| **Obsidian plugin** | `npm run check` (tsc) and `npm run build` must both succeed from `obsidian_plugin/` |
| **Specs** | Must stay compatible with the existing schema, or clearly declare a version bump and update every affected spec + translation |
| **Docs** | Must pass Markdown lint (no serious syntax errors); links must resolve |
| **Seed Packages** | Must pass `validate_seed.py` |

```bash
# P0 — seed generator + validator
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/

# P1 — LLM Wiki Engine, all three audit branches
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_pass --mock --audit-fail-mode pass
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_corr --mock --audit-fail-mode corrected
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_quar --quarantine /tmp/ci_q --mock --audit-fail-mode quarantine

# P2 — publish / verify / tamper-detect / resolve
python -m p2p_exchange publish --package seed_output/seed_goldman_20260725 --mock
python -m p2p_exchange verify --package seed_output/seed_goldman_20260725 --cid <CID> --mock
```

The authoritative definition is [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) — including the cross-compatibility checks that run the P0 validator over P1 and P2 output. If you change the schema, **those cross-compat steps are the ones that will break.**

---

## 📌 Code Style

- **Python**: PEP 8, formatted with `black` or `ruff`. Type hints on public functions. Docstrings on anything a contributor will call.
- **TypeScript** (`obsidian_plugin/`): follow the existing `tsconfig.json`; no `any` in exported types.
- **Markdown**: `#` for headings, `-` for lists, fenced code blocks with a language tag.
- **File naming**: lowercase + underscores (`snake_case`) for Python; `camelCase.ts` for plugin sources, matching what's already there.
- **Comments and docstrings**: English, so the whole network can read them. User-facing docs are bilingual (see below).

---

## 🌏 Translations

The canonical documents are English; Traditional Chinese lives in [`docs/zh-HK/`](./docs/zh-HK/). If you change a spec or the README in a way that alters meaning, either update the zh-HK counterpart in the same PR or open a follow-up issue tagged `translation` so it doesn't silently drift.

---

## 🤝 Code of Conduct

Be respectful, assume good faith, and critique ideas rather than people. Harassment, discrimination, and personal attacks are not tolerated and will result in removal from the project's spaces. Report conduct concerns privately to <cto@goldmanglobal.com.au>. Full text: [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).

---

## 🛡️ Reporting a Security or Privacy Issue

**Do not open a public issue** for a security vulnerability, a leaked credential, or PII you've found in the repo or in a published package. Email <cto@goldmanglobal.com.au> with the details and give us a reasonable window to respond before disclosing publicly. Full policy: [`SECURITY.md`](./SECURITY.md).

---

## 💬 Communication Channels

- **GitHub Issues**: bug reports, feature requests, Seed Package submissions
- **GitHub Discussions**: general discussion, proofs of concept, questions before you build
- **Email**: <cto@goldmanglobal.com.au> — licensing, security, privacy
- **Discord**: (opening soon)

---

## 🙏 Thank You for Your Contribution!

Every Seed Package, every line of code, every document is an important step toward bringing Hive.AGI closer to a "human-perspective AGI".

**Thank you for joining this movement.**
