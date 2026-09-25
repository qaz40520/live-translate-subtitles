"""Model-independent contracts used inside the local service."""

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    text: str
    source_language: str
    target_language: str
    context: Sequence[str] = ()
    is_final: bool = False


@dataclass(frozen=True, slots=True)
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    latency_ms: int


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    segment_id: str
    source_language: str
    text: str
    start_time_ms: int
    end_time_ms: int
    is_final: bool


@dataclass(frozen=True, slots=True)
class SubtitleUpdate:
    segment: TranscriptSegment
    translated_text: str


class TranslationEngine(Protocol):
    async def load(self) -> None: ...

    async def translate(self, request: TranslationRequest) -> TranslationResult: ...

    async def unload(self) -> None: ...


class SpeechToTextEngine(Protocol):
    async def load(self) -> None: ...

    async def transcribe(self, pcm_s16le: bytes) -> Sequence[TranscriptSegment]: ...

    async def reset(self) -> None: ...

    async def unload(self) -> None: ...

