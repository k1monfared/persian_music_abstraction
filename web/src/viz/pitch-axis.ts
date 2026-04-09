/**
 * Shared pitch axis rendered to the left of the strip.
 *
 * Shows note names at qt positions where ANY maayeh in the strip has a note.
 */

import type { MaayehData } from "../types";
import type { LayoutConfig, Palette } from "./palette";
import { DEFAULT_LAYOUT } from "./palette";
import { createSvg, svgEl } from "./svg-utils";
import type { RootNote } from "./note-names";
import { getNoteName } from "./note-names";

export interface PitchAxisOptions {
  layout?: LayoutConfig;
  palette?: Palette;
  rootNote?: RootNote;
  maxQt?: number;
}

export function renderPitchAxis(
  maayehs: MaayehData[],
  options: PitchAxisOptions = {},
): SVGSVGElement {
  const layout = options.layout ?? DEFAULT_LAYOUT;
  const root = options.rootNote ?? "C";
  const palette = options.palette;

  // Collect all unique qt positions across all maayehs
  const allQts = new Set<number>();
  for (const m of maayehs) {
    for (const n of m.notes) {
      allQts.add(n.qt);
    }
  }

  const maxQt =
    options.maxQt ??
    Math.max(...maayehs.map((m) =>
      m.notes.length > 0 ? m.notes[m.notes.length - 1].qt : 0,
    ));
  const totalQt = maxQt + layout.headroom;
  const svgH = totalQt * layout.cellHeight + 4;
  const svgW = 44;

  const svg = createSvg(svgW, svgH);

  const sortedQts = [...allQts].sort((a, b) => a - b);
  const labelColor = palette?.labelColor ?? "#c8c0b0";

  for (const qt of sortedQts) {
    const y = svgH - qt * layout.cellHeight;
    const noteName = getNoteName(qt, root);

    const textEl = svgEl(
      "text",
      {
        x: svgW - 4,
        y: y - (layout.cellHeight - 1) + layout.squareSize / 2 + 1,
        "text-anchor": "end",
        "dominant-baseline": "middle",
        "font-family": "'Inconsolata', monospace",
        "font-size": "10",
        fill: labelColor,
      },
      svg,
    ) as SVGTextElement;
    textEl.textContent = noteName;
  }

  return svg;
}
