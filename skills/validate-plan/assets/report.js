"use strict";
let closedForPrint = null;
window.addEventListener("beforeprint", () => {
  if (closedForPrint !== null) return;
  closedForPrint = [...document.querySelectorAll("details:not([open])")];
  closedForPrint.forEach(details => { details.open = true; });
});
window.addEventListener("afterprint", () => {
  closedForPrint?.forEach(details => { details.open = false; });
  closedForPrint = null;
});
document.getElementById("print-report").addEventListener("click", () => window.print());
// getElementById, not a selector: phase IDs may contain dots.
document.querySelectorAll("button[data-copy-target]").forEach(copyButton => {
  copyButton.addEventListener("click", async () => {
    const prompt = document.getElementById(copyButton.dataset.copyTarget);
    const status = copyButton.nextElementSibling;
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(prompt.textContent);
      status.textContent = "Prompt copied. Paste it into a fresh session.";
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(prompt);
      selection.removeAllRanges();
      selection.addRange(range);
      prompt.focus();
      status.textContent = "Copy was unavailable. The prompt is selected; press Ctrl+C (or Command+C).";
    }
  });
});
