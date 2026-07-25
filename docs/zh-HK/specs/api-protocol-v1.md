[English](../../../specs/api-protocol-v1.md) | 繁體中文

# LLM Wiki Engine API 協議 v1.0

## 1. 概覽

呢份文件定義 **P1 LLM Wiki Engine** 嘅 API 設計。P0 階段唔需要 LLM，但個 spec 提前寫好，確保未來整合順暢。

**核心決定**：
- ✅ 基於 API（唔用本地 Llama 3.2）
- ✅ **雙 LLM 架構**：一個 generator + 一個 auditor，將產生同埋審查分開
- ✅ 兩個 provider 都係 OpenAI 兼容，所以可以用同一個 SDK（只係換 `base_url`）
- ✅ PII Stripping 喺 API 呼叫之前完成

---

## 2. 雙 LLM 架構

```
            Raw Data（PII 已剝離）
                    │
                    ▼
        ┌────────────────────────┐
        │  Generator: MiniMax M3 │   ← Wiki 條目嘅主要產生者
        │  model: MiniMax-M3     │      （消耗 token 計畫，主要預算）
        └────────────────────────┘
                    │ 草稿條目（JSON）
                    ▼
        ┌────────────────────────┐
        │  Auditor: DeepSeek V4  │   ← 審查草稿
        │           Flash        │      （平 + 快，用嚟做驗證）
        │  model: deepseek-v4-   │
        │         flash          │
        └────────────────────────┘
                    │ pass → 直接寫入儲存
                    │ fail + corrected → 自動修正，然後寫入
                    │ fail 冇 corrected → 重試 / 隔離
                    ▼
              最終條目（寫入 /01_Entries/）
```

| 角色 | Provider | 模型名 | 用途 | 點解揀佢 |
| :--- | :--- | :--- | :--- | :--- |
| **Generator** | MiniMax | `MiniMax-M3` | 將 Raw Data 轉做標準化 wiki 條目（人類描述 + AI 分析 + 雙向連結） | 強多多模態推理、coding/agent 導向、1M context |
| **Auditor** | DeepSeek | `deepseek-v4-flash` | 審查 generator 輸出：幻覺、schema 合規、情感偏見 | MoE 13B 激活、快、平、適合高頻驗證 |

> ⚠️ **重要**：舊嘅 DeepSeek 名 `deepseek-chat` / `deepseek-reasoner` 已經喺 **2026-07-24 正式廢棄**。
> 你必須用新名 `deepseek-v4-flash`（或 `deepseek-v4-pro`）。

---

## 3. Provider 配置

兩者都用 OpenAI SDK；只係換 `base_url` 同 `api_key`：

### Generator（MiniMax M3）

```python
from openai import OpenAI
import os

generator = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],     # 由 MiniMax 平台取得
    base_url="https://api.minimax.io/v1",       # 2026-06 確認
)
# model = "MiniMax-M3"
# GroupId（MINIMAX_GROUP_ID）：喺平台註冊帳號時取得；
#   某啲 legacy / 管理 endpoint 會用到；chat/completions 唔需要。
#   不過佢仍然係帳號識別碼 → 放落 .env，唔好 commit。
```

### Auditor（DeepSeek V4 Flash）

```python
auditor = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],    # 由 DeepSeek 平台取得
    base_url="https://api.deepseek.com/v1",     # 2026-06 確認
)
# model = "deepseek-v4-flash"
```

**憑證管理**：全部放落 `.env`；唔好 commit 去 git（`.gitignore` 已經包含 `.env`）。

```bash
# .env（唔好 commit）
MINIMAX_API_KEY=...
MINIMAX_GROUP_ID=...
DEEPSEEK_API_KEY=...
```

> 🔒 **點解 GroupId 都要放落 .env？** 佢本身唔係 secret（單獨唔可以登入），但係一個帳號識別碼。
> 公開 repo 嘅好習慣：將帳號識別碼同憑證一齊放落 env，避免喺 code / spec 入面暴露你個帳號。

---

## 4. Generator 流程（MiniMax M3）

### Endpoint

```
POST https://api.minimax.io/v1/chat/completions
```

### 請求

```json
{
  "model": "MiniMax-M3",
  "messages": [
    { "role": "system", "content": "[System Prompt — 見下面]" },
    { "role": "user", "content": "[User Input — Raw Data JSON]" }
  ],
  "temperature": 0.3,
  "max_tokens": 500,
  "response_format": { "type": "json_object" }
}
```

### User Input（Raw Data，PII 已剝離）

```json
{
  "timestamp": "2026-07-25T19:30:00Z",
  "gps": { "lat": -33.8568, "lng": 151.2153 },
  "trigger_type": "aesthetic_gaze",
  "domain": "tourism",
  "human_label": "beautiful",
  "human_description": "夕陽光線穿過貨櫃之間嘅罅隙，形成一道道金色光束。",
  "tags": ["sunset", "container terminal"]
}
```

### System Prompt（Generator）

```
你係一個「人類視角知識工程師」。

任務：將參與者嘅觸發數據轉換成標準化 Markdown 筆記。

輸出格式必須係 JSON，包含：
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
    "ai_analysis": "[由描述推斷場景、情感同埋專業判斷，200-300 字]",
    "related_links": ["[[wikilink_1]]", "[[wikilink_2]]"]
  }
}

規則：
- 語言跟參與者輸入嘅語言（英文 / 廣東話 / 普通話）
- 如果 human_label = "beautiful" → 加 #aesthetic 標籤
- 如果 human_label = "anomaly" → 加 #anomaly 標籤
- 唔好作事實；只可以基於提供嘅數據去推斷
```

### 回應

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
    "human_description": "夕陽光線穿過貨櫃之間嘅罅隙，形成一道道金色光束。",
    "ai_analysis": "呢個場景展現咗悉尼港獨特嘅工業美學...",
    "related_links": ["[[Sydney Harbour]]", "[[Industrial Aesthetics]]"]
  }
}
```

---

## 5. Auditor 流程（DeepSeek V4 Flash）

Generator 產生嘅草稿條目，會先經過 auditor 審查，先至寫入 `/01_Entries/`。

### Endpoint

```
POST https://api.deepseek.com/chat/completions
```

### Auditor System Prompt

```
你係一個「知識審查員」。你會收到一份草稿 wiki 條目同埋佢嘅原始數據。

驗證以下項目並輸出 JSON：
{
  "verdict": "pass" | "fail",
  "issues": [                          // 失敗原因（verdict=fail 時填寫）
    {
      "type": "hallucination" | "schema_violation" | "bias" | "missing_field",
      "detail": "..."
    }
  ],
  "corrected": { ... }                 // 選填：提供修正版本（verdict=fail 時）
}

驗證規則：
- hallucination：AI 分析有冇提及原始數據入面冇嘅事實？
- schema_violation：frontmatter 有冇齊 timestamp/gps_lat/gps_lng/trigger_type/domain？
  trigger_type / domain 係咪有效嘅枚舉值？
- bias：AI 分析有冇超出「人類視角」範圍嘅不當偏見或主觀價值判斷？
- missing_field：body 三部分有冇齊（human_description / ai_analysis / related_links）？
```

### 審查結果處理（**預設：自動修正**）

| Verdict | 動作 |
| :--- | :--- |
| `pass` | 寫入 `/01_Entries/` |
| `fail` + 有 `corrected` | **自動**用 auditor 嘅 `corrected` 版本並寫入 `/01_Entries/`；喺 frontmatter 加 `audited: corrected`，並且喺條目底部加一段 `<!-- audit_log -->` 記錄原本嘅問題 |
| `fail` + 冇 `corrected` | 先自動重新行一次 generator（temperature +0.1，最多 2 次重試）；如果都係 fail，寫入 `/00_Inbox/quarantine/` 等人手處理，並附上 auditor 問題 |

**設計原因**：P1 嘅目標係一條被動捕捉嘅流水線，盡量減少人手介入。Auditor（DeepSeek V4 Flash）夠平，所以自動修正 + audit_log 係最有效率嘅吞吐方式。所有修正都會留低 log，之後可以覆核。

---

## 6. PII 剝離（喺 API 之前做）

Raw Data 送俾 generator 之前，先用 `tools/pii_anonymizer/` 處理：

```python
def strip_pii(input_data):
    # 人面模糊（blur_faces.py）
    # 車牌模糊（blur_plates.py）
    # 移除姓名 / 電話 / email（文字掃描）
    return sanitized_data
```

**鐵律**：任何未通過 PII 剝離嘅數據，一律唔可以送去 LLM API。

---

## 7. Token / 成本考量

| 維度 | Generator（MiniMax M3） | Auditor（DeepSeek V4 Flash） |
| :--- | :--- | :--- |
| 呼叫頻率 | 每個原始 entry 1 次 | 每個草稿 entry 1 次 |
| 預計 token | ~400 in + ~500 out | ~700 in（草稿+原始）+ ~200 out |
| 成本策略 | 消耗 token 計畫（主要預算） | 用 flash 控制成本 |
| 可調參數 | `temperature=0.3`（穩定） | `temperature=0.0`（驗證必須確定性） |

---

## 8. 錯誤處理

| HTTP Code | 情況 | 處理 |
| :--- | :--- | :--- |
| 400 | 輸入無效 | 返回 schema 錯誤訊息 |
| 401 | API key 無效 | 檢查 `.env` |
| 429 | Rate Limit | 指數退避 |
| 500 | Provider 錯誤 | 寫入 `/00_Inbox/` 等重試 |
| Auditor `fail` | 審查失敗 | 睇 §5 審查結果處理 |
