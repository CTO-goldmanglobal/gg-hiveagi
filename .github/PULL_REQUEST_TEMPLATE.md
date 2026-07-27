## 📌 Pull Request Type

- [ ] 🐛 Bug Fix
- [ ] ✨ New Feature
- [ ] 📄 Docs Update
- [ ] 🔧 Tooling / Infrastructure
- [ ] 🌏 Translation (zh-HK mirror update)

> ℹ️ **Seed Packages are not contributed by PR.** `seed_output/` is gitignored. To contribute a Seed Package, follow [§ Contributing a Seed Package](../CONTRIBUTING.md#-contributing-a-seed-package) and open an issue with the CID.

---

## 📝 Description

<!-- Explain WHAT changed and WHY. Reference the issue: `Closes #123`, `Related to #456`. -->

---

## 🧪 Test Results

I ran the full local CI suite (see [CONTRIBUTING.md § Testing Requirements](../CONTRIBUTING.md#-testing-requirements)):

- [ ] P0 — `generate_seed.py` runs, `validate_seed.py` passes
- [ ] P1 — `llm_wiki_engine` mock passes all three audit branches (pass / corrected / quarantine)
- [ ] P2 — `p2p_exchange` mock passes publish / verify / tamper-detect / resolve
- [ ] Cross-compat — P0 validator accepts P1 and P2 output
- [ ] `obsidian_plugin/` — `npm run check` and `npm run build` both succeed (if plugin touched)
- [ ] No new warnings or errors

---

## 🔒 Privacy & PII Check

(Required if this PR adds any sample data, screenshots, test fixtures, or Seed Package examples.)

- [ ] No identifiable faces or license plates in any image
- [ ] No names, phone numbers, emails, ID numbers, or addresses of third parties
- [ ] GPS coordinates do not reveal private locations (homes, schools, routines)
- [ ] I have the right to share all data included in this PR

---

## ✅ CLA Confirmation

**I agree to the following terms** (matching [CONTRIBUTING.md § CLA](../CONTRIBUTING.md#-contributor-license-agreement-cla)):

1. I retain the copyright to the content I contribute.
2. I grant Goldman Global Research Labs a perpetual, worldwide, irrevocable, royalty-free licence to use, reproduce, modify, sublicense and distribute my contribution — **including under commercial licence terms**.
3. Code I contribute is released to the public under **AGPL-3.0**.
4. Seed Data I contribute is released to the public under **CC-BY-NC-SA-4.0**.
5. The contribution is my own work, I have the right to grant this licence, and it complies with the Privacy & PII rules.

- [ ] I have read and agree to the CLA terms

> ℹ️ Term 2 is an **explicit licence grant** (corrected from the earlier "retains the right" wording, which was a legal nullity). If you have questions about the grant, email <cto@goldmanglobal.com.au> **before** ticking the box.

---

## 📎 Related Issue

<!-- `Closes #123`, `Related to #456`, or "n/a" -->

---

## 🙏 Thanks

Thanks for contributing! 🔥
