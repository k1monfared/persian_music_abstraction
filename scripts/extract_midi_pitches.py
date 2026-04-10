#!/usr/bin/env python3
"""Extract pitch sets and melodies from MIDI files and update .maayeh files.

Reads each goosheh's MIDI file from the IranianMusicKnowledgeBase,
extracts the actual notes played (including pitch bends for quarter-tones),
and updates the corresponding .maayeh file with:
  - Accurate interval sequence based on actual pitches used
  - Melody (sequence of degrees)
  - Correct ist/shahed mapped to actual degrees
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import mido


# Pitch bend range: +/- 2 semitones = +/- 200 cents = +/- 4 qt
BEND_RANGE_SEMITONES = 2
BEND_RANGE_QT = BEND_RANGE_SEMITONES * 2  # 4 qt


def midi_to_qt(note: int, pitch_bend: int) -> float:
    """Convert MIDI note + pitch bend to quarter-tone position.

    MIDI semitone = 2 qt. Pitch bend range is +/- 2 semitones (+/- 4 qt).
    """
    qt_base = note * 2  # each MIDI semitone = 2 qt
    qt_bend = (pitch_bend / 8192) * BEND_RANGE_QT
    return qt_base + qt_bend


def extract_pitches_from_midi(midi_path: Path) -> tuple[list[int], list[int]]:
    """Extract unique pitch set and melody from a MIDI file.

    Returns:
        (sorted unique qt positions relative to lowest note,
         melody as sequence of qt positions relative to lowest note)
    """
    mid = mido.MidiFile(str(midi_path))

    # Collect all note-on events with their current pitch bend
    raw_events: list[float] = []
    pitch_bend = 0

    for track in mid.tracks:
        pitch_bend = 0
        for msg in track:
            if msg.type == "pitchwheel":
                pitch_bend = msg.pitch
            elif msg.type == "note_on" and msg.velocity > 0:
                qt = midi_to_qt(msg.note, pitch_bend)
                raw_events.append(qt)

    if not raw_events:
        return [], []

    # Round to nearest quarter-tone (integer)
    rounded = [round(q) for q in raw_events]

    # Make relative to lowest note
    min_qt = min(rounded)
    relative = [q - min_qt for q in rounded]

    # Unique sorted pitch set
    pitch_set = sorted(set(relative))

    return pitch_set, relative


def pitch_set_to_intervals(pitch_set: list[int]) -> list[int]:
    """Convert a sorted pitch set to consecutive intervals."""
    if len(pitch_set) < 2:
        return []
    return [pitch_set[i + 1] - pitch_set[i] for i in range(len(pitch_set) - 1)]


def intervals_to_dangs(intervals: list[int]) -> tuple[list[list[int]], list[int]]:
    """Split intervals into dangs + gaps using DP (reuse from convert_radif)."""
    from convert_radif import split_into_dangs
    return split_into_dangs(intervals)


def format_dang_string(dangs: list[list[int]], gaps: list[int]) -> str:
    """Format dangs and gaps into .maayeh interval line."""
    parts = []
    for i, dang in enumerate(dangs):
        parts.append(" ".join(str(iv) for iv in dang))
        if i < len(dangs) - 1:
            gap = gaps[i] if i < len(gaps) else 4
            if gap == 4:
                parts.append("|")
            else:
                parts.append(f"|{gap}|")
    return " ".join(parts)


def melody_to_degrees(melody_qt: list[int], pitch_set: list[int]) -> list[int]:
    """Convert melody qt positions to 1-based degree indices."""
    qt_to_deg = {qt: i + 1 for i, qt in enumerate(pitch_set)}
    return [qt_to_deg.get(qt, 0) for qt in melody_qt if qt in qt_to_deg]


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[''`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def update_maayeh_files(
    json_path: Path,
    midi_base: Path,
    maayeh_dir: Path,
) -> tuple[int, int]:
    """Update .maayeh files with MIDI-extracted pitch data.

    Returns (updated_count, skipped_count).
    """
    with open(json_path) as f:
        data = json.load(f)

    updated = 0
    skipped = 0

    for radif in data["Radifs"]:
        for dastgah in radif["Dastgahs"]:
            dastgah_name = dastgah["Name"]

            for avaz in dastgah["Avazes"]:
                avaz_name = avaz["Name"]

                for gushe in avaz["Gushes"]:
                    gushe_name = gushe["Name"]
                    midi_rel_path = gushe.get("Path", "")

                    file_slug = slugify(f"{dastgah_name}-{avaz_name}-{gushe_name}")
                    maayeh_path = maayeh_dir / f"{file_slug}.maayeh"

                    if not maayeh_path.exists():
                        skipped += 1
                        continue

                    midi_path = midi_base / midi_rel_path
                    if not midi_path.exists():
                        skipped += 1
                        continue

                    # Extract pitches from MIDI
                    pitch_set, melody_qt = extract_pitches_from_midi(midi_path)

                    if len(pitch_set) < 3:
                        skipped += 1
                        continue

                    # Convert to intervals
                    intervals = pitch_set_to_intervals(pitch_set)

                    # Try to split into dangs
                    try:
                        dangs, gaps = intervals_to_dangs(intervals)
                    except Exception:
                        # If dang splitting fails, use raw intervals as one group
                        dangs = [intervals]
                        gaps = []

                    interval_line = format_dang_string(dangs, gaps)

                    # Convert melody to degrees
                    degrees = melody_to_degrees(melody_qt, pitch_set)

                    # Get ist/shahed from JSON
                    temoin = gushe.get("Temoin Note", None)
                    arret = gushe.get("Arret Note", None)

                    # Map original degree numbers to new pitch-set degrees
                    # The original degrees were relative to the dastgah scale,
                    # but now we have a goosheh-specific pitch set.
                    # We keep the original values if they fit, otherwise omit.
                    num_notes = len(pitch_set)

                    # Read existing file to preserve metadata
                    existing = maayeh_path.read_text(encoding="utf-8")
                    lines = existing.strip().splitlines()

                    # Extract metadata lines (before interval line)
                    meta_lines = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped == "--- maayeh ---":
                            meta_lines.append(stripped)
                            continue
                        if re.match(r"^[\d\s|]+$", stripped):
                            break
                        if stripped.startswith("--- goosheh"):
                            break
                        if stripped:
                            meta_lines.append(stripped)

                    # Build updated content
                    new_lines = meta_lines.copy()
                    new_lines.append("")
                    new_lines.append(interval_line)

                    # Goosheh block
                    new_lines.append("")
                    new_lines.append("--- goosheh ---")
                    new_lines.append(f"name: {gushe_name}")
                    if temoin is not None and temoin != 1000 and 1 <= temoin <= num_notes:
                        new_lines.append(f"shahed: {temoin}")
                    if arret is not None and arret != 1000 and 1 <= arret <= num_notes:
                        new_lines.append(f"ist: {arret}")

                    # Add melody (simplified: unique degree sequence, max 50 entries)
                    if degrees:
                        melody_str = " ".join(str(d) for d in degrees[:80])
                        new_lines.append(f"melody: {melody_str}")

                    content = "\n".join(new_lines) + "\n"
                    maayeh_path.write_text(content, encoding="utf-8")
                    updated += 1

    return updated, skipped


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    json_path = project_root / "research" / "iranian-knowledge-base" / "IRMusic_Structure.JSON"
    midi_base = project_root / "research" / "iranian-knowledge-base"
    maayeh_dir = project_root / "data" / "maayehs"

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return

    updated, skipped = update_maayeh_files(json_path, midi_base, maayeh_dir)
    print(f"Updated {updated} .maayeh files with MIDI pitch data")
    print(f"Skipped {skipped} (missing MIDI or too few notes)")


if __name__ == "__main__":
    main()
