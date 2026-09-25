# Model and licensing policy

## Default alpha models

| Capability | Default | Purpose | License note |
| --- | --- | --- | --- |
| Speech recognition | Whisper large-v3-turbo through faster-whisper | Multilingual local STT | Whisper weights are MIT; dependencies retain their licenses |
| Translation | NLLB-200 distilled 600M | Fast multilingual prototype translation | CC-BY-NC-4.0; alpha and non-commercial use only |
| Chinese normalization | OpenCC | Taiwan-oriented Traditional Chinese normalization | Apache-2.0 |

Model files are not committed to this repository or bundled under the repository's Apache-2.0 license.

## Replacement policy

- Application code depends only on stable engine interfaces.
- Each adapter declares model ID, version, hash, approximate download size, supported languages, execution requirements, and license metadata.
- Adding an adapter must not require extension or transport changes.
- Shared conformance tests cover loading, cancellation, language handling, provisional results, final results, errors, and unloading.
- Commercial releases must not enable NLLB by default and must use a model whose terms permit the intended distribution and use.

Candidate commercial-capable translation adapters include TranslateGemma and MADLAD, subject to a fresh license review at integration time.

