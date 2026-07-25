[English](../../PROJECT_MASTER_PLAN.md) | 繁體中文

# Project Hive.AGI — 總計畫

> 完整總計畫：由願景到代碼。
> 由 Goldman Global Research Labs 發起。
> 聯絡：cto@goldmanglobal.com.au

---

## 📌 一句話定位

**Project Hive.AGI** 係一個由 Goldman Global Research Labs 發起嘅開源研究計畫，目標係構建一個**由人類貢獻、由人類定義、分佈式嘅知識共生網絡。**

核心口號：

> 等電腦學識點樣理解人類，而唔係人類學識點樣遷就電腦。

---

## 🎯 願景

> 大廠做嘅 AGI，係電腦訓練電腦，最終服務嘅係電腦嘅邏輯。
> 我哋做嘅 AGI，係人類貢獻人類視角，最終服務嘅係人類多元價值。

**Project Hive.AGI** 嘅最終目標唔係一個中心化嘅超級 AI，而係一個**分佈式、開源嘅「人類視角知識共生網絡」，由世界各地嘅人類節點共同維護。**

任何人都可以用自己嘅裝置（眼鏡、手機、電腦、工業感測器），喺自己擅長嘅領域貢獻「人類視角數據」，然後透過 LLM Wiki，將呢啲數據蒸餾成可以交換同埋合成嘅結構化知識。

---

## 🧩 技術核心

- **捕捉層**：AI 眼鏡 / 手機 / 工業感測器收集「人類視角數據」（一個人喺當下覺得重要 / 靚 / 異常嘅時刻）。
- **Wiki 層**：Obsidian Vault + 雙向連結，將原始數據蒸餾成結構化 Markdown 知識。
- **LLM 層**：雙 LLM API 架構 — **MiniMax M3**（generator，wiki 條目嘅主要產生者）+ **DeepSeek V4 Flash**（auditor，自動審查 + 修正幻覺 / schema 違規）。兩者都係 OpenAI 兼容。唔用本地 Llama。睇 `specs/api-protocol-v1.md`。
- **P2P 層**：Seed Package（標準化知識包）透過 IPFS / libp2p 喺貢獻者之間交換。

---

## 📐 MVP 開發路線圖

優先順序策略：一個最簡可行產品（MVP），由最簡單嘅組件開始。

| 優先級 | 組件 | 複雜度 | 預計時間 | 原因 |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | Seed Package Generator（Python 腳本） | ⭐ | 1–2 日 | 將現有數據轉換成標準化 Seed Package |
| **P0** | Obsidian Vault Setup 腳本 | ⭐ | 1 日 | 自動建立 Vault 目錄結構同埋 Templates |
| **P0** | Specs（Schema / Vault / API） | ⭐ | 1 日 | 鎖定規格，避免返工 |
| **P1** | LLM Wiki Engine（基於 API） | ⭐⭐ | 1 星期 | 用 OpenAI 兼容 API 將 Raw Data 轉做 Markdown |
| **P1** | 流動捕捉 App（基礎版） | ⭐⭐⭐ | 2–4 星期 | 取代人手㩒；達成 Passive Capture |
| **P2** | P2P Exchange（IPFS） | ⭐⭐⭐⭐ | 1–2 個月 | 自動 Seed Package 交換 |
| **P2** | Obsidian Plugin | ⭐⭐⭐⭐ | 1–2 個月 | 等其他 Obsidian 用家可以直接參與 |

---

## 📂 Repo 結構

```
gg-hiveagi/
├── README.md                       # 計畫介紹
├── LICENSE                         # AGPL-3.0
├── DATA_LICENSE.md                 # CC-BY-NC-SA-4.0（Seed Data）
├── COMMERCIAL_LICENSE.md           # 商業授權
├── CONTRIBUTING.md                 # 點樣貢獻 + CLA
├── PROJECT_MASTER_PLAN.md          # 呢份文件
│
├── specs/                          # 規格文件（Markdown）
│   ├── seed-package-schema-v1.md
│   ├── vault-structure-spec.md
│   └── api-protocol-v1.md
│
├── tools/                          # 輔助工具腳本
│   ├── seed_generator/             # P0：Seed Package Generator
│   ├── vault_setup/                # P0：Obsidian Vault Setup
│   └── pii_anonymizer/             # 私隱工具
│
├── llm_wiki_engine/                # P1：LLM Wiki Engine（之後）
├── mobile_app/                     # P1：流動 App（之後）
├── p2p_exchange/                   # P2：IPFS 交換（之後）
└── obsidian_plugin/                # P2：Obsidian Plugin（之後）
```

---

## 📄 授權策略（雙重授權）

| 組件 | 授權 | 原因 |
| :--- | :--- | :--- |
| **代碼** | AGPL-3.0 | 強 copyleft + 塞返 SaaS 漏洞；想 SaaS 部署 / 商業用途嘅大廠必須傾商業授權。確保衍生作品必須分享改進。 |
| **Seed Data** | CC-BY-NC-SA-4.0 | 允許分享同埋改編，但禁止商業用途，保護貢獻者。 |
| **商業授權** | Commercial | 需要商業用途嘅企業，請聯絡 cto@goldmanglobal.com.au。費用直接支援開發者同埋社群。 |

**雙重授權機制**：Goldman Global 保留版權，所以可以同時向社群提供 AGPL 開源授權，同埋向企業提供商業授權。所有外部貢獻者必須簽 CLA（睇 CONTRIBUTING.md）。

---

## 🚀 即刻行動

1. **Star** 我哋嘅 GitHub repo
2. **加入** Discord 討論（即將推出）
3. **貢獻** 你嘅第一個 Seed Package

聯絡：cto@goldmanglobal.com.au

---

## 🙏 鳴謝

由 [Goldman Global Research Labs](https://goldmanglobal.com.au) 發起，多謝所有參與「人類視角數據貢獻計畫」嘅開源貢獻者。

---

**用一句講**：

> 等電腦學識點樣理解人類，而唔係人類學識點樣遷就電腦。
