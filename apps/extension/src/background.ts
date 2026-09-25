import {
  PROTOCOL_VERSION,
  type AudioChunkMessage,
  type ServiceToExtensionMessage,
  type StartSessionMessage,
  type StopSessionMessage,
} from "@lts/protocol";

const NATIVE_HOST = "com.livetranslatesubtitles.service";
const OFFSCREEN_DOCUMENT_PATH = "offscreen.html";

interface ActiveSession {
  readonly sessionId: string;
  readonly tabId: number;
  readonly nativePort: chrome.runtime.Port;
}

let activeSession: ActiveSession | undefined;
let creatingOffscreenDocument: Promise<void> | undefined;

interface OffscreenResponse {
  readonly ok: boolean;
  readonly error?: string;
}

async function ensureOffscreenDocument(): Promise<void> {
  const offscreenUrl = chrome.runtime.getURL(OFFSCREEN_DOCUMENT_PATH);
  const contexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
    documentUrls: [offscreenUrl],
  });
  if (contexts.length > 0) {
    return;
  }

  creatingOffscreenDocument ??= chrome.offscreen.createDocument({
    url: OFFSCREEN_DOCUMENT_PATH,
    reasons: [chrome.offscreen.Reason.USER_MEDIA],
    justification: "Capture audio from the user-selected tab for local transcription",
  });

  try {
    await creatingOffscreenDocument;
  } finally {
    creatingOffscreenDocument = undefined;
  }
}

function forwardServiceMessage(message: ServiceToExtensionMessage): void {
  if (!activeSession || message.sessionId !== activeSession.sessionId) {
    return;
  }

  void chrome.tabs.sendMessage(activeSession.tabId, message).catch(() => {});
}

async function stopOffscreenCapture(sessionId?: string): Promise<void> {
  const response = (await chrome.runtime.sendMessage({
    type: "capture.stop",
    target: "offscreen",
    sessionId,
  })) as OffscreenResponse | undefined;
  if (response && !response.ok) {
    throw new Error(response.error ?? "Unable to stop tab audio capture");
  }
}

function connectNativeHost(sessionId: string, tabId: number): chrome.runtime.Port {
  const port = chrome.runtime.connectNative(NATIVE_HOST);
  port.onMessage.addListener((message: ServiceToExtensionMessage) => {
    forwardServiceMessage(message);
  });
  port.onDisconnect.addListener(() => {
    if (activeSession?.sessionId !== sessionId) {
      return;
    }

    const error = chrome.runtime.lastError?.message ?? "Local service disconnected";
    void chrome.tabs.sendMessage(tabId, {
      protocolVersion: PROTOCOL_VERSION,
      type: "service.error",
      sessionId,
      code: "native_host_disconnected",
      message: error,
      recoverable: true,
    } satisfies ServiceToExtensionMessage);
    activeSession = undefined;
    void stopOffscreenCapture(sessionId).catch(() => {});
  });
  return port;
}

async function startSession(): Promise<{ sessionId: string }> {
  if (activeSession) {
    throw new Error("A translation session is already active");
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id === undefined) {
    throw new Error("No active browser tab is available");
  }

  await ensureOffscreenDocument();
  // Clear a stream left behind by a crashed native host before requesting a
  // new tab-capture token. The offscreen response resolves after tracks close.
  await stopOffscreenCapture();
  const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"],
  });

  const sessionId = crypto.randomUUID();
  const nativePort = connectNativeHost(sessionId, tab.id);
  activeSession = { sessionId, tabId: tab.id, nativePort };

  try {
    nativePort.postMessage({
      protocolVersion: PROTOCOL_VERSION,
      type: "session.start",
      sessionId,
      requestedSourceLanguage: "auto",
      targetLanguage: "zh-TW",
    } satisfies StartSessionMessage);

    const response = (await chrome.runtime.sendMessage({
      type: "capture.start",
      target: "offscreen",
      sessionId,
      streamId,
    })) as OffscreenResponse | undefined;
    if (!response?.ok) {
      throw new Error(response?.error ?? "Unable to start tab audio capture");
    }
  } catch (error) {
    activeSession = undefined;
    await stopOffscreenCapture(sessionId).catch(() => {});
    try {
      nativePort.postMessage({
        protocolVersion: PROTOCOL_VERSION,
        type: "session.stop",
        sessionId,
        reason: "capture-error",
      } satisfies StopSessionMessage);
    } catch {
      // The native host may already be disconnected.
    }
    nativePort.disconnect();
    await chrome.tabs.sendMessage(tab.id, { type: "overlay.stop" }).catch(() => {});
    throw error;
  }

  return { sessionId };
}

async function stopSession(reason: StopSessionMessage["reason"] = "user"): Promise<void> {
  const session = activeSession;
  if (!session) {
    await ensureOffscreenDocument();
    await stopOffscreenCapture().catch(() => {});
    return;
  }

  activeSession = undefined;
  await stopOffscreenCapture(session.sessionId).catch(() => {});
  try {
    session.nativePort.postMessage({
      protocolVersion: PROTOCOL_VERSION,
      type: "session.stop",
      sessionId: session.sessionId,
      reason,
    } satisfies StopSessionMessage);
  } catch {
    // Cleanup still succeeds when the native host has already disconnected.
  }
  session.nativePort.disconnect();
  await chrome.tabs.sendMessage(session.tabId, { type: "overlay.stop" }).catch(() => {});
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.target === "offscreen") {
    return false;
  }

  if (message?.type === "capture.audio") {
    const session = activeSession;
    if (session && session.sessionId === message.sessionId) {
      session.nativePort.postMessage({
        protocolVersion: PROTOCOL_VERSION,
        type: "audio.chunk",
        sessionId: message.sessionId,
        sequence: message.sequence,
        capturedAtMs: message.capturedAtMs,
        encoding: "pcm-s16le",
        sampleRateHz: 16000,
        channels: 1,
        audioBase64: message.audioBase64,
      } satisfies AudioChunkMessage);
    }
    return false;
  }

  if (message?.type === "capture.error") {
    const session = activeSession;
    if (session && session.sessionId === message.sessionId) {
      void chrome.tabs.sendMessage(session.tabId, {
        protocolVersion: PROTOCOL_VERSION,
        type: "service.error",
        sessionId: session.sessionId,
        code: "capture_error",
        message: String(message.error ?? "Tab audio capture failed"),
        recoverable: true,
      } satisfies ServiceToExtensionMessage);
      void stopSession("capture-error");
    }
    return false;
  }

  if (message?.type === "ui.start") {
    void startSession()
      .then((result) => sendResponse({ ok: true, ...result }))
      .catch((error: unknown) =>
        sendResponse({
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        }),
      );
    return true;
  }

  if (message?.type === "ui.stop") {
    void stopSession().then(() => sendResponse({ ok: true }));
    return true;
  }

  if (message?.type === "ui.status") {
    sendResponse({
      active: activeSession !== undefined,
      sessionId: activeSession?.sessionId,
    });
  }
  return false;
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (activeSession?.tabId === tabId) {
    void stopSession("tab-closed");
  }
});
