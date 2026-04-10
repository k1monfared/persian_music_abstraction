#!/usr/bin/env python3
"""Fix ist/shahed mapping in .maayeh files.

The JSON knowledge base stores ist (Arret) and shahed (Temoin) as degree
numbers relative to the dastgah scale. After MIDI extraction, each goosheh
has its own pitch set with different degree numbering. This script maps
the dastgah-level degrees to goosheh-level degrees by matching qt positions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

INTERVAL_QT = {
    "Tanini": 4,
    "Baghie": 2,
    "Mojannab": 3,
    "Tanini_plus_Baghie": 6,
}


def dastgah_scale_qt(named_intervals: list[str]) -> list[int]:
    """Build the full dastgah scale as qt positions from root (degree 1 = qt 0)."""
    positions = [0]
    qt = 0
    for name in named_intervals:
        qt += INTERVAL_QT[name]
        positions.append(qt)
    return positions


def extract_goosheh_pitch_set(maayeh_path: Path) -> list[int] | None:
    """Extract the pitch set (as qt intervals) from a .maayeh file's interval line."""
    text = maayeh_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and re.match(r"^[\d\s|]+$", stripped):
            # Parse interval line to get qt positions
            # Remove gap syntax and split
            clean = re.sub(r"\|(\d+)\|", lambda m: f"G{m.group(1)}G", stripped)
            parts = clean.split("|")
            positions = [0]
            qt = 0
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Check for gap marker
                gap_match = re.match(r"G(\d+)G", part)
                if gap_match:
                    qt += int(gap_match.group(1))
                    continue
                tokens = part.split()
                for t in tokens:
                    t = t.strip()
                    if t.startswith("G") and t.endswith("G"):
                        qt += int(t[1:-1])
                    elif t.isdigit():
                        qt += int(t)
                        positions.append(qt)
            return positions
    return None


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[''`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fix_all(json_path: Path, maayeh_dir: Path) -> tuple[int, int]:
    """Fix ist/shahed in all .maayeh files.

    Returns (fixed_count, skipped_count).
    """
    with open(json_path) as f:
        data = json.load(f)

    fixed = 0
    skipped = 0

    for radif in data["Radifs"]:
        for dastgah in radif["Dastgahs"]:
            dastgah_name = dastgah["Name"]

            # Build dastgah scale qt positions
            dastgah_qt = dastgah_scale_qt(dastgah["Dastgah Domain Intervals"])

            for avaz in dastgah["Avazes"]:
                avaz_name = avaz["Name"]

                for gushe in avaz["Gushes"]:
                    gushe_name = gushe["Name"]
                    file_slug = slugify(f"{dastgah_name}-{avaz_name}-{gushe_name}")
                    maayeh_path = maayeh_dir / f"{file_slug}.maayeh"

                    if not maayeh_path.exists():
                        skipped += 1
                        continue

                    temoin = gushe.get("Temoin Note", 1000)
                    arret = gushe.get("Arret Note", 1000)

                    # Get goosheh's pitch set (qt positions)
                    goosheh_qt = extract_goosheh_pitch_set(maayeh_path)
                    if not goosheh_qt:
                        skipped += 1
                        continue

                    # Map dastgah degree to qt position
                    def dastgah_deg_to_qt(deg: int) -> int | None:
                        # Degrees are 1-based, can be negative or 0
                        # Negative means below root, 0 means root itself
                        idx = deg - 1  # convert to 0-based
                        if 0 <= idx < len(dastgah_qt):
                            return dastgah_qt[idx]
                        elif idx < 0:
                            # Below root: mirror
                            return -dastgah_qt[-idx] if -idx < len(dastgah_qt) else None
                        return None

                    # Find which goosheh degree matches that qt position
                    def qt_to_goosheh_deg(target_qt: int) -> int | None:
                        # The goosheh's lowest note is qt=0
                        # The dastgah's degree 1 is qt=0
                        # So we need to find target_qt in goosheh_qt
                        # But goosheh pitches are relative to the goosheh's own root
                        # while dastgah qt are relative to dastgah root
                        # Since all gooshehs start from somewhere within the dastgah,
                        # we need to find the offset.
                        # Actually, the goosheh's qt=0 may not be the dastgah's qt=0.
                        # We need to check all possible alignments.
                        # Simplest: check if target_qt matches any goosheh position directly
                        for i, gqt in enumerate(goosheh_qt):
                            if gqt == target_qt:
                                return i + 1  # 1-based
                        return None

                    # Try to map shahed and ist
                    new_shahed = None
                    new_ist = None

                    if temoin != 1000:
                        shahed_qt = dastgah_deg_to_qt(temoin)
                        if shahed_qt is not None:
                            new_shahed = qt_to_goosheh_deg(shahed_qt)

                    if arret != 1000:
                        ist_qt = dastgah_deg_to_qt(arret)
                        if ist_qt is not None:
                            new_ist = qt_to_goosheh_deg(ist_qt)

                    # Update the file
                    text = maayeh_path.read_text(encoding="utf-8")
                    lines = text.splitlines()

                    new_lines = []
                    in_goosheh = False
                    wrote_shahed = False
                    wrote_ist = False

                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("--- goosheh"):
                            in_goosheh = True
                            new_lines.append(line)
                            continue

                        if in_goosheh:
                            if stripped.startswith("shahed:"):
                                if new_shahed is not None:
                                    new_lines.append(f"shahed: {new_shahed}")
                                    wrote_shahed = True
                                # else: drop the line (unmappable)
                                continue
                            if stripped.startswith("ist:"):
                                if new_ist is not None:
                                    new_lines.append(f"ist: {new_ist}")
                                    wrote_ist = True
                                continue
                            if stripped.startswith("melody:"):
                                # Insert shahed/ist before melody if not yet written
                                if new_shahed is not None and not wrote_shahed:
                                    new_lines.append(f"shahed: {new_shahed}")
                                    wrote_shahed = True
                                if new_ist is not None and not wrote_ist:
                                    new_lines.append(f"ist: {new_ist}")
                                    wrote_ist = True

                        new_lines.append(line)

                    # If we never encountered melody line, append at end
                    if new_shahed is not None and not wrote_shahed:
                        new_lines.append(f"shahed: {new_shahed}")
                    if new_ist is not None and not wrote_ist:
                        new_lines.append(f"ist: {new_ist}")

                    maayeh_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                    fixed += 1

    return fixed, skipped


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    json_path = project_root / "research" / "iranian-knowledge-base" / "IRMusic_Structure.JSON"
    maayeh_dir = project_root / "data" / "maayehs"

    fixed, skipped = fix_all(json_path, maayeh_dir)
    print(f"Fixed {fixed} files, skipped {skipped}")


if __name__ == "__main__":
    main()
