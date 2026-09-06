"""
Gate 1 — Echo proof (Cantonese ASR only, no LLM, no TTS).

Pipeline:
  Mac mic → LocalAudioTransport.input()
         → VADProcessor(SileroVADAnalyzer)   # emits speech start/stop frames
         → FunASRSTTService (SenseVoice, yue) # transcribes each speech segment
         → TranscriptPrinter                 # prints the transcript + latency

Success criteria (per docs/internal/voice-pipecat-plan.md §3, Gate 1):
  - speak Cantonese → transcript prints
  - silence doesn't crash
  - AirPods Max mic works
  - latency (VAD-stop → transcript) is measured

Run (from repo root, in .venv-voice):
    .venv-voice/bin/python -m tools.voice_pipecat.gate1_echo

Speak in Cantonese. Each utterance prints with its ASR latency. Ctrl-C to quit.
"""

from __future__ import annotations

import asyncio
import sys
import time

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    VADUserStartedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.funasr.stt import FunASRSTTService, FunASRSTTSettings
from pipecat.transcriptions.language import Language
from pipecat.transports.local.audio import (
    LocalAudioTransport,
    LocalAudioTransportParams,
)

# Silence pipecat's chatty INFO logs; keep warnings+.
logger.remove()
logger.add(sys.stderr, level="WARNING")


class TranscriptPrinter(FrameProcessor):
    """Sink: prints each finalized Cantonese transcript with ASR latency.

    Measures the delay from VAD user-stopped-speaking (end of utterance) to the
    finalized TranscriptionFrame arriving — the ASR processing latency.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._vad_stop_time: float | None = None
        self._turn = 0

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Make VAD activity VISIBLE — so it's clear the pipeline is hearing
        # you (vs hung). If you never see "🗣️", the VAD threshold is too strict.
        if isinstance(frame, VADUserStartedSpeakingFrame):
            self._vad_stop_time = None
            print("🗣️  (聽到人聲)", flush=True)

        elif isinstance(frame, VADUserStoppedSpeakingFrame):
            self._vad_stop_time = time.monotonic()
            self._turn += 1
            print("   (停咗講，轉做文字中...)", flush=True)

        elif isinstance(frame, TranscriptionFrame):
            text = frame.text.strip()
            if not text:
                return
            latency = ""
            if self._vad_stop_time is not None:
                ms = (time.monotonic() - self._vad_stop_time) * 1000
                latency = f"  [ASR {ms:.0f}ms]"
            print(f"👂 {text}{latency}", flush=True)


async def main() -> int:
    print("=== Gate 1 — Echo proof (Cantonese ASR) ===")
    print("    mic → VAD → FunASR(SenseVoice, yue) → print")
    print("    戴住 AirPods Max，用廣東話講嘢。Ctrl-C 退出。\n")

    # Transport: local mic (16kHz mono, the format SenseVoice expects)
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,
            audio_in_channels=1,
        )
    )

    # VAD: Silero. Defaults (confidence=0.7, min_volume=0.6) are too strict for
    # AirPods Max at normal distance — speech never clears them, so no segment
    # ever closes and no transcript prints. Loosen: low min_volume + lower
    # confidence so conversational speech reliably fires; 0.5s trailing silence
    # to close a turn.
    vad = VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(
                confidence=0.5,
                min_volume=0.1,
                start_secs=0.2,
                stop_secs=0.5,
            ),
        )
    )

    # STT: SenseVoice, Cantonese (yue). FunASR weights load on first segment.
    stt = FunASRSTTService(
        device="cpu",
        settings=FunASRSTTSettings(
            model="iic/SenseVoiceSmall",
            language=Language.YUE,
            use_itn=True,
        ),
    )

    printer = TranscriptPrinter()

    pipeline = Pipeline(
        source=transport.input(),
        processors=[vad, stt, printer],
    )

    task = PipelineTask(pipeline, params=PipelineParams())
    runner = PipelineRunner(handle_sigint=True)

    print("⏳ 載入模型... (第一次講嘢要等SenseVoice load)\n")
    await runner.run(task)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
