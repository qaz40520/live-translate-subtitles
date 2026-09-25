"""Local NLLB translation adapter with Taiwan Traditional Chinese normalization."""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from .contracts import TranslationRequest, TranslationResult
from .faster_whisper_engine import configure_windows_cuda_dlls, default_model_root

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
DEFAULT_REVISION = "f8d333a098d19b4fd9a8b18f94170487ad3f821d"
CONVERTED_MODEL_DIRECTORY = "nllb-200-distilled-600M-ct2-int8_float16"

LANGUAGE_CODES = {
    "en": "eng_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "zh": "zho_Hans",
    "zh-CN": "zho_Hans",
    # NLLB's Simplified Chinese path preserves more sentence content for the
    # tested language pairs; OpenCC then applies Taiwan Traditional Chinese.
    "zh-TW": "zho_Hans",
}


class NllbTranslationEngine:
    """Translate through a locally cached Transformers NLLB checkpoint."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model_name = model_name
        self._translator: Any | None = None
        self._tokenizer: Any | None = None
        self._normalizer: Any | None = None
        self._device = "cpu"

    async def load(self) -> None:
        configure_windows_cuda_dlls()
        try:
            import ctranslate2  # type: ignore[import-untyped]
            from opencc import OpenCC  # type: ignore[import-not-found,import-untyped]
            from transformers import AutoTokenizer  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "Translation dependencies are missing. Install the local service with the "
                "'translation' extra."
            ) from error

        model_root = default_model_root()
        converted_model = model_root / CONVERTED_MODEL_DIRECTORY
        if not (converted_model / "model.bin").is_file():
            raise RuntimeError(
                "Local translation model is missing. Run "
                "live-translate-download-translation --yes first."
            )

        has_cuda = ctranslate2.get_cuda_device_count() > 0
        self._device = "cuda" if has_cuda else "cpu"
        compute_type = "int8_float16" if has_cuda else "int8"
        self._tokenizer = AutoTokenizer.from_pretrained(
            converted_model,
            local_files_only=True,
            fix_mistral_regex=True,
        )
        self._translator = ctranslate2.Translator(
            str(converted_model),
            device=self._device,
            compute_type=compute_type,
        )
        self._normalizer = OpenCC("s2twp")

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        return await asyncio.to_thread(self._translate_sync, request)

    def _translate_sync(self, request: TranslationRequest) -> TranslationResult:
        if self._translator is None or self._tokenizer is None or self._normalizer is None:
            raise RuntimeError("Translation model is not loaded")

        source_code = _language_code(request.source_language)
        target_code = _language_code(request.target_language)
        self._tokenizer.src_lang = source_code
        source_tokens = self._tokenizer.convert_ids_to_tokens(
            self._tokenizer.encode(request.text, truncation=True, max_length=512)
        )

        started = perf_counter()
        result = self._translator.translate_batch(
            [source_tokens],
            target_prefix=[[target_code]],
            beam_size=1,
            max_decoding_length=256,
        )[0]
        target_tokens = result.hypotheses[0][1:]
        token_ids = self._tokenizer.convert_tokens_to_ids(target_tokens)
        translated = self._tokenizer.decode(token_ids, skip_special_tokens=True)
        if request.target_language == "zh-TW":
            translated = self._normalizer.convert(translated)

        return TranslationResult(
            translated_text=str(translated).strip(),
            source_language=request.source_language,
            target_language=request.target_language,
            latency_ms=round((perf_counter() - started) * 1000),
        )

    async def unload(self) -> None:
        self._translator = None
        self._tokenizer = None
        self._normalizer = None


def _language_code(language: str) -> str:
    try:
        return LANGUAGE_CODES[language]
    except KeyError as error:
        raise ValueError(f"Unsupported translation language: {language}") from error
