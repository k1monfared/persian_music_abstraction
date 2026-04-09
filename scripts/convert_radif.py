#!/usr/bin/env python3
"""Convert IranianMusicKnowledgeBase JSON + MIDI into .maayeh files.

Reads IRMusic_Structure.JSON, converts named intervals (Tanini, Baghie,
Mojannab, Tanini_plus_Baghie) to quarter-tones, splits into dangs,
and writes .maayeh files organized by radif/dastgah.

The radif is attributed to Mirza Abdollah as narrated by Dariush Talai
(the transcription source for the MIDI files in the knowledge base).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Interval name to quarter-tone mapping
INTERVAL_QT = {
    "Tanini": 4,              # whole tone (204 cents)
    "Baghie": 2,              # semitone (90 cents)
    "Mojannab": 3,            # neutral second (~150 cents)
    "Tanini_plus_Baghie": 6,  # augmented second (270 cents)
}


def intervals_to_qt(named: list[str]) -> list[int]:
    """Convert named intervals to quarter-tone values."""
    result = []
    for name in named:
        if name not in INTERVAL_QT:
            raise ValueError(f"Unknown interval: {name}")
        result.append(INTERVAL_QT[name])
    return result


def split_into_dangs(intervals: list[int]) -> tuple[list[list[int]], list[int]]:
    """Split a sequence of intervals into dangs + gaps.

    The dastgah domain intervals describe the full scale as a flat list.
    For example, Mahur = [4,4,2, 4, 4,4,2, 4,4,2, 4, 4,4,2].
    The structure is: dang, gap, dang, gap, ... where dangs sum to 9-11
    and gaps are single intervals (typically 2 or 4 qt).

    Strategy: try all possible splits using dynamic programming.
    At each position, try consuming 3 or 4 intervals as a dang (if sum 9-11),
    then 0 or 1 intervals as a gap, and recurse.

    Returns (dangs, gaps) where gaps[i] is the gap after dang[i].
    """
    best = _split_dp(intervals, 0, {})
    if best is None:
        # Fallback: treat entire sequence as one chunk
        return [intervals], []
    return best


def _split_dp(
    intervals: list[int],
    pos: int,
    memo: dict,
) -> tuple[list[list[int]], list[int]] | None:
    """Recursive DP for splitting intervals into dangs + gaps."""
    if pos >= len(intervals):
        return [], []
    if pos in memo:
        return memo[pos]

    best_result = None
    best_dang_count = -1

    # Try dang lengths 3 and 4
    for dang_len in (3, 4):
        if pos + dang_len > len(intervals):
            continue
        dang = intervals[pos:pos + dang_len]
        dang_sum = sum(dang)
        if not (9 <= dang_sum <= 11):
            continue

        # After the dang, try gap of 0 or 1 interval
        for gap_len in (0, 1):
            next_pos = pos + dang_len + gap_len
            if gap_len > 0 and pos + dang_len + gap_len > len(intervals):
                continue

            gap_val = intervals[pos + dang_len] if gap_len == 1 else 0

            rest = _split_dp(intervals, next_pos, memo)
            if rest is not None:
                rest_dangs, rest_gaps = rest
                total_dangs = 1 + len(rest_dangs)
                if total_dangs > best_dang_count:
                    best_dang_count = total_dangs
                    all_dangs = [dang] + rest_dangs
                    all_gaps = ([gap_val] + rest_gaps) if rest_dangs else []
                    best_result = (all_dangs, all_gaps)
            elif next_pos >= len(intervals):
                # This dang consumes everything
                if 1 > best_dang_count:
                    best_dang_count = 1
                    best_result = ([dang], [])

    # Also try: skip this interval as a leading gap (only at start or after another gap)
    # This handles cases where the sequence starts with a gap interval

    memo[pos] = best_result
    return best_result


def format_dang_string(dangs: list[list[int]], gaps: list[int]) -> str:
    """Format dangs and gaps into the .maayeh interval line."""
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


def slugify(name: str) -> str:
    """Convert a name to a filename-safe slug."""
    s = name.lower().strip()
    s = re.sub(r"[''`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def format_gap(gap: int) -> str | None:
    """Format a gap value for the .maayeh notation. Returns None for default (4)."""
    if gap == 4:
        return None  # default
    return str(gap)


def generate_maayeh_files(
    json_path: Path,
    output_base: Path,
) -> int:
    """Generate .maayeh files from the knowledge base JSON."""
    with open(json_path) as f:
        data = json.load(f)

    total = 0

    for radif in data["Radifs"]:
        radif_name = radif["Name"]
        radif_slug = slugify(radif_name)

        for dastgah in radif["Dastgahs"]:
            dastgah_name = dastgah["Name"]
            dastgah_slug = slugify(dastgah_name)

            # Convert dastgah domain intervals to quarter-tones
            domain_intervals = intervals_to_qt(dastgah["Dastgah Domain Intervals"])

            # Split into dangs + gaps
            dangs, gaps = split_into_dangs(domain_intervals)

            # Create output directory
            out_dir = output_base / "maayehs"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Create radif index directory
            radif_dir = output_base / "radifs" / f"{radif_slug}-{dastgah_slug}"
            radif_dir.mkdir(parents=True, exist_ok=True)

            radif_entries: list[str] = []

            for avaz in dastgah["Avazes"]:
                avaz_name = avaz["Name"]
                avaz_temoin = avaz.get("Temoin Note", None)
                avaz_arret = avaz.get("Arret Note", None)

                for gushe in avaz["Gushes"]:
                    gushe_name = gushe["Name"]
                    temoin = gushe.get("Temoin Note", avaz_temoin)
                    arret = gushe.get("Arret Note", avaz_arret)

                    # Build filename
                    file_slug = slugify(f"{dastgah_name}-{avaz_name}-{gushe_name}")

                    # Build tags
                    tags = []
                    if gushe.get("Daramad"):
                        tags.append("daramad")
                    if gushe.get("Forud"):
                        tags.append("forud")
                    if gushe.get("Rhythmic"):
                        tags.append("rhythmic")
                    if gushe.get("Melodic"):
                        tags.append("melodic")
                    if gushe.get("Modgardan"):
                        tags.extend(f"modulation-{slugify(m)}" for m in gushe["Modgardan"])
                    if gushe.get("Repeated in"):
                        tags.extend(f"shared-{slugify(r)}" for r in gushe["Repeated in"])
                    importance = gushe.get("Sadeghi Importance", 0)
                    if importance:
                        tags.append(f"importance-{importance}")

                    # Format the interval line
                    interval_line = format_dang_string(dangs, gaps)

                    # Build .maayeh content
                    lines = ["--- maayeh ---"]
                    lines.append(f"name: {file_slug}")
                    lines.append(f"dastgah: {dastgah_slug}")
                    lines.append(f"radifs: {radif_slug}")
                    lines.append("sources: khalij-knowledgebase")
                    if tags:
                        lines.append(f"tags: {', '.join(tags)}")
                    lines.append("")
                    lines.append(interval_line)

                    # Goosheh block
                    lines.append("")
                    lines.append("--- goosheh ---")
                    lines.append(f"name: {gushe_name}")
                    if temoin is not None and temoin != 1000:
                        lines.append(f"shahed: {temoin}")
                    if arret is not None and arret != 1000:
                        lines.append(f"ist: {arret}")

                    content = "\n".join(lines) + "\n"

                    # Write file
                    out_path = out_dir / f"{file_slug}.maayeh"
                    out_path.write_text(content, encoding="utf-8")
                    radif_entries.append(file_slug)
                    total += 1

            # Write radif index
            radif_lines = ["--- radif ---"]
            radif_lines.append(f"name: {radif_slug}-{dastgah_slug}")
            radif_lines.append(f"description: Radif of {radif_name}, Dastgah-e {dastgah_name} (Talai transcription)")
            radif_lines.append("")
            radif_lines.extend(radif_entries)
            radif_path = radif_dir / "index.radif"
            radif_path.write_text("\n".join(radif_lines) + "\n", encoding="utf-8")

    return total


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    json_path = project_root / "research" / "iranian-knowledge-base" / "IRMusic_Structure.JSON"
    output_base = project_root / "data"

    if not json_path.exists():
        print(f"Error: {json_path} not found")
        return

    count = generate_maayeh_files(json_path, output_base)
    print(f"Generated {count} .maayeh files in {output_base}/maayehs/")
    print(f"Radif indices in {output_base}/radifs/")


if __name__ == "__main__":
    main()
