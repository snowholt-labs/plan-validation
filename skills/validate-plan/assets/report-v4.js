"use strict";
// Without JavaScript every panel stays visible and the tab bar stays hidden.
const tablist = document.querySelector('[role="tablist"]');
const tabs = tablist ? [...tablist.querySelectorAll('[role="tab"]')] : [];
const panelOf = tab => document.getElementById(tab.getAttribute("aria-controls"));

function activate(tab, focus) {
  tabs.forEach(other => {
    const selected = other === tab;
    other.setAttribute("aria-selected", selected ? "true" : "false");
    other.tabIndex = selected ? 0 : -1;
    panelOf(other).hidden = !selected;
  });
  if (focus) tab.focus();
}

// The hash is only ever an element id, looked up with getElementById: never a selector or HTML.
function targetOf(hash) {
  if (!hash || hash.length < 2) return null;
  try {
    return document.getElementById(decodeURIComponent(hash.slice(1)));
  } catch {
    return null;
  }
}

// Open the tab whose panel holds the target. Returns true when a tab was opened.
function openPanelFor(target) {
  const panel = target?.closest('[role="tabpanel"]');
  const tab = panel && tabs.find(candidate => panelOf(candidate) === panel);
  if (!tab) return false;
  activate(tab, false);
  return true;
}

function route() {
  const target = targetOf(window.location.hash);
  if (openPanelFor(target)) target.scrollIntoView();
}

if (tabs.length) {
  const start = tabs.find(tab => tab.getAttribute("aria-selected") === "true") || tabs[0];
  activate(start, false);
  tablist.hidden = false;
  route();

  // The tab the reader last chose. Hash links switch tabs without changing it, so going Back
  // to the URL without a fragment returns to the tab in use before the link was followed.
  let chosen = start;
  const choose = tab => {
    chosen = tab;
    activate(tab, true);
  };

  tabs.forEach(tab => tab.addEventListener("click", () => choose(tab)));
  tablist.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const index = tabs.indexOf(document.activeElement);
    if (index === -1) return;
    const moves = {
      "ArrowRight": (index + 1) % tabs.length,
      "ArrowLeft": (index - 1 + tabs.length) % tabs.length,
      "Home": 0,
      "End": tabs.length - 1,
    };
    if (!(event.key in moves)) return;
    event.preventDefault();
    choose(tabs[moves[event.key]]);
  });

  // Count cards link to their panel for readers without JavaScript; here they choose the tab instead.
  document.querySelectorAll("[data-open-tab]").forEach(card => {
    card.addEventListener("click", event => {
      const tab = document.getElementById("tab-" + card.dataset.openTab);
      if (!tabs.includes(tab)) return;
      event.preventDefault();
      choose(tab);
    });
  });

  // A link to the hash already in the URL fires no hashchange, so open its panel on click;
  // the browser then scrolls to the now-visible target.
  document.addEventListener("click", event => {
    // A modified or non-primary click opens a new tab or window, so this page's tab stays put.
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest?.('a[href^="#"]');
    if (link) openPanelFor(targetOf(link.getAttribute("href")));
  });
  window.addEventListener("hashchange", () => {
    if (window.location.hash.length < 2) activate(chosen, false);
    else route();
  });
}

// Print shows every panel and opens every details element, then restores them.
// The print button and copy buttons below mirror report.js: fix a bug in both files.
let restoreAfterPrint = null;
window.addEventListener("beforeprint", () => {
  if (restoreAfterPrint !== null) return;
  restoreAfterPrint = {
    details: [...document.querySelectorAll("details:not([open])")],
    panels: [...document.querySelectorAll('[role="tabpanel"][hidden]')],
  };
  restoreAfterPrint.details.forEach(details => { details.open = true; });
  restoreAfterPrint.panels.forEach(panel => { panel.hidden = false; });
});
window.addEventListener("afterprint", () => {
  if (restoreAfterPrint === null) return;
  restoreAfterPrint.details.forEach(details => { details.open = false; });
  restoreAfterPrint.panels.forEach(panel => { panel.hidden = true; });
  restoreAfterPrint = null;
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
