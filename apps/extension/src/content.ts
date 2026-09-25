const ROOT_ID = "live-translate-subtitles-root";

export function ensureSubtitleRoot(): HTMLElement {
  const existing = document.getElementById(ROOT_ID);
  if (existing) {
    return existing;
  }

  const root = document.createElement("div");
  root.id = ROOT_ID;
  root.setAttribute("aria-live", "polite");
  root.hidden = true;
  document.documentElement.append(root);
  return root;
}

ensureSubtitleRoot();

