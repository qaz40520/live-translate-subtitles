# Product specification

## Product statement

Live Translate Subtitles is a Windows-first browser extension plus local companion service that generates real-time Traditional Chinese subtitles for video and live streams without sending audio or subtitle content to a cloud service.

## Initial user and platforms

- Initial user: an individual watching foreign-language browser video or live streams.
- Browsers: Chrome and Firefox.
- Operating system: Windows first.
- Primary test sites: YouTube and Twitch.
- General scope: any ordinary web page whose tab audio can be captured.
- Out of scope: browser-internal pages, inaccessible protected content, microphone input, system-wide audio, meetings, games, and native desktop applications.

## Session behavior

1. The user explicitly clicks **Start translation**.
2. The session binds to that tab and continues if the user switches tabs.
3. Only one tab can be translated at a time.
4. Source language is detected at session start and locked for the session.
5. The first release prioritizes English, Japanese, and Korean input.
6. Output is Traditional Chinese normalized for Taiwan terminology.
7. The user stops the session manually, closes the source tab, or encounters an unrecoverable capture error.

The system always transcribes tab audio. It does not depend on a site's existing captions.

## Subtitle behavior

- Provisional source text appears as speech is recognized.
- The current subtitle line may be rewritten as recognition improves.
- Translation is refreshed no more often than approximately every 800 ms.
- Translation receives the previous two or three confirmed source segments as context.
- Confirmed historical subtitles are not rewritten.
- Users can switch between translated-only and bilingual display.
- No speaker diarization is included in the MVP.
- Subtitle controls: font size, position, text color, and background opacity.
- Subtitle overlay remains visible during fullscreen playback.

## Controls and errors

- Extension popup: start, stop, model selection, detailed settings, and status.
- In-video controls: pause/resume and stop.
- If the local service is unavailable, show local repair guidance; never silently fall back to cloud processing.
- If latency grows, show measured delay and ask before switching to a smaller model.
- If a second tab requests translation, ask the user to stop the existing session.

## Privacy and storage

- Audio and subtitle content remain in memory unless the user explicitly exports subtitles.
- No product telemetry is transmitted.
- Local diagnostic logs may contain performance and error metadata, but not captured audio or subtitle text.
- Users can manually export SRT, WebVTT, or TXT.
- Downloaded models are stored under `%LOCALAPPDATA%\LiveTranslateSubtitles\models` by default.
- The settings UI shows model size and supports delete and redownload.

## Acceptance criteria

- Chrome and Firefox can start translation for a selected tab.
- English, Japanese, and Korean input can be detected and translated into Traditional Chinese.
- Typical subtitle delay remains between two and four seconds under ordinary speech on the reference machine.
- A 30-minute session does not continually accumulate delay.
- Fullscreen, pause, resume, and stop work correctly.
- After model download, the full translation workflow works without internet access.
- Audio and subtitle text are not written to disk unless the user exports them.
- SRT, WebVTT, and TXT exports are valid.

For the alpha, Chrome is the release gate. Firefox should remain functionally equivalent, while browser-specific compatibility fixes may follow shortly afterward.

