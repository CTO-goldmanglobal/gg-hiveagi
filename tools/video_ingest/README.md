# Video Ingest

將 street video 轉為 Hive.AGI RawData。**兩條 path**，配合唔同需求。

---

## Path 1: Manual curate（推薦，零 PII 風險）

由**人**定義邊個瞬間值得記錄 —— 呢個本身就係「人類視角」嘅核心。

### 流程

```bash
# 1. （可選）抽指定時間點嘅 frame 做參考
python tools/video_ingest/extract_frames.py video.mp4 \
    --at 00:01:23,00:03:45,00:07:12 \
    --out frames/

# 2. 用任何 player 播片，見到 moment 就暫停
# 3. 行 helper，填寫每筆 trigger
python tools/video_ingest/capture_helper.py \
    --video street_walk_001.mp4 \
    --inbox ./00_Inbox
# （helper 會逐筆問你 timestamp / 地點 / trigger_type / 描述）

# 4. 收集完之後，跑 P1 engine（純文字，唔碰 vision API）
python -m llm_wiki_engine process \
    --inbox ./00_Inbox --entries ./01_Entries
```

**點解推薦**：
- 零 PII 風險（唔上傳任何圖片）
- 每筆 trigger 都有你嘅人類判斷（唔係 AI 自動猜）
- 一條長片可以 curate 出 5–20 個高質 trigger

---

## Path 2: Auto-vision（實驗性，需 PII blur）

AI 自動睇 frame 生成描述。**必須先過 PII blur**（人臉 + 車牌）。

### 流程

```bash
# 1. 抽 frame（每 30 秒一帧）
python tools/video_ingest/extract_frames.py video.mp4 --every 30 --out frames/

# 2. Auto-vision：blur + MiniMax M3 + 寫 inbox
python -m llm_wiki_engine process-video \
    --frames frames/ \
    --inbox ./00_Inbox \
    --location Sydney \
    --every 30
# （每個 frame：先 blur 人臉/車牌 → 送 MiniMax M3 → 寫 RawData JSON）

# 3. 跑 P1 engine 做 audit（DeepSeek V4 Flash）
python -m llm_wiki_engine process \
    --inbox ./00_Inbox --entries ./01_Entries
```

### ⚠️ 安全設計

- **冇 `--skip-blur` flag**。呢個係刻意嘅。
- 每個 frame 送 LLM 之前必須過 `anonymize_image()`（MediaPipe face + OpenCV plate）
- blur 失敗 → 拒絕送 LLM（`SafetyError`）
- 詳見 `tools/pii_anonymizer/`

### 準確度限制

- **車牌偵測**：edge-based 通用偵測器，AU 車牌 recall 中等。請人手 review 低置信度 frame。
- **Vision token 成本**：每 frame 約等於 ~500–1000 tokens。抽 frame 間隔係成本旋鈕。

---

## 依賴

| Path | 需要安裝 |
|---|---|
| **Path 1 (manual)** | ffmpeg（`brew install ffmpeg`）|
| **Path 2 (auto-vision)** | ffmpeg + `pip install -r tools/pii_anonymizer/requirements.txt` + MiniMax API key |

## 檔案

```
tools/video_ingest/
├── extract_frames.py        # ffmpeg wrapper（兩條 path 共用）
├── capture_helper.py        # Path 1 互動 helper（純 stdlib）
├── templates/
│   └── manual_capture.json  # 手填 template
└── README.md                # 呢份
```

## License

AGPL-3.0（同主 repo 一致）。
