# LLM Wiki Engine — Project Hive.AGI P1

將 Raw Data（硬件 / App 採集）轉為結構化 Wiki Entry，經 Dual-LLM 審計後自動入庫。

## 架構

```
Raw Data (JSON)
    │
    ▼
┌───────────────────┐
│   PII Stripping   │   文字 regex 脫敏（圖片 stub，P1.5 接 MediaPipe）
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  WikiGenerator    │   MiniMax M3 (generator)  → DraftEntry
└─────────┬─────────┘   temperature 0.3
          ▼
┌───────────────────┐
│  WikiAuditor      │   DeepSeek V4 Flash (auditor) → AuditResult
└─────────┬─────────┘   temperature 0.0 (deterministic)
          │
    ┌─────┴──────┬──────────────┐
   pass      fail+corrected   fail 無corrected
    │            │                │
    │     自動修正入庫          重試（temp +0.1）×2
    │     (audited: corrected)     │
    │                           仍 fail → quarantine/
    ▼
Final Entry (.md)  ←  格式對齊 P0 generate_seed.py（可用 validate_seed.py 校驗）
```

## 安裝

```bash
pip install -r llm_wiki_engine/requirements.txt
```

## 用法

### Mock 模式（唔使 API key，用嚟測試 pipeline）

```bash
python -m llm_wiki_engine process \
    --inbox llm_wiki_engine/test_samples \
    --entries /tmp/test_entries \
    --mock
```

### 測試三個 audit 分支（mock）

```bash
# pass
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_pass --mock --audit-fail-mode pass

# corrected（自動修正入庫）
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_corr --mock --audit-fail-mode corrected

# quarantine
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_quar --quarantine /tmp/q --mock --audit-fail-mode quarantine
```

### 真實模式（需要 API key）

1. 複製 `.env.example` 到 project root 做 `.env`，填入真 key：
   ```bash
   cp llm_wiki_engine/.env.example .env
   ```

2. 跑（唔加 `--mock`）：
   ```bash
   python -m llm_wiki_engine process \
       --inbox ./inbox \
       --entries ./entries \
       --quarantine ./quarantine
   ```

### 單筆處理

```bash
python -m llm_wiki_engine process-one \
    --input raw.json --output entry.md --mock
```

## 跨工具兼容

P1 產出嘅 `.md` 與 P0 `generate_seed.py` 格式 1:1 對齊，可用 P0 validator 校驗：

```bash
python tools/seed_generator/validate_seed.py --path /tmp/test_entries/
```

## 設計重點

- **Dual-LLM 分工**：generator（MiniMax M3）同 auditor（DeepSeek V4 Flash）分離，
  生成同審查唔係同一個 model，避免 self-confirmation bias。
- **Mock / Real 抽象**：`LLMClient` 介面統一，Mock 行晒成個 pipeline + 三個 audit 分支，
  接 API key 後零 orchestration 改動。
- **自動修正政策**（spec §5）：fail + corrected → 自動入庫 + `<!-- audit_log -->`；
  fail 無 corrected → retry 2 次（temp +0.1）→ quarantine。
- **Pydantic v2 strict parse**：所有 LLM JSON output 過 strict schema，捕捉漏欄 / 類型錯 / 幻覺。

## 檔案結構

```
llm_wiki_engine/
├── __init__.py
├── __main__.py
├── cli.py              # process / process-one / --mock / --audit-fail-mode
├── config.py           # .env loader
├── models.py           # Pydantic: RawData / DraftEntry / AuditResult / FinalEntry
├── client.py           # LLMClient ABC + RealLLMClient + MockLLMClient
├── generator.py        # MiniMax M3 wrapper
├── auditor.py          # DeepSeek V4 Flash wrapper
├── engine.py           # orchestrator（retry / auto-correct / quarantine）
├── pii.py              # text PII regex strip
├── prompts/
│   ├── generator_system.txt
│   └── auditor_system.txt
├── test_samples/       # 3 個 sample JSON（含 quarantine 觸發用）
├── .env.example
├── requirements.txt
└── README.md
```

## License

AGPL-3.0（同 Project Hive.AGI 主項目一致）。
