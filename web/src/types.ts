/**
 * TypeScript types matching the JSON schema (schema/maayeh.schema.json).
 * These define the contract between the Python build step and the web UI.
 */

export interface MaayehNote {
  degree: number; // 1-based
  qt: number; // quarter-tone position from root
  dang: number; // primary dang index (0-based)
  dangIndices: number[]; // all dang affiliations
  boundary: boolean; // true if at a dang boundary
}

export interface MaayehGoosheh {
  name: string;
  ist: number | null; // degree (1-based)
  shahed: number | null; // degree (1-based)
  melody: number[] | null; // null = all notes touched
  touchedSet: number[]; // sorted unique degrees
}

export interface MaayehMetadata {
  dastgah: string;
  radifs: string[];
  sources: string[];
  tags: string[];
}

export interface SourceInfo {
  name: string;
  shortName: string;
  author: string;
  basedOn: string;
  license: string;
  url: string;
  year: number;
  type: string;
  coverage: string;
  citation: string;
}

export interface SourcesRegistry {
  sources: Record<string, SourceInfo>;
}

export interface MaayehDerived {
  intervalVector: number[];
  rangeQt: number;
}

export interface MaayehData {
  schemaVersion: number;
  name: string;
  metadata: MaayehMetadata;
  dangs: number[][];
  gaps: (number | null)[];
  notes: MaayehNote[];
  gooshehs: MaayehGoosheh[];
  derived: MaayehDerived;
}

export interface MaayehManifest {
  schemaVersion: number;
  maayehs: {
    name: string;
    file: string;
    dastgah: string;
    tags: string[];
    noteCount: number;
    dangCount: number;
  }[];
}
