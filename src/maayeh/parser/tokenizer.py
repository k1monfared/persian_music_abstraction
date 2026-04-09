"""Low-level tokenizer for .maayeh text format.

Handles the two-pass gap syntax: first extracts explicit gaps |N|,
then splits by bare | for default gaps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DangToken:
    """A parsed dang: its interval sequence."""
    intervals: tuple[int, ...]


@dataclass
class GapToken:
    """A gap between dangs. value=None means default (4 qt), int means explicit."""
    value: Optional[int]


# Matches |N| where N is one or more digits (explicit gap).
# Must be checked before splitting on bare |.
EXPLICIT_GAP_RE = re.compile(r"\|(\d+)\|")

# The interval line: only digits, whitespace, pipes, and nothing else.
INTERVAL_LINE_RE = re.compile(r"^[\d\s|]+$")


def tokenize_interval_line(line: str) -> tuple[list[DangToken], list[GapToken]]:
    """Parse an interval line into dang tokens and gap tokens.

    Two-pass approach:
    1. Replace |N| with a placeholder, recording explicit gaps.
    2. Split by bare | to get dang interval strings.

    Returns:
        (dangs, gaps) where len(gaps) == len(dangs) - 1.
    """
    line = line.strip()
    if not line:
        raise ValueError("Empty interval line")

    # Pass 1: extract explicit gaps, replace with sentinel
    explicit_gaps: dict[int, int] = {}
    sentinel = "\x00"
    gap_index = [0]

    def replace_explicit(match: re.Match) -> str:
        idx = gap_index[0]
        explicit_gaps[idx] = int(match.group(1))
        gap_index[0] += 1
        return sentinel

    processed = EXPLICIT_GAP_RE.sub(replace_explicit, line)

    # Pass 2: split by sentinel or bare |
    # Each separator (sentinel or |) is a gap.
    parts: list[str] = []
    gaps: list[GapToken] = []

    # Split on sentinel or |, tracking which separator was used
    current = ""
    overall_gap_idx = 0
    i = 0
    while i < len(processed):
        ch = processed[i]
        if ch == sentinel:
            parts.append(current.strip())
            current = ""
            # This gap was explicitly specified
            gaps.append(GapToken(value=explicit_gaps[overall_gap_idx]))
            overall_gap_idx += 1
            i += 1
        elif ch == "|":
            parts.append(current.strip())
            current = ""
            gaps.append(GapToken(value=None))
            i += 1
        else:
            current += ch
            i += 1
    parts.append(current.strip())

    # Filter empty parts from leading/trailing separators
    # Actually, we should not have leading/trailing separators in well-formed input.
    # But handle gracefully: remove empty leading/trailing parts.
    while parts and not parts[0]:
        parts.pop(0)
        if gaps:
            gaps.pop(0)
    while parts and not parts[-1]:
        parts.pop()
        if gaps:
            gaps.pop()

    if not parts:
        raise ValueError(f"No dang intervals found in: {line!r}")

    # Parse each part into intervals
    dangs: list[DangToken] = []
    for part in parts:
        if not part:
            raise ValueError(f"Empty dang in interval line: {line!r}")
        intervals = tuple(int(x) for x in part.split())
        if not intervals:
            raise ValueError(f"Empty dang in interval line: {line!r}")
        dangs.append(DangToken(intervals=intervals))

    if len(gaps) != len(dangs) - 1:
        raise ValueError(
            f"Expected {len(dangs) - 1} gaps for {len(dangs)} dangs, "
            f"got {len(gaps)} in: {line!r}"
        )

    return dangs, gaps


def is_interval_line(line: str) -> bool:
    """Check if a line looks like an interval line (digits, spaces, pipes only)."""
    stripped = line.strip()
    return bool(stripped) and bool(INTERVAL_LINE_RE.match(stripped))
