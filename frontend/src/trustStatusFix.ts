function patchTrustStatus() {
  const candidates = Array.from(document.querySelectorAll<HTMLElement>(".overview-main-area *"));
  const status = candidates.find((element) => element.textContent?.trim() === "Local evidence lab");

  if (!status) {
    return;
  }

  status.textContent = "Local processing";
  status.classList.add("local-processing-status");
  status.title = "Evidence is processed locally. Nothing leaves your network.";
  status.setAttribute("aria-label", "Local processing. Evidence stays on this device.");
}

patchTrustStatus();

const trustStatusObserver = new MutationObserver(() => patchTrustStatus());
trustStatusObserver.observe(document.body, { childList: true, subtree: true });
