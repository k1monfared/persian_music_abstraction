"""Modulation analysis (spec section 6.3).

A modulation from M1 to M2 is defined by a pivot degree: a degree d1 in M1
and degree d2 in M2 such that qt(d1) = qt(d2) (same absolute pitch).

The modulation distance is the number of notes that must change between
the two full note sets when aligned at the pivot.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.types import Maayeh


@dataclass(frozen=True)
class Pivot:
    """A modulation pivot between two maayehs."""
    degree_a: int  # degree in maayeh A
    degree_b: int  # degree in maayeh B
    qt: int        # shared qt position


@dataclass(frozen=True)
class ModulationResult:
    """Result of modulation analysis between two maayehs."""
    pivot: Pivot
    distance: int  # number of differing note positions
    shared_count: int  # number of notes at the same qt in both


def find_pivots(a: Maayeh, b: Maayeh) -> list[Pivot]:
    """Find all possible pivot points between two maayehs.

    A pivot exists at every qt position where both maayehs have a note.
    """
    a_qt_to_deg = {n.qt: n.degree for n in a.notes}
    b_qt_to_deg = {n.qt: n.degree for n in b.notes}

    pivots = []
    for qt in sorted(a_qt_to_deg.keys() & b_qt_to_deg.keys()):
        pivots.append(Pivot(
            degree_a=a_qt_to_deg[qt],
            degree_b=b_qt_to_deg[qt],
            qt=qt,
        ))
    return pivots


def modulation_distance(
    a: Maayeh,
    b: Maayeh,
    pivot: Pivot,
) -> ModulationResult:
    """Compute modulation distance when aligning two maayehs at a pivot.

    Both maayehs are offset so that the pivot qt becomes the shared reference.
    Then we count how many note positions differ.
    """
    offset_a = pivot.qt
    offset_b = pivot.qt

    # Compute qt positions relative to the pivot for each maayeh
    a_qts = {n.qt - offset_a + pivot.qt for n in a.notes}
    b_qts = {n.qt - offset_b + pivot.qt for n in b.notes}

    # Since both are already in absolute qt with the same root reference,
    # and the pivot aligns them, the distance is the symmetric difference size
    shared = a_qts & b_qts
    diff = len((a_qts | b_qts) - shared)

    return ModulationResult(
        pivot=pivot,
        distance=diff,
        shared_count=len(shared),
    )


def best_modulation(a: Maayeh, b: Maayeh) -> ModulationResult | None:
    """Find the modulation with minimum distance between two maayehs.

    Returns None if there are no shared qt positions (no pivot possible).
    """
    pivots = find_pivots(a, b)
    if not pivots:
        return None

    best = None
    for pivot in pivots:
        result = modulation_distance(a, b, pivot)
        if best is None or result.distance < best.distance:
            best = result

    return best
