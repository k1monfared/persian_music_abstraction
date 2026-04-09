"""Dang catalog and similarity (spec sections 3.2, 6.4).

Enumerates all valid dang interval sequences (length 3-4, sum 9-11).
Identifies modal families: sets of maayehs sharing at least one dang type.
"""

from __future__ import annotations

from itertools import product

from ..core.types import Dang, Maayeh


def enumerate_valid_dangs(
    min_interval: int = 1,
    max_interval: int = 6,
) -> list[Dang]:
    """Enumerate all valid dang interval sequences.

    A dang has 3 or 4 positive integer intervals summing to 9, 10, or 11.
    """
    valid: list[Dang] = []

    for length in (3, 4):
        for intervals in product(
            range(min_interval, max_interval + 1), repeat=length
        ):
            s = sum(intervals)
            if 9 <= s <= 11:
                valid.append(Dang(intervals))

    return valid


def dang_signature(dang: Dang) -> tuple[int, ...]:
    """The canonical signature of a dang (its interval tuple)."""
    return dang.intervals


def are_identical(a: Dang, b: Dang) -> bool:
    """Two dangs are identical if their interval sequences are equal."""
    return a.intervals == b.intervals


def maayeh_dang_set(maayeh: Maayeh) -> frozenset[tuple[int, ...]]:
    """The set of unique dang signatures in a maayeh."""
    return frozenset(dang_signature(d) for d in maayeh.dangs)


def modal_families(
    maayehs: dict[str, Maayeh],
) -> dict[tuple[int, ...], list[str]]:
    """Group maayehs into modal families by shared dang types.

    Returns a dict mapping dang signature to list of maayeh names that use it.
    """
    families: dict[tuple[int, ...], list[str]] = {}
    for name, m in maayehs.items():
        for dang in m.dangs:
            sig = dang_signature(dang)
            families.setdefault(sig, []).append(name)

    # Deduplicate (a maayeh with repeated dangs should appear once per family)
    for sig in families:
        families[sig] = sorted(set(families[sig]))

    return families
