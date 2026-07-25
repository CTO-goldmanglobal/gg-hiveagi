# Contributing to Project Hive.AGI

感謝你有興趣參與呢個計劃！呢份文件會幫你了解點樣貢獻、需要遵守嘅規則，以及我哋點樣一齊建立「人類視角知識共生網絡」。

---

## 🧭 貢獻方式

| 類型 | 說明 | 需要嘅技能 |
| :--- | :--- | :--- |
| **Seed Package 貢獻** | 分享你嘅人類視角數據（旅遊、法律、工業等） | 任何有 Obsidian Vault 嘅人 |
| **Code 貢獻** | 改善 Python Scripts / Specs / Tools | Python, Markdown, Git |
| **文檔貢獻** | 改善 README、規範文件、教學 | 寫作、技術文檔 |
| **社群貢獻** | 測試、反饋、推廣 | 溝通、測試 |

---

## 📄 Contributor License Agreement (CLA)

由於 Project Hive.AGI 採用 **雙重授權 (AGPL-3.0 + CC-BY-NC-SA-4.0 + Commercial)**，所有貢獻者必須同意 CLA：

**CLA 條款**（你提交 PR 時會確認）：

1. 你貢獻嘅 Code 將以 **AGPL-3.0** 授權釋出
2. 你貢獻嘅 Seed Data 將以 **CC-BY-NC-SA-4.0** 授權釋出
3. Goldman Global Research Labs 保留提供 **商業授權** 嘅權利
4. 你保留你貢獻內容嘅著作權

**點樣簽署**：喺每個 Pull Request 入面，Check 返 CLA 確認 checkbox（我哋提供咗 PR Template）。

---

## 🚀 貢獻流程（Code）

### 1. Fork Repo

```bash
git clone https://github.com/CTO-goldmanglobal/gg-hiveagi.git
cd gg-hiveagi
git checkout -b feature/your-feature-name
```

### 2. 寫 Code 並測試

```bash
# 確保通過 Smoke Test
python tools/seed_generator/generate_seed.py
python tools/seed_generator/validate_seed.py --path seed_output/seed_goldman_20260725/
```

### 3. Commit & Push

```bash
git add .
git commit -m "feat: 你嘅改動說明"
git push origin feature/your-feature-name
```

### 4. Open Pull Request

- 標題清楚說明改動內容
- 描述改動原因同測試結果
- Check CLA 確認 checkbox

---

## 🧪 測試要求

| 類型 | 要求 |
| :--- | :--- |
| **Python Scripts** | 必須通過 `generate_seed.py` + `validate_seed.py` Smoke Test |
| **Specs** | 必須同現有 Schema 相容，或者清楚標明版本升級 |
| **Docs** | 必須通過 Markdown lint（無嚴重語法錯誤） |

---

## 📌 Code 風格

- Python：PEP 8（用 `black` 或 `ruff` 格式化）
- Markdown：用 `#` 做標題，`-` 做列表
- 檔案命名：用小寫 + 底線（snake_case）

---

## 💬 溝通渠道

- **GitHub Issues**：Bug Report / Feature Request
- **GitHub Discussions**：一般討論、概念驗證
- **Discord**：（即將開放）

---

## 🙏 感謝你嘅貢獻！

每一個 Seed Package、每一行 Code、每一份文檔，都係令 Hive.AGI 更接近「人類視角 AGI」嘅重要一步。

**多謝你加入呢個運動。**
