"""Bounded streaming transcription worker."""

from __future__ import annotations

import asyncio
import base64
import queue
import re
import threading
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from .contracts import TranscriptSegment, TranslationEngine, TranslationRequest
from .faster_whisper_engine import FasterWhisperEngine

SAMPLE_RATE_HZ = 16000
BYTES_PER_SAMPLE = 2
TRANSCRIBE_AFTER_SECONDS = 2.4
ROLLING_WINDOW_SECONDS = 10
TRANSLATION_THROTTLE_SECONDS = 0.8
_SENTENCE_PATTERN = re.compile(
    r"[^.!?。！？]+[.!?。！？](?:\s+|$)"  # noqa: RUF001 - CJK punctuation is intentional
)


@dataclass(frozen=True, slots=True)
class AudioChunk:
    sequence: int
    captured_at_ms: int
    pcm_s16le: bytes


class StreamingSpeechToTextEngine(Protocol):
    last_latency_ms: int

    async def load(self) -> None: ...

    async def transcribe(self, pcm_s16le: bytes) -> Sequence[TranscriptSegment]: ...

    async def unload(self) -> None: ...


class TranscriptionSession:
    def __init__(
        self,
        session_id: str,
        emit: Callable[[Mapping[str, object]], None],
        engine: StreamingSpeechToTextEngine | None = None,
        translator: TranslationEngine | None = None,
        target_language: str = "zh-TW",
    ) -> None:
        self._session_id = session_id
        self._emit = emit
        self._engine = engine or FasterWhisperEngine()
        self._translator = translator
        self._target_language = target_language
        self._translation_context: list[str] = []
        self._recently_translated: deque[str] = deque(maxlen=32)
        self._previous_completed: set[str] = set()
        self._last_translation_at = 0.0
        self._queue: queue.Queue[AudioChunk | None] = queue.Queue(maxsize=32)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stopped = threading.Event()

    def start(self) -> None:
        self._thread.start()

    @property
    def session_id(self) -> str:
        return self._session_id

    def submit_base64(self, message: Mapping[str, object]) -> None:
        encoded = message.get("audioBase64")
        if not isinstance(encoded, str):
            raise TypeError("audioBase64 must be a string")
        chunk = AudioChunk(
            sequence=_required_int(message, "sequence"),
            captured_at_ms=_required_int(message, "capturedAtMs"),
            pcm_s16le=base64.b64decode(encoded, validate=True),
        )
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            self._emit(
                {
                    "protocolVersion": 1,
                    "type": "service.error",
                    "sessionId": self._session_id,
                    "code": "audio_backpressure",
                    "message": "Audio queue is full; transcription cannot keep up.",
                    "recoverable": True,
                }
            )

    def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._stopped.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._thread.join(timeout=5)

    def _run(self) -> None:
        asyncio.run(self._run_async())

    async def _run_async(self) -> None:
        self._emit_status("starting", 0)
        try:
            await self._engine.load()
            await self._load_translator()
            self._emit_status("ready", 0)
            await self._consume_audio()
        except Exception as error:  # noqa: BLE001 - worker boundary reports model failures
            self._emit(
                {
                    "protocolVersion": 1,
                    "type": "service.error",
                    "sessionId": self._session_id,
                    "code": "stt_failure",
                    "message": str(error),
                    "recoverable": True,
                }
            )
        finally:
            if self._translator is not None:
                await self._translator.unload()
            await self._engine.unload()

    async def _load_translator(self) -> None:
        if self._translator is None:
            return
        try:
            await self._translator.load()
        except Exception as error:  # noqa: BLE001 - source subtitles remain available
            self._emit(
                {
                    "protocolVersion": 1,
                    "type": "service.error",
                    "sessionId": self._session_id,
                    "code": "translation_unavailable",
                    "message": str(error),
                    "recoverable": True,
                }
            )
            self._translator = None

    async def _consume_audio(self) -> None:
        rolling = bytearray()
        bytes_since_transcription = 0
        threshold = round(TRANSCRIBE_AFTER_SECONDS * SAMPLE_RATE_HZ * BYTES_PER_SAMPLE)
        max_window = ROLLING_WINDOW_SECONDS * SAMPLE_RATE_HZ * BYTES_PER_SAMPLE
        update_sequence = 0

        while not self._stopped.is_set():
            chunk = await asyncio.to_thread(self._queue.get)
            if chunk is None:
                return
            rolling.extend(chunk.pcm_s16le)
            bytes_since_transcription += len(chunk.pcm_s16le)
            if len(rolling) > max_window:
                del rolling[: len(rolling) - max_window]
            if bytes_since_transcription < threshold:
                continue

            bytes_since_transcription = 0
            segments = await self._engine.transcribe(bytes(rolling))
            for segment in segments:
                translated_source_text, translated_text = await self._translate(segment)
                self._emit(
                    {
                        "protocolVersion": 1,
                        "type": "subtitle.update",
                        "sessionId": self._session_id,
                        "sequence": update_sequence,
                        "segmentId": segment.segment_id,
                        "sourceLanguage": segment.source_language,
                        "sourceText": segment.text,
                        "translatedSourceText": translated_source_text,
                        "translatedText": translated_text,
                        "startTimeMs": segment.start_time_ms,
                        "endTimeMs": segment.end_time_ms,
                        "isFinal": segment.is_final,
                    }
                )
                update_sequence += 1
            if any(segment.is_final for segment in segments):
                rolling.clear()
            self._emit_status("busy", self._engine.last_latency_ms)

    async def _translate(self, segment: TranscriptSegment) -> tuple[str, str]:
        if self._translator is None:
            return "", ""
        completed = _completed_sentences(segment.text, segment.is_final)
        stable = completed if segment.is_final else tuple(
            text for text in completed if text in self._previous_completed
        )
        self._previous_completed = set(completed)
        untranslated = [text for text in stable if text not in self._recently_translated]
        if not untranslated:
            return "", ""
        source_text = " ".join(untranslated)
        wait_seconds = TRANSLATION_THROTTLE_SECONDS - (monotonic() - self._last_translation_at)
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        try:
            result = await self._translator.translate(
                TranslationRequest(
                    text=source_text,
                    source_language=segment.source_language,
                    target_language=self._target_language,
                    context=tuple(self._translation_context[-3:]),
                    is_final=segment.is_final,
                )
            )
        except Exception as error:  # noqa: BLE001 - keep source subtitles running
            self._emit(
                {
                    "protocolVersion": 1,
                    "type": "service.error",
                    "sessionId": self._session_id,
                    "code": "translation_failure",
                    "message": str(error),
                    "recoverable": True,
                }
            )
            return "", ""
        self._translation_context.append(source_text)
        self._recently_translated.extend(untranslated)
        self._last_translation_at = monotonic()
        return source_text, result.translated_text

    def _emit_status(self, status: str, queue_delay_ms: int) -> None:
        message: dict[str, object] = {
            "protocolVersion": 1,
            "type": "service.status",
            "sessionId": self._session_id,
            "status": status,
            "queueDelayMs": queue_delay_ms,
            "activeSttModel": "large-v3-turbo",
        }
        if self._translator is not None:
            message["activeTranslationModel"] = "nllb-200-distilled-600M"
        self._emit(message)


def _required_int(message: Mapping[str, object], key: str) -> int:
    value = message.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer")
    return value


def _completed_sentences(text: str, is_final: bool) -> tuple[str, ...]:
    completed: list[str] = []
    consumed_until = 0
    for match in _SENTENCE_PATTERN.finditer(text):
        sentence = match.group(0).strip()
        if sentence:
            completed.append(sentence)
        consumed_until = match.end()
    if is_final:
        tail = text[consumed_until:].strip()
        if tail:
            completed.append(tail)
    return tuple(completed)
