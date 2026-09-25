import type { ServiceToExtensionMessage } from "@lts/protocol";
import {
  DEFAULT_SUBTITLE_SETTINGS,
  loadSubtitleSettings,
  normalizeSubtitleSettings,
  SUBTITLE_SETTINGS_KEY,
  type SubtitleSettings,
} from "./settings";

const ROOT_ID = "live-translate-subtitles-root";
const LIVE_SOURCE_ID = "live-translate-subtitles-live-source";
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
    color: DEFAULT_SUBTITLE_SETTINGS.textColor,
    fontFamily: "system-ui, sans-serif",
    fontSize: "24px",
    lineHeight: "1.35",
    textAlign: "center",
    pointerEvents: "none",
  });
  root.hidden = true;

  const liveSource = document.createElement("div");
  liveSource.id = LIVE_SOURCE_ID;
  liveSource.style.opacity = "0.58";
  liveSource.style.fontSize = "0.62em";
  liveSource.style.fontStyle = "italic";

  const source = document.createElement("div");
  source.id = SOURCE_ID;
  source.style.opacity = "0.78";
  source.style.fontSize = "0.72em";

  const translation = document.createElement("div");
  translation.id = TRANSLATION_ID;

  root.append(liveSource, source, translation);
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

type ContentMessage =
  | ServiceToExtensionMessage
  | { type: "overlay.stop" }
  | { type: "overlay.reset" };

function initializeOverlay(): void {
  const root = ensureSubtitleRoot();
  if (root.dataset.liveTranslateInitialized === "true") {
    moveOverlayToFullscreenContainer();
    return;
  }
  root.dataset.liveTranslateInitialized = "true";

  let settings = DEFAULT_SUBTITLE_SETTINGS;
  let confirmedSourceText = "";
  let provisionalSourceText = "";

  function requiredOverlayElement(id: string): HTMLElement {
    const element = root.querySelector<HTMLElement>(`#${id}`);
    if (!element) {
      throw new Error(`Subtitle overlay element is missing: ${id}`);
    }
    return element;
  }
  const liveSource = requiredOverlayElement(LIVE_SOURCE_ID);
  const source = requiredOverlayElement(SOURCE_ID);
  const translation = requiredOverlayElement(TRANSLATION_ID);

  function renderSources(): void {
    const bilingual = settings.displayMode === "bilingual";
    source.textContent = confirmedSourceText;
    source.hidden = !bilingual || !confirmedSourceText;
    liveSource.textContent = provisionalSourceText ? `辨識中：${provisionalSourceText}` : "";
    liveSource.hidden = !bilingual || !provisionalSourceText;
  }

  function applySettings(nextSettings: SubtitleSettings): void {
    settings = nextSettings;
    root.style.fontSize = `${settings.fontSizePx}px`;
    root.style.background = `rgba(0, 0, 0, ${settings.backgroundOpacity})`;
    root.style.color = settings.textColor;
    if (settings.position === "middle") {
      root.style.top = "50%";
      root.style.bottom = "auto";
      root.style.transform = "translate(-50%, -50%)";
    } else {
      root.style.top = "auto";
      root.style.bottom = "10%";
      root.style.transform = "translateX(-50%)";
    }
    renderSources();
  }

  function resetOverlay(): void {
    confirmedSourceText = "";
    provisionalSourceText = "";
    translation.textContent = "";
    renderSources();
    root.hidden = true;
  }

  function getUnconfirmedText(fullText: string): string {
    const current = fullText.trim();
    if (!confirmedSourceText) {
      return current;
    }
    const confirmedAt = current.lastIndexOf(confirmedSourceText);
    if (confirmedAt < 0) {
      return current === confirmedSourceText ? "" : current;
    }
    return current.slice(confirmedAt + confirmedSourceText.length).trim();
  }

  document.addEventListener("fullscreenchange", moveOverlayToFullscreenContainer);
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === "local" && changes[SUBTITLE_SETTINGS_KEY]) {
      applySettings(normalizeSubtitleSettings(changes[SUBTITLE_SETTINGS_KEY].newValue));
    }
  });
  chrome.runtime.onMessage.addListener((message: ContentMessage) => {
    if (message.type === "overlay.stop" || message.type === "overlay.reset") {
      resetOverlay();
      return;
    }

    if (message.type === "subtitle.update") {
      if (message.translatedText) {
        confirmedSourceText = message.translatedSourceText;
        translation.textContent = message.translatedText;
      } else if (!translation.textContent) {
        translation.textContent = "等待完整句子…";
      }
      provisionalSourceText = getUnconfirmedText(message.sourceText);
      renderSources();
      root.style.opacity = message.isFinal ? "1" : "0.88";
      root.hidden = false;
    } else if (message.type === "service.error") {
      provisionalSourceText = "";
      translation.textContent = `錯誤：${message.message}`;
      renderSources();
      root.hidden = false;
    }
  });

  void loadSubtitleSettings().then(applySettings);
  moveOverlayToFullscreenContainer();
}

initializeOverlay();
