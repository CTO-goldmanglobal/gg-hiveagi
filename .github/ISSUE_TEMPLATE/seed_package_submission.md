---
name: Seed Package Submission
about: Publish a Seed Package to the Hive.AGI network
title: "[Seed Package] <short name> — <domain>"
labels: ["seed-package"]
---

## 🌱 Seed Package Details

<!-- Required. Seed Packages are content-addressed on IPFS and exchanged peer-to-peer — they are NOT contributed by Pull Request. See CONTRIBUTING.md § Contributing a Seed Package. -->

- **CID**: `<!-- IPFS content ID, e.g. Qm... (CIDv0) or bafy... (CIDv1) -->`
- **Domain**: `<!-- tourism / legal / medical / industrial / education / other -->`
- **Entry count**: `<!-- integer -->`
- **Language of entries**: `<!-- en / zh-HK / other -->`

### Description

<!-- One paragraph: what knowledge does this package cover, and what is it useful for? Be specific and rigorous — name the domain, the perspective captured, and what a consumer would do with it. -->

### How it was produced

<!-- Check one. -->
- [ ] Manual curation via `tools/video_ingest/capture_helper.py`
- [ ] Auto-vision via `python -m llm_wiki_engine process-video`
- [ ] Other: `<!-- describe -->`

---

## 🔒 PII Confirmation

Required. See [CONTRIBUTING.md § Privacy & PII](../../CONTRIBUTING.md#-privacy--pii--read-before-contributing-any-data).

- [ ] No identifiable faces or license plates in any image or frame
- [ ] No names, phone numbers, emails, ID numbers, or addresses of third parties (in `human_description`, `tags`, filenames, or anywhere else)
- [ ] GPS coordinates do not reveal private locations (homes, schools, routines) — coordinates near sensitive locations have been coarsened or dropped
- [ ] I have the right to share all data in this package (not employer-confidential, not client work, not copyrighted footage)

---

## ✅ CLA Confirmation

- [ ] I agree to the [CLA terms in CONTRIBUTING.md](../../CONTRIBUTING.md#-contributor-license-agreement-cla).

> ℹ️ CLA term 2 is an **explicit licence grant** to Goldman Global Research Labs, including for commercial re-licensing. Email <cto@goldmanglobal.com.au> before ticking if you have questions.

---

<details>
<summary>🔧 Maintainer verification (do not edit)</summary>

- [ ] CID resolves via `python -m p2p_exchange resolve --cid <CID>` (add `--mock` if no live kubo daemon)
- [ ] Manifest validates (`python tools/seed_generator/validate_seed.py` over the resolved package)
- [ ] Entries validate against the spec
- [ ] Added to network registry — date: `<!-- YYYY-MM-DD -->`
- [ ] Announced (Discussions / Discord) once registry updates

**Verified by**: `<!-- @maintainer -->`

</details>
