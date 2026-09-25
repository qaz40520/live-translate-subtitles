import {
  PROTOCOL_VERSION,
  type StartSessionMessage,
} from "@lts/protocol";

const NATIVE_HOST = "com.livetranslatesubtitles.service";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "ui.start") {
    return false;
  }

  void (async () => {
    const [activeTab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (activeTab?.id === undefined) {
      throw new Error("No active browser tab is available");
    }

    await chrome.scripting.executeScript({
      target: { tabId: activeTab.id },
      files: ["content.js"],
    });

    const request: StartSessionMessage = {
      protocolVersion: PROTOCOL_VERSION,
      type: "session.start",
      sessionId: crypto.randomUUID(),
      requestedSourceLanguage: "auto",
      targetLanguage: "zh-TW",
    };

    return chrome.runtime.sendNativeMessage(NATIVE_HOST, request);
  })()
    .then((response) => sendResponse({ ok: true, response }))
    .catch((error: unknown) =>
      sendResponse({
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      }),
    );

  return true;
});
