# Project Hive.AGI — Master Plan

> 完整計劃書：由願景到 Code。
> 由 Goldman Global Research Labs 發起。
> 聯絡：cto@goldmanglobal.com.au

---

## 📌 一句話定位

**Project Hive.AGI** 係一個由 Goldman Global Research Labs 發起嘅開源研究計劃，目標係建立一個 **由人類貢獻、人類定義、分散式嘅知識共生網絡**。

核心口號：

> 等電腦學習點樣理解人類，而唔係人類學習點樣適應電腦。

---

## 🎯 願景

> 大廠建造嘅 AGI，係由電腦訓練電腦，最終服務於電腦嘅邏輯。
> 我哋建造嘅 AGI，係由人類貢獻人類視角，最終服務於人類嘅多元價值。

**Project Hive.AGI** 嘅終點，唔係一個中央超級 AI，而係一個 **由全球人類節點共同維護、分散式、開源嘅「人類視角知識共生網絡」**。

任何人都可以用自己嘅設備（眼鏡、手機、電腦、工業感應器）貢獻自己專業領域嘅「人類視角數據」，並透過 LLM Wiki 將呢啲數據沉澱為可交換、可綜合嘅結構化知識。

---

## 🧩 技術核心

- **Capture 層**：AI glasses / 手機 / 工業感應器採集「人類視角數據」（人在呢一刻覺得重要 / 靚 / 異常嘅瞬間）。
- **Wiki 層**：Obsidian Vault + 雙向鏈接，將 Raw Data 沉澱為結構化 Markdown 知識。
- **LLM 層**：Dual-LLM API 架構 —— **MiniMax M3**（generator，主力產出 wiki entry）+ **DeepSeek V4 Flash**（auditor，自動審查 + 修正 hallucination / schema 違規）。兩者皆 OpenAI-compatible。唔用 local Llama。詳見 `specs/api-protocol-v1.md`。
- **P2P 層**：Seed Package（標準化知識包）透過 IPFS / libp2p 喺貢獻者之間交換。

---

## 📐 MVP 開發路線圖

優先級策略：最小可行產品（MVP），由最簡單嗰樣開始。

| 優先級 | 組件 | 複雜度 | 預計時間 | 原因 |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | Seed Package Generator (Python Script) | ⭐ | 1–2 日 | 將現有數據轉為標準化 Seed Package |
| **P0** | Obsidian Vault Setup Script | ⭐ | 1 日 | 自動建立 Vault 目錄結構同 Templates |
| **P0** | Specs（Schema / Vault / API） | ⭐ | 1 日 | 鎖死規範，避免返工 |
| **P1** | LLM Wiki Engine (API-based) | ⭐⭐ | 1 星期 | 用 OpenAI-compatible API 將 Raw Data 轉為 Markdown |
| **P1** | 手機 Capture App (Basic) | ⭐⭐⭐ | 2–4 星期 | 取代手動㩒制，做到 Passive Capture |
| **P2** | P2P Exchange (IPFS) | ⭐⭐⭐⭐ | 1–2 個月 | Seed Package 自動交換 |
| **P2** | Obsidian Plugin | ⭐⭐⭐⭐ | 1–2 個月 | 俾其他 Obsidian 用戶直接參與 |

---

## 📂 Repository 結構

```
gg-hiveagi/
├── README.md                       # 計劃簡介
├── LICENSE                         # AGPL-3.0
├── DATA_LICENSE.md                 # CC-BY-NC-SA-4.0 (Seed Data)
├── COMMERCIAL_LICENSE.md           # 商業授權
├── CONTRIBUTING.md                 # 點樣參與 + CLA
├── PROJECT_MASTER_PLAN.md          # 呢份文件
│
├── specs/                          # 規範文件 (Markdown)
│   ├── seed-package-schema-v1.md
│   ├── vault-structure-spec.md
│   └── api-protocol-v1.md
│
├── tools/                          # 輔助工具 Scripts
│   ├── seed_generator/             # P0: Seed Package Generator
│   ├── vault_setup/                # P0: Obsidian Vault Setup
│   └── pii_anonymizer/             # 私隱工具
│
├── llm_wiki_engine/                # P1: LLM Wiki Engine（之後做）
├── mobile_app/                     # P1: 手機 App（之後做）
├── p2p_exchange/                   # P2: IPFS 交換（之後做）
└── obsidian_plugin/                # P2: Obsidian Plugin（之後做）
```

---

## 📄 License 策略（雙重授權）

| 組件 | License | 原因 |
| :--- | :--- | :--- |
| **Code** | AGPL-3.0 | 強 copyleft + 封閉 SaaS 漏洞；corporate 想 SaaS 部署 / 商用就要談 commercial license。確保衍生作品必須共享改進。 |
| **Seed Data** | CC-BY-NC-SA-4.0 | 允許分享與改編，但唔准商業使用，保障貢獻者。 |
| **商業授權** | Commercial | 企業如需商業使用，請聯絡 cto@goldmanglobal.com.au。費用直接支持開發者同社群。 |

**Dual-license 機制**：Goldman Global 保留版權，因此可以同時向社群提供 AGPL 開源授權，並向企業提供商業授權。所有外部貢獻者需簽 CLA（見 CONTRIBUTING.md）。

---

## 🚀 立即行動

1. **Star** 我哋嘅 GitHub Repo
2. **加入** Discord 討論（Coming Soon）
3. **貢獻**你嘅第一個 Seed Package

聯絡：cto@goldmanglobal.com.au

---

## 🙏 鳴謝

由 [Goldman Global Research Labs](https://goldmanglobal.com.au) 發起，感謝所有參與「人類視角數據貢獻計劃」嘅開源貢獻者。

---

**一句話總結**：

> 等電腦學習點樣理解人類，而唔係人類學習點樣適應電腦。
