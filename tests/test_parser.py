"""Tests for the .maayeh parser and serializer."""

import pytest

from maayeh.parser import parse_maayeh, serialize_maayeh, parse_bulk
from maayeh.parser.tokenizer import tokenize_interval_line, is_interval_line


class TestTokenizer:
    def test_simple_two_dangs(self):
        dangs, gaps = tokenize_interval_line("4 4 2 | 4 4 2")
        assert len(dangs) == 2
        assert dangs[0].intervals == (4, 4, 2)
        assert dangs[1].intervals == (4, 4, 2)
        assert len(gaps) == 1
        assert gaps[0].value is None  # default

    def test_explicit_gap(self):
        dangs, gaps = tokenize_interval_line("4 4 2 |6| 4 4 2")
        assert len(dangs) == 2
        assert gaps[0].value == 6

    def test_explicit_gap_zero(self):
        dangs, gaps = tokenize_interval_line("4 4 2 |0| 4 4 2")
        assert gaps[0].value == 0

    def test_four_dangs(self):
        dangs, gaps = tokenize_interval_line("4 4 2 | 4 4 2 | 4 4 2 | 4 4 2")
        assert len(dangs) == 4
        assert all(g.value is None for g in gaps)

    def test_mixed_gaps(self):
        dangs, gaps = tokenize_interval_line("4 4 2 |6| 3 4 3 | 4 3 4")
        assert len(dangs) == 3
        assert gaps[0].value == 6
        assert gaps[1].value is None

    def test_single_dang(self):
        dangs, gaps = tokenize_interval_line("4 4 2")
        assert len(dangs) == 1
        assert len(gaps) == 0

    def test_is_interval_line(self):
        assert is_interval_line("4 4 2 | 4 4 2")
        assert is_interval_line("3 4 3")
        assert not is_interval_line("ist: 1")
        assert not is_interval_line("name: test")
        assert not is_interval_line("")
        assert not is_interval_line("--- maayeh ---")


class TestParser:
    def test_minimal(self):
        defn = parse_maayeh("4 4 2 | 4 4 2")
        assert len(defn.maayeh.dangs) == 2
        assert len(defn.maayeh.notes) == 8
        assert defn.metadata.name == ""
        assert len(defn.gooshehs) == 0

    def test_with_annotations(self):
        text = """4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 1"""
        defn = parse_maayeh(text)
        assert len(defn.gooshehs) == 1
        g = defn.gooshehs[0]
        assert g.ist == 1
        assert g.shahed == 3
        assert g.melody == (1, 2, 3, 4, 3, 2, 1)

    def test_with_header_and_metadata(self):
        text = """--- maayeh ---
name: daramad-mahur
dastgah: mahur
radifs: mirza-abdollah, karimi
tags: daramad, tetrachord

4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1"""
        defn = parse_maayeh(text)
        assert defn.metadata.name == "daramad-mahur"
        assert defn.metadata.dastgah == "mahur"
        assert defn.metadata.radifs == ("mirza-abdollah", "karimi")
        assert defn.metadata.tags == ("daramad", "tetrachord")
        assert len(defn.maayeh.dangs) == 4
        assert len(defn.maayeh.notes) == 16

    def test_explicit_gap(self):
        defn = parse_maayeh("4 4 2 |6| 4 4 2")
        assert defn.maayeh.gaps == (6,)
        assert defn.maayeh.notes[4].qt == 16

    def test_goosheh_blocks(self):
        text = """--- maayeh ---
name: test

3 4 3 | 4 3 4

--- goosheh ---
name: daramad
ist: 1
shahed: 5
melody: 1 2 3 4 5 4 3 2 1

--- goosheh ---
name: kereshmeh
ist: 3
shahed: 7"""
        defn = parse_maayeh(text)
        assert len(defn.gooshehs) == 2
        assert defn.gooshehs[0].name == "daramad"
        assert defn.gooshehs[0].ist == 1
        assert defn.gooshehs[0].melody == (1, 2, 3, 4, 5, 4, 3, 2, 1)
        assert defn.gooshehs[1].name == "kereshmeh"
        assert defn.gooshehs[1].ist == 3
        assert defn.gooshehs[1].melody is None

    def test_spec_example_mahur(self):
        """Full spec section 9 example 1."""
        text = """4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
name: daramad mahur"""
        defn = parse_maayeh(text)
        m = defn.maayeh
        assert len(m.notes) == 16
        assert m.notes[0].qt == 0
        assert m.notes[1].qt == 4
        assert m.notes[2].qt == 8
        assert m.notes[3].qt == 10
        assert m.notes[4].qt == 14
        assert list(m.interval_vector) == [4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2]

        g = defn.gooshehs[0]
        assert g.ist == 1
        assert g.shahed == 3
        assert g.touched_set == frozenset({1, 2, 3, 4, 5})

    def test_spec_example_shur(self):
        """Spec section 9 example 2."""
        text = """3 4 3 | 4 3 4
ist: 1
shahed: 5
name: shur"""
        defn = parse_maayeh(text)
        m = defn.maayeh
        assert len(m.notes) == 8
        assert m.notes[4].qt == 14


class TestSerializer:
    def test_round_trip_simple(self):
        original = "--- maayeh ---\n\n4 4 2 | 4 4 2\n"
        defn = parse_maayeh(original)
        result = serialize_maayeh(defn)
        defn2 = parse_maayeh(result)
        assert defn.maayeh.notes == defn2.maayeh.notes
        assert defn.maayeh.gaps == defn2.maayeh.gaps

    def test_round_trip_with_metadata(self):
        original = """--- maayeh ---
name: daramad-mahur
dastgah: mahur
radifs: mirza-abdollah, karimi
tags: daramad, tetrachord

4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
"""
        defn = parse_maayeh(original)
        result = serialize_maayeh(defn)
        defn2 = parse_maayeh(result)
        assert defn2.metadata.name == "daramad-mahur"
        assert defn2.metadata.dastgah == "mahur"
        assert defn2.metadata.radifs == ("mirza-abdollah", "karimi")
        assert defn2.maayeh.notes == defn.maayeh.notes
        assert defn2.gooshehs[0].ist == 1
        assert defn2.gooshehs[0].shahed == 3

    def test_round_trip_explicit_gap(self):
        original = "4 4 2 |6| 4 4 2"
        defn = parse_maayeh(original)
        result = serialize_maayeh(defn)
        defn2 = parse_maayeh(result)
        assert defn2.maayeh.gaps == (6,)
        assert defn2.maayeh.notes[4].qt == 16

    def test_round_trip_goosheh_blocks(self):
        original = """--- maayeh ---
name: test

3 4 3 | 4 3 4

--- goosheh ---
name: daramad
ist: 1
shahed: 5
melody: 1 2 3 4 5 4 3 2 1

--- goosheh ---
name: kereshmeh
ist: 3
shahed: 7
"""
        defn = parse_maayeh(original)
        result = serialize_maayeh(defn)
        defn2 = parse_maayeh(result)
        assert len(defn2.gooshehs) == 2
        assert defn2.gooshehs[0].name == "daramad"
        assert defn2.gooshehs[1].name == "kereshmeh"
        assert defn2.gooshehs[0].melody == (1, 2, 3, 4, 5, 4, 3, 2, 1)
        assert defn2.gooshehs[1].melody is None


class TestBulkParse:
    def test_two_documents(self):
        text = """--- maayeh ---
name: first
4 4 2 | 4 4 2

--- maayeh ---
name: second
3 4 3 | 4 3 4
"""
        results = parse_bulk(text)
        assert len(results) == 2
        assert results[0].metadata.name == "first"
        assert results[1].metadata.name == "second"
