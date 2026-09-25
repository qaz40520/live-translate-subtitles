"""Faster Whisper implementation of the speech-to-text engine contract."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

from .contracts import TranscriptSegment


def default_model_root() -> Path:
    configured = os.environ.get("LTS_MODEL_DIR")
    if configured:
        return Path(configured)
    local_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return local_data / "LiveTranslateSubtitles" / "models"


class FasterWhisperEngine:
    def __init__(self, model_name: str = "large-v3-turbo") -> None:
        self._model_name = model_name
        self._model: object | None = None
        self._language: str | None = None
        self.last_latency_ms = 0

    async def load(self) -> None:
        try:
            import ctranslate2  # type: ignore[import-untyped]
            from faster_whisper import WhisperModel  # type: ignore[import-untyped]
        except ImportError as error:
            raise RuntimeError(
                "STT dependencies are missing. Install the local service with the 'stt' extra."
            ) from error

        model_root = default_model_root()
        model_root.mkdir(parents=True, exist_ok=True)
        allow_download = os.environ.get("LTS_ALLOW_MODEL_DOWNLOAD") == "1"

        has_cuda = ctranslate2.get_cuda_device_count() > 0
        device = "cuda" if has_cuda else "cpu"
        compute_type = "int8_float16" if has_cuda else "int8"
        self._model = WhisperModel(
            self._model_name,
            device=device,
            compute_type=compute_type,
            download_root=str(model_root),
            local_files_only=not allow_download,
        )

    async def transcribe(self, pcm_s16le: bytes) -> Sequence[TranscriptSegment]:
        if self._model is None:
            raise RuntimeError("Speech-to-text model is not loaded")

        import numpy as np

        audio = np.frombuffer(pcm_s16le, dtype=np.int16).astype(np.float32) / 32768.0
        started = perf_counter()
        segments, info = self._model.transcribe(  # type: ignore[attr-defined]
            audio,
            language=self._language,
            beam_size=1,
            best_of=1,
            condition_on_previous_text=False,
            vad_filter=True,
            word_timestamps=False,
        )
        materialized = list(segments)
        self.last_latency_ms = round((perf_counter() - started) * 1000)
        if self._language is None:
            self._language = str(info.language)

        text = " ".join(str(segment.text).strip() for segment in materialized).strip()
        if not text:
            return ()

        start_seconds = min(float(segment.start) for segment in materialized)
        end_seconds = max(float(segment.end) for segment in materialized)
        return (
            TranscriptSegment(
                segment_id="live",
                source_language=self._language,
                text=text,
                start_time_ms=round(start_seconds * 1000),
                end_time_ms=round(end_seconds * 1000),
                is_final=False,
            ),
        )

    async def reset(self) -> None:
        self._language = None

    async def unload(self) -> None:
        self._model = None
        self._language = None
