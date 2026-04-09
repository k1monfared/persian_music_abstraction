/**
 * Quarter-tone note name computation.
 *
 * Maps qt positions to Western note names with Persian accidentals
 * (koron = half-flat, sori = half-sharp) given a root note.
 */

export type RootNote = "C" | "D" | "E" | "F" | "G" | "A" | "B";

/** Qt offset from C for each root note. */
const ROOT_OFFSETS: Record<RootNote, number> = {
  C: 0,
  D: 4,
  E: 8,
  F: 10,
  G: 14,
  A: 18,
  B: 22,
};

/**
 * Note names for each of the 24 quarter-tone positions in an octave,
 * starting from C. Index = qt position mod 24.
 */
const QT_NOTE_NAMES: string[] = [
  "C",        // 0
  "Cs",       // 1  C sori (half-sharp)
  "C#",       // 2
  "Dk",       // 3  D koron (half-flat)
  "D",        // 4
  "Ds",       // 5  D sori
  "Eb",       // 6
  "Ek",       // 7  E koron
  "E",        // 8
  "Fk",       // 9  F koron (= E sori)
  "F",        // 10
  "Fs",       // 11 F sori
  "F#",       // 12
  "Gk",       // 13 G koron
  "G",        // 14
  "Gs",       // 15 G sori
  "G#",       // 16
  "Ak",       // 17 A koron
  "A",        // 18
  "As",       // 19 A sori
  "Bb",       // 20
  "Bk",       // 21 B koron
  "B",        // 22
  "Ck",       // 23 C koron (= B sori)
];

/**
 * Format a note name for display.
 * "Ak" -> "A koron", "Bb" -> "B♭", "Fs" -> "F sori", "C" -> "C"
 */
/**
 * Format a raw note name for display.
 *
 * The proper Unicode symbols are U+1D1E9 (sori) and U+1D1EA (koron)
 * but they have near-zero font support. We use reliable fallbacks:
 *   koron (half-flat): lowered b = ♭ with down arrow  -> "Eᵇ" or just "E↓"
 *   sori (half-sharp): raised # = ♯ with up arrow     -> "F↑"
 *
 * Using small arrows: ↓ for koron (pitch lowered), ↑ for sori (pitch raised)
 */
function formatNoteName(raw: string): string {
  if (raw.length === 1) return raw;
  const base = raw[0];
  const acc = raw.slice(1);
  switch (acc) {
    case "b":
      return `${base}\u266D`; // ♭
    case "#":
      return `${base}\u266F`; // ♯
    case "k":
      return `${base}\u1D4F`; // ᵏ superscript k for koron
    case "s":
      return `${base}\u02E2`; // ˢ superscript s for sori
    default:
      return raw;
  }
}

/**
 * Get the note name for a qt position given a root note.
 *
 * @param qt - Absolute qt position from the maayeh root (0, 4, 8, ...)
 * @param root - The root note (which note qt=0 corresponds to)
 * @returns Formatted note name string
 */
export function getNoteName(qt: number, root: RootNote): string {
  const rootOffset = ROOT_OFFSETS[root];
  const absoluteQt = (rootOffset + qt) % 24;
  // Handle negative modulo
  const idx = ((absoluteQt % 24) + 24) % 24;
  return formatNoteName(QT_NOTE_NAMES[idx]);
}

/**
 * Get all note names for a set of qt positions.
 */
export function getNoteNames(
  qtPositions: number[],
  root: RootNote,
): Map<number, string> {
  const result = new Map<number, string>();
  for (const qt of qtPositions) {
    result.set(qt, getNoteName(qt, root));
  }
  return result;
}

export const ALL_ROOTS: RootNote[] = ["C", "D", "E", "F", "G", "A", "B"];
