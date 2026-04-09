"""Topology module: adjacency graph, distance matrix, ordering.

Builds a graph where nodes are maayehs and edges represent connections:
shared dangs, modulation pivots, common tones.

The distance matrix and shared-dang incidence are stored for future
extensions (simplicial complexes, persistent homology, UMAP embeddings).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.types import Maayeh
from .dang_catalog import maayeh_dang_set
from .modulation import best_modulation


@dataclass
class Edge:
    """An edge in the adjacency graph."""
    source: str
    target: str
    shared_dangs: list[tuple[int, ...]]
    modulation_distance: int | None  # None if no pivot exists
    shared_note_count: int


@dataclass
class TopologyGraph:
    """Adjacency graph of maayehs with distance information."""
    nodes: list[str]
    edges: list[Edge]
    distance_matrix: dict[tuple[str, str], int] = field(default_factory=dict)
    shared_dang_incidence: dict[tuple[int, ...], list[str]] = field(default_factory=dict)


def build_topology(maayehs: dict[str, Maayeh]) -> TopologyGraph:
    """Build the full topology graph from a collection of maayehs."""
    names = sorted(maayehs.keys())
    edges: list[Edge] = []
    distance_matrix: dict[tuple[str, str], int] = {}

    # Shared dang incidence
    incidence: dict[tuple[int, ...], list[str]] = {}
    for name, m in maayehs.items():
        for sig in maayeh_dang_set(m):
            incidence.setdefault(sig, []).append(name)
    for sig in incidence:
        incidence[sig] = sorted(set(incidence[sig]))

    # Pairwise analysis
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a_name, b_name = names[i], names[j]
            a, b = maayehs[a_name], maayehs[b_name]

            # Shared dangs
            a_dangs = maayeh_dang_set(a)
            b_dangs = maayeh_dang_set(b)
            shared = sorted(a_dangs & b_dangs)

            # Modulation
            mod = best_modulation(a, b)
            mod_dist = mod.distance if mod else None
            shared_notes = mod.shared_count if mod else 0

            # Only create an edge if there's some connection
            if shared or (mod and mod.shared_count > 0):
                edges.append(Edge(
                    source=a_name,
                    target=b_name,
                    shared_dangs=shared,
                    modulation_distance=mod_dist,
                    shared_note_count=shared_notes,
                ))

            # Distance: use modulation distance if available, else large number
            dist = mod_dist if mod_dist is not None else 999
            distance_matrix[(a_name, b_name)] = dist
            distance_matrix[(b_name, a_name)] = dist

    return TopologyGraph(
        nodes=names,
        edges=edges,
        distance_matrix=distance_matrix,
        shared_dang_incidence=incidence,
    )


def nearest_neighbor_ordering(
    graph: TopologyGraph,
    start: str | None = None,
) -> list[str]:
    """Greedy nearest-neighbor traversal for column ordering.

    Starts from the given node (or the first node) and always visits
    the closest unvisited neighbor.
    """
    if not graph.nodes:
        return []

    start = start or graph.nodes[0]
    visited = [start]
    remaining = set(graph.nodes) - {start}

    while remaining:
        current = visited[-1]
        closest = min(
            remaining,
            key=lambda n: graph.distance_matrix.get((current, n), 999),
        )
        visited.append(closest)
        remaining.remove(closest)

    return visited


def neighbors(graph: TopologyGraph, name: str) -> list[str]:
    """Get all nodes connected to the given node by an edge."""
    result = []
    for edge in graph.edges:
        if edge.source == name:
            result.append(edge.target)
        elif edge.target == name:
            result.append(edge.source)
    return sorted(result)
