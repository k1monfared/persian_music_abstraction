"""Interval content computation (spec section 6.1).

The interval content of a maayeh is the multiset of all pairwise intervals
between notes in the touched set:

    IC(M, T) = { |qt(a) - qt(b)| : a,b in T, a != b }

Useful for comparing modal color across maayehs.
"""

from __future__ import annotations

from collections import Counter

from ..core.types import Maayeh, Goosheh


def interval_content(
    maayeh: Maayeh,
    goosheh: Goosheh | None = None,
) -> Counter[int]:
    """Compute the interval content as a Counter of interval sizes.

    If goosheh is provided and has a melody, only touched notes are used.
    Otherwise all notes are used.
    """
    if goosheh is not None:
        touched = maayeh.touched_set_for(goosheh)
    else:
        touched = frozenset(n.degree for n in maayeh.notes)

    qt_values = sorted(
        n.qt for n in maayeh.notes if n.degree in touched
    )

    ic: Counter[int] = Counter()
    for i in range(len(qt_values)):
        for j in range(i + 1, len(qt_values)):
            interval = abs(qt_values[j] - qt_values[i])
            ic[interval] += 1

    return ic


def interval_content_vector(
    maayeh: Maayeh,
    goosheh: Goosheh | None = None,
    max_interval: int | None = None,
) -> list[int]:
    """Interval content as a vector: index = interval size, value = count.

    Useful for comparison and distance computation.
    """
    ic = interval_content(maayeh, goosheh)
    if max_interval is None:
        max_interval = max(ic.keys()) if ic else 0
    return [ic.get(i, 0) for i in range(max_interval + 1)]
