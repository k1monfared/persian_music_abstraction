/**
 * References panel: displays all data sources with citations and links.
 * Also loads the sources registry for use by other UI components.
 */

import type { SourcesRegistry, SourceInfo } from "../types";

let sourcesRegistry: SourcesRegistry | null = null;

export async function loadSources(): Promise<SourcesRegistry | null> {
  if (sourcesRegistry) return sourcesRegistry;
  try {
    const resp = await fetch("/sources.json");
    if (!resp.ok) return null;
    sourcesRegistry = await resp.json();
    return sourcesRegistry;
  } catch {
    return null;
  }
}

export function getSourceInfo(sourceId: string): SourceInfo | null {
  if (!sourcesRegistry) return null;
  return sourcesRegistry.sources[sourceId] ?? null;
}

export function getSourceShortName(sourceId: string): string {
  const info = getSourceInfo(sourceId);
  return info?.shortName ?? sourceId;
}

export function formatSourceBadge(sourceIds: string[]): string {
  if (sourceIds.length === 0) return "";
  const totalSources = sourcesRegistry
    ? Object.keys(sourcesRegistry.sources).filter(
        (k) => sourcesRegistry!.sources[k].type === "data",
      ).length
    : 0;
  const dataSources = sourceIds.filter((id) => {
    const info = getSourceInfo(id);
    return info?.type === "data";
  });

  if (totalSources > 0 && dataSources.length === totalSources) {
    return "all sources";
  }
  return sourceIds.map(getSourceShortName).join(", ");
}

export function initReferences(container: HTMLElement): void {
  if (!sourcesRegistry) {
    container.textContent = "Loading sources...";
    return;
  }

  container.innerHTML = "";

  const intro = document.createElement("p");
  intro.className = "references-intro";
  intro.textContent =
    "Data and theoretical foundations used in this project. " +
    "Each maayeh in the database is attributed to its source(s).";
  container.appendChild(intro);

  const entries = Object.entries(sourcesRegistry.sources);

  // Group by type
  const dataEntries = entries.filter(([, s]) => s.type === "data");
  const refEntries = entries.filter(([, s]) => s.type === "reference");

  if (dataEntries.length > 0) {
    renderGroup(container, "Data Sources", dataEntries);
  }
  if (refEntries.length > 0) {
    renderGroup(container, "Theoretical References", refEntries);
  }
}

function renderGroup(
  container: HTMLElement,
  title: string,
  entries: [string, SourceInfo][],
): void {
  const header = document.createElement("h3");
  header.className = "references-group-header";
  header.textContent = title;
  container.appendChild(header);

  for (const [id, source] of entries) {
    const card = document.createElement("div");
    card.className = "reference-card";

    const nameRow = document.createElement("div");
    nameRow.className = "reference-name";
    const link = document.createElement("a");
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = source.name;
    nameRow.appendChild(link);

    const idBadge = document.createElement("span");
    idBadge.className = "reference-id";
    idBadge.textContent = id;
    nameRow.appendChild(idBadge);

    card.appendChild(nameRow);

    const author = document.createElement("div");
    author.className = "reference-author";
    author.textContent = `${source.author} (${source.year})`;
    card.appendChild(author);

    const based = document.createElement("div");
    based.className = "reference-based";
    based.textContent = source.basedOn;
    card.appendChild(based);

    const coverage = document.createElement("div");
    coverage.className = "reference-coverage";
    coverage.textContent = source.coverage;
    card.appendChild(coverage);

    const citation = document.createElement("div");
    citation.className = "reference-citation";
    citation.textContent = source.citation;
    card.appendChild(citation);

    const license = document.createElement("div");
    license.className = "reference-license";
    license.textContent = `License: ${source.license}`;
    card.appendChild(license);

    container.appendChild(card);
  }
}
