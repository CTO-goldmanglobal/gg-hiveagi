# LLM Wiki Engine API Protocol v1.0

## 1. 概述

呢份文件定義 **P1 LLM Wiki Engine** 嘅 API 設計。P0 階段唔需要 LLM，但 spec 預先寫定，確保未來整合順暢。

**核心決策**：
- ✅ API-based（唔用 local Llama 3.2）
- ✅ **Dual-LLM 架構**：一個 generator + 一個 auditor，生成同審查分離
- ✅ 兩個 provider 都係 OpenAI-compatible，可用同一個 SDK（淨係換 base_url）
- ✅ PII Stripping 喺 API 之前完成

---

## 2. Dual-LLM 架構

```
            Raw Data (已 strip PII)
                    │
                    ▼
        ┌────────────────────────┐
        │  Generator: MiniMax M3 │   ← 主力生成 wiki entry
        │  model: MiniMax-M3     │      （食 token plan，主預算）
        └────────────────────────┘
                    │ draft entry (JSON)
                    ▼
        ┌────────────────────────┐
        │  Auditor: DeepSeek V4  │   ← 審查 draft
        │           Flash        │      （平 + 快，校驗用）
        │  model: deepseek-v4-   │
        │         flash          │
        └────────────────────────┘
                    │ pass → 直接入庫
                    │ fail + corrected → 自動修正後入庫
                    │ fail 無 corrected → 重試 / quarantine
                    ▼
              Final Entry (寫入 /01_Entries/)
```

| 角色 | Provider | Model 名 | 用途 | 點解揀佢 |
| :--- | :--- | :--- | :--- | :--- |
| **Generator** | MiniMax | `MiniMax-M3` | 將 Raw Data 轉為標準化 wiki entry（人類描述 + AI 分析 + 雙向鏈接） | 多模態推理強、coding/agent 導向、1M context |
| **Auditor** | DeepSeek | `deepseek-v4-flash` | 審查 generator 產出：hallucination、schema 合規、情感偏差 | MoE 13B activated、快、平、適合高頻校驗 |

> ⚠️ **重要**：DeepSeek 旧名 `deepseek-chat` / `deepseek-reasoner` 已喺 **2026-07-24 正式 deprecate**。
> 必須用新名 `deepseek-v4-flash`（或 `deepseek-v4-pro`）。

---

## 3. Provider 配置

兩者都用 OpenAI SDK，只係換 `base_url` 同 `api_key`：

### Generator (MiniMax M3)

```python
from openai import OpenAI
import os

generator = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],     # 由 MiniMax platform 拎
    base_url="https://api.minimax.io/v1",       # 確認 2026-06
)
# model = "MiniMax-M3"
# GroupId（MINIMAX_GROUP_ID）：喺 platform 註冊帳號時拎到，
#   某啲 legacy / management endpoint 會用到；chat/completions 唔一定要傳。
#   仍屬帳號識別碼 → 放 .env，唔好 commit。
```

### Auditor (DeepSeek V4 Flash)

```python
auditor = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],    # 由 DeepSeek platform 拎
    base_url="https://api.deepseek.com/v1",     # 確認 2026-06
)
# model = "deepseek-v4-flash"
```

**Credentials 管理**：全部放 `.env`，唔好入 git（`.gitignore` 已含 `.env`）。

```bash
# .env (唔 commit)
MINIMAX_API_KEY=...
MINIMAX_GROUP_ID=...
DEEPSEEK_API_KEY=...
```

> 🔒 **點解 GroupId 都放 .env？** 佢本身唔係 secret（單獨唔能登入），但係帳號識別碼。
> Public repo 嘅良好慣例：帳號識別碼同 credential 一齊放 env，避免喺 code/spec 度暴露你嘅帳號。

---

## 4. Generator Flow（MiniMax M3）

### Endpoint

```
POST https://api.minimax.io/v1/chat/completions
```

### Request

```json
{
  "model": "MiniMax-M3",
  "messages": [
    { "role": "system", "content": "[System Prompt — 見下]" },
    { "role": "user", "content": "[User Input — Raw Data JSON]" }
  ],
  "temperature": 0.3,
  "max_tokens": 500,
  "response_format": { "type": "json_object" }
}
```

### User Input（Raw Data，已 strip PII）

```json
{
  "timestamp": "2026-07-25T19:30:00Z",
  "gps": { "lat": -33.8568, "lng": 151.2153 },
  "trigger_type": "aesthetic_gaze",
  "domain": "tourism",
  "human_label": "靚",
  "human_description": "夕陽穿過貨櫃之間嘅縫隙，形成金色光柱。",
  "tags": ["日落", "貨櫃碼頭"]
}
```

### System Prompt（Generator）

```
你係一個「人類視角知識工程師」。

任務：將參與者嘅觸發數據轉化為一篇標準化嘅 Markdown 筆記。

輸出格式必須為 JSON，包含：
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
    "human_description": "[保留原文]",
    "ai_analysis": "[根據描述推測場景、情感、專業判斷，200-300字]",
    "related_links": ["[[wikilink_1]]", "[[wikilink_2]]"]
  }
}

規則：
- 語言跟隨參與者輸入嘅語言（粵語/英文/普通話）
- 如果 human_label = "靚" → 加入 #aesthetic 標籤
- 如果 human_label = "異常" → 加入 #anomaly 標籤
- 唔好憑空創作事實，只係根據提供嘅資料推測
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
    "tags": "日落, 貨櫃碼頭, 黃金時刻"
  },
  "body": {
    "human_description": "夕陽穿過貨櫃之間嘅縫隙，形成金色光柱。",
    "ai_analysis": "呢個景觀展現了悉尼港口獨特嘅工業美學...",
    "related_links": ["[[悉尼港口]]", "[[工業美學]]"]
  }
}
```

---

## 5. Auditor Flow（DeepSeek V4 Flash）

Generator 產出嘅 draft entry 會先過 auditor，通過先寫入 `/01_Entries/`。

### Endpoint

```
POST https://api.deepseek.com/chat/completions
```

### Auditor System Prompt

```
你係一個「知識審計員」。你會收到一份 draft wiki entry 同佢嘅原始數據。

校驗以下項目，輸出 JSON：
{
  "verdict": "pass" | "fail",
  "issues": [                          // 失敗原因（verdict=fail 時填）
    {
      "type": "hallucination" | "schema_violation" | "bias" | "missing_field",
      "detail": "..."
    }
  ],
  "corrected": { ... }                 // 可選：提供修正版（verdict=fail 時）
}

校驗規則：
- hallucination：AI 分析入面有冇原始數據冇提到嘅事實？
- schema_violation：frontmatter 係咪齊 timestamp/gps_lat/gps_lng/trigger_type/domain？
  trigger_type / domain 係咪屬於有效列舉值？
- bias：AI 分析有冇不當偏見或主觀價值判斷超出「人類視角」範圍？
- missing_field：body 三部分（human_description / ai_analysis / related_links）齊唔齊？
```

### 審查結果處理（**預設：自動修正**）

| Verdict | 動作 |
| :--- | :--- |
| `pass` | 寫入 `/01_Entries/` |
| `fail` + 有 `corrected` | **自動**用 auditor 嘅 `corrected` 版寫入 `/01_Entries/`，frontmatter 加 `audited: corrected`，並喺 entry 底部附 `<!-- audit_log -->` 記錄原 issues |
| `fail` + 無 `corrected` | 先自動重跑 generator 1 次（temperature +0.1，max 2 次重試）；仍 fail 先寫入 `/00_Inbox/quarantine/` 待人手處理，附 auditor issues |

**設計理由**：P1 目標係 passive capture pipeline，要盡量少人手介入。auditor（DeepSeek V4 Flash）夠平，自動修正 + audit_log 係最有效率嘅 throughput。所有修正都留 log，事後可翻查。

---

## 6. PII Stripping（喺 API 前做）

喺 Raw Data 送 generator 之前，先用 `tools/pii_anonymizer/` 處理：

```python
def strip_pii(input_data):
    # 人臉模糊（blur_faces.py）
    # 車牌模糊（blur_plates.py）
    # 移除姓名/電話/email（文字掃描）
    return sanitized_data
```

**鐵律**：任何未過 PII stripping 嘅數據，唔可以送 LLM API。

---

## 7. Token / 成本考量

| 維度 | Generator (MiniMax M3) | Auditor (DeepSeek V4 Flash) |
| :--- | :--- | :--- |
| 調用頻率 | 每個 raw entry 1 次 | 每個 draft entry 1 次 |
| 預期 token | ~400 in + ~500 out | ~700 in（draft+raw）+ ~200 out |
| 成本策略 | 食 token plan（主預算） | 用 flash 控成本 |
| 可調參數 | `temperature=0.3`（穩定） | `temperature=0.0`（校驗要 deterministic） |

---

## 8. 錯誤處理

| HTTP Code | 情況 | 處理 |
| :--- | :--- | :--- |
| 400 | Invalid Input | 返回 schema 錯誤訊息 |
| 401 | API key 無效 | 檢查 `.env` |
| 429 | Rate Limit | Exponential backoff |
| 500 | Provider Error | 寫入 `/00_Inbox/` 待重試 |
| Auditor `fail` | 審查唔通過 | 見 §5 審查結果處理 |
