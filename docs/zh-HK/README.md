[English](../../README.md) | 繁體中文

# Project Hive.AGI

## 一個為人類而設嘅分佈式知識共生網絡

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Data License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![CI](https://github.com/CTO-goldmanglobal/gg-hiveagi/actions/workflows/ci.yml/badge.svg)](https://github.com/CTO-goldmanglobal/gg-hiveagi/actions/workflows/ci.yml)

---

## 🎯 願景

> 大廠做嘅 AGI，係電腦訓練電腦，最終服務嘅係電腦嘅邏輯。
> 我哋做嘅 AGI，係人類貢獻人類視角，最終服務嘅係人類多元價值。

**Project Hive.AGI** 嘅最終目標唔係一個中心化嘅超級 AI，而係一個**分佈式、開源嘅「人類視角知識共生網絡」，由世界各地嘅人類節點共同維護。**

任何人都可以用自己嘅裝置（眼鏡、手機、電腦、工業感測器），喺自己擅長嘅領域貢獻「人類視角數據」，然後透過 LLM Wiki，將呢啲數據蒸餾成可以交換同埋合成嘅結構化知識。

---

## 🚀 快速開始（P0 — 即開即用）

### 1. Clone 個 Repo

```bash
git clone https://github.com/CTO-goldmanglobal/gg-hiveagi.git
cd gg-hiveagi
```

### 2. 安裝依賴

```bash
# P0（種子產生器 + 驗證器）
pip install -r tools/seed_generator/requirements.txt

# P1（llm_wiki_engine）
pip install -r llm_wiki_engine/requirements.txt
```

### 3. 設定 LLM 憑證（只有 P1 真實模式先需要）

P1 LLM Wiki Engine 預設用 mock 模式（唔使 key）。
要用真實嘅 MiniMax / DeepSeek API，就整一個 `.env`：

```bash
cp llm_wiki_engine/.env.example .env
# 然後用編輯器填入真實 key（唔好貼落 chat / commit）
```

需要嘅 key（睇 `specs/api-protocol-v1.md`）：

| 變數 | 用途 |
| :--- | :--- |
| `MINIMAX_API_KEY` | Generator（MiniMax M3） |
| `DEEPSEEK_API_KEY` | Auditor（DeepSeek V4 Flash） |

`.env` 已經喺 `.gitignore` 入面，唔會被 commit。

### 4. 產生你嘅第一個 Seed Package（P0）

```bash
python tools/seed_generator/generate_seed.py
```

輸出會喺 `seed_output/seed_goldman_20260725/`，包含：
- `manifest.json` — 貢獻者中繼資料、領域分類、數據統計
- `entries/entry_001.md` — 標準化 Markdown 筆記
- `README.md` — 使用說明

### 5. 驗證 Seed Package（P0）

```bash
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/
```

### 6. LLM Wiki Engine（P1，mock 模式）

```bash
python -m llm_wiki_engine process \
    --inbox llm_wiki_engine/test_samples \
    --entries /tmp/test_entries \
    --mock
```

設定好 `.env` 之後，移除 `--mock` 就可以用真實嘅 MiniMax + DeepSeek API。睇 [`llm_wiki_engine/README.md`](../../llm_wiki_engine/README.md)。

### 7. 從影片收集 RawData（兩條路徑）

```bash
# 路徑 1（推薦，零 PII 風險）：人手挑選
python tools/video_ingest/extract_frames.py video.mp4 --at 00:01:23 --out frames/
python tools/video_ingest/capture_helper.py --video video.mp4 --inbox ./00_Inbox
python -m llm_wiki_engine process --inbox ./00_Inbox --entries ./01_Entries

# 路徑 2（自動視覺，強制 PII 模糊）
python tools/video_ingest/extract_frames.py video.mp4 --every 30 --out frames/
python -m llm_wiki_engine process-video --frames frames/ --inbox ./00_Inbox --location Sydney
python -m llm_wiki_engine process --inbox ./00_Inbox --entries ./01_Entries
```

睇 [`tools/video_ingest/README.md`](../../tools/video_ingest/README.md)。

> 🔒 **安全閘**：自動視覺路徑**必須**先通過人面 + 車牌模糊處理（MediaPipe + OpenCV），
> 先可以送去 LLM。冇 `--skip-blur` 呢個選項。如果模糊失敗，數據會被拒絕送去 LLM（spec §6 鐵律，由代碼強制執行）。

---

## 📂 核心規格文件

| 文件 | 描述 |
| :--- | :--- |
| `PROJECT_MASTER_PLAN.md` | 完整總計畫（由願景到代碼） |
| `specs/seed-package-schema-v1.md` | Seed Package JSON / Markdown 格式規格 |
| `specs/vault-structure-spec.md` | Obsidian Vault 目錄結構同埋命名規範 |
| `specs/api-protocol-v1.md` | P1 LLM Wiki Engine API 設計（MiniMax M3 generator + DeepSeek V4 Flash auditor） |

---

## 🧩 開發路線圖

| 階段 | 組件 | 狀態 |
| :--- | :--- | :--- |
| **P0** | Seed Generator + Validator + Vault Setup | ✅ 完成 |
| **P0** | Specs（Schema / Vault / API） | ✅ 完成 |
| **P1** | LLM Wiki Engine（MiniMax M3 + DeepSeek V4 Flash 雙 LLM） | ✅ 完成（mock 已驗證） |
| **P1** | 流動捕捉 App（基礎版） | 📋 規劃中 |
| **P2** | P2P Exchange（IPFS / 內容定址） | ✅ 完成（mock 已驗證） |
| **P2** | Obsidian Plugin | ✅ 完成（build + 跨平台兼容已驗證） |

---

## 📄 授權概覽

| 組件 | 授權 | 原因 |
| :--- | :--- | :--- |
| **代碼**（Python 腳本、Specs、Tools） | [AGPL-3.0](../../LICENSE) | 確保開源衍生作品必須分享改進，鼓勵企業贊助 |
| **Seed Data**（貢獻者產生嘅知識包） | [CC-BY-NC-SA-4.0](../../DATA_LICENSE.md) | 允許分享同埋改編，但禁止商業用途，保護貢獻者 |
| **商業授權** | [Commercial](../../COMMERCIAL_LICENSE.md) | 需要商業用途嘅企業，請聯絡 cto@goldmanglobal.com.au |

---

## 🤝 點樣貢獻

1. **Star 同 Fork** 呢個 repo
2. **睇** [CONTRIBUTING.md](../../CONTRIBUTING.md)
3. **簽 CLA**（Contributor License Agreement）
4. **貢獻** 你嘅 Seed Package 或者改善代碼
5. **加入討論**：Discord（即將推出）

---

## 📬 聯絡

- **研究合作 / 商業授權**：cto@goldmanglobal.com.au

---

## 🙏 鳴謝

由 [Goldman Global Research Labs](https://goldmanglobal.com.au) 發起，多謝所有參與「人類視角數據貢獻計畫」嘅開源貢獻者。

---

**用一句講**：

> 等電腦學識點樣理解人類，而唔係人類學識點樣遷就電腦。
