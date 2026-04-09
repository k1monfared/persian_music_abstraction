/**
 * Lightweight browser-side parser for .maayeh text notation.
 * Enables instant preview without the Python build step.
 *
 * This duplicates the Python parser's core logic in TypeScript.
 * It produces the same MaayehData JSON structure.
 */

import type { MaayehData, MaayehGoosheh, MaayehNote } from "./types";

const HEADER_RE = /^---\s*(maayeh|goosheh)\s*---\s*$/i;
const INTERVAL_LINE_RE = /^[\d\s|]+$/;
const EXPLICIT_GAP_RE = /\|(\d+)\|/g;

export function parseMaayehText(text: string): MaayehData {
  const lines = text.trim().split("\n");
  if (lines.length === 0) throw new Error("Empty input");

  let idx = 0;

  // Skip optional --- maayeh --- header
  if (HEADER_RE.test(lines[idx].trim())) {
    const match = lines[idx].trim().match(HEADER_RE);
    if (match && match[1].toLowerCase() === "maayeh") idx++;
  }

  // Parse metadata
  const metadata: Record<string, string> = {};
  while (idx < lines.length) {
    const line = lines[idx].trim();
    if (!line) { idx++; continue; }
    if (INTERVAL_LINE_RE.test(line)) break;
    if (HEADER_RE.test(line)) break;
    if (line.includes(":")) {
      const colon = line.indexOf(":");
      metadata[line.slice(0, colon).trim().toLowerCase()] =
        line.slice(colon + 1).trim();
    }
    idx++;
  }

  // Parse interval line
  if (idx >= lines.length) throw new Error("No interval line found");
  const intervalLine = lines[idx].trim();
  if (!INTERVAL_LINE_RE.test(intervalLine))
    throw new Error(`Expected interval line, got: ${intervalLine}`);
  idx++;

  const { dangs, gaps } = tokenizeIntervalLine(intervalLine);

  // Parse default annotations
  const defaultAnnotations: Record<string, string> = {};
  while (idx < lines.length) {
    const line = lines[idx].trim();
    if (!line) { idx++; continue; }
    if (HEADER_RE.test(line)) break;
    if (line.includes(":")) {
      const colon = line.indexOf(":");
      defaultAnnotations[line.slice(0, colon).trim().toLowerCase()] =
        line.slice(colon + 1).trim();
    }
    idx++;
  }

  // Parse goosheh blocks
  const gooshehBlocks: Record<string, string>[] = [];
  while (idx < lines.length) {
    const line = lines[idx].trim();
    if (HEADER_RE.test(line)) {
      const match = line.match(HEADER_RE);
      if (match && match[1].toLowerCase() === "goosheh") {
        idx++;
        const block: Record<string, string> = {};
        while (idx < lines.length) {
          const gline = lines[idx].trim();
          if (!gline) { idx++; continue; }
          if (HEADER_RE.test(gline)) break;
          if (gline.includes(":")) {
            const colon = gline.indexOf(":");
            block[gline.slice(0, colon).trim().toLowerCase()] =
              gline.slice(colon + 1).trim();
          }
          idx++;
        }
        gooshehBlocks.push(block);
      } else {
        idx++;
      }
    } else {
      idx++;
    }
  }

  // Build notes
  const notes = buildNotes(dangs, gaps);

  // Build gooshehs
  const gooshehs: MaayehGoosheh[] = [];
  if (gooshehBlocks.length > 0) {
    for (const block of gooshehBlocks) {
      gooshehs.push(annotationsToGoosheh(block, notes.length));
    }
  } else if (Object.keys(defaultAnnotations).length > 0) {
    gooshehs.push(annotationsToGoosheh(defaultAnnotations, notes.length));
  }

  // Derived
  const intervalVector: number[] = [];
  for (let i = 0; i < notes.length - 1; i++) {
    intervalVector.push(notes[i + 1].qt - notes[i].qt);
  }
  const rangeQt =
    notes.length > 0 ? notes[notes.length - 1].qt - notes[0].qt : 0;

  return {
    schemaVersion: 1,
    name: metadata["name"] ?? "",
    metadata: {
      dastgah: metadata["dastgah"] ?? "",
      radifs: parseCommaList(metadata["radifs"] ?? ""),
      tags: parseCommaList(metadata["tags"] ?? ""),
    },
    dangs,
    gaps,
    notes,
    gooshehs,
    derived: { intervalVector, rangeQt },
  };
}

function tokenizeIntervalLine(line: string): {
  dangs: number[][];
  gaps: (number | null)[];
} {
  // Two-pass: extract explicit gaps, then split on bare |
  const explicitGaps: Map<number, number> = new Map();
  let gapIdx = 0;

  const processed = line.replace(EXPLICIT_GAP_RE, (_match, digits) => {
    explicitGaps.set(gapIdx, parseInt(digits, 10));
    gapIdx++;
    return "\0";
  });

  const dangs: number[][] = [];
  const gaps: (number | null)[] = [];
  let current = "";
  let overallGapIdx = 0;

  for (const ch of processed) {
    if (ch === "\0") {
      dangs.push(parseInts(current));
      current = "";
      gaps.push(explicitGaps.get(overallGapIdx) ?? null);
      overallGapIdx++;
    } else if (ch === "|") {
      dangs.push(parseInts(current));
      current = "";
      gaps.push(null);
    } else {
      current += ch;
    }
  }
  if (current.trim()) dangs.push(parseInts(current));

  return { dangs, gaps };
}

function parseInts(s: string): number[] {
  return s
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((x) => parseInt(x, 10));
}

function buildNotes(
  dangs: number[][],
  gaps: (number | null)[],
): MaayehNote[] {
  const notes: MaayehNote[] = [];
  let qt = 0;

  for (let di = 0; di < dangs.length; di++) {
    if (di > 0) {
      const gapVal = gaps[di - 1] ?? 4;
      qt += gapVal;
    }

    if (notes.length === 0 || notes[notes.length - 1].qt !== qt) {
      notes.push({
        degree: notes.length + 1,
        qt,
        dang: di,
        dangIndices: [di],
        boundary: false,
      });
    } else {
      const prev = notes[notes.length - 1];
      notes[notes.length - 1] = {
        ...prev,
        dang: di,
        dangIndices: [...prev.dangIndices, di],
        boundary: true,
      };
    }

    for (const interval of dangs[di]) {
      qt += interval;
      notes.push({
        degree: notes.length + 1,
        qt,
        dang: di,
        dangIndices: [di],
        boundary: false,
      });
    }
  }

  return notes;
}

function annotationsToGoosheh(
  annotations: Record<string, string>,
  noteCount: number,
): MaayehGoosheh {
  const ist = annotations["ist"] ? parseInt(annotations["ist"], 10) : null;
  const shahed = annotations["shahed"]
    ? parseInt(annotations["shahed"], 10)
    : null;
  let melody: number[] | null = null;
  if ("melody" in annotations) {
    const melStr = annotations["melody"].trim();
    melody = melStr
      ? melStr.split(/\s+/).map((x) => parseInt(x, 10))
      : [];
  }

  let touchedSet: number[];
  if (melody === null) {
    touchedSet = Array.from({ length: noteCount }, (_, i) => i + 1);
  } else {
    touchedSet = [...new Set(melody)].sort((a, b) => a - b);
  }

  return {
    name: annotations["name"] ?? "",
    ist,
    shahed,
    melody,
    touchedSet,
  };
}

function parseCommaList(s: string): string[] {
  if (!s) return [];
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}
