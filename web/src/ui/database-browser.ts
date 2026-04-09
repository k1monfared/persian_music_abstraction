/**
 * Database browser: list, search, and filter maayehs.
 * Provides controls for selecting which maayehs appear in the strip.
 */

import type { MaayehData } from "../types";

export interface BrowserCallbacks {
  onFilterChange: (filtered: MaayehData[]) => void;
  onReorder: (reordered: MaayehData[]) => void;
}

let allMaayehs: MaayehData[] = [];
let displayedMaayehs: MaayehData[] = [];
let callbacks: BrowserCallbacks | null = null;
let containerEl: HTMLElement | null = null;

export function initBrowser(
  container: HTMLElement,
  maayehs: MaayehData[],
  cbs: BrowserCallbacks,
): void {
  allMaayehs = maayehs;
  displayedMaayehs = [...maayehs];
  callbacks = cbs;
  containerEl = container;
  renderBrowser();
}

export function updateBrowserMaayehs(maayehs: MaayehData[]): void {
  allMaayehs = maayehs;
  displayedMaayehs = [...maayehs];
  renderBrowser();
}

function renderBrowser(): void {
  if (!containerEl) return;
  containerEl.innerHTML = "";

  // Search input
  const search = document.createElement("input");
  search.type = "text";
  search.placeholder = "Search by name, dastgah, or tag...";
  search.className = "browser-search";
  search.addEventListener("input", () => {
    filterMaayehs(search.value);
  });
  containerEl.appendChild(search);

  // Dastgah filter chips
  const dastgahs = [...new Set(allMaayehs.map((m) => m.metadata.dastgah).filter(Boolean))];
  if (dastgahs.length > 1) {
    const chipRow = document.createElement("div");
    chipRow.className = "browser-chips";

    const allChip = document.createElement("button");
    allChip.className = "browser-chip active";
    allChip.textContent = "All";
    allChip.addEventListener("click", () => {
      chipRow.querySelectorAll(".browser-chip").forEach((c) => c.classList.remove("active"));
      allChip.classList.add("active");
      filterMaayehs(search.value);
    });
    chipRow.appendChild(allChip);

    for (const d of dastgahs) {
      const chip = document.createElement("button");
      chip.className = "browser-chip";
      chip.textContent = d;
      chip.addEventListener("click", () => {
        chipRow.querySelectorAll(".browser-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        filterMaayehs(search.value, d);
      });
      chipRow.appendChild(chip);
    }
    containerEl.appendChild(chipRow);
  }

  // Maayeh list
  const list = document.createElement("div");
  list.className = "browser-list";
  list.id = "browser-list";
  renderList(list, displayedMaayehs);
  containerEl.appendChild(list);

  // Radif export
  const exportRow = document.createElement("div");
  exportRow.className = "browser-actions";
  const exportBtn = document.createElement("button");
  exportBtn.textContent = "Export radif order";
  exportBtn.addEventListener("click", exportRadif);
  exportRow.appendChild(exportBtn);
  containerEl.appendChild(exportRow);
}

function renderList(list: HTMLElement, maayehs: MaayehData[]): void {
  list.innerHTML = "";
  for (let i = 0; i < maayehs.length; i++) {
    const m = maayehs[i];
    const item = document.createElement("div");
    item.className = "browser-item";
    item.draggable = true;
    item.dataset.index = String(i);

    const name = document.createElement("span");
    name.className = "browser-item-name";
    name.textContent = m.name;

    const meta = document.createElement("span");
    meta.className = "browser-item-meta";
    meta.textContent = [
      m.metadata.dastgah,
      `${m.notes.length} notes`,
      `${m.dangs.length} dangs`,
    ].join(" · ");

    item.appendChild(name);
    item.appendChild(meta);

    // Drag and drop for reordering
    item.addEventListener("dragstart", (e) => {
      e.dataTransfer?.setData("text/plain", String(i));
      item.classList.add("dragging");
    });
    item.addEventListener("dragend", () => {
      item.classList.remove("dragging");
    });
    item.addEventListener("dragover", (e) => {
      e.preventDefault();
      item.classList.add("drag-over");
    });
    item.addEventListener("dragleave", () => {
      item.classList.remove("drag-over");
    });
    item.addEventListener("drop", (e) => {
      e.preventDefault();
      item.classList.remove("drag-over");
      const fromIdx = parseInt(e.dataTransfer?.getData("text/plain") ?? "0", 10);
      const toIdx = i;
      if (fromIdx !== toIdx) {
        const moved = displayedMaayehs.splice(fromIdx, 1)[0];
        displayedMaayehs.splice(toIdx, 0, moved);
        const listEl = document.getElementById("browser-list");
        if (listEl) renderList(listEl, displayedMaayehs);
        callbacks?.onReorder(displayedMaayehs);
      }
    });

    list.appendChild(item);
  }
}

function filterMaayehs(query: string, dastgah?: string): void {
  const q = query.toLowerCase().trim();
  displayedMaayehs = allMaayehs.filter((m) => {
    if (dastgah && m.metadata.dastgah !== dastgah) return false;
    if (!q) return true;
    return (
      m.name.toLowerCase().includes(q) ||
      m.metadata.dastgah.toLowerCase().includes(q) ||
      m.metadata.tags.some((t) => t.toLowerCase().includes(q))
    );
  });
  const listEl = document.getElementById("browser-list");
  if (listEl) renderList(listEl, displayedMaayehs);
  callbacks?.onFilterChange(displayedMaayehs);
}

function exportRadif(): void {
  const entries = displayedMaayehs.map((m) => m.name).join("\n");
  const text = `--- radif ---\nname: custom\ndescription: Custom arrangement\n\n${entries}\n`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "custom.radif";
  a.click();
  URL.revokeObjectURL(url);
}
