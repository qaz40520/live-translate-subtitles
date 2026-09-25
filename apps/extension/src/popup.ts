const startButton = document.querySelector<HTMLButtonElement>("#start");
const stopButton = document.querySelector<HTMLButtonElement>("#stop");
const statusElement = document.querySelector<HTMLElement>("#status");

if (!startButton || !stopButton || !statusElement) {
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

stopButton.addEventListener("click", async () => {
  stopButton.disabled = true;
  await chrome.runtime.sendMessage({ type: "ui.stop" });
  statusElement.textContent = "Stopped";
  startButton.disabled = false;
  stopButton.disabled = false;
});

void chrome.runtime.sendMessage({ type: "ui.status" }).then((state) => {
  const active = Boolean(state?.active);
  statusElement.textContent = active ? "Translation is active" : "Ready";
  startButton.disabled = active;
});

export {};
