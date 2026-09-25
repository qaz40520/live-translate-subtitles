# Roadmap

## Milestone 0 — Architecture scaffold

- Product specification and architecture are versioned.
- Monorepo layout exists.
- Cross-component protocol types compile.
- Local engine contracts have unit tests.

## Milestone 1 — Audio-to-text technical spike

- [x] Capture Chrome tab audio after an explicit click.
- [x] Stream canonical PCM chunks to the native service.
- [x] Add a guarded Faster Whisper adapter and detect the RTX 3070 CUDA runtime.
- [x] Download the selected Whisper model after explicit developer consent.
- [x] Run Faster Whisper on recorded tab audio using the RTX 3070 reference machine.
- Measure provisional and final transcript latency for English, Japanese, and Korean.
- Prove 30 minutes of bounded-memory operation.

## Milestone 2 — Local translation pipeline

- [x] Add NLLB adapter and OpenCC normalization.
- [x] Add rolling context and 800 ms translation throttling.
- Add adapter conformance tests.
- Measure end-to-end latency and GPU memory.

## Milestone 3 — Subtitle experience

- Add translated-only and bilingual overlays.
- Add fullscreen support and basic styling.
- Add pause, resume, stop, and user-confirmed performance fallback.
- Export SRT, WebVTT, and TXT.

## Milestone 4 — Firefox and packaging

- Validate the shared extension core in Firefox.
- Package the Windows native host and register browser manifests.
- Add model download, license consent, hash verification, deletion, and update prompts.
- Publish a developer Alpha through GitHub Releases.

## Milestone 5 — Public beta

- Run privacy and threat-model reviews.
- Improve recovery, accessibility, localization, and diagnostics.
- Evaluate commercially usable translation adapters.
- Prepare Chrome Web Store and Firefox Add-ons submissions.
