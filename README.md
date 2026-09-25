# Live Translate Subtitles

Local-first, real-time translated subtitles for browser video and live streams.

> Status: working Chrome alpha with local tab capture, speech recognition, and translation.

## Goals

- Capture audio from a user-selected Chrome or Firefox tab.
- Transcribe locally with Whisper and translate locally into Traditional Chinese.
- Show provisional bilingual subtitles directly over the video, including fullscreen playback.
- Keep audio and subtitle content off the network and off disk by default.
- Prefer free and open-source components with replaceable model adapters.

## Planned default stack

- Speech-to-text: `faster-whisper` with `whisper-large-v3-turbo`
- Translation: `TranslateGemma 4B` through the local Ollama runtime
- Traditional Chinese normalization: OpenCC with Taiwan terminology
- Extension: TypeScript, shared Chrome/Firefox code
- Local service: Python, packaged as a Windows executable
- Browser-to-service transport: Native Messaging

Model weights are not included in this repository. Each model keeps its own license; see [Model policy](docs/model-policy.md).

## Repository layout

```text
apps/
  extension/       Chrome and Firefox extension
  local-service/   Local STT and translation service
packages/
  protocol/        Shared message contracts
docs/              Product, architecture, and delivery documents
```

## Development

Prerequisites for the current scaffold:

- Node.js 20 or newer
- pnpm 9 or newer
- Python 3.11 or newer

```bash
pnpm install
pnpm check
pnpm build
python -m unittest discover -s apps/local-service/tests -v
```

### Chrome local subtitle spike

The current milestone contains an experimental Chrome tab-audio pipeline with
local TranslateGemma translation. The NLLB adapter remains available for model experiments.

1. Create `.venv` and install `apps/local-service[models,dev]` in editable mode.
2. Build with `pnpm build`.
3. Load `apps/extension/dist/chrome` as an unpacked extension.
4. Register the native host. The manifest key keeps the development extension
   ID fixed at `lkmcdfehamclallnfmcobgecooedokpm`:

   ```powershell
   ./apps/local-service/scripts/register-chrome-native-host.ps1 -ExtensionId lkmcdfehamclallnfmcobgecooedokpm
   ```

5. Review the Whisper MIT license and expected download size, then explicitly
   download the development model:

   ```powershell
   ./.venv/Scripts/live-translate-download-stt.exe --model large-v3-turbo --yes
   ```

   Development runs use the ignored repository directory `models/`. A packaged
   release uses `%LOCALAPPDATA%\LiveTranslateSubtitles\models`.

6. Review the Gemma usage terms, install Ollama, and download TranslateGemma 4B:

   ```powershell
   ollama pull translategemma:4b
   ```

Normal service startup refuses network model downloads. Missing local models
are reported in the subtitle overlay while the available pipeline continues.

The repeatable local audio fixture is available at
`apps/extension/manual-test/index.html`; serve the repository over localhost so
Chrome can inject the subtitle overlay without file-URL permissions.

## Documentation

- [Product specification](docs/product-spec.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Model and licensing policy](docs/model-policy.md)

## License

Project source code is licensed under Apache-2.0. Third-party models and dependencies retain their own licenses.
