const TARGET_SAMPLE_RATE = 16000;

interface CaptureState {
  readonly sessionId: string;
  readonly stream: MediaStream;
  readonly captureContext: AudioContext;
  readonly playbackContext: AudioContext;
  readonly worklet: AudioWorkletNode;
}

let captureState: CaptureState | undefined;
let sequence = 0;

function bytesToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const blockSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += blockSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + blockSize));
  }
  return btoa(binary);
}

async function stopCapture(): Promise<void> {
  const state = captureState;
  captureState = undefined;
  if (!state) {
    return;
  }

  state.worklet.disconnect();
  for (const track of state.stream.getTracks()) {
    track.stop();
  }
  await Promise.all([state.captureContext.close(), state.playbackContext.close()]);
}

async function startCapture(sessionId: string, streamId: string): Promise<void> {
  await stopCapture();
  sequence = 0;

  const chromeAudioConstraints = {
    mandatory: {
      chromeMediaSource: "tab",
      chromeMediaSourceId: streamId,
    },
  };
  let stream: MediaStream | undefined;
  let captureContext: AudioContext | undefined;
  let playbackContext: AudioContext | undefined;
  let worklet: AudioWorkletNode | undefined;

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: chromeAudioConstraints as unknown as MediaTrackConstraints,
      video: false,
    });
    captureContext = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
    if (captureContext.sampleRate !== TARGET_SAMPLE_RATE) {
      throw new Error(
        `Browser created a ${captureContext.sampleRate} Hz audio context; 16000 Hz is required`,
      );
    }
    await captureContext.audioWorklet.addModule("audio-worklet.js");

    const captureSource = captureContext.createMediaStreamSource(stream);
    worklet = new AudioWorkletNode(captureContext, "pcm-capture-processor");
    const silentOutput = captureContext.createGain();
    silentOutput.gain.value = 0;
    captureSource.connect(worklet).connect(silentOutput).connect(captureContext.destination);

    playbackContext = new AudioContext();
    playbackContext.createMediaStreamSource(stream).connect(playbackContext.destination);

    worklet.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
      void chrome.runtime.sendMessage({
        type: "capture.audio",
        sessionId,
        sequence,
        capturedAtMs: Date.now(),
        audioBase64: bytesToBase64(event.data),
      });
      sequence += 1;
    };

    captureState = { sessionId, stream, captureContext, playbackContext, worklet };
  } catch (error) {
    worklet?.disconnect();
    for (const track of stream?.getTracks() ?? []) {
      track.stop();
    }
    await Promise.allSettled(
      [captureContext, playbackContext]
        .filter((context): context is AudioContext => context !== undefined)
        .map((context) => context.close()),
    );
    throw error;
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.target !== "offscreen") {
    return false;
  }

  if (message.type === "capture.start") {
    void startCapture(String(message.sessionId), String(message.streamId))
      .then(() => sendResponse({ ok: true }))
      .catch((error: unknown) =>
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        }),
      );
    return true;
  } else if (message.type === "capture.stop") {
    void stopCapture()
      .then(() => sendResponse({ ok: true }))
      .catch((error: unknown) =>
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        }),
      );
    return true;
  }
  return false;
});

export {};
