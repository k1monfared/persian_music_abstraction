"""Tests for JSON export and schema validation."""

from pathlib import Path

from maayeh.parser import parse_maayeh
from maayeh.export.json_export import maayeh_to_dict, maayeh_to_json, validate_json


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestJsonExport:
    def test_basic_export(self):
        defn = parse_maayeh("4 4 2 | 4 4 2\nist: 1\nshahed: 3")
        data = maayeh_to_dict(defn)
        assert data["schemaVersion"] == 1
        assert data["dangs"] == [[4, 4, 2], [4, 4, 2]]
        assert data["gaps"] == [None]
        assert len(data["notes"]) == 8
        assert data["gooshehs"][0]["ist"] == 1
        assert data["gooshehs"][0]["shahed"] == 3

    def test_schema_validation(self):
        defn = parse_maayeh("""--- maayeh ---
name: test
dastgah: mahur

4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3
""")
        data = maayeh_to_dict(defn)
        validate_json(data)  # should not raise

    def test_daramad_mahur_schema(self):
        text = """--- maayeh ---
name: daramad-mahur
dastgah: mahur
tags: daramad, tetrachord

4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
"""
        defn = parse_maayeh(text)
        data = maayeh_to_dict(defn)
        validate_json(data)

        assert data["name"] == "daramad-mahur"
        assert data["metadata"]["dastgah"] == "mahur"
        assert data["derived"]["intervalVector"] == [4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2]
        assert data["derived"]["rangeQt"] == 52
        assert data["gooshehs"][0]["touchedSet"] == [1, 2, 3, 4, 5]

    def test_explicit_gap_in_json(self):
        defn = parse_maayeh("4 4 2 |6| 4 4 2")
        data = maayeh_to_dict(defn)
        assert data["gaps"] == [6]

    def test_null_melody_all_touched(self):
        defn = parse_maayeh("4 4 2 | 4 4 2\nist: 1")
        data = maayeh_to_dict(defn)
        g = data["gooshehs"][0]
        assert g["melody"] is None
        assert g["touchedSet"] == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_json_string(self):
        defn = parse_maayeh("4 4 2 | 4 4 2")
        json_str = maayeh_to_json(defn)
        assert '"schemaVersion": 1' in json_str

    def test_data_file_daramad_mahur(self):
        """Validate the actual data file."""
        data_file = Path(__file__).parent.parent / "data" / "maayehs" / "daramad-mahur.maayeh"
        if data_file.exists():
            text = data_file.read_text()
            defn = parse_maayeh(text)
            data = maayeh_to_dict(defn)
            validate_json(data)

    def test_data_file_shur(self):
        """Validate the actual data file."""
        data_file = Path(__file__).parent.parent / "data" / "maayehs" / "shur.maayeh"
        if data_file.exists():
            text = data_file.read_text()
            defn = parse_maayeh(text)
            data = maayeh_to_dict(defn)
            validate_json(data)
