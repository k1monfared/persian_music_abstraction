/**
 * Main application entry point.
 *
 * Controls: root note, note names toggle, view mode, dark/light theme.
 */

import type { MaayehData, MaayehManifest } from "../types";
import { renderColumn, type ViewMode } from "../viz/maayeh-column";
import { renderPitchAxis } from "../viz/pitch-axis";
import { renderConnectors } from "../viz/connectors";
import { DARK_PALETTE, LIGHT_PALETTE, DEFAULT_LAYOUT, type Palette } from "../viz/palette";
import { ALL_ROOTS, type RootNote } from "../viz/note-names";
import {
  initEditor,
  updateEditorPalette,
  updateEditorRoot,
  clearEditor,
  exportMaayeh,
} from "./grid-editor";
import { initBrowser } from "./database-browser";
import { initDiscovery } from "./discovery-panel";
import { loadSources, initReferences } from "./references-panel";

// Global state
let currentRoot: RootNote = "C";
let currentViewMode: ViewMode = "sparse";
let showNoteNames = true;
let isDark = true;
let allMaayehs: MaayehData[] = [];     // everything from manifest
let loadedMaayehs: MaayehData[] = [];  // currently displayed in strip

function getPalette(): Palette {
  return isDark ? DARK_PALETTE : LIGHT_PALETTE;
}

export function initApp(): void {
  const stripContainer = document.getElementById("strip-container");
  if (!stripContainer) return;

  setupTabs();
  setupRootSelector();
  setupViewModeToggle();
  setupNoteNamesToggle();
  setupThemeToggle();
  setupEditor();

  loadAllMaayehs(stripContainer);
}

// --- Tabs ---

function setupTabs(): void {
  const tabs = document.querySelectorAll<HTMLButtonElement>(".tab[data-tab]");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      const panel = document.getElementById(`tab-${tab.dataset.tab}`);
      panel?.classList.add("active");
    });
  });
}

// --- Controls ---

function setupRootSelector(): void {
  const select = document.getElementById("root-select") as HTMLSelectElement;
  if (!select) return;
  for (const root of ALL_ROOTS) {
    const opt = document.createElement("option");
    opt.value = root;
    opt.textContent = root;
    if (root === currentRoot) opt.selected = true;
    select.appendChild(opt);
  }
  select.addEventListener("change", () => {
    currentRoot = select.value as RootNote;
    rerenderAll();
  });
}

function setupViewModeToggle(): void {
  const buttons = document.querySelectorAll<HTMLButtonElement>("[data-view-mode]");
  buttons.forEach((btn) => {
    if (btn.dataset.viewMode === currentViewMode) btn.classList.add("active");
    btn.addEventListener("click", () => {
      currentViewMode = btn.dataset.viewMode as ViewMode;
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      rerenderAll();
    });
  });
}

function setupNoteNamesToggle(): void {
  const btn = document.getElementById("toggle-names") as HTMLButtonElement;
  if (!btn) return;
  updateNamesButton(btn);
  btn.addEventListener("click", () => {
    showNoteNames = !showNoteNames;
    updateNamesButton(btn);
    rerenderAll();
  });
}

function updateNamesButton(btn: HTMLButtonElement): void {
  btn.classList.toggle("active", showNoteNames);
}

function setupThemeToggle(): void {
  const btn = document.getElementById("toggle-theme") as HTMLButtonElement;
  if (!btn) return;
  btn.addEventListener("click", () => {
    isDark = !isDark;
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    btn.textContent = isDark ? "Light" : "Dark";
    rerenderAll();
  });
}

function setupEditor(): void {
  const gridEl = document.getElementById("editor-grid");
  const textEl = document.getElementById("editor-text");
  const statusEl = document.getElementById("editor-status");
  const clearBtn = document.getElementById("editor-clear");
  const exportBtn = document.getElementById("editor-export");

  if (!gridEl || !textEl || !statusEl) return;

  initEditor(gridEl, textEl, statusEl, getPalette(), currentRoot);

  clearBtn?.addEventListener("click", () => clearEditor());

  exportBtn?.addEventListener("click", () => {
    const text = exportMaayeh();
    if (!text) return;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "custom.maayeh";
    a.click();
    URL.revokeObjectURL(url);
  });
}

function updateStripTitle(maayehs: MaayehData[]): void {
  const titleEl = document.getElementById("strip-title");
  if (!titleEl) return;
  const dastgahs = [...new Set(maayehs.map((m) => m.metadata.dastgah).filter(Boolean))];
  if (dastgahs.length === 1) {
    titleEl.textContent = `Dastgah-e ${dastgahs[0].charAt(0).toUpperCase() + dastgahs[0].slice(1)}`;
  } else {
    titleEl.textContent = `Radif (${maayehs.length} maayehs)`;
  }
}

// --- Rendering ---

function rerenderAll(): void {
  const stripContainer = document.getElementById("strip-container");
  if (stripContainer && loadedMaayehs.length > 0) {
    renderStrip(loadedMaayehs, stripContainer);
  }
  updateEditorPalette(getPalette());
  updateEditorRoot(currentRoot);
}

async function loadAllMaayehs(container: HTMLElement): Promise<void> {
  try {
    const base = import.meta.env.BASE_URL;
    const resp = await fetch(`${base}index.json`);
    if (!resp.ok) return;
    const manifest: MaayehManifest = await resp.json();

    const maayehs: MaayehData[] = [];
    for (const entry of manifest.maayehs) {
      const r = await fetch(`${base}${entry.file}`);
      if (r.ok) maayehs.push(await r.json());
    }

    allMaayehs = maayehs;
    // Start with Mahur as default view (manageable size)
    loadedMaayehs = maayehs.filter((m) => m.metadata.dastgah === "mahur");
    updateStripTitle(loadedMaayehs);
    renderStrip(loadedMaayehs, container);

    // Initialize browser with all maayehs
    const browserEl = document.getElementById("database-browser");
    if (browserEl) {
      initBrowser(browserEl, allMaayehs, {
        onFilterChange: (filtered) => {
          loadedMaayehs = filtered;
          updateStripTitle(filtered);
          renderStrip(loadedMaayehs, container);
        },
        onReorder: (reordered) => {
          loadedMaayehs = reordered;
          renderStrip(loadedMaayehs, container);
        },
      });
    }

    // Initialize discovery with all maayehs
    const discoveryEl = document.getElementById("discovery-panel");
    if (discoveryEl) {
      initDiscovery(discoveryEl, allMaayehs);
    }

    // Load sources and initialize references panel
    await loadSources();
    const refsEl = document.getElementById("references-panel");
    if (refsEl) {
      initReferences(refsEl);
    }
  } catch {
    // Manifest not available
  }
}

function renderStrip(maayehs: MaayehData[], container: HTMLElement): void {
  container.innerHTML = "";

  const maxQt = Math.max(
    ...maayehs.map((m) =>
      m.notes.length > 0 ? m.notes[m.notes.length - 1].qt : 0,
    ),
  );
  const palette = getPalette();

  // Wrapper with relative positioning for background bands
  const stripWrapper = document.createElement("div");
  stripWrapper.className = "strip-wrapper";

  // Render dang background bands spanning full width
  // Use the tallest maayeh's dang ranges as representative
  const tallest = maayehs.reduce((a, b) =>
    (a.notes.length > 0 ? a.notes[a.notes.length - 1].qt : 0) >=
    (b.notes.length > 0 ? b.notes[b.notes.length - 1].qt : 0) ? a : b,
    maayehs[0],
  );
  if (tallest) {
    const layout = DEFAULT_LAYOUT;
    const totalQt = maxQt + layout.headroom;
    const svgH = totalQt * layout.cellHeight + 4;

    // Compute dang ranges
    const dangRanges: { dang: number; minQt: number; maxQt: number }[] = [];
    for (const note of tallest.notes) {
      const existing = dangRanges.find((r) => r.dang === note.dang);
      if (existing) {
        existing.minQt = Math.min(existing.minQt, note.qt);
        existing.maxQt = Math.max(existing.maxQt, note.qt);
      } else {
        dangRanges.push({ dang: note.dang, minQt: note.qt, maxQt: note.qt });
      }
    }

    const bandsContainer = document.createElement("div");
    bandsContainer.className = "strip-bands";
    bandsContainer.style.height = `${svgH}px`;

    for (const range of dangRanges) {
      const col = palette.dangColors[range.dang] ?? palette.dangColors[0];
      const topY = svgH - range.maxQt * layout.cellHeight - layout.cellHeight;
      const botY = svgH - range.minQt * layout.cellHeight + 2;
      const bandH = botY - topY;

      const band = document.createElement("div");
      band.className = "strip-band";
      band.style.top = `${topY}px`;
      band.style.height = `${bandH}px`;
      band.style.backgroundColor = col.fill;
      band.style.opacity = String(palette.dangBandOpacity);
      bandsContainer.appendChild(band);
    }
    stripWrapper.appendChild(bandsContainer);
  }

  // SVG row: pitch axis (always present, visibility toggled) + columns
  const svgRow = document.createElement("div");
  svgRow.className = "strip-svg-row";

  const axis = renderPitchAxis(maayehs, {
    palette,
    rootNote: currentRoot,
    maxQt,
  });
  const axisWrapper = document.createElement("div");
  axisWrapper.className = "pitch-axis-wrapper";
  if (!showNoteNames) axisWrapper.style.visibility = "hidden";
  axisWrapper.appendChild(axis);
  svgRow.appendChild(axisWrapper);

  for (let i = 0; i < maayehs.length; i++) {
    const data = maayehs[i];
    const colDiv = document.createElement("div");
    colDiv.className = "strip-column";
    const svg = renderColumn(data, {
      maxQt,
      palette,
      viewMode: currentViewMode,
      rootNote: currentRoot,
    });
    colDiv.appendChild(svg);
    svgRow.appendChild(colDiv);

    // Connector between this column and the next
    if (i < maayehs.length - 1) {
      const connSvg = renderConnectors(data, maayehs[i + 1], {
        palette,
        maxQt,
      });
      const connDiv = document.createElement("div");
      connDiv.className = "strip-connector";
      connDiv.appendChild(connSvg);
      svgRow.appendChild(connDiv);
    }
  }

  stripWrapper.appendChild(svgRow);
  container.appendChild(stripWrapper);

  // Label row
  const labelRow = document.createElement("div");
  labelRow.className = "strip-label-row";

  const spacer = document.createElement("div");
  spacer.className = "pitch-axis-spacer";
  labelRow.appendChild(spacer);

  for (let i = 0; i < maayehs.length; i++) {
    const label = document.createElement("div");
    label.className = "column-label";
    label.textContent = maayehs[i].name;
    labelRow.appendChild(label);

    // Spacer matching connector width
    if (i < maayehs.length - 1) {
      const connSpacer = document.createElement("div");
      connSpacer.className = "strip-connector-spacer";
      labelRow.appendChild(connSpacer);
    }
  }

  container.appendChild(labelRow);
}
