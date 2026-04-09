"""Parser for .radif index files.

Format:
    --- radif ---
    name: mirza-abdollah
    description: Radif of Mirza Abdollah

    daramad-mahur
    kereshmeh-mahur
    delkash
"""

from __future__ import annotations

import re
from dataclasses import dataclass


HEADER_RE = re.compile(r"^---\s*radif\s*---\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class RadifIndex:
    """Parsed radif index: metadata + ordered list of maayeh names."""

    name: str
    description: str
    entries: tuple[str, ...]


def parse_radif(text: str) -> RadifIndex:
    """Parse a .radif index file."""
    lines = text.strip().splitlines()
    if not lines:
        raise ValueError("Empty radif file")

    idx = 0

    # Skip optional header
    if HEADER_RE.match(lines[idx].strip()):
        idx += 1

    # Parse metadata
    metadata: dict[str, str] = {}
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip().lower()] = value.strip()
            idx += 1
        else:
            break

    # Remaining non-blank lines are maayeh names (one per line)
    entries: list[str] = []
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if not line:
            continue
        entries.append(line)

    return RadifIndex(
        name=metadata.get("name", ""),
        description=metadata.get("description", ""),
        entries=tuple(entries),
    )


def serialize_radif(radif: RadifIndex) -> str:
    """Serialize a RadifIndex back to .radif text."""
    lines: list[str] = ["--- radif ---"]
    if radif.name:
        lines.append(f"name: {radif.name}")
    if radif.description:
        lines.append(f"description: {radif.description}")
    lines.append("")
    for entry in radif.entries:
        lines.append(entry)
    return "\n".join(lines) + "\n"
