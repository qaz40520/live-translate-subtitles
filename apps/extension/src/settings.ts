export type SubtitleDisplayMode = "translated" | "bilingual";
export type SubtitlePosition = "bottom" | "middle";
export type SourceLanguage = "auto" | "en" | "ja" | "ko";

export interface SubtitleSettings {
  readonly displayMode: SubtitleDisplayMode;
  readonly fontSizePx: number;
  readonly position: SubtitlePosition;
  readonly backgroundOpacity: number;
  readonly textColor: string;
  readonly sourceLanguage: SourceLanguage;
}

export const DEFAULT_SUBTITLE_SETTINGS: SubtitleSettings = {
  displayMode: "bilingual",
  fontSizePx: 24,
  position: "bottom",
  backgroundOpacity: 0.72,
  textColor: "#ffffff",
  sourceLanguage: "ko",
};

export const SUBTITLE_SETTINGS_KEY = "subtitleSettings";

export async function loadSubtitleSettings(): Promise<SubtitleSettings> {
  const stored = await chrome.storage.local.get(SUBTITLE_SETTINGS_KEY);
  return normalizeSubtitleSettings(stored[SUBTITLE_SETTINGS_KEY]);
}

export async function saveSubtitleSettings(settings: SubtitleSettings): Promise<void> {
  await chrome.storage.local.set({ [SUBTITLE_SETTINGS_KEY]: normalizeSubtitleSettings(settings) });
}

export function normalizeSubtitleSettings(value: unknown): SubtitleSettings {
  if (typeof value !== "object" || value === null) {
    return DEFAULT_SUBTITLE_SETTINGS;
  }
  const candidate = value as Partial<SubtitleSettings>;
  return {
    displayMode: candidate.displayMode === "translated" ? "translated" : "bilingual",
    fontSizePx: clampNumber(candidate.fontSizePx, 18, 40, DEFAULT_SUBTITLE_SETTINGS.fontSizePx),
    position: candidate.position === "middle" ? "middle" : "bottom",
    backgroundOpacity: clampNumber(
      candidate.backgroundOpacity,
      0.35,
      0.95,
      DEFAULT_SUBTITLE_SETTINGS.backgroundOpacity,
    ),
    textColor:
      typeof candidate.textColor === "string" && /^#[0-9a-f]{6}$/i.test(candidate.textColor)
        ? candidate.textColor
        : DEFAULT_SUBTITLE_SETTINGS.textColor,
    sourceLanguage:
      candidate.sourceLanguage === "auto" ||
      candidate.sourceLanguage === "en" ||
      candidate.sourceLanguage === "ja"
        ? candidate.sourceLanguage
        : "ko",
  };
}

function clampNumber(value: unknown, minimum: number, maximum: number, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.min(maximum, Math.max(minimum, value))
    : fallback;
}
