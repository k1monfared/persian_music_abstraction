/**
 * Single-column SVG renderer for a maayeh.
 *
 * Supports three display modes:
 *   "sparse"    - gaps between note squares
 *   "grid"      - empty/ghost squares fill every qt position
 *   "stretched" - note squares stretch vertically to fill the gap to the next note
 */

import type { MaayehData, MaayehGoosheh, MaayehNote } from "../types";
import type { ColorPair, LayoutConfig, Palette } from "./palette";
import { DEFAULT_LAYOUT, DEFAULT_PALETTE } from "./palette";
import { createSvg, svgEl } from "./svg-utils";
import type { RootNote } from "./note-names";
import { getNoteName } from "./note-names";

export type ViewMode = "sparse" | "grid" | "stretched";

export interface ColumnOptions {
  palette?: Palette;
  layout?: LayoutConfig;
  gooshehIndex?: number;
  maxQt?: number;
  viewMode?: ViewMode;
  rootNote?: RootNote;
}

export function renderColumn(
  data: MaayehData,
  options: ColumnOptions = {},
): SVGSVGElement {
  const palette = options.palette ?? DEFAULT_PALETTE;
  const layout = options.layout ?? DEFAULT_LAYOUT;
  const gooshehIdx = options.gooshehIndex ?? 0;
  const viewMode = options.viewMode ?? "sparse";
  const root = options.rootNote ?? "C";

  const goosheh: MaayehGoosheh | undefined = data.gooshehs[gooshehIdx];
  const touchedSet = new Set(goosheh?.touchedSet ?? []);
  const hasMelody = goosheh?.melody !== null && goosheh?.melody !== undefined;

  const ownMaxQt =
    data.notes.length > 0 ? data.notes[data.notes.length - 1].qt : 0;
  const totalQt = (options.maxQt ?? ownMaxQt) + layout.headroom;
  const svgH = totalQt * layout.cellHeight + 4;

  const svg = createSvg(layout.columnWidth, svgH);
  const cx = layout.columnWidth / 2;

  // Build a set of note qt positions for quick lookup
  const noteQtSet = new Set(data.notes.map((n) => n.qt));

  // Grid mode: draw ghost squares for every qt position.
  // Colored by the dang they fall within, dashed border, very faint fill.
  if (viewMode === "grid") {
    // Build dang ranges: each dang spans from its first note's qt to its last note's qt
    const dangRanges: { dang: number; minQt: number; maxQt: number }[] = [];
    for (const note of data.notes) {
      const existing = dangRanges.find((r) => r.dang === note.dang);
      if (existing) {
        existing.minQt = Math.min(existing.minQt, note.qt);
        existing.maxQt = Math.max(existing.maxQt, note.qt);
      } else {
        dangRanges.push({ dang: note.dang, minQt: note.qt, maxQt: note.qt });
      }
    }

    const gridOpacity = palette.untouchedOpacity / 2;

    for (let qt = 0; qt <= (options.maxQt ?? ownMaxQt); qt++) {
      if (noteQtSet.has(qt)) continue;
      const y = svgH - qt * layout.cellHeight;

      // Find which dang this qt falls within
      const range = dangRanges.find((r) => qt >= r.minQt && qt <= r.maxQt);
      const dangCol = range
        ? palette.dangColors[range.dang] ?? palette.dangColors[0]
        : null;

      svgEl(
        "rect",
        {
          x: cx - layout.squareSize / 2,
          y: y - (layout.cellHeight - 1),
          width: layout.squareSize,
          height: layout.squareSize,
          fill: dangCol ? dangCol.fill : "transparent",
          stroke: dangCol ? dangCol.stroke : palette.emptyStroke,
          "stroke-width": 1,
          "stroke-dasharray": "2 2",
          rx: layout.borderRadius,
          opacity: gridOpacity,
        },
        svg,
      );
    }
  }

  // Draw notes
  for (let i = 0; i < data.notes.length; i++) {
    const note = data.notes[i];
    const y = svgH - note.qt * layout.cellHeight;
    const col = noteColor(note, palette);
    const isTouched = !hasMelody || touchedSet.has(note.degree);
    const role = noteRole(note, goosheh);

    let rectY: number;
    let rectH: number;

    if (viewMode === "stretched" && i < data.notes.length - 1) {
      const nextQt = data.notes[i + 1].qt;
      const spanPx = (nextQt - note.qt) * layout.cellHeight;
      rectH = Math.max(spanPx - 2, layout.squareSize);
      rectY = y - rectH + layout.squareSize / 2;
    } else {
      rectH = layout.squareSize;
      rectY = y - (layout.cellHeight - 1);
    }

    const fill = col.fill;
    const stroke = col.stroke;
    const strokeWidth = isTouched ? layout.strokeWidth : 1;
    const opacity = isTouched ? 1 : palette.untouchedOpacity;

    const rect = svgEl(
      "rect",
      {
        x: cx - layout.squareSize / 2,
        y: rectY,
        width: layout.squareSize,
        height: rectH,
        fill,
        stroke,
        "stroke-width": strokeWidth,
        rx: layout.borderRadius,
        opacity,
      },
      svg,
    );

    // Role markers: O for ist, X for shahed, centered in the square
    if (role) {
      const markerCx = cx;
      const markerCy = rectY + rectH / 2;
      const markerColor = palette.roleMarkerColor;
      const r = Math.min(layout.squareSize, rectH) * 0.2;

      if (role === "ist") {
        // Circle
        svgEl("circle", {
          cx: markerCx,
          cy: markerCy,
          r,
          fill: "none",
          stroke: markerColor,
          "stroke-width": 1.5,
          opacity,
        }, svg);
      } else {
        // X cross
        svgEl("line", {
          x1: markerCx - r, y1: markerCy - r,
          x2: markerCx + r, y2: markerCy + r,
          stroke: markerColor,
          "stroke-width": 1.5,
          "stroke-linecap": "round",
          opacity,
        }, svg);
        svgEl("line", {
          x1: markerCx + r, y1: markerCy - r,
          x2: markerCx - r, y2: markerCy + r,
          stroke: markerColor,
          "stroke-width": 1.5,
          "stroke-linecap": "round",
          opacity,
        }, svg);
      }
    }

    // Hover tooltip
    const noteName = getNoteName(note.qt, root);
    const title = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "title",
    );
    title.textContent = [
      `${noteName} (degree ${note.degree})`,
      `qt: ${note.qt}`,
      `dang: ${note.dang}`,
      role ? `role: ${role}` : null,
      isTouched ? "active" : "inactive",
    ]
      .filter(Boolean)
      .join("\n");
    rect.appendChild(title);
  }

  return svg;
}

function noteRole(
  note: MaayehNote,
  goosheh?: MaayehGoosheh,
): "ist" | "shahed" | null {
  if (!goosheh) return null;
  if (note.degree === goosheh.ist) return "ist";
  if (note.degree === goosheh.shahed) return "shahed";
  return null;
}

function noteColor(
  note: MaayehNote,
  palette: Palette,
): ColorPair {
  return palette.dangColors[note.dang] ?? palette.dangColors[0];
}
