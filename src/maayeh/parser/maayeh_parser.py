"""Parser and serializer for .maayeh text notation.

Handles the full file format:
  --- maayeh ---
  name: daramad-mahur
  dastgah: mahur
  ...

  4 4 2 | 4 4 2

  --- goosheh ---
  name: daramad
  ist: 1
  shahed: 3
  melody: 1 2 3 4 3 2 1
"""

from __future__ import annotations

import re
from typing import Optional

from ..core.types import Dang, Goosheh, MaayehDefinition, MaayehMetadata
from ..core.factory import create_maayeh
from .tokenizer import tokenize_interval_line, is_interval_line


HEADER_RE = re.compile(r"^---\s*(maayeh|goosheh)\s*---\s*$", re.IGNORECASE)


def parse_maayeh(text: str) -> MaayehDefinition:
    """Parse a single .maayeh file into a MaayehDefinition.

    The format is:
      [--- maayeh ---]          (optional header)
      key: value                (metadata lines)
      <blank line>
      interval line             (digits, pipes)
      [annotation lines]        (ist, shahed, melody for default goosheh)

      [--- goosheh ---]         (repeatable goosheh blocks)
      key: value
    """
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError("Empty input")

    idx = 0

    # Skip optional --- maayeh --- header
    if lines[idx].strip() and HEADER_RE.match(lines[idx].strip()):
        header_match = HEADER_RE.match(lines[idx].strip())
        if header_match and header_match.group(1).lower() == "maayeh":
            idx += 1

    # Parse metadata block (key: value lines before the interval line)
    metadata_dict: dict[str, str] = {}
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        if is_interval_line(line):
            break
        if HEADER_RE.match(line):
            break
        if ":" in line:
            key, _, value = line.partition(":")
            metadata_dict[key.strip().lower()] = value.strip()
        idx += 1

    # Parse interval line
    if idx >= len(lines):
        raise ValueError("No interval line found")

    interval_line = lines[idx].strip()
    if not is_interval_line(interval_line):
        raise ValueError(f"Expected interval line, got: {interval_line!r}")
    idx += 1

    dang_tokens, gap_tokens = tokenize_interval_line(interval_line)

    # Parse annotation lines (before any --- goosheh --- block)
    # These become the default goosheh if no explicit goosheh blocks exist.
    default_annotations: dict[str, str] = {}
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        if HEADER_RE.match(line):
            break
        if ":" in line:
            key, _, value = line.partition(":")
            default_annotations[key.strip().lower()] = value.strip()
        idx += 1

    # Parse goosheh blocks
    goosheh_blocks: list[dict[str, str]] = []
    while idx < len(lines):
        line = lines[idx].strip()
        if HEADER_RE.match(line):
            header_match = HEADER_RE.match(line)
            if header_match and header_match.group(1).lower() == "goosheh":
                idx += 1
                block: dict[str, str] = {}
                while idx < len(lines):
                    gline = lines[idx].strip()
                    if not gline:
                        idx += 1
                        continue
                    if HEADER_RE.match(gline):
                        break
                    if ":" in gline:
                        key, _, value = gline.partition(":")
                        block[key.strip().lower()] = value.strip()
                    idx += 1
                goosheh_blocks.append(block)
            else:
                idx += 1
        else:
            idx += 1

    # Build domain objects
    dangs = tuple(Dang(intervals=dt.intervals) for dt in dang_tokens)
    gaps: tuple[Optional[int], ...] = tuple(gt.value for gt in gap_tokens)

    maayeh = create_maayeh(dangs, gaps)

    # Build metadata
    metadata = MaayehMetadata(
        name=metadata_dict.get("name", ""),
        dastgah=metadata_dict.get("dastgah", ""),
        radifs=_parse_comma_list(metadata_dict.get("radifs", "")),
        sources=_parse_comma_list(metadata_dict.get("sources", "")),
        tags=_parse_comma_list(metadata_dict.get("tags", "")),
    )

    # Build gooshehs
    gooshehs: list[Goosheh] = []

    if goosheh_blocks:
        for block in goosheh_blocks:
            gooshehs.append(_annotations_to_goosheh(block))
    elif default_annotations:
        # No explicit goosheh blocks: treat annotations as a single default goosheh
        gooshehs.append(_annotations_to_goosheh(default_annotations))

    return MaayehDefinition(
        maayeh=maayeh,
        metadata=metadata,
        gooshehs=tuple(gooshehs),
    )


def serialize_maayeh(defn: MaayehDefinition) -> str:
    """Serialize a MaayehDefinition back to .maayeh text notation.

    Produces a lossless round-trip: explicit gaps are written as |N|,
    default gaps as bare |.
    """
    lines: list[str] = []

    lines.append("--- maayeh ---")

    # Metadata
    meta = defn.metadata
    if meta.name:
        lines.append(f"name: {meta.name}")
    if meta.dastgah:
        lines.append(f"dastgah: {meta.dastgah}")
    if meta.radifs:
        lines.append(f"radifs: {', '.join(meta.radifs)}")
    if meta.sources:
        lines.append(f"sources: {', '.join(meta.sources)}")
    if meta.tags:
        lines.append(f"tags: {', '.join(meta.tags)}")

    lines.append("")

    # Interval line
    dang_strs: list[str] = []
    for i, dang in enumerate(defn.maayeh.dangs):
        dang_strs.append(" ".join(str(iv) for iv in dang.intervals))

    # Build the interval line with gaps
    interval_parts: list[str] = [dang_strs[0]]
    for i in range(len(defn.maayeh.gaps)):
        gap = defn.maayeh.gaps[i]
        if gap is None:
            interval_parts.append(f" | {dang_strs[i + 1]}")
        else:
            interval_parts.append(f" |{gap}| {dang_strs[i + 1]}")
    lines.append("".join(interval_parts))

    # Gooshehs
    if len(defn.gooshehs) == 1 and not any(
        HEADER_RE.match(line) for line in lines
        if line.startswith("--- goosheh")
    ):
        # Single goosheh: write as inline annotations (backwards-compatible)
        g = defn.gooshehs[0]
        if g.ist is not None:
            lines.append(f"ist: {g.ist}")
        if g.shahed is not None:
            lines.append(f"shahed: {g.shahed}")
        if g.melody is not None:
            lines.append(f"melody: {' '.join(str(d) for d in g.melody)}")
        if g.name:
            lines.append(f"name: {g.name}")
    else:
        for g in defn.gooshehs:
            lines.append("")
            lines.append("--- goosheh ---")
            if g.name:
                lines.append(f"name: {g.name}")
            if g.ist is not None:
                lines.append(f"ist: {g.ist}")
            if g.shahed is not None:
                lines.append(f"shahed: {g.shahed}")
            if g.melody is not None:
                lines.append(f"melody: {' '.join(str(d) for d in g.melody)}")

    return "\n".join(lines) + "\n"


def parse_bulk(text: str) -> list[MaayehDefinition]:
    """Parse a multi-document file (multiple --- maayeh --- blocks)."""
    # Split on --- maayeh --- headers
    parts = re.split(r"(?=^---\s*maayeh\s*---\s*$)", text.strip(), flags=re.MULTILINE)
    results = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        results.append(parse_maayeh(part))
    return results


def _parse_comma_list(s: str) -> tuple[str, ...]:
    """Parse a comma-separated list, stripping whitespace."""
    if not s:
        return ()
    return tuple(item.strip() for item in s.split(",") if item.strip())


def _annotations_to_goosheh(annotations: dict[str, str]) -> Goosheh:
    """Convert a dict of annotation key-values to a Goosheh."""
    ist = int(annotations["ist"]) if "ist" in annotations else None
    shahed = int(annotations["shahed"]) if "shahed" in annotations else None
    melody = None
    if "melody" in annotations:
        melody_str = annotations["melody"].strip()
        if melody_str:
            melody = tuple(int(x) for x in melody_str.split())
        else:
            melody = ()
    name = annotations.get("name", "")
    return Goosheh(name=name, ist=ist, shahed=shahed, melody=melody)
