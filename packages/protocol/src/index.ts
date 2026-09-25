export const PROTOCOL_VERSION = 1 as const;

export type SessionId = string;

export interface StartSessionMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "session.start";
  readonly sessionId: SessionId;
  readonly targetLanguage: "zh-TW";
  readonly requestedSourceLanguage: "auto" | "en" | "ja" | "ko";
  readonly captureMode: "browser" | "system";
}

export interface StopSessionMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "session.stop";
  readonly sessionId: SessionId;
  readonly reason: "user" | "tab-closed" | "capture-error";
}

export interface AudioChunkMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "audio.chunk";
  readonly sessionId: SessionId;
  readonly sequence: number;
  readonly capturedAtMs: number;
  readonly encoding: "pcm-s16le";
  readonly sampleRateHz: 16000;
  readonly channels: 1;
  readonly audioBase64: string;
}

export interface SubtitleUpdateMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "subtitle.update";
  readonly sessionId: SessionId;
  readonly sequence: number;
  readonly segmentId: string;
  readonly sourceLanguage: string;
  readonly sourceText: string;
  readonly translatedSourceText: string;
  readonly translatedText: string;
  readonly startTimeMs: number;
  readonly endTimeMs: number;
  readonly isFinal: boolean;
}

export interface ServiceStatusMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "service.status";
  readonly sessionId?: SessionId;
  readonly status: "starting" | "ready" | "busy" | "stopping";
  readonly queueDelayMs: number;
  readonly activeSttModel?: string;
  readonly activeTranslationModel?: string;
}

export interface ServiceErrorMessage {
  readonly protocolVersion: typeof PROTOCOL_VERSION;
  readonly type: "service.error";
  readonly sessionId?: SessionId;
  readonly code: string;
  readonly message: string;
  readonly recoverable: boolean;
}

export type ExtensionToServiceMessage =
  | StartSessionMessage
  | StopSessionMessage
  | AudioChunkMessage;

export type ServiceToExtensionMessage =
  | SubtitleUpdateMessage
  | ServiceStatusMessage
  | ServiceErrorMessage;

export function hasSupportedProtocolVersion(value: unknown): value is {
  protocolVersion: typeof PROTOCOL_VERSION;
} {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  return (
    "protocolVersion" in value &&
    value.protocolVersion === PROTOCOL_VERSION
  );
}
