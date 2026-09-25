"""Bounded streaming transcription worker."""

from __future__ import annotations

import asyncio
import base64
import queue
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .contracts import TranscriptSegment
from .faster_whisper_engine import FasterWhisperEngine

SAMPLE_RATE_HZ = 16000
BYTES_PER_SAMPLE = 2
TRANSCRIBE_AFTER_SECONDS = 2.4
ROLLING_WINDOW_SECONDS = 10


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
    ) -> None:
        self._session_id = session_id
        self._emit = emit
        self._engine = engine or FasterWhisperEngine()
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
            await self._engine.unload()

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
                self._emit(
                    {
                        "protocolVersion": 1,
                        "type": "subtitle.update",
                        "sessionId": self._session_id,
                        "sequence": update_sequence,
                        "segmentId": segment.segment_id,
                        "sourceLanguage": segment.source_language,
                        "sourceText": segment.text,
                        "translatedText": "",
                        "startTimeMs": segment.start_time_ms,
                        "endTimeMs": segment.end_time_ms,
                        "isFinal": segment.is_final,
                    }
                )
                update_sequence += 1
            self._emit_status("busy", self._engine.last_latency_ms)

    def _emit_status(self, status: str, queue_delay_ms: int) -> None:
        self._emit(
            {
                "protocolVersion": 1,
                "type": "service.status",
                "sessionId": self._session_id,
                "status": status,
                "queueDelayMs": queue_delay_ms,
                "activeSttModel": "large-v3-turbo",
            }
        )


def _required_int(message: Mapping[str, object], key: str) -> int:
    value = message.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer")
    return value
