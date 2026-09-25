import base64
import sys
import time
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.contracts import (
    TranscriptSegment,
    TranslationRequest,
    TranslationResult,
)
from live_translate_subtitles.session import TranscriptionSession


class FakeEngine:
    def __init__(self) -> None:
        self.last_latency_ms = 12
        self.loaded = False

    async def load(self) -> None:
        self.loaded = True

    async def transcribe(self, pcm_s16le: bytes) -> tuple[TranscriptSegment, ...]:
        return (
            TranscriptSegment(
                segment_id="live",
                source_language="en",
                text=f"received {len(pcm_s16le)} bytes",
                start_time_ms=0,
                end_time_ms=2400,
                is_final=False,
            ),
        )

    async def unload(self) -> None:
        self.loaded = False


class FakeTranslator:
    def __init__(self) -> None:
        self.loaded = False

    async def load(self) -> None:
        self.loaded = True

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        return TranslationResult(
            translated_text=f"translated: {request.text}",
            source_language=request.source_language,
            target_language=request.target_language,
            latency_ms=8,
        )

    async def unload(self) -> None:
        self.loaded = False


class SessionTests(unittest.TestCase):
    def test_three_audio_chunks_trigger_a_provisional_transcript(self) -> None:
        emitted: list[dict[str, object]] = []
        engine = FakeEngine()
        session = TranscriptionSession("session-1", emitted.append, engine)
        session.start()

        chunk = base64.b64encode(bytes(25600)).decode("ascii")
        for sequence in range(3):
            session.submit_base64(
                {
                    "sequence": sequence,
                    "capturedAtMs": sequence * 800,
                    "audioBase64": chunk,
                }
            )

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if any(message.get("type") == "subtitle.update" for message in emitted):
                break
            time.sleep(0.01)

        session.stop()
        updates = [message for message in emitted if message.get("type") == "subtitle.update"]
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["sourceText"], "received 76800 bytes")
        self.assertFalse(engine.loaded)

    def test_translated_text_is_emitted_without_coupling_to_an_adapter(self) -> None:
        emitted: list[dict[str, object]] = []
        translator = FakeTranslator()
        session = TranscriptionSession(
            "session-2",
            emitted.append,
            FakeEngine(),
            translator=translator,
        )
        session.start()

        chunk = base64.b64encode(bytes(25600)).decode("ascii")
        for sequence in range(3):
            session.submit_base64(
                {
                    "sequence": sequence,
                    "capturedAtMs": sequence * 800,
                    "audioBase64": chunk,
                }
            )

        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if any(message.get("type") == "subtitle.update" for message in emitted):
                break
            time.sleep(0.01)

        session.stop()
        updates = [message for message in emitted if message.get("type") == "subtitle.update"]
        self.assertEqual(updates[0]["translatedText"], "translated: received 76800 bytes")
        self.assertFalse(translator.loaded)


if __name__ == "__main__":
    unittest.main()
