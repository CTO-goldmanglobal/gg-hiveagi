# Voice pipecat — Cantonese voice assistant

Local-first Cantonese voice loop built on the [pipecat](https://github.com/pipecat-ai/pipecat)
framework. Supersedes `tools/voice_router/` (the hand-built version — see
`docs/internal/voice-pipecat-plan.md` for why we adopted a mature foundation).

## Two-venv setup (important)

This tool runs in its **own venv on Python 3.12**, separate from the main repo
venv (Python 3.14). pipecat's mic transport needs `pyaudio`, which doesn't build
on 3.14. Do NOT mix them.

```
.venv          → Python 3.14   (main repo: videogen, p2p_exchange, llm_wiki_engine)
.venv-voice    → Python 3.12   (this tool: pipecat, pyaudio, funasr, torch)
```

### First-time setup
```bash
# 1. Python 3.12 (via pyenv, or brew install python@3.12)
pyenv install 3.12
"$(pyenv root)/versions/3.12.12/bin/python3.12" -m venv .venv-voice

# 2. PortAudio (pyaudio dependency)
brew install portaudio

# 3. pipecat + services + torch (for funasr)
.venv-voice/bin/pip install "pipecat-ai[local,ollama,funasr,silero]" torch torchaudio
```

## Health check (Gate 0 — run before any voice work)

```bash
.venv-voice/bin/python -m tools.voice_pipecat.health_check
```

Verifies: Python 3.12, pipecat services import, pyaudio mic, Ollama + qwen3:4b,
Sinji (yue-HK) + Karen (en) voices. Must be all-green before Gate 1.

## Quality commands

Lint + format use the **main venv's ruff** (it's not voice-specific):
```bash
.venv/bin/ruff check tools/voice_pipecat/
.venv/bin/ruff format tools/voice_pipecat/
```

Tests run in `.venv-voice` (they import pipecat):
```bash
.venv-voice/bin/python -m pytest tools/voice_pipecat/tests/ --no-cov
```

## Layout (per the plan)
```
tools/voice_pipecat/
  __init__.py
  health_check.py      # Gate 0 — environment verification
  config.toml          # models, language=yue, voices, ports (Gate 1+)
  pipeline.py          # build_pipeline(transport, config) — factory (Gate 1+)
  ...                  # see docs/internal/voice-pipecat-plan.md §3
```

## Status
- ✅ Gate 0 (environment proof) — passing
- ⬜ Gate 1 (echo pipeline: mic → VAD → FunASR → print transcript)
- ⬜ Gate 2 (conversation: FunASR → qwen3 → bilingual Apple TTS)
- ⬜ Gate 3 (capture: 「記低」→ JSON → 00_Inbox) — Phase 2

See `docs/internal/voice-pipecat-plan.md` for the full design.
