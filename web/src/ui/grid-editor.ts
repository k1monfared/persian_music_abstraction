/**
 * Grid editor: click quarter-tone cells to build a maayeh visually.
 *
 * Renders a column of clickable cells spanning 2 octaves (48 qt).
 * Clicking a cell toggles it on/off. The editor infers dang boundaries
 * and shows real-time text notation. Users can export as .maayeh text.
 */

import type { Palette, LayoutConfig } from "../viz/palette";
import { DEFAULT_LAYOUT } from "../viz/palette";
import { createSvg, svgEl } from "../viz/svg-utils";
import type { RootNote } from "../viz/note-names";
import { getNoteName } from "../viz/note-names";

const EDITOR_RANGE = 48; // 2 octaves of quarter-tones

interface EditorState {
  activeQts: Set<number>;
  palette: Palette;
  layout: LayoutConfig;
  rootNote: RootNote;
  container: HTMLElement;
  textEl: HTMLElement;
  statusEl: HTMLElement;
}

let state: EditorState | null = null;

export function initEditor(
  container: HTMLElement,
  textEl: HTMLElement,
  statusEl: HTMLElement,
  palette: Palette,
  rootNote: RootNote,
): void {
  state = {
    activeQts: new Set(),
    palette,
    layout: DEFAULT_LAYOUT,
    rootNote,
    container,
    textEl,
    statusEl,
  };
  renderEditor();
}

export function updateEditorPalette(palette: Palette): void {
  if (!state) return;
  state.palette = palette;
  renderEditor();
}

export function updateEditorRoot(root: RootNote): void {
  if (!state) return;
  state.rootNote = root;
  renderEditor();
}

export function clearEditor(): void {
  if (!state) return;
  state.activeQts.clear();
  renderEditor();
}

export function getEditorNotation(): string {
  if (!state) return "";
  return buildNotation(state.activeQts);
}

function renderEditor(): void {
  if (!state) return;
  const { container, palette, layout, rootNote, activeQts } = state;

  container.innerHTML = "";

  const svgH = EDITOR_RANGE * layout.cellHeight + 4;
  const labelW = 44;
  const colW = layout.columnWidth;
  const svgW = labelW + colW;

  const svg = createSvg(svgW, svgH);
  svg.style.cursor = "pointer";

  const cx = labelW + colW / 2;

  // Draw all cells
  for (let qt = 0; qt < EDITOR_RANGE; qt++) {
    const y = svgH - qt * layout.cellHeight;
    const rectY = y - (layout.cellHeight - 1);
    const isActive = activeQts.has(qt);

    // Determine color: active cells get a dang color based on position
    const dangIndex = inferDangIndex(qt, activeQts);

    if (isActive) {
      const col = palette.dangColors[dangIndex] ?? palette.dangColors[0];
      svgEl("rect", {
        x: cx - layout.squareSize / 2,
        y: rectY,
        width: layout.squareSize,
        height: layout.squareSize,
        fill: col.fill,
        stroke: col.stroke,
        "stroke-width": layout.strokeWidth,
        rx: layout.borderRadius,
      }, svg);
    } else {
      svgEl("rect", {
        x: cx - layout.squareSize / 2,
        y: rectY,
        width: layout.squareSize,
        height: layout.squareSize,
        fill: "transparent",
        stroke: palette.emptyStroke,
        "stroke-width": 1,
        "stroke-dasharray": "2 2",
        rx: layout.borderRadius,
        opacity: palette.gridOpacity,
      }, svg);
    }

    // Clickable overlay (invisible, full cell width)
    const hitArea = svgEl("rect", {
      x: labelW,
      y: rectY,
      width: colW,
      height: layout.cellHeight,
      fill: "transparent",
      cursor: "pointer",
    }, svg);

    const capturedQt = qt;
    hitArea.addEventListener("click", () => {
      if (!state) return;
      if (state.activeQts.has(capturedQt)) {
        state.activeQts.delete(capturedQt);
      } else {
        state.activeQts.add(capturedQt);
      }
      renderEditor();
    });

    // Note label on left
    const noteName = getNoteName(qt, rootNote);
    const textNode = svgEl("text", {
      x: labelW - 4,
      y: rectY + layout.squareSize / 2 + 1,
      "text-anchor": "end",
      "dominant-baseline": "middle",
      "font-family": "'Inconsolata', monospace",
      "font-size": "9",
      fill: isActive ? palette.labelColor : palette.labelDimColor,
      opacity: isActive ? 1 : 0.4,
    }, svg) as SVGTextElement;
    textNode.textContent = noteName;

    // Tooltip
    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = `${noteName} (qt ${qt})`;
    hitArea.appendChild(title);
  }

  container.appendChild(svg);

  // Update notation text
  updateNotation();
}

function inferDangIndex(qt: number, activeQts: Set<number>): number {
  // Simple heuristic: group active notes into dangs of ~10 qt span.
  // Count how many "groups" of active notes exist below this qt.
  const sorted = [...activeQts].sort((a, b) => a - b);
  if (sorted.length === 0) return 0;

  let dangIdx = 0;
  let dangStart = sorted[0];

  for (const q of sorted) {
    if (q === qt) return dangIdx;
    if (q - dangStart > 11) {
      dangIdx++;
      dangStart = q;
    }
  }
  return dangIdx;
}

function buildNotation(activeQts: Set<number>): string {
  const sorted = [...activeQts].sort((a, b) => a - b);
  if (sorted.length < 2) return "";

  // Compute intervals between consecutive active notes
  const intervals: number[] = [];
  for (let i = 1; i < sorted.length; i++) {
    intervals.push(sorted[i] - sorted[i - 1]);
  }

  // Try to split into dangs: groups where the sum is 9-11
  const dangGroups: number[][] = [];
  let current: number[] = [];
  let currentSum = 0;

  for (const iv of intervals) {
    current.push(iv);
    currentSum += iv;

    if (currentSum >= 9 && currentSum <= 11 && current.length >= 3) {
      dangGroups.push([...current]);
      current = [];
      currentSum = 0;
    }
  }

  // If there are leftover intervals, add them as a partial group
  if (current.length > 0) {
    dangGroups.push(current);
  }

  return dangGroups.map(g => g.join(" ")).join(" | ");
}

function updateNotation(): void {
  if (!state) return;

  const notation = buildNotation(state.activeQts);
  state.textEl.textContent = notation || "(click cells to add notes)";

  // Status: note count, span
  const sorted = [...state.activeQts].sort((a, b) => a - b);
  const noteCount = sorted.length;
  const span = noteCount > 1 ? sorted[sorted.length - 1] - sorted[0] : 0;

  const parts: string[] = [`${noteCount} notes`];
  if (span > 0) parts.push(`${span} qt span`);

  // Validate dangs
  const notation_ = buildNotation(state.activeQts);
  const dangParts = notation_.split("|").map(s => s.trim()).filter(Boolean);
  const dangInfo: string[] = [];
  for (const dp of dangParts) {
    const ivs = dp.split(/\s+/).map(Number);
    const sum = ivs.reduce((a, b) => a + b, 0);
    const valid = ivs.length >= 3 && ivs.length <= 4 && sum >= 9 && sum <= 11;
    dangInfo.push(valid ? `dang(${sum}qt)` : `partial(${sum}qt)`);
  }
  if (dangInfo.length > 0) parts.push(dangInfo.join(", "));

  state.statusEl.textContent = parts.join("  ·  ");
}

export function exportMaayeh(): string {
  if (!state) return "";
  const notation = buildNotation(state.activeQts);
  if (!notation) return "";
  return `--- maayeh ---\nname: custom\n\n${notation}\n`;
}
