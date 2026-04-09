/**
 * Discovery panel: shows valid dang interval sequences not yet in the database.
 *
 * Enumerates all valid dangs (length 3-4, sum 9-11), compares against
 * the dangs used in loaded maayehs, and displays the uncataloged ones.
 */

import type { MaayehData } from "../types";

interface DangInfo {
  intervals: number[];
  span: number;
  inDatabase: boolean;
  usedBy: string[];
}

export function initDiscovery(
  container: HTMLElement,
  maayehs: MaayehData[],
): void {
  const allDangs = enumerateValidDangs();
  const dbDangs = collectDatabaseDangs(maayehs);
  const dangInfos = classifyDangs(allDangs, dbDangs);

  renderDiscovery(container, dangInfos);
}

function enumerateValidDangs(): number[][] {
  const valid: number[][] = [];
  const maxIv = 6;

  // Length 3
  for (let a = 1; a <= maxIv; a++) {
    for (let b = 1; b <= maxIv; b++) {
      for (let c = 1; c <= maxIv; c++) {
        const s = a + b + c;
        if (s >= 9 && s <= 11) valid.push([a, b, c]);
      }
    }
  }

  // Length 4
  for (let a = 1; a <= maxIv; a++) {
    for (let b = 1; b <= maxIv; b++) {
      for (let c = 1; c <= maxIv; c++) {
        for (let d = 1; d <= maxIv; d++) {
          const s = a + b + c + d;
          if (s >= 9 && s <= 11) valid.push([a, b, c, d]);
        }
      }
    }
  }

  return valid;
}

function collectDatabaseDangs(
  maayehs: MaayehData[],
): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const m of maayehs) {
    for (const dang of m.dangs) {
      const key = dang.join(",");
      const existing = map.get(key) ?? [];
      if (!existing.includes(m.name)) existing.push(m.name);
      map.set(key, existing);
    }
  }
  return map;
}

function classifyDangs(
  all: number[][],
  db: Map<string, string[]>,
): DangInfo[] {
  return all.map((intervals) => {
    const key = intervals.join(",");
    const usedBy = db.get(key) ?? [];
    return {
      intervals,
      span: intervals.reduce((a, b) => a + b, 0),
      inDatabase: usedBy.length > 0,
      usedBy,
    };
  });
}

function renderDiscovery(container: HTMLElement, dangs: DangInfo[]): void {
  container.innerHTML = "";

  const cataloged = dangs.filter((d) => d.inDatabase);
  const uncataloged = dangs.filter((d) => !d.inDatabase);

  // Summary
  const summary = document.createElement("div");
  summary.className = "discovery-summary";
  summary.textContent =
    `${dangs.length} valid dangs total · ` +
    `${cataloged.length} in database · ` +
    `${uncataloged.length} uncataloged`;
  container.appendChild(summary);

  // Tabs
  const tabs = document.createElement("div");
  tabs.className = "discovery-tabs";

  const uncatTab = document.createElement("button");
  uncatTab.className = "discovery-tab active";
  uncatTab.textContent = `Uncataloged (${uncataloged.length})`;

  const catTab = document.createElement("button");
  catTab.className = "discovery-tab";
  catTab.textContent = `In Database (${cataloged.length})`;

  const listEl = document.createElement("div");
  listEl.className = "discovery-list";

  uncatTab.addEventListener("click", () => {
    uncatTab.classList.add("active");
    catTab.classList.remove("active");
    renderDangList(listEl, uncataloged);
  });
  catTab.addEventListener("click", () => {
    catTab.classList.add("active");
    uncatTab.classList.remove("active");
    renderDangList(listEl, cataloged);
  });

  tabs.appendChild(uncatTab);
  tabs.appendChild(catTab);
  container.appendChild(tabs);

  renderDangList(listEl, uncataloged);
  container.appendChild(listEl);
}

function renderDangList(container: HTMLElement, dangs: DangInfo[]): void {
  container.innerHTML = "";

  // Group by span
  const bySpan = new Map<number, DangInfo[]>();
  for (const d of dangs) {
    const list = bySpan.get(d.span) ?? [];
    list.push(d);
    bySpan.set(d.span, list);
  }

  for (const span of [9, 10, 11]) {
    const group = bySpan.get(span);
    if (!group || group.length === 0) continue;

    const header = document.createElement("div");
    header.className = "discovery-group-header";
    header.textContent = `Span ${span} qt (${group.length})`;
    container.appendChild(header);

    for (const d of group) {
      const item = document.createElement("div");
      item.className = d.inDatabase ? "discovery-item cataloged" : "discovery-item";

      const notation = document.createElement("span");
      notation.className = "discovery-notation";
      notation.textContent = d.intervals.join(" ");

      const meta = document.createElement("span");
      meta.className = "discovery-meta";
      meta.textContent = d.inDatabase
        ? `used in: ${d.usedBy.join(", ")}`
        : `${d.intervals.length} intervals`;

      item.appendChild(notation);
      item.appendChild(meta);
      container.appendChild(item);
    }
  }
}
