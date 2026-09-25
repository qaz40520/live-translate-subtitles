import type { ServiceToExtensionMessage } from "@lts/protocol";

const ROOT_ID = "live-translate-subtitles-root";
const SOURCE_ID = "live-translate-subtitles-source";
const TRANSLATION_ID = "live-translate-subtitles-translation";

function ensureSubtitleRoot(): HTMLElement {
  const existing = document.getElementById(ROOT_ID);
  if (existing) {
    return existing;
  }

  const root = document.createElement("section");
  root.id = ROOT_ID;
  root.setAttribute("aria-live", "polite");
  Object.assign(root.style, {
    position: "fixed",
    zIndex: "2147483647",
    left: "50%",
    bottom: "10%",
    transform: "translateX(-50%)",
    width: "min(900px, 90vw)",
    padding: "8px 12px",
    borderRadius: "8px",
    background: "rgba(0, 0, 0, 0.72)",
    color: "white",
    fontFamily: "system-ui, sans-serif",
    fontSize: "24px",
    lineHeight: "1.35",
    textAlign: "center",
    pointerEvents: "none",
  });
  root.hidden = true;

  const source = document.createElement("div");
  source.id = SOURCE_ID;
  source.style.opacity = "0.78";
  source.style.fontSize = "0.72em";

  const translation = document.createElement("div");
  translation.id = TRANSLATION_ID;

  root.append(source, translation);
  document.documentElement.append(root);
  return root;
}

function moveOverlayToFullscreenContainer(): void {
  const root = ensureSubtitleRoot();
  const container = document.fullscreenElement ?? document.documentElement;
  if (root.parentElement !== container) {
    container.append(root);
  }
}

document.addEventListener("fullscreenchange", moveOverlayToFullscreenContainer);

type ContentMessage = ServiceToExtensionMessage | { type: "overlay.stop" };

chrome.runtime.onMessage.addListener((message: ContentMessage) => {
  const root = ensureSubtitleRoot();
  if (message.type === "overlay.stop") {
    root.hidden = true;
    return;
  }

  if (message.type === "subtitle.update") {
    const source = root.querySelector<HTMLElement>(`#${SOURCE_ID}`);
    const translation = root.querySelector<HTMLElement>(`#${TRANSLATION_ID}`);
    if (source && translation) {
      source.textContent = message.sourceText;
      if (message.translatedText) {
        translation.textContent = message.translatedText;
      } else if (!translation.textContent) {
        translation.textContent = "Waiting for a complete sentence…";
      }
      root.style.opacity = message.isFinal ? "1" : "0.82";
      root.hidden = false;
    }
  } else if (message.type === "service.error") {
    const translation = root.querySelector<HTMLElement>(`#${TRANSLATION_ID}`);
    if (translation) {
      translation.textContent = message.message;
      root.hidden = false;
    }
  }
});

moveOverlayToFullscreenContainer();
