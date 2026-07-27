# Security Policy

## Supported versions

Project Hive.AGI is research software. Only the latest `main` branch receives security fixes — there are no LTS releases and no backports to past tags.

| Version | Supported |
| :--- | :--- |
| `main` (latest) | Yes |
| Tagged releases | Best-effort; update to `main` for any reported issue |

---

## Reporting a vulnerability

**Email <cto@goldmanglobal.com.au>. Do not open a public issue.**

Please include:

- **Description** of the vulnerability and the affected component (e.g. `p2p_exchange`, `llm_wiki_engine`, `obsidian_plugin`, `tools/`).
- **Reproduction steps** — a minimal command sequence is ideal.
- **Impact assessment** — what an attacker could do, and what data could be exposed.

Please give us **90 days** from your report before any public disclosure. We will keep you informed throughout and coordinate publication of details with you.

---

## What qualifies

In scope:

- Security vulnerabilities in code shipped from this repo — RCE, SSRF, path traversal, authentication or authorization bypasses, and dependency CVEs with a real exploit path.
- Leaked credentials: API keys, tokens, or private keys in commits, the repository, or published packages.
- **PII found in the repository or in a published Seed Package.** See the special note below.

Out of scope (please use [Issues](https://github.com/CTO-goldmanglobal/gg-hiveagi/issues) instead):

- Feature requests, general bugs, and documentation errors.
- Theoretical issues without a working reproduction.
- Findings from automated scanners with no manual validation.

---

## Response timeline

| Step | Target |
| :--- | :--- |
| Acknowledge your report | within 72 hours |
| Initial assessment + severity rating | within 14 days |
| Fix or mitigation shipped to `main` | within 90 days of report |

These are targets, not guarantees. Research software with a small team means we will communicate clearly if a timeline slips — and we would rather ship a correct fix slowly than a broken one fast.

---

## Disclosure

We follow **coordinated disclosure**. After a fix ships to `main`, we publish details in a security advisory and credit you by name or handle unless you prefer to remain anonymous. We do not publicize unpatched issues.

---

## PII leaks — special note

Hive.AGI collects human-perspective data that can include faces, license plates, names, and precise coordinates. **If you find any of this in a published Seed Package or anywhere in this repository, report it immediately to <cto@goldmanglobal.com.au> — not via a public issue.**

We treat PII leaks as **severity-high regardless of intent**. The affected CID is pulled from the network registry and a corrected package re-published as the first item of business. If the leak is in this repo's history, we rotate secrets and rewrite history as needed.
