# Project Hive.AGI

## 人類分散式知識共生網絡

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Data License: CC BY-NC-SA 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## 🎯 願景

> 大廠建造嘅 AGI，係由電腦訓練電腦，最終服務於電腦嘅邏輯。
> 我哋建造嘅 AGI，係由人類貢獻人類視角，最終服務於人類嘅多元價值。

**Project Hive.AGI** 嘅終點，唔係一個中央超級 AI，而係一個 **由全球人類節點共同維護、分散式、開源嘅「人類視角知識共生網絡」**。

任何人都可以用自己嘅設備（眼鏡、手機、電腦、工業感應器）貢獻自己專業領域嘅「人類視角數據」，並透過 LLM Wiki 將呢啲數據沉澱為可交換、可綜合嘅結構化知識。

---

## 🚀 快速開始 (P0 — 今日用得)

### 1. Clone Repo

```bash
git clone https://github.com/CTO-goldmanglobal/gg-hiveagi.git
cd gg-hiveagi
```

### 2. 安裝依賴

```bash
pip install -r tools/seed_generator/requirements.txt
```

### 3. 生成第一個 Seed Package

```bash
python tools/seed_generator/generate_seed.py
```

輸出會喺 `seed_output/seed_goldman_20260725/`，包含：
- `manifest.json` — 貢獻者資訊、領域分類、數據統計
- `entries/entry_001.md` — 標準化 Markdown 筆記
- `README.md` — 使用說明

### 4. 校驗 Seed Package

```bash
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/
```

---

## 📂 核心規範文件

| 文件 | 說明 |
| :--- | :--- |
| `PROJECT_MASTER_PLAN.md` | 完整計劃書（由願景到 Code） |
| `specs/seed-package-schema-v1.md` | Seed Package JSON / Markdown 格式規範 |
| `specs/vault-structure-spec.md` | Obsidian Vault 目錄結構與命名規範 |
| `specs/api-protocol-v1.md` | P1 LLM Wiki Engine API 設計（MiniMax M3 generator + DeepSeek V4 Flash auditor） |

---

## 🧩 開發路線圖

| 階段 | 組件 | 狀態 |
| :--- | :--- | :--- |
| **P0** | Seed Generator + Validator + Vault Setup | ✅ 已完成 |
| **P0** | Specs (Schema / Vault / API) | ✅ 已完成 |
| **P1** | LLM Wiki Engine (MiniMax M3 + DeepSeek V4 Flash dual-LLM) | ✅ 已完成（mock 驗證） |
| **P1** | Mobile Capture App (Basic) | 📋 規劃中 |
| **P2** | P2P Exchange (IPFS / libp2p) | 📋 規劃中 |
| **P2** | Obsidian Plugin | 📋 規劃中 |

---

## 📄 License 說明

| 組件 | License | 原因 |
| :--- | :--- | :--- |
| **Code** (Python Scripts, Specs, Tools) | [AGPL-3.0](./LICENSE) | 確保開源衍生作品必須共享改進，鼓勵企業贊助 |
| **Seed Data** (貢獻者產生嘅知識包) | [CC-BY-NC-SA-4.0](./DATA_LICENSE.md) | 允許分享與改編，但唔准商業使用，保障貢獻者 |
| **商業授權** | [Commercial](./COMMERCIAL_LICENSE.md) | 企業如需商業使用，請聯絡 cto@goldmanglobal.com.au |

---

## 🤝 點樣參與

1. **Star & Fork** 呢個 Repo
2. **閱讀** [CONTRIBUTING.md](./CONTRIBUTING.md)
3. **簽署 CLA**（Contributor License Agreement）
4. **貢獻**你嘅 Seed Package 或改善 Code
5. **加入討論**：Discord (Coming Soon)

---

## 📬 聯絡

- **研究合作 / 商業授權**：cto@goldmanglobal.com.au

---

## 🙏 鳴謝

由 [Goldman Global Research Labs](https://goldmanglobal.com.au) 發起，感謝所有參與「人類視角數據貢獻計劃」嘅開源貢獻者。

---

**一句話總結**：

> 等電腦學習點樣理解人類，而唔係人類學習點樣適應電腦。
