"""CLI for the maayeh system.

Usage:
    python -m maayeh build [--data-dir DIR] [--output-dir DIR]
    python -m maayeh import FILE [--output-dir DIR]
    python -m maayeh validate FILE
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_build(args: argparse.Namespace) -> None:
    """Parse all .maayeh files and export JSON."""
    from .export.json_export import export_all

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    if not data_dir.exists():
        print(f"Error: data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    radifs_dir = Path(args.radifs_dir) if args.radifs_dir else None
    exported = export_all(data_dir, output_dir, radifs_dir=radifs_dir)
    print(f"Exported {len(exported)} maayeh(s) to {output_dir}/")
    for name in exported:
        print(f"  {name}")


def cmd_import(args: argparse.Namespace) -> None:
    """Import a bulk file (multiple --- maayeh --- blocks) into individual .maayeh files."""
    from .parser import parse_bulk, serialize_maayeh

    input_path = Path(args.file)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    definitions = parse_bulk(text)

    output_dir.mkdir(parents=True, exist_ok=True)

    for defn in definitions:
        name = defn.metadata.name or f"unnamed-{definitions.index(defn)}"
        out_path = output_dir / f"{name}.maayeh"
        out_path.write_text(serialize_maayeh(defn), encoding="utf-8")
        print(f"  {out_path}")

    print(f"Imported {len(definitions)} maayeh(s) to {output_dir}/")


def cmd_validate(args: argparse.Namespace) -> None:
    """Parse and validate a .maayeh file."""
    from .parser import parse_maayeh
    from .export.json_export import maayeh_to_dict, validate_json

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    defn = parse_maayeh(text)
    data = maayeh_to_dict(defn)
    validate_json(data)

    m = defn.maayeh
    print(f"Valid: {defn.metadata.name or input_path.stem}")
    print(f"  Dangs: {len(m.dangs)}")
    print(f"  Notes: {len(m.notes)}")
    print(f"  Range: {m.range_qt} qt")
    print(f"  Gooshehs: {len(defn.gooshehs)}")
    for g in defn.gooshehs:
        print(f"    {g.name or '(default)'}: ist={g.ist}, shahed={g.shahed}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="maayeh",
        description="Persian modal structure representation system",
    )
    sub = parser.add_subparsers(dest="command")

    build_p = sub.add_parser("build", help="Export .maayeh files to JSON")
    build_p.add_argument(
        "--data-dir", default="data/maayehs",
        help="Directory containing .maayeh files (default: data/maayehs)",
    )
    build_p.add_argument(
        "--output-dir", default="build/data",
        help="Output directory for JSON files (default: build/data)",
    )
    build_p.add_argument(
        "--radifs-dir", default="data/radifs",
        help="Directory containing radif index folders (default: data/radifs)",
    )

    import_p = sub.add_parser("import", help="Import a bulk file into .maayeh files")
    import_p.add_argument("file", help="Path to bulk input file")
    import_p.add_argument(
        "--output-dir", default="data/maayehs",
        help="Output directory for .maayeh files (default: data/maayehs)",
    )

    validate_p = sub.add_parser("validate", help="Validate a .maayeh file")
    validate_p.add_argument("file", help="Path to .maayeh file")

    args = parser.parse_args()

    if args.command == "build":
        cmd_build(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
