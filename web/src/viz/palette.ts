/**
 * Color and layout configuration for maayeh visualization.
 * Supports dark and light themes.
 *
 * Three visual tiers:
 *   1. Active notes (in melody): solid fill, full opacity
 *   2. Scale notes (in maayeh, not in melody): colored outline, untouchedOpacity
 *   3. Grid positions (empty qt slots): subtle ghost squares, gridOpacity
 */

export interface ColorPair {
  fill: string;
  stroke: string;
}

export interface Palette {
  dangColors: ColorPair[];
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
  roleColors: {
    ist: { fill: "#F0EDE8", stroke: "#FFFFFF" },
    shahed: { fill: "#E8503A", stroke: "#FF6B52" },
  },
  roleMarkerColor: "#FFFFFF",
  untouchedOpacity: 0.25,
  gridOpacity: 0.4,
  emptyFill: "transparent",
  emptyStroke: "#888890",
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
  roleColors: {
    ist: { fill: "#2C2C2C", stroke: "#000000" },
    shahed: { fill: "#D03020", stroke: "#B02010" },
  },
  roleMarkerColor: "#000000",
  untouchedOpacity: 0.22,
  gridOpacity: 0.4,
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
