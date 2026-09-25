const startButton = document.querySelector<HTMLButtonElement>("#start");
const statusElement = document.querySelector<HTMLElement>("#status");

if (!startButton || !statusElement) {
  throw new Error("Popup controls are missing");
}

startButton.addEventListener("click", async () => {
  startButton.disabled = true;
  statusElement.textContent = "Starting local service…";

  const result = await chrome.runtime.sendMessage({ type: "ui.start" });
  statusElement.textContent = result?.ok
    ? "Local service connected"
    : `Unable to start: ${result?.error ?? "Unknown error"}`;
  startButton.disabled = false;
});

export {};
