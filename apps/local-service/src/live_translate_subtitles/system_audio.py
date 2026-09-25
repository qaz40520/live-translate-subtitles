"""Windows system-output capture for browsers without tab-audio APIs."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

SAMPLE_RATE_HZ = 16000
CHUNK_SECONDS = 0.8
CHUNK_FRAMES = round(SAMPLE_RATE_HZ * CHUNK_SECONDS)


class SystemAudioCapture:
    """Capture the default Windows output device through WASAPI loopback."""

    def __init__(
        self,
        submit: Callable[..., None],
        emit: Callable[[Mapping[str, object]], None],
        session_id: str,
    ) -> None:
        self._submit = submit
        self._emit = emit
        self._session_id = session_id
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        self._thread.join(timeout=3)

    def _run(self) -> None:
        try:
            import soundcard as soundcard  # type: ignore[import-untyped]

            speaker = soundcard.default_speaker()
            if speaker is None:
                raise RuntimeError("Windows has no default audio output device")
            loopback = soundcard.get_microphone(speaker.name, include_loopback=True)
            if loopback is None:
                raise RuntimeError(f"No WASAPI loopback device found for {speaker.name}")

            sequence = 0
            with loopback.recorder(
                samplerate=SAMPLE_RATE_HZ,
                channels=[0, 1],
                blocksize=3200,
            ) as recorder:
                while not self._stopped.is_set():
                    audio = recorder.record(numframes=CHUNK_FRAMES)
                    self._submit(
                        _float_audio_to_pcm_s16le(audio),
                        sequence=sequence,
                        captured_at_ms=round(time.time() * 1000),
                    )
                    sequence += 1
        except Exception as error:  # noqa: BLE001 - capture thread reports device failures
            self._emit(
                {
                    "protocolVersion": 1,
                    "type": "service.error",
                    "sessionId": self._session_id,
                    "code": "system_audio_capture_failure",
                    "message": str(error),
                    "recoverable": True,
                }
            )


def _float_audio_to_pcm_s16le(audio: Any) -> bytes:
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim == 2:
        samples = samples.mean(axis=1)
    if samples.ndim != 1:
        raise ValueError("System audio capture returned an invalid sample shape")
    scaled = np.clip(samples, -1.0, 1.0) * 32767.0
    return scaled.astype("<i2").tobytes()
