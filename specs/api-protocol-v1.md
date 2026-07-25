# LLM Wiki Engine API Protocol v1.0

## 1. 概述

呢份文件定義 **P1 LLM Wiki Engine** 嘅 API 設計。P0 階段唔需要 LLM，但 spec 預先寫定，確保未來整合順暢。

**核心決策**：
- ✅ API-based（唔用 local Llama 3.2）
- ✅ OpenAI-compatible endpoint（方便切換 provider）
- ✅ PII Stripping 喺 API 之前完成

---

## 2. API Endpoint

```
POST /v1/chat/completions
```

---

## 3. Request Format (OpenAI-compatible)

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "[System Prompt — 見 Section 5]"
    },
    {
      "role": "user",
      "content": "[User Input — 見 Section 4]"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 500,
  "response_format": { "type": "json_object" }
}
```

---

## 4. User Input Format

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

---

## 5. System Prompt

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

---

## 6. Response Format

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

## 7. Provider 選擇（建議）

| Provider | 優點 | 注意 |
| :--- | :--- | :--- |
| OpenAI (GPT-4o-mini) | 最穩定、低延遲 | 數據出境需合規 |
| Azure OpenAI | 澳洲區 hosting | 符合私隱要求 |
| DeepSeek API | 低成本、OpenAI-compatible | 中國 hosting |
| Groq (Llama 3) | 開源、快速 | 需自訂 prompt |

**建議 P1 先用 DeepSeek API 測試**（符合你嘅生態方向），後期可切換。

---

## 8. PII Stripping（喺 API 前做）

```python
def strip_pii(input_data):
    # 人臉模糊
    # 車牌模糊
    # 移除姓名/電話/email
    return sanitized_data
```

---

## 9. 錯誤處理

| HTTP Code | 情況 | 處理 |
| :--- | :--- | :--- |
| 400 | Invalid Input | 返回 schema 錯誤訊息 |
| 429 | Rate Limit | Exponential backoff |
| 500 | LLM Provider Error | 寫入 `/00_Inbox/` 待重試 |
