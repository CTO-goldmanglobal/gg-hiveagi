# Contributing to Project Hive.AGI

Thank you for your interest in participating in this project! This document will help you understand how to contribute, the rules to follow, and how we work together to build the "human-perspective knowledge symbiosis network".

---

## 🧭 Ways to Contribute

| Type | Description | Skills Required |
| :--- | :--- | :--- |
| **Seed Package Contribution** | Share your human-perspective data (travel, legal, industrial, etc.) | Anyone with an Obsidian Vault |
| **Code Contribution** | Improve Python Scripts / Specs / Tools | Python, Markdown, Git |
| **Documentation Contribution** | Improve README, specifications, tutorials | Writing, technical documentation |
| **Community Contribution** | Testing, feedback, promotion | Communication, testing |

---

## 📄 Contributor License Agreement (CLA)

Because Project Hive.AGI uses **dual licensing (AGPL-3.0 + CC-BY-NC-SA-4.0 + Commercial)**, all contributors must agree to the CLA:

**CLA Terms** (you will confirm these when submitting a PR):

1. The Code you contribute will be released under **AGPL-3.0**
2. The Seed Data you contribute will be released under **CC-BY-NC-SA-4.0**
3. Goldman Global Research Labs retains the right to offer **commercial licenses**
4. You retain the copyright to the content you contribute

**How to sign**: In each Pull Request, check the CLA confirmation checkbox (we provide a PR Template).

---

## 🚀 Contribution Workflow (Code)

### 1. Fork the Repo

```bash
git clone https://github.com/CTO-goldmanglobal/gg-hiveagi.git
cd gg-hiveagi
git checkout -b feature/your-feature-name
```

### 2. Write Code and Test

```bash
# Ensure it passes the Smoke Test
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/
```

### 3. Commit & Push

```bash
git add .
git commit -m "feat: description of your change"
git push origin feature/your-feature-name
```

### 4. Open a Pull Request

- Title should clearly describe the change
- Describe the reason for the change and the test results
- Check the CLA confirmation checkbox

---

## 🧪 Testing Requirements

| Type | Requirement |
| :--- | :--- |
| **Python Scripts** | Must pass the `generate_seed.py` + `validate_seed.py` Smoke Test |
| **Specs** | Must be compatible with the existing schema, or clearly indicate a version upgrade |
| **Docs** | Must pass Markdown lint (no serious syntax errors) |

---

## 📌 Code Style

- Python: PEP 8 (format with `black` or `ruff`)
- Markdown: use `#` for headings, `-` for lists
- File naming: use lowercase + underscores (snake_case)

---

## 💬 Communication Channels

- **GitHub Issues**: Bug Reports / Feature Requests
- **GitHub Discussions**: General discussion, proof of concepts
- **Discord**: (opening soon)

---

## 🙏 Thank You for Your Contribution!

Every Seed Package, every line of code, every document is an important step toward bringing Hive.AGI closer to a "human-perspective AGI".

**Thank you for joining this movement.**
