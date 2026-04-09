"""Tests for core domain types and factory."""

import pytest

from maayeh.core import Dang, Note, Goosheh, Maayeh, MaayehMetadata, MaayehDefinition
from maayeh.core.factory import create_maayeh


class TestDang:
    def test_valid_dang(self):
        d = Dang((4, 4, 2))
        assert d.span == 10
        assert d.note_count == 4

    def test_valid_dang_4_intervals(self):
        d = Dang((3, 2, 2, 2))
        assert d.span == 9
        assert d.note_count == 5

    def test_invalid_too_few_intervals(self):
        with pytest.raises(ValueError, match="3-4 intervals"):
            Dang((5, 5))

    def test_invalid_too_many_intervals(self):
        with pytest.raises(ValueError, match="3-4 intervals"):
            Dang((2, 2, 2, 2, 2))

    def test_invalid_span_too_small(self):
        with pytest.raises(ValueError, match="span must be 9-11"):
            Dang((2, 2, 2))

    def test_invalid_span_too_large(self):
        with pytest.raises(ValueError, match="span must be 9-11"):
            Dang((4, 4, 4))

    def test_invalid_negative_interval(self):
        with pytest.raises(ValueError, match="positive"):
            Dang((4, 0, 6))

    def test_frozen(self):
        d = Dang((4, 4, 2))
        with pytest.raises(AttributeError):
            d.intervals = (3, 3, 4)


class TestNote:
    def test_default_dang_indices(self):
        n = Note(degree=1, qt=0, dang=0)
        assert n.dang_indices == (0,)

    def test_explicit_dang_indices(self):
        n = Note(degree=4, qt=10, dang=1, dang_indices=(0, 1), boundary=True)
        assert n.dang_indices == (0, 1)
        assert n.boundary is True


class TestGoosheh:
    def test_with_melody(self):
        g = Goosheh(name="daramad", ist=1, shahed=3, melody=(1, 2, 3, 4, 3, 2, 1))
        assert g.has_melody is True
        assert g.touched_set == frozenset({1, 2, 3, 4})

    def test_without_melody(self):
        g = Goosheh(name="test", ist=1, shahed=3)
        assert g.has_melody is False
        assert g.touched_set == frozenset()

    def test_empty_melody(self):
        g = Goosheh(melody=())
        assert g.has_melody is True
        assert g.touched_set == frozenset()


class TestCreateMaayeh:
    def test_two_dangs_default_gap(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [None])
        assert len(m.notes) == 8
        assert m.notes[0].qt == 0
        assert m.notes[3].qt == 10
        assert m.notes[4].qt == 14  # 10 + gap(4)
        assert m.notes[7].qt == 24
        assert m.gap_value(0) == 4

    def test_two_dangs_explicit_gap(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [6])
        assert m.notes[4].qt == 16  # 10 + gap(6)

    def test_gap_zero_boundary_sharing(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [0])
        assert len(m.notes) == 7  # shared boundary note
        boundary = m.notes[3]
        assert boundary.boundary is True
        assert boundary.dang_indices == (0, 1)
        assert boundary.dang == 1  # assigned to later dang

    def test_four_dangs_mahur(self):
        """Verify against spec section 9 example."""
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d, d, d], [None, None, None])

        assert len(m.notes) == 16
        expected_qt = [0, 4, 8, 10, 14, 18, 22, 24, 28, 32, 36, 38, 42, 46, 50, 52]
        actual_qt = [n.qt for n in m.notes]
        assert actual_qt == expected_qt

        expected_iv = [4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2]
        assert list(m.interval_vector) == expected_iv
        assert m.range_qt == 52

    def test_shur(self):
        """Verify Shur from spec example 2."""
        d1 = Dang((3, 4, 3))
        d2 = Dang((4, 3, 4))
        m = create_maayeh([d1, d2], [None])
        assert len(m.notes) == 8
        assert m.notes[0].qt == 0
        assert m.notes[3].qt == 10
        assert m.notes[4].qt == 14

    def test_degree_to_qt(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [None])
        assert m.degree_to_qt(1) == 0
        assert m.degree_to_qt(5) == 14

    def test_qt_to_degree(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [None])
        assert m.qt_to_degree(14) == 5
        assert m.qt_to_degree(15) is None

    def test_touched_set_for(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [None])
        g = Goosheh(melody=(1, 2, 3))
        assert m.touched_set_for(g) == frozenset({1, 2, 3})

    def test_touched_set_for_no_melody(self):
        d = Dang((4, 4, 2))
        m = create_maayeh([d, d], [None])
        g = Goosheh()
        assert m.touched_set_for(g) == frozenset(range(1, 9))

    def test_gap_count_mismatch(self):
        d = Dang((4, 4, 2))
        with pytest.raises(ValueError, match="gaps"):
            create_maayeh([d, d], [None, None])
