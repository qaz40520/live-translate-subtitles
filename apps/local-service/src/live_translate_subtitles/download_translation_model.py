"""Explicit development-time download command for translation model weights."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from .faster_whisper_engine import default_model_root
from .nllb_engine import CONVERTED_MODEL_DIRECTORY, DEFAULT_MODEL, DEFAULT_REVISION

DEFAULT_WEIGHT_SHA256 = "c266c2cfd19758b6d09c1fc31ecdf1e485509035f6b51dfe84f1ada83eefcc42"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a translation model for local use")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm the model license, disk usage, and network download",
    )
    args = parser.parse_args()

    if not args.yes:
        parser.error(
            "Explicit confirmation is required. NLLB-200 is CC-BY-NC-4.0 and intended "
            "for non-commercial use. Review the license and expected size, then rerun "
            "with --yes."
        )

    from huggingface_hub import snapshot_download

    model_root = default_model_root()
    model_root.mkdir(parents=True, exist_ok=True)
    downloaded_path = snapshot_download(
        repo_id=args.model,
        revision=DEFAULT_REVISION if args.model == DEFAULT_MODEL else None,
        cache_dir=str(model_root),
    )
    print(f"Downloaded {args.model} to {downloaded_path}")

    if args.model == DEFAULT_MODEL:
        _verify_sha256(Path(downloaded_path) / "pytorch_model.bin", DEFAULT_WEIGHT_SHA256)

    from ctranslate2.converters import TransformersConverter  # type: ignore[import-untyped]

    converted_path = model_root / CONVERTED_MODEL_DIRECTORY
    converter = TransformersConverter(
        downloaded_path,
        copy_files=[
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "sentencepiece.bpe.model",
        ],
    )
    converter.convert(str(converted_path), quantization="int8_float16", force=True)
    print(f"Converted translation model to {converted_path}")


def _verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise RuntimeError(f"Model checksum mismatch: expected {expected}, got {actual}")
    print(f"Verified SHA-256: {actual}")


if __name__ == "__main__":
    main()
