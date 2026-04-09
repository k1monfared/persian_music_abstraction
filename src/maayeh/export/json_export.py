"""Export MaayehDefinition objects to JSON, validated against the schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.types import MaayehDefinition

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "maayeh.schema.json"


def maayeh_to_dict(defn: MaayehDefinition) -> dict[str, Any]:
    """Convert a MaayehDefinition to a JSON-serializable dict."""
    m = defn.maayeh
    meta = defn.metadata

    notes_list = []
    for note in m.notes:
        notes_list.append({
            "degree": note.degree,
            "qt": note.qt,
            "dang": note.dang,
            "dangIndices": list(note.dang_indices),
            "boundary": note.boundary,
        })

    gooshehs_list = []
    for g in defn.gooshehs:
        touched = sorted(m.touched_set_for(g))
        gooshehs_list.append({
            "name": g.name,
            "ist": g.ist,
            "shahed": g.shahed,
            "melody": list(g.melody) if g.melody is not None else None,
            "touchedSet": touched,
        })

    return {
        "schemaVersion": 1,
        "name": meta.name,
        "metadata": {
            "dastgah": meta.dastgah,
            "radifs": list(meta.radifs),
            "tags": list(meta.tags),
        },
        "dangs": [list(d.intervals) for d in m.dangs],
        "gaps": [g if g is not None else None for g in m.gaps],
        "notes": notes_list,
        "gooshehs": gooshehs_list,
        "derived": {
            "intervalVector": list(m.interval_vector),
            "rangeQt": m.range_qt,
        },
    }


def maayeh_to_json(defn: MaayehDefinition, indent: int = 2) -> str:
    """Convert a MaayehDefinition to a JSON string."""
    return json.dumps(maayeh_to_dict(defn), indent=indent, ensure_ascii=False)


def validate_json(data: dict[str, Any]) -> None:
    """Validate a maayeh JSON dict against the schema. Raises on invalid."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.validate(instance=data, schema=schema)


def export_all(
    data_dir: Path,
    output_dir: Path,
    radifs_dir: Path | None = None,
) -> list[str]:
    """Parse all .maayeh files in data_dir, export JSON to output_dir.

    If radifs_dir is provided, also parses .radif index files and includes
    radif ordering in the manifest.

    Returns list of exported file names.
    """
    from ..parser import parse_maayeh
    from ..parser.radif_parser import parse_radif

    output_dir.mkdir(parents=True, exist_ok=True)

    exported = []
    manifest_entries = []

    for maayeh_file in sorted(data_dir.glob("*.maayeh")):
        text = maayeh_file.read_text(encoding="utf-8")
        defn = parse_maayeh(text)

        data = maayeh_to_dict(defn)
        validate_json(data)

        out_name = maayeh_file.stem + ".json"
        out_path = output_dir / out_name
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        exported.append(out_name)

        manifest_entries.append({
            "name": defn.metadata.name,
            "file": out_name,
            "dastgah": defn.metadata.dastgah,
            "tags": list(defn.metadata.tags),
            "noteCount": len(defn.maayeh.notes),
            "dangCount": len(defn.maayeh.dangs),
        })

    # Parse radif indices
    radif_entries = []
    if radifs_dir and radifs_dir.exists():
        for radif_dir in sorted(radifs_dir.iterdir()):
            index_file = radif_dir / "index.radif"
            if index_file.exists():
                radif = parse_radif(index_file.read_text(encoding="utf-8"))
                radif_entries.append({
                    "name": radif.name,
                    "description": radif.description,
                    "entries": list(radif.entries),
                })

    # Write manifest
    manifest: dict[str, Any] = {
        "schemaVersion": 1,
        "maayehs": manifest_entries,
    }
    if radif_entries:
        manifest["radifs"] = radif_entries

    manifest_path = output_dir / "index.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return exported
