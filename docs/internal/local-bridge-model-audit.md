# Local-Bridge Model Audit — Decision Record

**System:** B (`tools/local_bridge/`) · **Phase:** 0 (model research, audit, review)
**Status:** Approved (founder, 2026-08-05) — `qwen3.6:27b` adopted, pulled, in use
**Date:** 2026-08-05 · **Host:** Mac Studio, Apple M4 Max, 64 GB unified memory, Ollama runtime

> This is the Phase-0 decision record the build plan required: the local-model
> choice is researched, audited, and reviewed *before* the blind-critic proof.
> The research below was produced by an independent cowork pass and adopted by
> the main agent; it is committed here so the choice is traceable, not implicit.

---

## 1. TL;DR — what was chosen and why

- **Generator and critic (Phase 1): ONE model, `qwen3.6:27b`.** Apache-2.0,
  dense, ~17 GB @Q4, official Ollama library. Both roles use it; the critic's
  *blindness* (separate call, draft never in its checklist-stage context) — not
  a different model family — carries the anti-anchoring weight.
- **Why one model:** the founder directed "too heavy for the Mac Studio." One
  ~17 GB model is the lightest credible setup. Research (Huang et al., ICLR
  2024; Du et al. 2023; Wang et al. 2022) establishes that *independence* is
  mandatory and *diversity* helps — but does not conclusively prove a different
  family beats a same-family independent instance. The blind protocol supplies
  the independence; same-vs-different family remains a one-line config swap for
  later rigor (v3 OQ-C).
- **Why `qwen3.6:27b`:** newest purpose-built coder in the Qwen line that fits
  the box, clean Apache-2.0 (commercial-safe for the Goldman half), official
  Ollama namespace (no community-blob supply-chain risk).

## 2. What was retired

- **`gpt-oss:20b` — removed** (founder directive, twice confirmed). ~1 year old
  (Aug-2025), not a purpose-built coder, off the Aider open-model table. Freed
  ~13 GB. `ollama rm gpt-oss:20b` executed 2026-08-05 after explicit founder OK.

## 3. The 2026 frontier set — real, but wrong tier for local

Each is genuine and mostly clean-licensed, but **none fit 64 GB as a local
generator/critic** — they are cloud/orchestration-tier models, not System-B
local models:

| Candidate | Size / arch | License | Local fit | Verdict |
|---|---|---|---|---|
| GLM-5.2 | 744B MoE | open-weight (MIT-family) | ❌ (~256 GB) | **Cloud only** — already the orchestration model |
| DeepSeek-V4 / V4-Flash | ~1.6T / large MoE | MIT | ❌ | Cloud only |
| Kimi K2.7-Code | 1T | Modified MIT (legal flag) | ❌ | Cloud only + license flag |
| Mistral-Medium-3.5 | 128B dense | open-weight | ❌ (~70 GB @Q4) | Excluded on size |

**Conclusion:** the only 2026 release that both beats the incumbent *and* fits
the box is **Qwen3.6**. This confirms a clean architectural split — frontier
models live in the cloud/synthesizer tier (Phase 2 `synthesizer.py`), the
27–33B tier lives on the Mac. That split is healthy for the plugin's escalation
design.

## 4. Card verification (verified against live cards, 2026-08-04/05)

| Model | Exact tag | Params | License | Ctx | ~Size @Q4_K_M | Source |
|---|---|---|---|---|---|---|
| **Qwen3.6 27B** *(chosen)* | `qwen3.6:27b` | 27B dense | **Apache-2.0** | 262K (→1M RoPE) | **~17 GB** | Ollama official library ✅ |
| Qwen3.6 35B (alt) | `qwen3.6:35b` | 35B MoE | Apache-2.0 | 256K | ~24 GB | Ollama official ✅ |
| Qwen3-Coder-30B (fallback) | `qwen3-coder:30b` | 30.5B/3.3B-active MoE | Apache-2.0 | 262K (→1M) | ~19 GB | Ollama official ✅ (fastest; MoE) |
| DeepSeek-R1 32B (alt critic) | `deepseek-r1:32b` | 32B (Qwen2.5 distill) | **MIT** | ~128K | ~20 GB | Ollama official ✅ |
| GLM-Z1-32B-0414 (alt critic) | `JollyLlama/GLM-Z1-32B-0414-Q4_K_M` | 33B dense | **MIT** | 8K native (→32K YaRN) | ~20 GB | ⚠️ Community upload |
| Devstral Small (fallback gen) | `devstral:24b-small-2505-q4_K_M` | 23.6B dense | Apache-2.0 | 128K | ~14 GB | Ollama official ✅ |

## 5. License audit — commercial / open dual use

Goldman (the commercial half) must stay entirely on the **clean-for-commercial**
list. The chosen model qualifies.

- ✅ **Clean (permissive, commercial + derivatives OK):** Qwen3.6 (Apache-2.0),
  Qwen3-Coder-30B (Apache-2.0), Devstral (Apache-2.0), GLM-4/Z1-32B (MIT),
  DeepSeek-R1-Distill-Qwen-32B (**MIT** — corrected from the handoff's "Apache";
  the distills are relicensed MIT even though the Qwen2.5 base is Apache-2.0;
  net effect identical: commercial-safe).
- ⛔ **Excluded:** Codestral-22B (**MNPL**, Mistral Non-Production License) —
  no production/commercial use; keep off both halves.
- ⚠️ **Legal-flag (usable but needs counsel before Goldman):** Kimi (Modified
  MIT), Llama 4 (Community License — accept-use + >700M-MAU clause). Avoid for
  the golden half.

## 6. Runtime + RAM

- **Runtime: Ollama** for velocity. OpenAI-compatible localhost-no-auth endpoint
  (`http://localhost:11434/v1/`); the plugin's `ollama.py` client adapts the
  `urllib` pattern from `tools/code_review/review.py` and `tools/audit/council.py`.
  MLX noted as a later throughput option, not now.
- **RAM fit (64 GB M4 Max):** one ~17 GB model resident leaves ~45 GB headroom
  for OS + KV-cache + the longest task. Comfortable. If a second family is later
  added for the critic (OQ-C rigor), run sequentially (peak ~24 GB), not
  concurrently — concurrent instances split the ~546 GB/s memory bandwidth.

## 7. OQ-C resolution (same vs different model for generator/critic)

**Resolved → same model in Phase 1; different-family remains a one-line swap.**

The 64 GB budget *would* allow a different family, but the founder directed the
lightest setup, and the research does not conclusively prove different-family
beats same-family-independent-instance. The blind protocol's independence is
the load-bearing part. **If Phase 1 fails with the same model, that is a
stronger falsification** — and directly answers OQ-C (swap to
`deepseek-r1:32b` or GLM-Z1-32B as critic and re-run).

## 8. One-line swaps (config-driven — `tools/local_bridge/config.toml`)

```toml
[models]
generator = "qwen3.6:27b"     # alt: qwen3-coder:30b (MoE, faster), devstral (smaller)
critic    = "qwen3.6:27b"     # alt: deepseek-r1:32b (reasoning), GLM-Z1-32B (independent family)
```

---

## Sources (verified 2026-08-04/05)

- Qwen3.6: https://huggingface.co/Qwen/Qwen3.6-27B · https://ollama.com/library/qwen3.6
- Qwen3-Coder-30B: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- DeepSeek-R1-Distill-Qwen-32B (MIT): https://ollama.com/library/deepseek-r1:32b-qwen-distill-q4_K_M
- GLM-Z1-32B-0414 (MIT): https://huggingface.co/zai-org/GLM-Z1-32B-0414
- Devstral Small (Apache-2.0): https://ollama.com/library/devstral:24b-small-2505-q4_K_M
- Codestral MNPL (excluded): https://mistral.ai/news/mistral-ai-non-production-license-mnpl/
- GLM-5.2 size/hardware (744B MoE, cloud-tier): https://unsloth.ai/docs/models/glm-5.2
- Same-vs-different critique: Huang et al. ICLR 2024 (arXiv:2310.01798);
  Du et al. 2023 (arXiv:2305.14325); Wang et al. 2022 (arXiv:2203.11171)
