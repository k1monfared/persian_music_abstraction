"""Melodic contour extraction (spec section 6.2).

The contour of a melody P is the sign sequence of consecutive differences:

    C(P) = (sign(qt(d2)-qt(d1)), sign(qt(d3)-qt(d2)), ...)

Where sign in {-1, 0, +1}. This abstracts the shape of the phrase
independently of interval size.
"""

from __future__ import annotations

from ..core.types import Maayeh, Goosheh


def melodic_contour(
    maayeh: Maayeh,
    goosheh: Goosheh,
) -> tuple[int, ...]:
    """Extract the melodic contour as a tuple of -1, 0, +1.

    Returns empty tuple if no melody is defined.
    """
    if not goosheh.has_melody or goosheh.melody is None:
        return ()

    melody = goosheh.melody
    if len(melody) < 2:
        return ()

    result: list[int] = []
    for i in range(len(melody) - 1):
        qt_a = maayeh.degree_to_qt(melody[i])
        qt_b = maayeh.degree_to_qt(melody[i + 1])
        diff = qt_b - qt_a
        if diff > 0:
            result.append(1)
        elif diff < 0:
            result.append(-1)
        else:
            result.append(0)

    return tuple(result)


def contour_to_string(contour: tuple[int, ...]) -> str:
    """Convert a contour tuple to a readable string: + - 0."""
    mapping = {1: "+", -1: "-", 0: "0"}
    return " ".join(mapping[c] for c in contour)
