"""Explicit development-time download command for translation model weights."""

from __future__ import annotations

import argparse

from .faster_whisper_engine import default_model_root
from .nllb_engine import DEFAULT_MODEL, DEFAULT_REVISION


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


if __name__ == "__main__":
    main()
