"""Factory functions for constructing domain objects.

These handle the non-trivial construction logic (computing note positions
from dangs and gaps) that doesn't belong in __init__.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .types import Dang, Goosheh, Maayeh, MaayehDefinition, MaayehMetadata, Note


def create_maayeh(
    dangs: Sequence[Dang],
    gaps: Sequence[Optional[int]],
) -> Maayeh:
    """Build a Maayeh from dangs and gaps, computing the full note set.

    The note-building logic follows the spec (section 5.3) and the prototype
    (daramad-mahur.html lines 147-176):
    - First note of each dang: if it would duplicate the previous note's qt
      position (gap=0 boundary), the previous note is reassigned to the new dang
      instead of creating a new note.
    - After the last interval of a non-final dang, the gap is added to qt.
    """
    dangs_tuple = tuple(dangs)
    gaps_tuple = tuple(gaps)

    if len(gaps_tuple) != len(dangs_tuple) - 1:
        raise ValueError(
            f"Expected {len(dangs_tuple) - 1} gaps for {len(dangs_tuple)} dangs, "
            f"got {len(gaps_tuple)}"
        )

    notes: list[Note] = []
    qt = 0

    for di, dang in enumerate(dangs_tuple):
        gap_val = 4 if (di > 0 and gaps_tuple[di - 1] is None) else (
            gaps_tuple[di - 1] if di > 0 else 0
        )

        if di > 0:
            qt += gap_val

        if not notes or notes[-1].qt != qt:
            notes.append(Note(
                degree=len(notes) + 1,
                qt=qt,
                dang=di,
                dang_indices=(di,),
                boundary=False,
            ))
        else:
            prev = notes[-1]
            notes[-1] = Note(
                degree=prev.degree,
                qt=prev.qt,
                dang=di,
                dang_indices=prev.dang_indices + (di,),
                boundary=True,
            )

        for interval in dang.intervals:
            qt += interval
            is_last_interval_of_dang = (
                interval == dang.intervals[-1]
                and dang.intervals.index(interval) == len(dang.intervals) - 1
            )
            notes.append(Note(
                degree=len(notes) + 1,
                qt=qt,
                dang=di,
                dang_indices=(di,),
                boundary=False,
            ))

    return Maayeh(
        dangs=dangs_tuple,
        gaps=gaps_tuple,
        notes=tuple(notes),
    )


def create_definition(
    dangs: Sequence[Dang],
    gaps: Sequence[Optional[int]],
    metadata: MaayehMetadata | None = None,
    gooshehs: Sequence[Goosheh] = (),
) -> MaayehDefinition:
    """Convenience: build a full MaayehDefinition from parts."""
    maayeh = create_maayeh(dangs, gaps)
    return MaayehDefinition(
        maayeh=maayeh,
        metadata=metadata or MaayehMetadata(),
        gooshehs=tuple(gooshehs),
    )
