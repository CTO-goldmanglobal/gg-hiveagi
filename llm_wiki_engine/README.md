# LLM Wiki Engine — Project Hive.AGI P1

Converts Raw Data (collected by hardware / app) into structured Wiki Entries, which are automatically committed after Dual-LLM auditing.

## Architecture

```
Raw Data (JSON)
    │
    ▼
┌───────────────────┐
│   PII Stripping   │   Text regex desensitization (image stub, P1.5 connects MediaPipe)
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
   pass      fail+corrected   fail without corrected
    │            │                │
    │     auto-corrected,         retry (temp +0.1) ×2
    │     committed                  │
    │     (audited: corrected)    still fails → quarantine/
    ▼
Final Entry (.md)  ←  format aligned with P0 generate_seed.py (validatable with validate_seed.py)
```

## Installation

```bash
pip install -r llm_wiki_engine/requirements.txt
```

## Usage

### Mock Mode (no API key needed, for testing the pipeline)

```bash
python -m llm_wiki_engine process \
    --inbox llm_wiki_engine/test_samples \
    --entries /tmp/test_entries \
    --mock
```

### Testing the Three Audit Branches (mock)

```bash
# pass
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_pass --mock --audit-fail-mode pass

# corrected (auto-corrected and committed)
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_corr --mock --audit-fail-mode corrected

# quarantine
python -m llm_wiki_engine process --inbox llm_wiki_engine/test_samples \
    --entries /tmp/t_quar --quarantine /tmp/q --mock --audit-fail-mode quarantine
```

### Real Mode (requires API key)

1. Copy `.env.example` to the project root as `.env`, and fill in the real key:
   ```bash
   cp llm_wiki_engine/.env.example .env
   ```

2. Run (without `--mock`):
   ```bash
   python -m llm_wiki_engine process \
       --inbox ./inbox \
       --entries ./entries \
       --quarantine ./quarantine
   ```

### Single Entry Processing

```bash
python -m llm_wiki_engine process-one \
    --input raw.json --output entry.md --mock
```

## Cross-Tool Compatibility

The `.md` output produced by P1 is 1:1 aligned with the format of the P0 `generate_seed.py`, and can be validated with the P0 validator:

```bash
python tools/seed_generator/validate_seed.py --path /tmp/test_entries/
```

## Design Highlights

- **Dual-LLM division of labor**: the generator (MiniMax M3) and the auditor (DeepSeek V4 Flash) are separate,
  so generation and review are not the same model, avoiding self-confirmation bias.
- **Mock / Real abstraction**: a unified `LLMClient` interface; Mock exercises the full pipeline + the three audit branches,
  and switching in an API key requires zero orchestration changes.
- **Auto-correction policy** (spec §5): fail + corrected → auto-commit + `<!-- audit_log -->`;
  fail without corrected → retry 2 times (temp +0.1) → quarantine.
- **Pydantic v2 strict parse**: all LLM JSON output passes a strict schema, catching missing fields / type errors / hallucinations.

## File Structure

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
├── engine.py           # orchestrator (retry / auto-correct / quarantine)
├── pii.py              # text PII regex strip
├── prompts/
│   ├── generator_system.txt
│   └── auditor_system.txt
├── test_samples/       # 3 sample JSONs (including one to trigger quarantine)
├── .env.example
├── requirements.txt
└── README.md
```

## License

AGPL-3.0 (consistent with the main Project Hive.AGI project).
