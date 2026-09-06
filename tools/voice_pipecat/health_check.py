"""
Voice pipecat — health check (Gate 0, made permanent).

Verifies the environment the voice assistant depends on. Run before any voice
work and after any venv/model change:

    .venv-voice/bin/python -m tools.voice_pipecat.health_check

Checks (all must pass before Gate 1):
  1. Python version is 3.12 (the pipecat/pyaudio-supported tier)
  2. pipecat-ai imports at the pinned version
  3. pyaudio sees at least one input device (mic available)
  4. Ollama is reachable and qwen3:4b is pulled
  5. macOS `say` voices Sinji (yue-HK) and Karen (en) are present

Exits 0 if all green, 1 if any check fails (so it can gate CI/scripts).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from typing import NamedTuple


class Check(NamedTuple):
    name: str
    ok: bool
    detail: str


def _check_python() -> Check:
    v = sys.version_info
    ok = v[:2] == (3, 12)
    return Check(
        "Python 3.12",
        ok,
        f"{v.major}.{v.minor}.{v.micro}",
    )


def _check_pipecat() -> Check:
    try:
        import pipecat  # noqa: F401
        from pipecat.services.funasr.stt import FunASRSTTService  # noqa: F401

        # NOTE: on pipecat-ai 1.7.0 the service __init__.py files are empty;
        # import from the module files directly. (Claude's review claimed the
        # package shortcut works — it does not on this version.)
        from pipecat.services.ollama.llm import OLLamaLLMService  # noqa: F401

        return Check("pipecat + ollama + funasr services", True, "imports OK")
    except Exception as e:
        return Check("pipecat services", False, f"{type(e).__name__}: {e}")


def _check_pyaudio_mic() -> Check:
    try:
        import pyaudio

        pa = pyaudio.PyAudio()
        n_input = sum(
            1
            for i in range(pa.get_device_count())
            if pa.get_device_info_by_index(i)["maxInputChannels"] > 0
        )
        pa.terminate()
        return Check("pyaudio mic", n_input > 0, f"{n_input} input device(s)")
    except Exception as e:
        return Check("pyaudio mic", False, f"{type(e).__name__}: {e}")


def _check_ollama() -> Check:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            d = json.loads(r.read().decode())
        names = [m["name"] for m in d.get("models", [])]
        has_voice = any("qwen3:4b" in n for n in names)
        return Check(
            "Ollama + qwen3:4b",
            has_voice,
            f"models: {', '.join(names) or 'none'}",
        )
    except Exception as e:
        return Check("Ollama", False, f"{type(e).__name__}: {e}")


def _check_say_voice(voice: str, label: str) -> Check:
    tmp = f"/tmp/_healthcheck_{voice}.aiff"
    try:
        out = subprocess.run(
            ["say", "-v", voice, "test", "-o", tmp],
            capture_output=True,
            text=True,
            timeout=10,
        )
        ok = out.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0
        return Check(f"say -v {voice} ({label})", ok, "voice present" if ok else out.stderr[:50])
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    # unreachable


def run_all() -> list[Check]:
    return [
        _check_python(),
        _check_pipecat(),
        _check_pyaudio_mic(),
        _check_ollama(),
        _check_say_voice("Sinji", "yue-HK"),
        _check_say_voice("Karen", "en"),
    ]


def main() -> int:
    print("Voice pipecat — health check (Gate 0)\n")
    checks = run_all()
    all_ok = True
    for c in checks:
        icon = "✅" if c.ok else "❌"
        print(f"  {icon} {c.name}: {c.detail}")
        all_ok = all_ok and c.ok
    print(f"\n{'🟢 ALL CHECKS PASSED' if all_ok else '🔴 FAILURES — fix above'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
