/**
 * SVG element creation helpers.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

export function svgEl(
  tag: string,
  attrs: Record<string, string | number>,
  parent?: SVGElement,
): SVGElement {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    el.setAttribute(k, String(v));
  }
  if (parent) parent.appendChild(el);
  return el;
}

export function createSvg(
  width: number,
  height: number,
): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, "svg") as SVGSVGElement;
  svg.setAttribute("width", String(width));
  svg.setAttribute("height", String(height));
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.style.background = "transparent";
  svg.style.display = "block";
  return svg;
}
