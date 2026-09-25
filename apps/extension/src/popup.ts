import {
  loadSubtitleSettings,
  saveSubtitleSettings,
  type SourceLanguage,
  type SubtitleDisplayMode,
  type SubtitlePosition,
  type SubtitleSettings,
} from "./settings";

interface UiStatus {
  readonly active?: boolean;
  readonly serviceStatus?: "starting" | "ready" | "busy" | "stopping";
  readonly queueDelayMs?: number;
  readonly error?: string;
}

function requiredElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) {
    throw new Error(`Popup control is missing: ${selector}`);
  }
  return element;
}

const startButton = requiredElement<HTMLButtonElement>("#start");
const stopButton = requiredElement<HTMLButtonElement>("#stop");
const statusElement = requiredElement<HTMLElement>("#status");
const displayMode = requiredElement<HTMLSelectElement>("#display-mode");
const sourceLanguage = requiredElement<HTMLSelectElement>("#source-language");
const position = requiredElement<HTMLSelectElement>("#position");
const fontSize = requiredElement<HTMLInputElement>("#font-size");
const fontSizeValue = requiredElement<HTMLOutputElement>("#font-size-value");
const backgroundOpacity = requiredElement<HTMLInputElement>("#background-opacity");
const backgroundOpacityValue = requiredElement<HTMLOutputElement>("#background-opacity-value");
const textColor = requiredElement<HTMLInputElement>("#text-color");
let actionError: string | undefined;

function renderSettings(settings: SubtitleSettings): void {
  displayMode.value = settings.displayMode;
  sourceLanguage.value = settings.sourceLanguage;
  position.value = settings.position;
  fontSize.value = String(settings.fontSizePx);
  fontSizeValue.value = `${settings.fontSizePx}px`;
  backgroundOpacity.value = String(Math.round(settings.backgroundOpacity * 100));
  backgroundOpacityValue.value = `${Math.round(settings.backgroundOpacity * 100)}%`;
  textColor.value = settings.textColor;
}

async function persistSettings(): Promise<void> {
  const settings: SubtitleSettings = {
    displayMode: displayMode.value as SubtitleDisplayMode,
    position: position.value as SubtitlePosition,
    fontSizePx: fontSize.valueAsNumber,
    backgroundOpacity: backgroundOpacity.valueAsNumber / 100,
    textColor: textColor.value,
    sourceLanguage: sourceLanguage.value as SourceLanguage,
  };
  renderSettings(settings);
  await saveSubtitleSettings(settings);
}

function renderStatus(state: UiStatus): void {
  const active = Boolean(state.active);
  startButton.disabled = active;
  stopButton.disabled = !active;

  if (actionError || state.error) {
    statusElement.textContent = `錯誤：${actionError ?? state.error}`;
  } else if (!active) {
    statusElement.textContent = "準備就緒";
  } else if (!state.serviceStatus || state.serviceStatus === "starting") {
    statusElement.textContent = "正在載入本機語音與翻譯模型…";
  } else if (state.serviceStatus === "ready") {
    statusElement.textContent = "模型已就緒，正在等待聲音";
  } else if (state.serviceStatus === "busy") {
    const latency = state.queueDelayMs === undefined ? "" : ` · STT ${state.queueDelayMs} ms`;
    statusElement.textContent = `正在本機辨識與翻譯${latency}`;
  } else {
    statusElement.textContent = "正在停止…";
  }
}

async function refreshStatus(): Promise<void> {
  const state = (await chrome.runtime.sendMessage({ type: "ui.status" })) as UiStatus;
  renderStatus(state);
}

startButton.addEventListener("click", async () => {
  actionError = undefined;
  startButton.disabled = true;
  statusElement.textContent = "正在啟動本機服務…";
  const result = await chrome.runtime.sendMessage({ type: "ui.start" });
  if (!result?.ok) {
    actionError = String(result?.error ?? "未知錯誤");
  }
  await refreshStatus();
});

stopButton.addEventListener("click", async () => {
  actionError = undefined;
  stopButton.disabled = true;
  await chrome.runtime.sendMessage({ type: "ui.stop" });
  await refreshStatus();
});

for (const control of [sourceLanguage, displayMode, position, textColor]) {
  control.addEventListener("change", () => void persistSettings());
}
for (const control of [fontSize, backgroundOpacity]) {
  control.addEventListener("input", () => void persistSettings());
}

void loadSubtitleSettings().then(renderSettings);
void refreshStatus();
setInterval(() => void refreshStatus(), 750);

export {};
