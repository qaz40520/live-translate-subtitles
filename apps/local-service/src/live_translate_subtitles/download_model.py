"""Explicit development-time download command for STT model weights."""

from __future__ import annotations

import argparse

from .faster_whisper_engine import default_model_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Download an STT model for local use")
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm the model license, disk usage, and network download",
    )
    args = parser.parse_args()

    if not args.yes:
        parser.error(
            "Explicit confirmation is required. Review the model license and expected size, "
            "then rerun with --yes."
        )

    from faster_whisper.utils import download_model  # type: ignore[import-untyped]

    model_root = default_model_root()
    model_root.mkdir(parents=True, exist_ok=True)
    downloaded_path = download_model(args.model, cache_dir=str(model_root))
    print(f"Downloaded {args.model} to {downloaded_path}")

