# Model and licensing policy

## Default alpha models

| Capability | Default | Purpose | License note |
| --- | --- | --- | --- |
| Speech recognition | Whisper large-v3-turbo through faster-whisper | Multilingual local STT | Whisper weights are MIT; dependencies retain their licenses |
| Translation | NLLB-200 distilled 600M | Fast multilingual prototype translation | CC-BY-NC-4.0; alpha and non-commercial use only |
| Chinese normalization | OpenCC | Taiwan-oriented Traditional Chinese normalization | Apache-2.0 |

Model files are not committed to this repository or bundled under the repository's Apache-2.0 license.

The alpha pins NLLB to revision `f8d333a098d19b4fd9a8b18f94170487ad3f821d`.
Its PyTorch weight file is approximately 2.46 GB and has SHA-256
`c266c2cfd19758b6d09c1fc31ecdf1e485509035f6b51dfe84f1ada83eefcc42`.

## Replacement policy

- Application code depends only on stable engine interfaces.
- Each adapter declares model ID, version, hash, approximate download size, supported languages, execution requirements, and license metadata.
- Adding an adapter must not require extension or transport changes.
- Shared conformance tests cover loading, cancellation, language handling, provisional results, final results, errors, and unloading.
- Commercial releases must not enable NLLB by default and must use a model whose terms permit the intended distribution and use.

Candidate commercial-capable translation adapters include TranslateGemma and MADLAD, subject to a fresh license review at integration time.
