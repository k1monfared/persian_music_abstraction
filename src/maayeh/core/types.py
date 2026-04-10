"""Core domain types for Persian modal structures.

All types are frozen dataclasses (immutable value objects).
Derived quantities are computed properties, not stored fields.
No rendering or I/O concerns belong here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional


# --- Primitives ---

IntervalSequence = tuple[int, ...]
"""An ordered sequence of positive integers representing intervals in quarter-tones."""


@dataclass(frozen=True)
class Dang:
    """A tetrachordal unit: an interval sequence of 3-4 notes spanning ~9-11 qt.

    The dang is the irreducible modal unit in Persian music.
    """

    intervals: IntervalSequence

    def __post_init__(self) -> None:
        if len(self.intervals) < 1:
            raise ValueError("Dang must have at least 1 interval")
        if any(i <= 0 for i in self.intervals):
            raise ValueError(f"All intervals must be positive, got {self.intervals}")

    @property
    def is_canonical(self) -> bool:
        """True if this dang meets the formal constraint: 3-4 intervals, sum 9-11."""
        return (
            3 <= len(self.intervals) <= 4
            and 9 <= sum(self.intervals) <= 11
        )

    @property
    def span(self) -> int:
        return sum(self.intervals)

    @property
    def note_count(self) -> int:
        """Number of notes in this dang (intervals + 1, counting both endpoints)."""
        return len(self.intervals) + 1


@dataclass(frozen=True)
class Note:
    """A single note in a maayeh's full note set.

    Attributes:
        degree: 1-based index in the full note set.
        qt: Absolute position in quarter-tones from the root.
        dang: Primary dang index (0-based). For boundary notes, this is the later dang.
        dang_indices: All dang affiliations. Boundary notes belong to two dangs.
        boundary: True if this note sits at a dang boundary (last of one, first of next).
    """

    degree: int
    qt: int
    dang: int
    dang_indices: tuple[int, ...] = field(default_factory=lambda: ())
    boundary: bool = False

    def __post_init__(self) -> None:
        if not self.dang_indices:
            object.__setattr__(self, "dang_indices", (self.dang,))


@dataclass(frozen=True)
class Goosheh:
    """A behavioral overlay on a maayeh: specific role assignments and melodic profile.

    The spec (section 3.6) says ist and shahed are properties of a goosheh
    within a maayeh, not of the maayeh itself.

    Attributes:
        name: Goosheh name (e.g., "daramad", "kereshmeh").
        ist: Degree of the tonal center (1-based), or None.
        shahed: Degree of the characteristic tone (1-based), or None.
        melody: Sequence of degrees, or None if not provided (all notes touched).
    """

    name: str = ""
    ist: Optional[int] = None
    shahed: Optional[int] = None
    melody: Optional[tuple[int, ...]] = None

    @cached_property
    def touched_set(self) -> frozenset[int]:
        """Set of degrees that appear in the melody.

        If melody is None, returns empty frozenset (caller should treat all as touched).
        """
        if self.melody is None:
            return frozenset()
        return frozenset(self.melody)

    @property
    def has_melody(self) -> bool:
        return self.melody is not None


@dataclass(frozen=True)
class Maayeh:
    """A scale structure: ordered dangs with gaps, producing a full note set.

    This is the pure mathematical/musical object. It knows nothing about
    metadata (name, dastgah, tags) or rendering.

    Attributes:
        dangs: Ordered list of Dang objects.
        gaps: Gaps between consecutive dangs. gaps[i] is the qt distance between
              the last note of dang i and the first note of dang i+1.
              None means "default (4 qt)", an int means "explicitly specified".
        notes: Full ordered note set, computed from dangs and gaps.
    """

    dangs: tuple[Dang, ...]
    gaps: tuple[Optional[int], ...]
    notes: tuple[Note, ...]

    def __post_init__(self) -> None:
        if len(self.gaps) != len(self.dangs) - 1:
            raise ValueError(
                f"Expected {len(self.dangs) - 1} gaps for {len(self.dangs)} dangs, "
                f"got {len(self.gaps)}"
            )

    def gap_value(self, index: int) -> int:
        """Return the actual qt value of a gap (resolving None to 4)."""
        g = self.gaps[index]
        return 4 if g is None else g

    @cached_property
    def interval_vector(self) -> tuple[int, ...]:
        """Consecutive qt differences across all notes."""
        return tuple(
            self.notes[i + 1].qt - self.notes[i].qt
            for i in range(len(self.notes) - 1)
        )

    @property
    def range_qt(self) -> int:
        """Total qt span from first to last note."""
        if not self.notes:
            return 0
        return self.notes[-1].qt - self.notes[0].qt

    def dang_span(self, index: int) -> int:
        return self.dangs[index].span

    def degree_to_qt(self, degree: int) -> int:
        """Convert a 1-based degree to its qt position."""
        return self.notes[degree - 1].qt

    def qt_to_degree(self, qt: int) -> Optional[int]:
        """Reverse lookup: qt position to degree. Returns None if not a note position."""
        for note in self.notes:
            if note.qt == qt:
                return note.degree
        return None

    def touched_set_for(self, goosheh: Goosheh) -> frozenset[int]:
        """Compute the effective touched set for a goosheh.

        If the goosheh has no melody, all notes are touched.
        """
        if not goosheh.has_melody:
            return frozenset(n.degree for n in self.notes)
        return goosheh.touched_set


# --- Storage wrapper (separates domain from metadata) ---


@dataclass(frozen=True)
class MaayehMetadata:
    """Storage and organizational metadata, not part of the musical domain.

    Attributes:
        name: Human-readable name (e.g., "daramad-mahur").
        dastgah: Dastgah name (e.g., "mahur"), or empty string.
        radifs: List of radif names this maayeh belongs to.
        tags: Free-form tags for categorization.
    """

    name: str = ""
    dastgah: str = ""
    radifs: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MaayehDefinition:
    """A complete maayeh file: domain object + metadata + gooshehs.

    This is what the parser produces and the exporter consumes.
    """

    maayeh: Maayeh
    metadata: MaayehMetadata
    gooshehs: tuple[Goosheh, ...] = ()

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def primary_goosheh(self) -> Optional[Goosheh]:
        """The first goosheh, if any."""
        return self.gooshehs[0] if self.gooshehs else None
