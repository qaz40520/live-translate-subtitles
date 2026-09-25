"""Translate complete sentences locally with TranslateGemma through Ollama."""

from __future__ import annotations

import asyncio
import json
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .contracts import TranslationRequest, TranslationResult

DEFAULT_MODEL = "translategemma:4b"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"

LANGUAGE_NAMES = {
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
}


class OllamaTranslationEngine:
    """Use the local Ollama API without adding an HTTP client dependency."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self.model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._normalizer: Any | None = None

    async def load(self) -> None:
        try:
            from opencc import OpenCC  # type: ignore[import-not-found,import-untyped]
        except ImportError as error:
            raise RuntimeError("OpenCC is required for Taiwan Traditional Chinese output") from error
        self._normalizer = OpenCC("s2twp")
        await asyncio.to_thread(
            self._post,
            "/api/generate",
            {"model": self.model_name, "prompt": "", "stream": False, "keep_alive": "10m"},
        )

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        return await asyncio.to_thread(self._translate_sync, request)

    def _translate_sync(self, request: TranslationRequest) -> TranslationResult:
        started = perf_counter()
        response = self._post(
            "/api/chat",
            {
                "model": self.model_name,
                "stream": False,
                "keep_alive": "10m",
                "messages": [
                    {"role": "user", "content": _translation_prompt(request)},
                ],
                "options": {"temperature": 0, "num_predict": 256},
            },
        )
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise RuntimeError("TranslateGemma returned an invalid response")
        translated = str(message["content"]).strip()
        if request.target_language == "zh-TW" and self._normalizer is not None:
            translated = str(self._normalizer.convert(translated)).strip()
        if not translated:
            raise RuntimeError("TranslateGemma returned an empty translation")
        return TranslationResult(
            translated_text=translated,
            source_language=request.source_language,
            target_language=request.target_language,
            latency_ms=round((perf_counter() - started) * 1000),
        )

    async def unload(self) -> None:
        try:
            await asyncio.to_thread(
                self._post,
                "/api/generate",
                {"model": self.model_name, "prompt": "", "stream": False, "keep_alive": 0},
            )
        except RuntimeError:
            pass
        self._normalizer = None

    def _post(self, path: str, payload: dict[str, object]) -> dict[str, Any]:
        request = Request(
            f"{self._base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=180) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(
                "Ollama is unavailable. Start Ollama and ensure translategemma:4b is installed."
            ) from error
        if not isinstance(decoded, dict):
            raise RuntimeError("Ollama returned an invalid JSON response")
        if isinstance(decoded.get("error"), str):
            raise RuntimeError(str(decoded["error"]))
        return decoded


def _translation_prompt(request: TranslationRequest) -> str:
    try:
        source_name = LANGUAGE_NAMES[request.source_language]
        target_name = LANGUAGE_NAMES[request.target_language]
    except KeyError as error:
        raise ValueError(f"Unsupported translation language: {error.args[0]}") from error
    return (
        f"You are a professional {source_name} ({request.source_language}) to "
        f"{target_name} ({request.target_language}) translator. Your goal is to accurately "
        f"convey the meaning and nuances of the original {source_name} text while adhering to "
        f"{target_name} grammar, vocabulary, and cultural sensitivities.\n"
        f"Produce only the {target_name} translation, without any additional explanations or "
        f"commentary. Please translate the following {source_name} text into {target_name}:\n\n"
        f"{request.text}"
    )
