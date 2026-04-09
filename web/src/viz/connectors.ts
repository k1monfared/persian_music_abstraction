/**
 * Horizontal connectors between adjacent maayeh columns.
 *
 * Draws lines between notes at matching qt positions across two columns,
 * showing shared scale tones.
 */

import type { MaayehData } from "../types";
import type { LayoutConfig, Palette } from "./palette";
import { DEFAULT_LAYOUT } from "./palette";
import { createSvg, svgEl } from "./svg-utils";

export interface ConnectorOptions {
  layout?: LayoutConfig;
  palette?: Palette;
  maxQt?: number;
}

export function renderConnectors(
  left: MaayehData,
  right: MaayehData,
  options: ConnectorOptions = {},
): SVGSVGElement {
  const layout = options.layout ?? DEFAULT_LAYOUT;
  const palette = options.palette;

  const maxQt = options.maxQt ?? Math.max(
    left.notes.length > 0 ? left.notes[left.notes.length - 1].qt : 0,
    right.notes.length > 0 ? right.notes[right.notes.length - 1].qt : 0,
  );
  const totalQt = maxQt + layout.headroom;
  const svgH = totalQt * layout.cellHeight + 4;
  const svgW = 8; // narrow gap between columns

  const svg = createSvg(svgW, svgH);

  // Find shared qt positions
  const leftQts = new Set(left.notes.map((n) => n.qt));
  const rightQts = new Set(right.notes.map((n) => n.qt));

  const connectorColor = palette?.labelDimColor ?? "#555560";

  for (const qt of leftQts) {
    if (!rightQts.has(qt)) continue;
    const y = svgH - qt * layout.cellHeight;
    const cy = y - (layout.cellHeight - 1) + layout.squareSize / 2;

    svgEl("line", {
      x1: 0,
      y1: cy,
      x2: svgW,
      y2: cy,
      stroke: connectorColor,
      "stroke-width": 0.75,
      opacity: 0.5,
    }, svg);
  }

  return svg;
}
