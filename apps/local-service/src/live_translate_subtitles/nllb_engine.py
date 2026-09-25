"""Local NLLB translation adapter with Taiwan Traditional Chinese normalization."""

from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import Any

from .contracts import TranslationRequest, TranslationResult
from .faster_whisper_engine import default_model_root

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
DEFAULT_REVISION = "f8d333a098d19b4fd9a8b18f94170487ad3f821d"

LANGUAGE_CODES = {
    "en": "eng_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "zh": "zho_Hans",
    "zh-CN": "zho_Hans",
    "zh-TW": "zho_Hant",
}


class NllbTranslationEngine:
    """Translate through a locally cached Transformers NLLB checkpoint."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model_name = model_name
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._normalizer: Any | None = None
        self._device = "cpu"

    async def load(self) -> None:
        try:
            import torch  # type: ignore[import-not-found]
            from opencc import OpenCC  # type: ignore[import-not-found]
            from transformers import (  # type: ignore[import-not-found]
                AutoModelForSeq2SeqLM,
                AutoTokenizer,
            )
        except ImportError as error:
            raise RuntimeError(
                "Translation dependencies are missing. Install the local service with the "
                "'translation' extra."
            ) from error

        model_root = default_model_root()
        model_root.mkdir(parents=True, exist_ok=True)
        allow_download = os.environ.get("LTS_ALLOW_MODEL_DOWNLOAD") == "1"
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if self._device == "cuda" else torch.float32
        common = {
            "cache_dir": str(model_root),
            "local_files_only": not allow_download,
            "revision": DEFAULT_REVISION,
        }
        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name, **common)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            self._model_name,
            torch_dtype=dtype,
            **common,
        )
        self._model.to(self._device)
        self._model.eval()
        self._normalizer = OpenCC("s2twp")

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        return await asyncio.to_thread(self._translate_sync, request)

    def _translate_sync(self, request: TranslationRequest) -> TranslationResult:
        if self._model is None or self._tokenizer is None or self._normalizer is None:
            raise RuntimeError("Translation model is not loaded")

        source_code = _language_code(request.source_language)
        target_code = _language_code(request.target_language)
        self._tokenizer.src_lang = source_code
        inputs = self._tokenizer(
            request.text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {name: value.to(self._device) for name, value in inputs.items()}
        target_token_id = self._tokenizer.convert_tokens_to_ids(target_code)

        started = perf_counter()
        generated = self._model.generate(
            **inputs,
            forced_bos_token_id=target_token_id,
            max_new_tokens=256,
            num_beams=1,
        )
        translated = self._tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
        if request.target_language == "zh-TW":
            translated = self._normalizer.convert(translated)

        return TranslationResult(
            translated_text=str(translated).strip(),
            source_language=request.source_language,
            target_language=request.target_language,
            latency_ms=round((perf_counter() - started) * 1000),
        )

    async def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._normalizer = None


def _language_code(language: str) -> str:
    try:
        return LANGUAGE_CODES[language]
    except KeyError as error:
        raise ValueError(f"Unsupported translation language: {language}") from error
