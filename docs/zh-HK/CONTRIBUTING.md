[English](../../CONTRIBUTING.md) | 繁體中文

# 貢獻 Project Hive.AGI

多謝你有興趣參與呢個計畫！呢份文件會講解點樣貢獻、要遵守嘅規則，同埋我哋點樣一齊建立「人類視角知識共生網絡」。

**第一次嚟？** 先睇 [README](./README.md) 了解願景同埋 Quick Start，之後再返嚟呢度。

---

## 🧭 貢獻方式

| 類型 | 描述 | 所需技能 | 去邊度 |
| :--- | :--- | :--- | :--- |
| **Seed Package 貢獻** | 分享你嘅人類視角數據（旅遊、法律、工業等等） | 任何有 Obsidian Vault 嘅人 | 透過 P2P CID 發佈 — 睇 [§ 貢獻 Seed Package](#-貢獻-seed-package) |
| **代碼貢獻** | 改善 Python 工具、LLM Wiki Engine、P2P 交換、Obsidian 插件 | Python、TypeScript、Git | Pull Request |
| **文件貢獻** | 改善 README、specs、教學、`docs/zh-HK/` 翻譯 | 寫作、技術文件 | Pull Request |
| **社群貢獻** | 測試、反饋、bug 報告、推廣 | 溝通、測試 | Issues / Discussions |

> ⚠️ **Seed Package 唔係透過 Pull Request 貢獻。** `seed_output/` 已經喺 `.gitignore` 入面 — 數據唔會儲存喺呢個 repo。睇下面嘅專屬章節。

---

## 🔒 私隱同埋 PII — 貢獻任何數據之前必讀

Hive.AGI 收集嘅係**人類視角數據**，即係話貢獻可能帶有真實嘅私隱風險。呢啲規則冇得傾，適用於 Seed Package、測試樣本、issue 入面嘅截圖，同埋 PR 入面嘅示例數據。

**絕對唔好貢獻：**

- 任何圖片或影格入面可以認出嘅樣或者車牌
- 其他人嘅姓名、電話、email、身分證號碼或者地址 — 喺 `human_description`、`tags`、檔名或者任何地方都唔得
- 喺在場人士合理預期有私隱嘅情況下錄製嘅任何嘢
- 你冇權分享嘅數據（僱主機密、客戶工作、有版權嘅影片）

**位置數據：** Seed Package 條目帶有 `gps_lat` / `gps_lng`。唔好發佈包含你屋企、你小朋友學校，或者任何會暴露私人生活規律嘅位置嘅 package。接近敏感位置嘅話，要將座標變得粗糙或者直接刪除 — 一個大致嘅地區通常已經夠令知識有用。

**匿名化：** 兩條捕捉路徑都會強制做人面 + 車牌模糊處理。
- **自動視覺路徑**（`python -m llm_wiki_engine process-video`）會行真實嘅 MediaPipe 人面偵測 + OpenCV 基於邊緣嘅車牌偵測，冇 `--skip-blur` 嘅繞過選項（spec §6，由代碼強制執行）。
- **人手挑選路徑**（`tools/video_ingest/capture_helper.py`）將 PII 風險保持喺零 — 你自己揀每一格，淨係寫文字。
至於你自己處理嘅靜態圖片，喺任何上傳或者 LLM call 之前，要行 `python tools/pii_anonymizer/anonymize.py <image>`。

**法律提示：** 作為貢獻者，澳洲 Privacy Act 嘅義務同埋你自己司法管轄區嘅同等法律都適用於你。有疑問嘅話，就唔好發佈，或者喺發佈之前問 <cto@goldmanglobal.com.au>。

---

## 📄 Contributor License Agreement（CLA）

因為 Project Hive.AGI 用嘅係**雙重授權（AGPL-3.0 + CC-BY-NC-SA-4.0 + Commercial）**，所有貢獻者都必須同意 CLA。

**CLA 條款**（你喺每一個 Pull Request 都要確認呢幾項）：

1. 你保留你所貢獻內容嘅版權。
2. 你授予 Goldman Global Research Labs 一個永久、全球性、不可撤銷、免版稅嘅授權，可以去使用、重製、修改、再授權同埋分發你嘅貢獻 — **包括以商業授權條款去使用**。
3. 你貢獻嘅代碼會以 **AGPL-3.0** 向公眾發佈（[LICENSE](../../LICENSE)）。
4. 你貢獻嘅 Seed Data 會以 **CC-BY-NC-SA-4.0** 向公眾發佈（[DATA_LICENSE.md](../../DATA_LICENSE.md)）。
5. 你確認呢個貢獻係你自己嘅作品，你有權授予呢個授權，而且符合上面嘅私隱同埋 PII 規則。

> ℹ️ **點解條款 2 係一個授予（grant），而唔係「保留（retention）」。** 雙重授權只有喺貢獻者明確授權 Goldman Global 商業再授權嘅權利嗰陣先至行得通。如果冇明確嘅授予，Goldman Global 根本冇嘢可以「保留」。**注意：呢個措辭仲未經律師審查。如果你對呢個授予有疑問 —— 包括佢喺你嘅司法管轄區係咪足夠或者可執行 —— 喺開 PR 之前 email 俾 <cto@goldmanglobal.com.au>。唔好盲咁剔個框。**

**點樣簽**：喺 [Pull Request 模板](../../.github/PULL_REQUEST_TEMPLATE.md)入面剔 CLA 確認框。Seed Package 貢獻者要喺提交 issue 入面確認相同嘅條款。

對授權有疑問，或者需要商業授權？→ <cto@goldmanglobal.com.au>（[COMMERCIAL_LICENSE.md](../../COMMERCIAL_LICENSE.md)）

---

## 🛠️ 開發環境

| 要求 | 版本 | 用於 |
| :--- | :--- | :--- |
| Python | **3.13**（同 CI 一致） | 除咗 Obsidian 插件之外嘅所有嘢 |
| Node.js | 20+（同 `obsidian_plugin/package.json` 入面嘅 `@types/node` 一致） | 只限 `obsidian_plugin/` |
| kubo（IPFS daemon） | latest | 只限 P2 真實模式 — `--mock` 唇晒都唔使 |

```bash
# 1. 喺 GitHub 上面 Fork 個 repo，然後 clone 你嘅 fork
git clone https://github.com/<your-username>/gg-hiveagi.git
cd gg-hiveagi
git remote add upstream https://github.com/CTO-goldmanglobal/gg-hiveagi.git

# 2. 虛擬環境
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. 依賴
pip install -r tools/seed_generator/requirements.txt
pip install -r llm_wiki_engine/requirements.txt
pip install -r p2p_exchange/requirements.txt
```

**憑證**：P1 預設用 mock 模式，唔使 API key。真實模式嘅話，`cp llm_wiki_engine/.env.example .env` 然後喺本地填入。`.env` 已經被 gitignore — **千祈唔好 commit 任何 key，亦都唔好將 key 貼落 issue、PR 或者 chat 視窗入面。**

---

## 🚀 貢獻流程（代碼同埋文件）

### 1. 建立一個 branch

```bash
git checkout -b feature/your-feature-name
```

Branch 前綴：`feature/`、`fix/`、`docs/`、`chore/`、`spec/`。

### 2. 寫代碼，然後喺本地行晒成個測試套件

要行晒 CI 行嘅所有嘢 — 紅色嘅 PR 唔會被 review。睇 [§ 測試要求](#-測試要求)嘅命令。

### 3. Commit

我哋用 [Conventional Commits](https://www.conventionalcommits.org/)：

```bash
git commit -m "feat: add plate-blur strength option to PII anonymizer"
```

類型：`feat`、`fix`、`docs`、`test`、`chore`、`refactor`、`spec`。Scope 係選填嘅，跟 CI/Dependabot 慣例 — `feat(p1):`、`fix(p2):`、`docs(zh-HK):`。

### 4. 同步同埋 push

```bash
git fetch upstream && git rebase upstream/main
git push origin feature/your-feature-name
```

### 5. 對住 `main` 開一個 Pull Request

- 標題要清楚描述個改動（理想係用 Conventional Commit 風格）
- 填好 PR 模板：改動類型、描述、測試結果
- 解釋**點解**，唔淨係講做咗咩
- 剔 CLA 確認框
- 連結相關嘅 issue（`Closes #123`）
- 等 CI 變綠；如果唔綠就 push 修正去同一個 branch

一個 PR 一個邏輯改動。如果你打算做一啲大型或者結構性嘅嘢，**先開一個 issue**，等我哋喺你花心機之前傾掂個做法。

---

## 🌱 貢獻 Seed Package

Seed data 係內容定址同埋點對點交換嘅 — 唔會 commit 入呢個 repository。

```bash
# 1. 設定一個 Vault（如果你未有嘅話）
python tools/vault_setup/setup_vault.py --target ~/HiveAGI

# 2. 將 Raw Data 捕捉落 00_Inbox/，然後蒸餾
python -m llm_wiki_engine process --inbox ~/HiveAGI/00_Inbox --entries ~/HiveAGI/01_Entries

# 3. 產生同埋驗證個 package
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/<your_package>/

# 4. 再睇一次上面嘅私隱同埋 PII 章節，然後發佈
python -m p2p_exchange publish --package seed_output/<your_package> --mock
```

然後**用 [Seed Package Submission 模板](../../.github/ISSUE_TEMPLATE/seed_package_submission.md)開一個 issue**（`seed-package` label 會自動套用）。模板會問你：CID、domain（`tourism` / `industrial` / `legal` / …）、條目數量、一段描述講解知識涵蓋咩，同埋你對 CLA 同 PII 規則嘅確認。維護者會驗證個 CID 同埋將佢加入網絡註冊表。

當你有一個本地 kubo daemon 行緊嗰陣，移除 `--mock` 就可以發佈真實嘅 IPFS CID。

---

## 🧪 測試要求

| 類型 | 要求 |
| :--- | :--- |
| **Python** | 必須通過下面嘅完整 CI smoke 套件（P0 + P1 mock + P2 mock + 跨兼容） |
| **Obsidian 插件** | 由 `obsidian_plugin/` 行 `npm run check`（tsc）同埋 `npm run build` 都必須成功 |
| **Specs** | 必須同現有 schema 保持兼容，或者清楚宣佈版本升級同埋更新每個受影響嘅 spec + 翻譯 |
| **Docs** | 必須通過 Markdown lint（冇嚴重語法錯誤）；連結必須可以解析 |
| **Seed Packages** | 必須通過 `validate_seed.py` |

```bash
# P0 — seed generator + 驗證器
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/

# P1 — LLM Wiki Engine，三條 audit branch
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_pass --mock --audit-fail-mode pass
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_corr --mock --audit-fail-mode corrected
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/ci_quar --quarantine /tmp/ci_q --mock --audit-fail-mode quarantine

# P2 — publish / verify / tamper-detect / resolve
python -m p2p_exchange publish --package seed_output/seed_goldman_20260725 --mock
python -m p2p_exchange verify --package seed_output/seed_goldman_20260725 --cid <CID> --mock
```

權威定義係 [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — 包括將 P0 驗證器行落 P1 同埋 P2 輸出嘅跨兼容檢查。如果你改 schema，**嗰啲跨兼容步驟就係會壞嗰啲。**

---

## 📌 代碼風格

- **Python**：PEP 8，用 `black` 或者 `ruff` 格式化。公開函式要有 type hints。任何貢獻者會用到嘅嘢都要有 docstring。
- **TypeScript**（`obsidian_plugin/`）：跟現有嘅 `tsconfig.json`；exported types 唔准用 `any`。
- **Markdown**：標題用 `#`，列表用 `-`，fenced code block 要有語言標籤。
- **檔案命名**：Python 用小寫 + 下劃線（`snake_case`）；插件原始碼用 `camelCase.ts`，要同現有嘅一致。
- **註釋同埋 docstring**：用英文，咁整個網絡先至睇得明。面向用戶嘅文件係雙語嘅（睇下面）。

---

## 🌏 翻譯

規範文件係英文嘅；繁體中文喺 [`docs/zh-HK/`](./) 入面。如果你改 spec 或者 README 改到意思變咗，要麼喺同一個 PR 入面更新對應嘅 zh-HK 版本，要麼開一個 tag 咗 `translation` 嘅 follow-up issue，咁就唔會暗中飄走。

---

## 🤝 行為準則

要尊重人，假設善意，評論 idea 而唔係評論人。騷擾、歧視同埋人身攻擊係唔會被容忍嘅，會導致被逐出計畫嘅空間。將行為問題私下報告俾 <cto@goldmanglobal.com.au>。全文：[`CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md)。

---

## 🛡️ 報告安全或者私隱問題

**唔好開公開 issue** 去報告安全漏洞、洩漏嘅憑證，或者你喺 repo 或者已發佈 package 入面搵到嘅 PII。Email 俾 <cto@goldmanglobal.com.au> 講詳情，俾一段合理嘅時間我哋回應，先至公開披露。完整政策：[`SECURITY.md`](../../SECURITY.md)。

---

## 💬 溝通渠道

- **GitHub Issues**：bug 報告、功能請求、Seed Package 提交
- **GitHub Discussions**：一般討論、概念驗證、動手前嘅問題
- **Email**：<cto@goldmanglobal.com.au> — 授權、安全、私隱
- **Discord**：（即將推出）

---

## 🙏 多謝你嘅貢獻！

每一個 Seed Package、每一行代碼、每一份文件，都係將 Hive.AGI 帶近「人類視角 AGI」嘅重要一步。

**多謝你加入呢個運動。**
