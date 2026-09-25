# Live Translate Subtitles

Local-first, real-time translated subtitles for browser video and live streams.

> Status: architecture scaffold. Audio capture, speech recognition, and translation are not implemented yet.

## Goals

- Capture audio from a user-selected Chrome or Firefox tab.
- Transcribe locally with Whisper and translate locally into Traditional Chinese.
- Show provisional bilingual subtitles directly over the video, including fullscreen playback.
- Keep audio and subtitle content off the network and off disk by default.
- Prefer free and open-source components with replaceable model adapters.

## Planned default stack

- Speech-to-text: `faster-whisper` with `whisper-large-v3-turbo`
- Translation for the non-commercial alpha: `NLLB-200-distilled-600M`
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

## Documentation

- [Product specification](docs/product-spec.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Model and licensing policy](docs/model-policy.md)

## License

Project source code is licensed under Apache-2.0. Third-party models and dependencies retain their own licenses.

