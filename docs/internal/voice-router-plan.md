# Voice Router — Build Plan

> **Status:** External review applied (2026-08-05); **verdict: approve to spike.**
> Ready for the latency spike (§5, Step 1) on founder go-ahead.
> **Author:** main agent (ZCode). **Date:** 2026-08-05.
> **Target host:** Mac Studio, Apple M4 Max, 64 GB unified memory, ~546 GB/s, Ollama runtime.
> **Language:** **Cantonese (粵語, zh-HK)** — the user's directive. An earlier draft assumed
> Mandarin; corrected here. This changes ASR/TTS choices (see §2).

---

## 0. What this is

A local-first **Cantonese** voice conversation loop on the Mac Studio:

```
mic → Cantonese ASR → local Qwen LLM → Cantonese TTS → speaker
 你講嘢  →   轉做文字    →   Qwen 諗 + 回答   →   講返出嚟   →   你聽到
```

Talk to it in Cantonese; it talks back. A desktop "talk with me" assistant —
System B's voice surface, distinct from the blind-critic tool (same-model
config falsified; different-family config untested — see §1e).

This plan is for review before implementation. It captures the model decisions,
the measured latency facts, the architecture, and the open questions.

---

## 1. Model decisions (researched + measured this session)

### 1a. Qwen 3.8 — no open-weight/local version exists (closed cloud flagships do)

Corrected per external review: the original draft's flat "Qwen 3.8 does not
exist" was **overconfident and wrong**. The precise picture:

- **Qwen 3.8-Max** is real — Alibaba previewed it at WAIC Shanghai (~19 July 2026).
  **Qwen 3.7-Max** is also real (May 2026).
- **Both are closed, cloud API-only flagships** — no repo, no license, no open
  weights yet ("open-weight soon," no date). You cannot run either on the Mac.
- **There is no open-weight Qwen 3.8 at any size**, and nothing beyond Qwen 3.6
  in the local/Ollama library (`https://ollama.com/library/qwen3.8` → HTTP 404;
  HuggingFace Qwen org lists **3.6 as the latest open generation**).

**Practical conclusion (unchanged):** Qwen3.6-27B (already pulled) remains the
latest 27B Qwen you can actually run locally. Anyone offering "Qwen 3.8-**27B**"
is mislabeling — there is no open 3.8 at any size, let alone a 27B. If 3.7/3.8
weights ever open up, they're a one-line `ollama pull` swap.

### 1b. AWQ is not worth it on this box (and we're already on INT4)

- The pulled `qwen3.6:27b` (17 GB) is **already Q4_K_M — a 4-bit INT quant**
  (27.8B params × ~4.9 bits ≈ 17 GB). "INT4" is already what's running.
- **AWQ gives negligible quality gain over Q4_K_M** at 4-bit (sub-1% on
  benchmarks, rarely perceptible).
- **AWQ has no accelerated runtime on Apple Silicon.** AutoAWQ is CUDA-only
  (archived 2025-05); Ollama serves GGUF only (no AWQ); llama.cpp's AWQ path
  isn't Metal-optimized. Switching would mean abandoning Ollama for a fragile
  setup with likely *worse* latency and ~no quality gain.
- **Decision: stay on Q4_K_M via Ollama.** The real Apple-Silicon throughput
  lever, *if* we ever outgrow Ollama, is **MLX** (Apple-native Metal kernels,
  its own 4-bit group quant), not AWQ — worth noting so it's clear the choice
  is "Ollama now, MLX later," not "Ollama vs AWQ." Reviewer: please flag if you
  disagree and have evidence of a Metal-accelerated AWQ path that beats Q4_K_M.

### 1c. Dual-tier models (both pulled and serving)

| Tier | Model | Size | Role | Why |
|---|---|---|---|---|
| Voice (fast) | `qwen3:4b` | 2.5 GB | the voice loop | small enough for sub-second replies; phone-portable later (user's point) |
| Heavy (reasoning) | `qwen3.6:27b` | 17 GB | non-voice / heavy work | kept from the blind-critic build |

### 1d. Measured latency facts (qwen3:4b, on this M4 Max)

These are **measured this session, not estimated**:

- **`/no_think` works** on qwen3:4b via Ollama's `/api/chat` with `think:false`.
  Thinking phase is suppressed; output is fluent.
- **Time-to-first-token (streaming) = 0.11s** — excellent for voice.
- **The bottleneck is output LENGTH, not thinking or TTFT.** With no length
  control the 4b rambles ~1300–3300 chars even with `/no_think` (it emits
  chain-of-thought *in the content*), making total latency 7–17s. A terse
  system prompt + token cap is required to collapse this.
- **Implication for the build:** the primary latency work is *controlling
  output length* (`think:false` + `max_tokens` cap + sentence-boundary
  early-stop + a terse spoken-reply system prompt). Solved empirically in the
  spike (§5, Step 1), not by over-planning.

### 1e. The blind-critic finding (context — why we pivoted to voice)

The prior task (the `tools/local_bridge/` blind-critic proof) ran and was
**falsified for the same-model configuration only**: on 2 of 3 tasks,
blind-critique showed **no advantage** over self-critique (in fact self-critique
was more thorough, finding 4 defects vs blind's 1). Hypothesis: qwen3.6:27b is a
*reasoning* model whose `<think>` phase already supplies independence, blunting
the blind protocol's edge.

**Important scope correction (per external review):** the Phase-0 model audit
existed to enable a **different-family** critic (Qwen generator + DeepSeek/GLM
critic) — the configuration that resolves v3 Open Question C — and we pivoted
to voice *before running that experiment*. So the honest status is: **same-model
blind critic falsified; different-family — the config the audit was built for —
untested.** The hypothesis is not retired, just parked. (OQ-C in
`docs/UNIFIED-ARCHITECTURE-v3.md` remains open; the finding so far is that
independence must come from a *different model family*, not merely from hiding
the draft.) The blind-critic code, tests, and partial results remain on disk,
uncommitted, for reference.

---

## 2. Language: Cantonese (zh-HK / 粵)

**The user wants Cantonese, not Mandarin.** This changes component choices:

- **ASR:** must transcribe **spoken Cantonese**. **SenseVoice-Small**
  (FunAudioLLM) is the right choice — a 2026 Cantonese benchmark puts it at
  **~7.09% CER vs Whisper Large-v3 at 10.41%**, and **52–118× realtime on Apple
  Silicon** (the earlier ~17× estimate was conservative). Whisper handles
  Cantonese (`yue`) but is weaker; no dedicated open Cantonese-only model beats
  SenseVoice. Still measure on *this* mic/accent in the spike, but the choice
  is settled.
- **TTS:** macOS `say` has **Sin-ji** (`-v Sin-ji`, zh-HK, verified installed).
  MiniMax T2A v2 supports Cantonese voices (confirm the exact `voice_id`).
- **LLM:** Qwen writes Cantonese fine. Prompts authored Cantonese-first, not
  Mandarin. The repo already runs in 粵 context (Cantonese comments +
  `docs/zh-HK/` mirror).

**Reviewer question (§7, Q1):** is there a better 2026 local Cantonese ASR
than Whisper/SenseVoice? Please flag.

---

## 3. Component research (verified where possible; flagged where not)

### Mic + turn-taking
- **Mic capture:** `sounddevice` (PortAudio ctypes, clean on Apple Silicon).
  Fallback `pyaudio` (needs `brew install portaudio`).
- **Turn-taking v1:** push-to-talk (hold-to-record) — zero tuning, no false
  cutoffs. **Turn-taking v2:** silero-vad (MIT, ~2MB, sub-ms per chunk, ONNX
  runtime) with ~450ms trailing-silence end-of-turn.

### ASR (Cantonese) — the critical stage
- **Primary: SenseVoice-Small** (FunAudioLLM/Alibaba). Non-autoregressive,
  **52–118× realtime on Apple Silicon**, MIT/commercial-OK. Verified Cantonese
  benchmark: **~7.09% CER (vs Whisper Large-v3 10.41%)**. Install
  `pip install funasr`. Still measure on this mic/accent, but the choice is
  settled (per external review).
- **Fallback: whisper.cpp** with `large-v3-turbo` + Metal + CoreML. First-class
  Apple Silicon (Neural Engine), true streaming (`whisper-stream`), MIT.
  Handles Cantonese (`yue`) but quality is lower than Mandarin. RTF on M4 Max
  **not published** (estimate 5–10× realtime for turbo — flagged unverified).

### LLM (conversational, fast)
- `qwen3:4b` via the existing Ollama endpoint, thinking OFF, streaming,
  `max_tokens` capped, terse Cantonese system prompt.
- **Endpoint-mismatch flag (resolve before the spike):** `think:false` is a
  **native** Ollama `/api/chat` field, but `tools/local_bridge/ollama.py` uses
  the **OpenAI-compatible `/v1`** endpoint, where the knob is
  `chat_template_kwargs={"enable_thinking": false}` and the cap is `max_tokens`,
  not `num_predict`. Pick one endpoint before Step 1 or it will trip on this.
  (Lean: use Ollama native `/api/chat` for the voice tier since `think:false`
  and `num_predict` both live there cleanly.)
- **Deeper cause of the rambling (per external review):** a *reasoning* model
  with thinking suppressed still tends to emit chain-of-thought *in the
  content* — exactly the 1300–3300-char ramble measured. The cleaner fix may be
  a **non-thinking instruct 3–4B model** (terse by default) rather than fighting
  a reasoning model into silence. **A/B a pure instruct model against qwen3:4b
  in the spike**; if the instruct model is terse by default, drop the
  suppression tax entirely.
- Keep `qwen3.6:27b` available for a `--heavy` mode (non-voice reasoning).

### TTS (Cantonese) — local default, cloud opt-in
- **Default (local): `say -v Sin-ji`** — zero setup, instant (<0.1s),
  commercial-safe, verified installed. **This is the default per external
  review:** the user asked for local, the privacy invariant says no transcript
  leaves the box, and Sin-ji is free. Be honest in the README that Sin-ji is an
  older, flatter voice.
- **Opt-in quality upgrade (`--hq`, cloud): MiniMax T2A v2** — reuse
  `.agents/skills/tour-video-finish/scripts/tts_vo.py::_tts_segment` call shape
  (urllib, Bearer `MINIMAX_API_KEY`, hex-decode `data.audio`), swap `voice_id`
  to a Cantonese voice (probe the live API for the exact id). **Note: MiniMax
  ships the transcript of everything you say to `api.minimax.io`** — fine as a
  deliberate upgrade, wrong as a default for a local-first assistant. Wire it
  behind `--hq` only.
- **Streaming TTS:** split LLM stream on Cantonese sentence boundaries
  (。！？and natural pauses); start TTS on the first sentence before the LLM
  finishes. `say` supports piping text to stdin for incremental speech.

### Orchestration — build the minimal stdlib loop, don't fork
- **Decision (per external review): build the loop, don't fork.** For a
  push-to-talk v1 the loop is four calls (record → SenseVoice → Ollama → `say`)
  — ~50 lines, matches the repo's stdlib-first convention, no framework weight.
- RealtimeSTT/RealtimeTTS earn their keep only at the **v2 hands-free stage**
  (silero-VAD + async barge-in), and even then we can lift just the VAD wiring
  rather than adopt the whole skeleton. Forking a framework to orchestrate four
  functions is the over-tooling this plan otherwise avoids.

---

## 4. Reuse audit (what already exists in the repo)

| Stage | Status | Reuse |
|---|---|---|
| Mic capture | **NEW** | nothing; add `sounddevice`+`numpy` |
| ASR | **NEW** | nothing in repo; add SenseVoice or whisper |
| Local LLM | **EXISTS** | `tools/local_bridge/ollama.py` (`chat()`, `model_available()`, `extract_json()`) — stdlib urllib, OpenAI-compatible |
| TTS | **EXISTS (English)** | `.agents/skills/tour-video-finish/scripts/tts_vo.py::_tts_segment` — copy call shape, swap `voice_id` to Cantonese |
| Config pattern | **EXISTS** | `tools/local_bridge/config.toml` + package layout (`__init__`/`__main__`/`cli`/`tests`/README) |
| Env keys | **EXISTS** | `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL`, `MINIMAX_GROUP_ID` (all set in `.env`) |

**Convention:** repo is stdlib-first (urllib only), heavy native deps in a
per-tool `requirements.txt`. `ffmpeg` is already a project assumption.

---

## 5. Architecture + build order

```
tools/voice_router/
  __init__.py          # invariants: no raw audio persisted; every turn = mic→asr→llm→tts
  __main__.py          # → cli.py
  cli.py               # `python -m tools.voice_router chat` (push-to-talk loop)
  config.toml          # ASR/TTS engine + endpoints, sample_rate, voice_id, model, VAD params
  mic.py               # sounddevice capture; push-to-talk (v1) → silero-vad (v2)
  asr.py               # Cantonese speech→text. PRIMARY: SenseVoice. FALLBACK: whisper.cpp turbo
  llm.py               # reuse local_bridge/ollama.py; qwen3:4b + think:false + streaming
  tts.py               # reuse tts_vo.py::_tts_segment shape. PRIMARY: say -v Sin-ji (local).
                      #   OPTIONAL: MiniMax T2A v2 (Cantonese voice_id, cloud)
  requirements.txt     # sounddevice, numpy, funasr, silero-vad (v2)
  README.md
  tests/
    test_no_audio_persisted.py   # invariant: no raw mic audio written to disk
    test_config_driven.py        # invariant: no hard-coded model/voice/endpoint (v3 §8)
```

**Build in small circles:**

1. **Latency spike (the gate).** ~50 lines: push-to-talk mic → ASR (SenseVoice)
   → Ollama (`qwen3:4b`, thinking OFF, streaming, `max_tokens≈80`, terse
   Cantonese system prompt) → `say -v Sin-ji`. **Use the Ollama native
   `/api/chat` endpoint** (where `think:false` and `num_predict` both live) —
   not the OpenAI `/v1` path, to avoid the endpoint-mismatch trap (§3 LLM).
   **Measure real speak→hear latency per stage.** **A/B a non-thinking instruct
   3–4B model against qwen3:4b in this step** — if the instruct model is terse
   by default, it eliminates the chain-of-thought-in-content ramble at the
   source (the measured bottleneck) rather than suppressing it. Proceed only if
   latency acceptable.
2. **Wire MiniMax TTS** (`--hq` opt-in, cloud). Copy `_tts_segment`, put
   `model`/`voice_id`/`endpoint` in `config.toml`. `say -v Sin-ji` stays the
   default; MiniMax is the deliberate quality upgrade.
3. **Turn-taking upgrade:** silero-vad (~450ms trailing silence) for hands-free.
   Push-to-talk stays as a `--push-to-talk` flag.
4. **Sentence-streamed TTS:** split LLM stream on sentence boundaries, start
   TTS on the first sentence before generation completes.

---

## 6. Latency budget (M4 Max, estimates — M4-Max-specific numbers unverified)

| Stage | Component | Latency (est.) |
|---|---|---|
| End-of-turn | push-to-talk (v1: ~0) / silero-vad (v2: ~0.4–0.5s) | 0 – 0.5s |
| ASR | SenseVoice (52–118× RTF on Apple Silicon) / whisper.cpp turbo | ~0.05–0.2s |
| LLM time-to-first-token | qwen3:4b, thinking OFF (measured 0.11s) | ~0.1–0.2s |
| LLM first sentence (~20 tok) | qwen3:4b (~60–100 tok/s; may be higher on M4 Max) | ~0.3–0.5s |
| TTS first-audio | `say -v Sin-ji` (default) / MiniMax `--hq` | ~0.1s (say) / ~0.3s (cloud) |
| **Speak → first audio heard** | | **~0.6–1.5s (say) / ~1.0–2.0s (MiniMax)** |

**Biggest levers:** (1) output-length control (the measured bottleneck —
uncontrolled it's 7–17s), (2) sentence-streamed TTS (start before LLM
finishes). Per external review: the per-stage numbers are conservative and
believable; the ASR figure understates SenseVoice's real speed.

---

## 7. Open questions — RESOLVED (external review, 2026-08-05)

All five answered by external review. Summaries; details folded into the
relevant sections above.

1. **Cantonese ASR — resolved.** SenseVoice-Small is the right call.
   Benchmark: **~7.09% CER vs Whisper Large-v3 10.41%**, **52–118× RTF on Apple
   Silicon**. No open Cantonese-only model beats it. §2/§3 updated with the real
   numbers; the "unverified" flag is retired (still measure on this mic/accent).
2. **Output-length control — resolved.** Cap (`num_predict≈64`) + terse
   Cantonese system prompt ("用口語廣東話答，最多兩句短句，唔好列點、唔好解釋") +
   stop-on-second-句號 early-stop, in that order. **Deeper cause:** a reasoning
   model with thinking off still emits CoT in the content — so A/B a non-thinking
   instruct 3–4B model in the spike; if terse by default, drop the suppression tax.
3. **TTS default — resolved.** Local (`say -v Sin-ji`) is the default; MiniMax
   is an opt-in `--hq` flag (cloud, ships the transcript). §3 updated.
4. **Qwen 3.8 — resolved.** No open-weight 3.8 exists; 3.7-Max and 3.8-Max exist
   but are closed cloud flagships. §1a corrected from the flat "does not exist."
5. **Orchestration — resolved.** Build the minimal stdlib loop; don't fork.
   RealtimeSTT/TTS only worth adopting at the v2 hands-free stage, and even then
   lift just the VAD wiring. §3 updated.

---

## 8. What the build will / won't do

- **Will:** build the spike first and measure; pull no new models (qwen3:4b +
  qwen3.6:27b already pulled); `pip install` audio deps into the project
  `.venv` (confirm exact list first).
- **Won't:** persist raw mic audio (privacy invariant); hard-code
  model/voice/endpoint (v3 §8 config-driven rule); touch `videogen/` or
  `p2p_exchange/`; commit without being asked.

---

## 9. Sources (verified 2026-08-05)

- Qwen 3.8-Max preview (closed cloud): `https://www.yottalabs.ai/post/qwen-3-8-max-release-date-specs-how-to-access-2026`
- Qwen 2026 open-vs-closed overview: `https://mysummit.school/blog/en/qwen-alibaba-review-2026/`
- Qwen 3.8 local: `https://ollama.com/library/qwen3.8` → 404; HuggingFace Qwen org → 3.6 latest open generation
- Qwen3.6-27B: `https://huggingface.co/Qwen/Qwen3.6-27B` (Apache-2.0, thinking by default)
- AWQ/AutoAWQ: `https://github.com/casper-hansen/AutoAWQ` (CUDA-only, archived 2025-05)
- Cantonese ASR benchmark (SenseVoice 7.09% vs Whisper 10.41%): `https://convertaudiototext.com/blog/best-transcription-for-asian-languages`
- SenseVoice-Small: `https://huggingface.co/FunAudioLLM/SenseVoiceSmall` (52–118× RTF on Apple Silicon, lists Cantonese)
- whisper.cpp: `https://github.com/ggml-org/whisper.cpp` (Metal+CoreML, streaming)
- silero-vad: `https://github.com/snakers4/silero-vad` (MIT, ONNX)
- MiniMax TTS reuse: `.agents/skills/tour-video-finish/scripts/tts_vo.py:54-97`
- Local LLM reuse: `tools/local_bridge/ollama.py`
- Architecture: `docs/UNIFIED-ARCHITECTURE-v3.md` §8 (config-driven model registry)
