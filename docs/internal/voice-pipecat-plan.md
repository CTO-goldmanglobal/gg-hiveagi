# Voice Assistant — pipecat Foundation + Obsidian/LLM Integration

> **Status:** Claude review applied (2026-08-06, 92% confidence — "GO with
> corrections"). Corrections folded in below. Ready for founder go-ahead to
> start Gate 0 (environment proof). NOT yet building.
> **Author:** main agent (ZCode). **Date:** 2026-08-06.
> **Supersedes:** `docs/internal/voice-router-plan.md` (the hand-built version —
> see §1 for why we're switching to a mature foundation).
> **Target host:** Mac Studio, Apple M4 Max, 64 GB, Python 3.14, Ollama, AirPods Max.

---

## 0. The decision this plan makes

**Stop hand-building the voice loop. Adopt [pipecat](https://github.com/pipecat-ai/pipecat)
(BSD-2, 13,943★, pushed today) as the foundation.** The hand-built
`tools/voice_router/` was fragile (GUI deadlocked 3 times, IndexError on empty
audio, port conflicts) because it reinvented pipeline orchestration, VAD
threading, and ASR/TTS plumbing that mature frameworks already solve. pipecat
gives us the async pipeline for free AND has **native Cantonese** support via
its `FunASRSTTService` (`yue` is a first-class language code) and **native
Ollama** support. What we actually write is small and bounded.

The Obsidian + LLM integration (the user's real goal: voice → capture → wiki)
is built **on top of** this foundation, in later phases, by reusing the
already-existing `obsidian_plugin/` ↔ `llm_wiki_engine` pipeline.

---

## 1. Why pipecat, not the hand-built router

| Hand-built `voice_router/` (weak) | pipecat foundation (solid) |
|---|---|
| mic capture + hand-rolled threading | async frame bus + queues, battle-tested |
| silero-vad wired by hand, crashed on empty audio | built-in VAD + interrupt/barge-in |
| SenseVoice wired by hand (IndexError on silence) | **`FunASRSTTService` — Cantonese `yue` native** |
| qwen3 via hand-written urllib streaming | **`OllamaLLMService` — config only** |
| 3 GUI deadlocks (rumps/PyObjC/web) | transport layer handles this |
| port conflict silent freeze | mature, debugged for years |

The hand-built code stays in git history as a learning spike; the pipecat
version is the production path. **Full audit comparison in §6 of the prior plan.**

**Alternatives rejected (verified 2026-08-06):**
- Open WebUI (148k★) — has voice mode, but license caps commercial at 50 users + branding lock-in. Not OSI-approved. Use as UI only, not core.
- HF speech-to-speech (11k★) — strong M4-Max story but **Alpha** + no Cantonese ASR.
- RealtimeSTT/TTS (10k★) — mature *components* but you still hand-build the loop (= the fragility we're escaping).
- Vocode — **dead** (last push 2024-11). ollama-voice-mac — AGPL + stale. LiveKit — cloud-leaning, overkill for single-machine.

---

## 2. Phased build (the user's "to need Obsidian + LLM when needed")

```
Phase 1 — FOUNDATION          Phase 2 — OBSIDIAN           Phase 3 — LLM AGENT
(now)                         (when needed)                (when needed)
┌──────────────────┐          ┌──────────────────┐         ┌──────────────────┐
│ pipecat voice    │          │ voice → write    │         │ function-calling │
│ loop:            │          │ to 00_Inbox/     │         │ LLM controls     │
│ yue ASR ↔ qwen3  │   ───►   │ (JSON) → trigger │  ───►   │ Obsidian + tools │
│ ↔ Sinji TTS      │          │ llm_wiki_engine  │         │ (read vault, etc)│
└──────────────────┘          └──────────────────┘         └──────────────────┘
   Cantonese chat                 voice capture               full agent
```

**The user's instruction:** build Phase 1 now; Phase 2 (Obsidian) and Phase 3
(LLM agent) come "when needed." Each phase is independently valuable.

---

## 3. Phase 1 — pipecat Cantonese voice loop (build now, in Gates)

**Scope discipline (per Claude review):** Phase 1 is ONLY the voice loop —
mic → Cantonese ASR → local Qwen → bilingual Apple TTS → speaker. It does NOT
connect Obsidian, Hermes, function-calling, or agents. The goal is a **solid
core that doesn't crash across 20 turns**, not a full assistant.

### What pipecat gives us free
- Async pipeline orchestration (frame bus, queues, threading)
- VAD (silero/ananse) + interrupt/barge-in handling
- `FunASRSTTService` — SenseVoice, Cantonese `yue` supported (a *candidate*;
  accuracy unproven — see §3.3)
- `OLLamaLLMService` — qwen3:4b / qwen3.6:27b
- Transport layer (Local / WebSocket / WebRTC) — no GUI deadlock
- LLM function-calling capability (Phase 2/3 only — NOT used in Phase 1)

**Honest caveat (Claude review):** pipecat solves pipeline orchestration. It
does NOT automatically solve Cantonese accuracy, Qwen rambling, Apple TTS
mixed-language quality, or tool safety. Those are still ours to handle.

### 3.1 Correct API (corrected per Claude review — the draft had errors)

```python
from pipecat.services.ollama import OLLamaLLMService

llm = OLLamaLLMService(
    base_url="http://localhost:11434/v1",
    settings=OLLamaLLMService.Settings(
        model="qwen3:4b",
        temperature=0.2,
    ),
)
```

- **The `OLLamaLLMService(model=...)` shorthand is deprecated.** Use the
  `Settings` nested class as shown. (Draft had the old form.)
- **Package shortcut import works** in the current version:
  `from pipecat.services.ollama import OLLamaLLMService`. The draft's claim
  that `__init__.py` doesn't re-export was wrong/outdated.
- **Pin exact `pipecat-ai` version** and only use that version's documented
  public imports. Add a CI import smoke test. Don't chase GitHub `main`.

### 3.2 Python: dedicated 3.12 venv (DECIDED — no longer open)

Per Claude review (98% confidence): **`.venv-voice` on Python 3.12.** Reasons:
- pipecat official support is 3.11–3.13; recommends 3.12+
- `pyaudio` (needed for `[local]` mic transport) doesn't build on 3.14
- Writing a custom sounddevice transport to stay on 3.14 would *defeat the
  purpose of switching to pipecat* (more custom plumbing = the fragility
  we're escaping)

```
.venv        → Python 3.14   (main repo)
.venv-voice  → Python 3.12   (voice runtime, pipecat)
```

### 3.3 Cantonese ASR: candidate, not "solved"

The draft said "SenseVoice crash solved." Correction: pipecat may solve the
*empty-frame/pipeline-lifecycle crash*, but it does NOT prove **your Cantonese
accuracy is good enough**. Phase 1 must TEST, not claim done.

**Acceptance = a 30-sentence founder test set** (per Claude review):
```
10 句純廣東話
10 句廣東話＋英文技術詞 (Hermes, Cursor, Paperclips...)
5 句命令
5 句自然思考／停頓／改口
```
Measure: character error rate, **intent-preservation rate** (most important —
not every word right, but command meaning unchanged), product-name accuracy,
empty/silence crash rate, end-of-turn latency. Tested on AirPods Max mic +
room noise.

### 3.4 TTS: bilingual Apple voice router (NOT just "all text → Sinji")

The draft's `SayTTS` was incomplete. Problem already discovered: **Sinji reads
English poorly.** Phase 1 must do language segmentation:

```
LLM response
→ language segmenter
    ├── yue-HK segment → Sinji
    └── en segment     → Karen (or other English voice)
```

Short English brand names stay inside the Cantonese segment (don't switch voice
every few words); only full English sentences switch. Rename `SayTTS` →
**`AppleTTSService`** containing: language detection, Sinji voice, English
voice, sample-rate normalization, interruption cancellation, temp audio
cleanup, unavailable-voice fallback. v1 = batch TTS (no streaming needed yet).

### 3.5 Qwen rambling: output governor (pipecat won't fix it)

Two response layers (per Claude review):
- **Spoken reply:** 1–2 sentences, ~20–60 tokens, no markdown/URLs/code,
  technical detail = conclusion only.
- **Screen reply (logged):** can be longer, full detail (for future phone/Mac/
  glasses display).

System prompt:
```
Reply in natural Hong Kong Cantonese.
This response will be spoken aloud.
Use no more than two short sentences unless the user asks for detail.
Do not use Markdown, lists, URLs or code in the spoken reply.
Use English only for established technical names.
```
Plus: `think=false`, low temperature, hard completion cap, sentence-boundary
stop on overrun, transcript logging (no raw audio saved).

### 3.6 Transport must be swappable (factory pattern)

The goal is Mac → phone → AI glasses. Don't hardcode `LocalAudioTransport`:

```python
def build_pipeline(transport, config):
    ...
```
v1 uses local mic; next version phone via Tailscale+WebRTC; future glasses =
just swap transport. pipecat already has Web/RN/Swift/Kotlin client SDKs.

### Revised layout (per Claude review)
```
tools/voice_pipecat/
  __init__.py
  config.toml
  pipeline.py            # build_pipeline(transport, config) — factory
  transports.py          # local mic now; WebRTC/glasses later
  stt.py                 # FunASR wrapper
  llm.py                 # OLLamaLLMService config + spoken-prompt
  tts/
    apple_tts.py         # AppleTTSService — Sinji + Karen, language-routed
    language_router.py   # segment yue-HK vs en
  prompts/
    spoken_yue.txt       # the spoken-reply system prompt
  evals/
    cantonese_test_cases.json   # the 30-sentence founder test set
    run_asr_eval.py
    run_latency_eval.py
  tests/
    test_imports.py             # CI smoke test (pin pipecat version)
    test_no_audio_persisted.py
    test_language_router.py
    test_output_length.py
    test_silence_does_not_crash.py
```

### Phase 1 is sliced into Gates (not one big build)

**Gate 0 — Environment proof.** Test only: 3.12 venv, pipecat import, pyaudio
I/O, Ollama reachable, Sinji + English voice exist. Any failure → don't proceed.

**Gate 1 — Echo proof.** Mic → pipecat → VAD → FunASR → **print transcript**
(no LLM, no TTS). Success: 30 sentences tested, silence doesn't crash, AirPods
Max works, latency measured.

**Gate 2 — Conversation proof.** Mic → FunASR → qwen3:4b → bilingual Apple
TTS. Success: first-audio ~<2s (goal, not hard promise), replies ≤2 sentences,
Cantonese+English audible, interruptible, 20 continuous turns no crash.

**Gate 3 — Capture proof (Phase 2 start).** 「記低……」→ confirm transcript →
write JSON to `00_Inbox/`. Only after Gates 0–2 pass. (See §4.)

---

## 4. Phase 2 — Obsidian integration (Gate 3, when needed)

**Reuse what already exists** — the Obsidian pipeline is already built:
- `obsidian_plugin/` (TypeScript) — captures triggers → writes JSON to `00_Inbox/` → shell-calls `llm_wiki_engine`
- `specs/vault-structure-spec.md` — vault layout (`~/HiveAGI/`, 00_Inbox / 01_Entries / 02_Topics)
- `tools/vault_setup/` — auto-creates the vault structure
- `llm_wiki_engine/` (Python) — CLI `python -m llm_wiki_engine process --inbox …` — processes inbox JSON → structured entries

**Integration seam = the file format, not the plugin code** (Claude review,
98% confidence). Voice path does NOT call the TypeScript plugin. It writes the
same `RawData` JSON contract to `00_Inbox/`, so:
- plugin keeps capturing from keyboard
- voice captures from Python
- both produce the same contract
- wiki engine doesn't know or care about the source

### Phase 2 trigger: deterministic intent, NOT free-form LLM tool-calling

Per Claude review (97% confidence): **do NOT trust a 4B model to reliably
decide when to call a tool.** Use a deterministic intent trigger first:

```
記低 / 記住 / 幫我寫低 / save this note
```

When the transcript matches → confirm with user → write JSON. Only AFTER that
match does the LLM clean up the note *content* (extract what to save). The LLM
never decides whether to call the tool — the deterministic trigger does.

### Phase 2 = exactly ONE whitelisted tool (per Claude review)

```
capture_note(text, source, timestamp)
```
- Writes ONLY to `00_Inbox/`
- CANNOT: delete, edit existing notes, run shell commands, browse arbitrary
  vault paths, call Hermes/OpenClaw/other systems
- Extended JSON schema (richer than plugin's, carries voice provenance):
```json
{
  "source": "voice_pipecat",
  "language": "yue-HK",
  "transcript": "...",
  "captured_at": "...",
  "device": "mac-studio",
  "audio_persisted": false,
  "schema_version": 1
}
```

### Function-calling reliability is untested — flagged
qwen3:4b's tool-calling via Ollama's OpenAI-compatible endpoint is not proven.
If unreliable in Phase 2 spike, the deterministic trigger is the fallback
(keyword detection in transcript, no LLM tool decision at all).

---

## 5. Phase 3 — LLM agent (when needed)

qwen3 gains **function-calling** over the vault + tools:
- Read/search `01_Entries/`, `02_Topics/` to answer questions ("我上次講過邊間茶樓好飲?")
- Create/edit topics, link entries
- Trigger the broader HiveAGI pipeline

This is the "full agent" surface. It depends on Phase 2's capture working and
on qwen3's function-calling reliability (untested — a Phase 3 spike). pipecat's
function-calling framework supports this natively.

---

## 6. Open questions (after Claude review — most resolved)

**RESOLVED by Claude review (2026-08-06):**
- ~~Python 3.14 vs 3.12 venv~~ → **3.12 venv decided** (§3.2)
- ~~OLLamaLLMService API~~ → **Settings nested class, package shortcut OK** (§3.1)
- ~~SayTTS design~~ → **AppleTTSService bilingual router** (§3.4)
- ~~Qwen rambling~~ → **output governor: spoken vs screen + system prompt** (§3.5)
- ~~Function-calling optimism~~ → **Phase 1 none; Phase 2 deterministic trigger + single whitelisted tool** (§4)
- ~~Obsidian integration seam~~ → **file format (JSON→00_Inbox), not plugin code** (§4)

**Still open (need founder input):**
1. **Obsidian vault location** — Phase 2 needs a vault path. No `~/HiveAGI/`
   found on this Mac Studio. Is the vault elsewhere, or to be created via
   `tools/vault_setup/`? (Blocks Phase 2 only, not Phase 1.)
2. **30-sentence Cantonese test set** — the founder must supply/confirm the
   sentences (esp. product names like Hermes/Paperclips/Cursor, and the
   command phrases). Needed for Gate 1 acceptance.

---

## 7. What the build will / won't do

- **Will (Phase 1 = Gates 0–2):** create `.venv-voice` on Python 3.12, install
  pipecat + pyaudio, prove the environment (Gate 0), build the echo pipeline
  (Gate 1), then the full conversation loop with bilingual Apple TTS + output
  governor (Gate 2). Measure against the 30-sentence test set.
- **Won't:** persist raw mic audio (privacy invariant); hard-code model/voice
  (config-driven, v3 §8); touch `videogen/` or `p2p_exchange/`; use function-
  calling or connect Obsidian/Hermes/agents in Phase 1; chase GitHub `main` API
  (pin pipecat version, smoke-test imports).
- **The hand-built `tools/voice_router/` stays** in git history (uncommitted)
  as the spike that proved pipecat was needed. Not deleted — referenced.

### The success picture (Claude review's framing)
> 你而家要造嘅唔係完整 assistant,而係一條**連續講 20 次都唔 crash、廣東話
> 聽得明、英文讀得清、兩秒左右開始出聲**嘅本地 voice loop。呢個 solid core
> 一成功,Pipecat transport 才可以自然延伸到電話同 AI 眼鏡。

---

## 8. Sources (verified 2026-08-06)

- pipecat: `https://github.com/pipecat-ai/pipecat` (13,943★, BSD-2, pushed 2026-08-05)
- pipecat 1.7.0 installed locally: 58 service packages, framework + per-service extras model
- pipecat FunASR service: `pipecat/services/funasr/stt.py` (`FunASRSTTService`, `yue` first-class via `language_to_funasr_language`)
- pipecat Ollama service: `pipecat/services/ollama/llm.py` (`OLLamaLLMService` — two L's; inherits `OpenAILLMService` → supports OpenAI-format function-calling)
- pyaudio build failure on Python 3.14: confirmed via `pip install "pipecat-ai[local]"` → wheel build error
- Reused Obsidian pipeline: `obsidian_plugin/`, `specs/vault-structure-spec.md`, `tools/vault_setup/`, `llm_wiki_engine/`
- Prior hand-built version: `tools/voice_router/` (this session, superseded)
- Alternatives rejected: Open WebUI (license), HF speech-to-speech (Alpha), RealtimeSTT/TTS (no loop), Vocode (dead), LiveKit (cloud-leaning)
