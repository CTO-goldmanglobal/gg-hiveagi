"""
Voice pipecat — Cantonese voice assistant built on the pipecat framework.

Supersedes tools/voice_router/ (the hand-built version — see
docs/internal/voice-pipecat-plan.md for why we switched to a mature foundation).

Phase 1 (Gates 0–2): mic → Cantonese ASR (FunASR/SenseVoice) → local Qwen →
bilingual Apple TTS (Sinji + Karen). NOT connected to Obsidian/agents in Phase 1.
"""

__version__ = "0.1.0"
