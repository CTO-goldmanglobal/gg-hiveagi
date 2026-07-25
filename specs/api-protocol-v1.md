# LLM Wiki Engine API Protocol v1.0

## 1. Overview

This document defines the API design for the **P1 LLM Wiki Engine**. The P0 phase does not require an LLM, but the spec is written in advance to ensure smooth future integration.

**Core decisions**:
- ✅ API-based (local Llama 3.2 is not used)
- ✅ **Dual-LLM architecture**: one generator + one auditor, separating generation from review
- ✅ Both providers are OpenAI-compatible, so the same SDK can be used (just swap the `base_url`)
- ✅ PII Stripping is completed before the API call

---

## 2. Dual-LLM Architecture

```
            Raw Data (PII stripped)
                    │
                    ▼
        ┌────────────────────────┐
        │  Generator: MiniMax M3 │   ← Primary generator of wiki entries
        │  model: MiniMax-M3     │      (consumes the token plan, main budget)
        └────────────────────────┘
                    │ draft entry (JSON)
                    ▼
        ┌────────────────────────┐
        │  Auditor: DeepSeek V4  │   ← Reviews the draft
        │           Flash        │      (cheap + fast, used for validation)
        │  model: deepseek-v4-   │
        │         flash          │
        └────────────────────────┘
                    │ pass → write directly to the store
                    │ fail + corrected → auto-corrected, then written
                    │ fail without corrected → retry / quarantine
                    ▼
              Final Entry (written to /01_Entries/)
```

| Role | Provider | Model Name | Purpose | Why It Was Chosen |
| :--- | :--- | :--- | :--- | :--- |
| **Generator** | MiniMax | `MiniMax-M3` | Convert Raw Data into standardized wiki entries (human description + AI analysis + bidirectional links) | Strong multimodal reasoning, coding/agent oriented, 1M context |
| **Auditor** | DeepSeek | `deepseek-v4-flash` | Review generator output: hallucination, schema compliance, sentiment bias | MoE 13B activated, fast, cheap, suitable for high-frequency validation |

> ⚠️ **Important**: The old DeepSeek names `deepseek-chat` / `deepseek-reasoner` were **officially deprecated on 2026-07-24**.
> You must use the new names `deepseek-v4-flash` (or `deepseek-v4-pro`).

---

## 3. Provider Configuration

Both use the OpenAI SDK; only the `base_url` and `api_key` are swapped:

### Generator (MiniMax M3)

```python
from openai import OpenAI
import os

generator = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],     # Obtain from the MiniMax platform
    base_url="https://api.minimax.io/v1",       # Confirmed 2026-06
)
# model = "MiniMax-M3"
# GroupId (MINIMAX_GROUP_ID): obtained when registering an account on the platform;
#   it is used by certain legacy / management endpoints; it is not required for chat/completions.
#   It is still an account identifier → put it in .env, do not commit.
```

### Auditor (DeepSeek V4 Flash)

```python
auditor = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],    # Obtain from the DeepSeek platform
    base_url="https://api.deepseek.com/v1",     # Confirmed 2026-06
)
# model = "deepseek-v4-flash"
```

**Credential management**: keep everything in `.env`; do not commit to git (`.gitignore` already contains `.env`).

```bash
# .env (do not commit)
MINIMAX_API_KEY=...
MINIMAX_GROUP_ID=...
DEEPSEEK_API_KEY=...
```

> 🔒 **Why put GroupId in .env too?** It is not a secret on its own (it cannot log in by itself), but it is an account identifier.
> A good convention for public repos: keep account identifiers in env alongside credentials, to avoid exposing your account in code/specs.

---

## 4. Generator Flow (MiniMax M3)

### Endpoint

```
POST https://api.minimax.io/v1/chat/completions
```

### Request

```json
{
  "model": "MiniMax-M3",
  "messages": [
    { "role": "system", "content": "[System Prompt — see below]" },
    { "role": "user", "content": "[User Input — Raw Data JSON]" }
  ],
  "temperature": 0.3,
  "max_tokens": 500,
  "response_format": { "type": "json_object" }
}
```

### User Input (Raw Data, PII stripped)

```json
{
  "timestamp": "2026-07-25T19:30:00Z",
  "gps": { "lat": -33.8568, "lng": 151.2153 },
  "trigger_type": "aesthetic_gaze",
  "domain": "tourism",
  "human_label": "beautiful",
  "human_description": "Sunset light piercing through the gaps between shipping containers, forming golden beams of light.",
  "tags": ["sunset", "container terminal"]
}
```

### System Prompt (Generator)

```
You are a "Human-Perspective Knowledge Engineer".

Task: Transform the participant's trigger data into a standardized Markdown note.

The output format must be JSON, containing:
{
  "frontmatter": {
    "timestamp": "...",
    "gps_lat": ...,
    "gps_lng": ...,
    "trigger_type": "...",
    "domain": "...",
    "tags": "..."
  },
  "body": {
    "human_description": "[preserve the original text]",
    "ai_analysis": "[infer the scene, sentiment, and professional judgment from the description, 200-300 words]",
    "related_links": ["[[wikilink_1]]", "[[wikilink_2]]"]
  }
}

Rules:
- The language follows the language of the participant's input (English / Cantonese / Mandarin)
- If human_label = "beautiful" → add the #aesthetic tag
- If human_label = "anomaly" → add the #anomaly tag
- Do not fabricate facts; only infer based on the provided data
```

### Response

```json
{
  "frontmatter": {
    "timestamp": "2026-07-25T19:30:00Z",
    "gps_lat": -33.8568,
    "gps_lng": 151.2153,
    "trigger_type": "aesthetic_gaze",
    "domain": "tourism",
    "tags": "sunset, container terminal, golden hour"
  },
  "body": {
    "human_description": "Sunset light piercing through the gaps between shipping containers, forming golden beams of light.",
    "ai_analysis": "This scene showcases the unique industrial aesthetics of Sydney Harbour...",
    "related_links": ["[[Sydney Harbour]]", "[[Industrial Aesthetics]]"]
  }
}
```

---

## 5. Auditor Flow (DeepSeek V4 Flash)

The draft entry produced by the generator first goes through the auditor before being written to `/01_Entries/`.

### Endpoint

```
POST https://api.deepseek.com/chat/completions
```

### Auditor System Prompt

```
You are a "Knowledge Auditor". You will receive a draft wiki entry and its raw data.

Validate the following items and output JSON:
{
  "verdict": "pass" | "fail",
  "issues": [                          // reasons for failure (filled when verdict=fail)
    {
      "type": "hallucination" | "schema_violation" | "bias" | "missing_field",
      "detail": "..."
    }
  ],
  "corrected": { ... }                 // optional: provide a corrected version (when verdict=fail)
}

Validation rules:
- hallucination: does the AI analysis contain facts not mentioned in the raw data?
- schema_violation: does the frontmatter include timestamp/gps_lat/gps_lng/trigger_type/domain?
  Are trigger_type / domain valid enumerated values?
- bias: does the AI analysis contain inappropriate bias or subjective value judgments beyond the "human perspective" scope?
- missing_field: are all three body parts present (human_description / ai_analysis / related_links)?
```

### Audit Result Handling (**Default: auto-correct**)

| Verdict | Action |
| :--- | :--- |
| `pass` | Write to `/01_Entries/` |
| `fail` + has `corrected` | **Automatically** use the auditor's `corrected` version and write to `/01_Entries/`; add `audited: corrected` to the frontmatter, and append an `<!-- audit_log -->` at the bottom of the entry recording the original issues |
| `fail` + no `corrected` | First automatically re-run the generator once (temperature +0.1, max 2 retries); if it still fails, write to `/00_Inbox/quarantine/` for manual handling, attaching the auditor issues |

**Design rationale**: The goal of P1 is a passive capture pipeline that minimizes manual intervention. The auditor (DeepSeek V4 Flash) is cheap enough that auto-correction + audit_log is the most efficient throughput. All corrections leave a log that can be reviewed afterward.

---

## 6. PII Stripping (Done Before the API)

Before Raw Data is sent to the generator, process it first with `tools/pii_anonymizer/`:

```python
def strip_pii(input_data):
    # Face blurring (blur_faces.py)
    # License plate blurring (blur_plates.py)
    # Remove names / phones / emails (text scan)
    return sanitized_data
```

**Ironclad rule**: any data that has not passed PII stripping must not be sent to the LLM API.

---

## 7. Token / Cost Considerations

| Dimension | Generator (MiniMax M3) | Auditor (DeepSeek V4 Flash) |
| :--- | :--- | :--- |
| Call frequency | 1 per raw entry | 1 per draft entry |
| Expected tokens | ~400 in + ~500 out | ~700 in (draft+raw) + ~200 out |
| Cost strategy | Consumes the token plan (main budget) | Use flash to control cost |
| Tunable parameters | `temperature=0.3` (stable) | `temperature=0.0` (validation must be deterministic) |

---

## 8. Error Handling

| HTTP Code | Situation | Handling |
| :--- | :--- | :--- |
| 400 | Invalid Input | Return the schema error message |
| 401 | Invalid API key | Check `.env` |
| 429 | Rate Limit | Exponential backoff |
| 500 | Provider Error | Write to `/00_Inbox/` for retry |
| Auditor `fail` | Audit failed | See §5 audit result handling |
