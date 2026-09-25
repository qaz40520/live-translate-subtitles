"""Load the configured STT model and transcribe three seconds of silence."""

from __future__ import annotations

import asyncio
from time import perf_counter

from live_translate_subtitles.faster_whisper_engine import FasterWhisperEngine


async def run() -> None:
    engine = FasterWhisperEngine()
    started = perf_counter()
    await engine.load()
    load_ms = round((perf_counter() - started) * 1000)
    segments = await engine.transcribe(bytes(3 * 16000 * 2))
    await engine.unload()
    print(
        {
            "model": "large-v3-turbo",
            "loadMs": load_ms,
            "transcribeMs": engine.last_latency_ms,
            "silenceSegments": len(segments),
        }
    )


if __name__ == "__main__":
    asyncio.run(run())

