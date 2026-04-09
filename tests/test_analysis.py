"""Tests for analysis operations, verifying against spec examples."""

from collections import Counter

from maayeh.core import Dang, Goosheh, create_maayeh
from maayeh.analysis import (
    interval_content,
    melodic_contour,
    contour_to_string,
    find_pivots,
    best_modulation,
    enumerate_valid_dangs,
    modal_families,
    build_topology,
    nearest_neighbor_ordering,
)


def make_mahur():
    """Daramad Mahur: 4 4 2 | 4 4 2 | 4 4 2 | 4 4 2"""
    d = Dang((4, 4, 2))
    return create_maayeh([d, d, d, d], [None, None, None])


def make_shur():
    """Shur: 3 4 3 | 4 3 4"""
    d1 = Dang((3, 4, 3))
    d2 = Dang((4, 3, 4))
    return create_maayeh([d1, d2], [None])


class TestIntervalContent:
    def test_mahur_touched(self):
        m = make_mahur()
        g = Goosheh(ist=1, shahed=3, melody=(1, 2, 3, 4, 3, 2, 3, 5, 3, 2, 1))
        ic = interval_content(m, g)
        # Touched set: {1,2,3,4,5} -> qt positions {0,4,8,10,14}
        # Pairwise intervals: 4,8,10,14, 4,6,10, 2,6, 4
        assert ic[4] == 3   # (0,4), (4,8), (10,14)
        assert ic[8] == 1   # (0,8)
        assert ic[10] == 2  # (0,10), (4,14)
        assert ic[14] == 1  # (0,14)
        assert ic[6] == 2   # (4,10), (8,14)
        assert ic[2] == 1   # (8,10)
        assert sum(ic.values()) == 10  # C(5,2) = 10 pairs

    def test_all_notes(self):
        m = make_mahur()
        ic = interval_content(m)
        # All 16 notes -> C(16,2) = 120 pairs
        assert sum(ic.values()) == 120


class TestMelodicContour:
    def test_mahur_contour(self):
        """Spec example: melody 1 2 3 4 3 2 3 5 3 2 1 -> + + + - - + + - - -"""
        m = make_mahur()
        g = Goosheh(ist=1, shahed=3, melody=(1, 2, 3, 4, 3, 2, 3, 5, 3, 2, 1))
        c = melodic_contour(m, g)
        assert c == (1, 1, 1, -1, -1, 1, 1, -1, -1, -1)
        assert contour_to_string(c) == "+ + + - - + + - - -"

    def test_no_melody(self):
        m = make_mahur()
        g = Goosheh(ist=1, shahed=3)
        c = melodic_contour(m, g)
        assert c == ()


class TestModulation:
    def test_mahur_shur_pivots(self):
        mahur = make_mahur()
        shur = make_shur()
        pivots = find_pivots(mahur, shur)
        # Both have notes at qt=0, qt=10, qt=14
        qt_values = [p.qt for p in pivots]
        assert 0 in qt_values
        assert 10 in qt_values
        assert 14 in qt_values

    def test_mahur_shur_best(self):
        mahur = make_mahur()
        shur = make_shur()
        result = best_modulation(mahur, shur)
        assert result is not None
        assert result.distance >= 0
        assert result.shared_count > 0

    def test_identical_maayehs(self):
        m = make_mahur()
        result = best_modulation(m, m)
        assert result is not None
        assert result.distance == 0
        assert result.shared_count == 16


class TestDangCatalog:
    def test_enumerate_dangs(self):
        dangs = enumerate_valid_dangs()
        assert len(dangs) > 0
        for d in dangs:
            assert 3 <= len(d.intervals) <= 4
            assert 9 <= sum(d.intervals) <= 11
            assert all(i > 0 for i in d.intervals)

    def test_common_dangs_present(self):
        dangs = enumerate_valid_dangs()
        sigs = {d.intervals for d in dangs}
        assert (4, 4, 2) in sigs  # Mahur tetrachord
        assert (3, 4, 3) in sigs  # Shur tetrachord
        assert (4, 3, 3) in sigs  # Another common one

    def test_modal_families(self):
        mahur = make_mahur()
        shur = make_shur()
        families = modal_families({"mahur": mahur, "shur": shur})
        # (4, 4, 2) should only be in mahur
        assert "mahur" in families[(4, 4, 2)]
        assert "shur" not in families[(4, 4, 2)]
        # (3, 4, 3) should only be in shur
        assert "shur" in families[(3, 4, 3)]


class TestTopology:
    def test_build_graph(self):
        mahur = make_mahur()
        shur = make_shur()
        graph = build_topology({"mahur": mahur, "shur": shur})
        assert set(graph.nodes) == {"mahur", "shur"}
        assert len(graph.edges) > 0

    def test_nearest_neighbor_ordering(self):
        mahur = make_mahur()
        shur = make_shur()
        d = Dang((4, 4, 2))
        kereshmeh = create_maayeh([d, d], [None])
        graph = build_topology({
            "mahur": mahur,
            "shur": shur,
            "kereshmeh": kereshmeh,
        })
        order = nearest_neighbor_ordering(graph, start="mahur")
        assert len(order) == 3
        assert order[0] == "mahur"
        assert set(order) == {"mahur", "shur", "kereshmeh"}

    def test_distance_matrix_symmetric(self):
        mahur = make_mahur()
        shur = make_shur()
        graph = build_topology({"mahur": mahur, "shur": shur})
        assert graph.distance_matrix[("mahur", "shur")] == \
               graph.distance_matrix[("shur", "mahur")]
