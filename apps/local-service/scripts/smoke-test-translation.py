"""Load the local translation model and run one English-to-zh-TW request."""

from __future__ import annotations

import asyncio
from time import perf_counter

from live_translate_subtitles.contracts import TranslationRequest
from live_translate_subtitles.nllb_engine import NllbTranslationEngine


async def run() -> None:
    engine = NllbTranslationEngine()
    started = perf_counter()
    await engine.load()
    load_ms = round((perf_counter() - started) * 1000)
    result = await engine.translate(
        TranslationRequest(
            text="Hello, this is a local real-time subtitle test.",
            source_language="en",
            target_language="zh-TW",
        )
    )
    await engine.unload()
    print(
        {
            "loadMs": load_ms,
            "translateMs": result.latency_ms,
            "translation": result.translated_text,
        }
    )


if __name__ == "__main__":
    asyncio.run(run())
