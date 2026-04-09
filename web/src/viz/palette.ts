/**
 * Color and layout configuration for maayeh visualization.
 *
 * Visual approach:
 *   - Dang colors are subtle background bands behind notes
 *   - Notes are neutral (light in dark mode, dark in light mode)
 *   - Active notes: full opacity. Inactive: ~45% opacity.
 *   - Grid: dashed empty squares, very faint.
 */

export interface ColorPair {
  fill: string;
  stroke: string;
}

export interface Palette {
  dangColors: ColorPair[];
  dangBandOpacity: number;
  noteFill: string;
  noteStroke: string;
  roleColors: Record<"ist" | "shahed", ColorPair>;
  roleMarkerColor: string;
  untouchedOpacity: number;
  gridOpacity: number;
  emptyFill: string;
  emptyStroke: string;
  labelColor: string;
  labelDimColor: string;
}

export const DARK_PALETTE: Palette = {
  dangColors: [
    { fill: "#8B5E3C", stroke: "#A67248" }, // dang 0: deep amber
    { fill: "#5C7A4E", stroke: "#74996A" }, // dang 1: muted olive
    { fill: "#3D5A80", stroke: "#5275A0" }, // dang 2: slate blue
    { fill: "#6B4E71", stroke: "#876092" }, // dang 3: dusty purple
  ],
  dangBandOpacity: 0.15,
  noteFill: "#e0dcd6",
  noteStroke: "#a8a4a0",
  roleColors: {
    ist: { fill: "#F0EDE8", stroke: "#FFFFFF" },
    shahed: { fill: "#E8503A", stroke: "#FF6B52" },
  },
  roleMarkerColor: "#333333",
  untouchedOpacity: 0.45,
  gridOpacity: 0.3,
  emptyFill: "transparent",
  emptyStroke: "#555560",
  labelColor: "#c8c0b0",
  labelDimColor: "#605850",
};

export const LIGHT_PALETTE: Palette = {
  dangColors: [
    { fill: "#C8943C", stroke: "#A67832" }, // dang 0: warm amber
    { fill: "#5A8A4A", stroke: "#4A7A3A" }, // dang 1: forest green
    { fill: "#4A72A0", stroke: "#3A6290" }, // dang 2: mid blue
    { fill: "#7A5A80", stroke: "#6A4A70" }, // dang 3: plum
  ],
  dangBandOpacity: 0.12,
  noteFill: "#2a2a2a",
  noteStroke: "#555555",
  roleColors: {
    ist: { fill: "#2C2C2C", stroke: "#000000" },
    shahed: { fill: "#D03020", stroke: "#B02010" },
  },
  roleMarkerColor: "#ffffff",
  untouchedOpacity: 0.45,
  gridOpacity: 0.3,
  emptyFill: "transparent",
  emptyStroke: "#888880",
  labelColor: "#333333",
  labelDimColor: "#999999",
};

export const DEFAULT_PALETTE = DARK_PALETTE;

export interface LayoutConfig {
  cellHeight: number;
  squareSize: number;
  columnWidth: number;
  strokeWidth: number;
  borderRadius: number;
  headroom: number;
}

export const DEFAULT_LAYOUT: LayoutConfig = {
  cellHeight: 14,
  squareSize: 12,
  columnWidth: 40,
  strokeWidth: 1.5,
  borderRadius: 2,
  headroom: 4,
};
