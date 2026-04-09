# Maayeh Representation System: Implementation Plan
**Date**: 2026-04-08
**Status**: Reviewed, Updated
**Review**: Critical review completed, all issues addressed below.

---

## Context

This project builds a complete system for representing, computing, visualizing, and interacting with Persian classical music modal structures (maayeh, dastgah, dang). The spec (`maayeh-spec.md`) defines quarter-tone-based math, a human-writable text notation, computational objects, analysis operations, and a visual column representation. A working prototype (`daramad-mahur.html`) demonstrates one SVG column for Daramad Mahur. The goal is to go from this single prototype to a full interactive system where users build and explore a database of maayehs, see them as side-by-side vertical columns, discover missing structures computationally, and compose custom radifs.

---

## Tech Stack

- **Core library (parser, domain, analysis, topology)**: Python
- **Web UI (rendering, interaction)**: TypeScript, vanilla SVG, Vite
- **Bridge**: Python generates JSON from `.maayeh` files. TypeScript UI consumes JSON. A shared JSON Schema file (`schema/maayeh.schema.json`) is the single source of truth, validated on both sides.
- **Tests**: pytest for Python core, vitest for TypeScript UI
- **No framework**: Vanilla DOM + SVG for the web. No React/Vue.
- **No runtime backend**: Python runs as a build/CLI tool. The web app is fully static. (A `--watch` mode auto-rebuilds on file changes for development.)

### How the bridge works

```
.maayeh files  -->  Python parser  -->  JSON files  -->  TypeScript UI  -->  SVG in browser
  (human)            (build step)       (computed)       (static site)       (visual)
```

1. User writes/edits `.maayeh` text files (or pastes notation into the browser's quick-entry box)
2. `python -m maayeh build` (or `--watch` mode) parses all `.maayeh` files, validates output against `schema/maayeh.schema.json`, writes JSON to `build/data/`
3. Vite serves `build/data/` as static assets alongside the TypeScript UI
4. The browser fetches JSON and renders SVG columns
5. For quick previews, the browser also includes a lightweight TypeScript parser that can render `.maayeh` text directly without the build step

### Type contract enforcement

A JSON Schema file (`schema/maayeh.schema.json`) is the single source of truth:
- Python validates its JSON output against it (using `jsonschema`)
- TypeScript types are generated from it (using `json-schema-to-typescript`)
- A CI test parses known `.maayeh` fixtures, exports JSON, and validates against the schema

---

## Key Design Decision: Goosheh as the Primary Unit

The spec (section 3.6) says ist and shahed are properties of a **goosheh within a maayeh**, not of the maayeh itself. A single maayeh (scale structure) can have multiple gooshehs (each with different ist, shahed, melody).

**Decision**: The maayeh defines the scale (dangs + gaps + notes). Gooshehs are overlays within that scale. The visual column shows one maayeh's scale structure. Goosheh data (which notes are touched, roles) is a selectable layer on top.

This means:
- The `.maayeh` file contains the scale definition plus one or more goosheh blocks
- The JSON output nests gooshehs inside the maayeh
- The column renderer receives a maayeh + a selected goosheh to determine colors/opacity
- The topology operates at the maayeh level (shared structure) with goosheh-level refinements

---

## Data Format: `.maayeh` Files

Each maayeh is a single human-readable text file:

```
--- maayeh ---
name: daramad-mahur
dastgah: mahur
radifs: mirza-abdollah, karimi
tags: daramad, tetrachord

4 4 2 | 4 4 2 | 4 4 2 | 4 4 2

--- goosheh ---
name: daramad
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1

--- goosheh ---
name: kereshmeh
ist: 5
shahed: 7
melody: 5 6 7 8 7 6 5
```

### Format rules

- `--- maayeh ---` header starts the file. Metadata lines follow (key: value).
- **Interval line**: the first non-blank line after metadata that matches `^[\d\s|]+$`. All integers and `|` separators with optional explicit gaps.
- `--- goosheh ---` headers introduce goosheh blocks (repeatable). Each carries its own ist, shahed, melody, name.
- If no `--- goosheh ---` block exists, the annotations (ist, shahed, melody) apply to a default unnamed goosheh (backwards-compatible with spec section 4).
- File naming: `<name>.maayeh` (kebab-case).

### Gap syntax (clarified)

The literal file syntax for explicit gaps is `|N|` where N is a positive integer. Example: `4 4 2 |6| 4 4 2`. The spec's `|<n>|` notation is metasyntax, not literal angle brackets.

The tokenizer uses a two-pass approach:
1. Regex `\|(\d+)\|` extracts explicit gaps, replacing them with a placeholder token
2. Remaining `|` characters are default-gap separators (gap = 4 qt)

### Round-trip fidelity

To support lossless round-trip serialization, the parser tracks which gaps were explicit vs. default. The internal representation stores gaps as `list[int | None]` where `None` means "default (4 qt)" and an integer means "explicitly written." The serializer reproduces `|` for default gaps and `|N|` for explicit ones.

### Radif index format (`.radif` files)

```
--- radif ---
name: mirza-abdollah
description: Radif of Mirza Abdollah

daramad-mahur
kereshmeh-mahur
daramad-shur
```

An ordered list of maayeh names (one per line, matching `.maayeh` file names without extension). A maayeh can appear in multiple radif files.

### Bulk import

A multi-document format is supported: multiple `--- maayeh ---` blocks in a single file, separated by the header. The CLI command `python -m maayeh import bulk-file.txt` splits them into individual `.maayeh` files. The web UI also accepts pasted multi-document text.

---

## JSON Schema (the bridge)

Every JSON file includes a schema version for forward compatibility.

```json
{
  "schemaVersion": 1,
  "name": "daramad-mahur",
  "metadata": {
    "dastgah": "mahur",
    "radifs": ["mirza-abdollah", "karimi"],
    "tags": ["daramad", "tetrachord"]
  },
  "dangs": [[4, 4, 2], [4, 4, 2], [4, 4, 2], [4, 4, 2]],
  "gaps": [null, null, null],
  "notes": [
    {"degree": 1, "qt": 0, "dang": 0, "dangIndices": [0], "boundary": false},
    {"degree": 2, "qt": 4, "dang": 0, "dangIndices": [0], "boundary": false},
    {"degree": 3, "qt": 8, "dang": 0, "dangIndices": [0], "boundary": false},
    {"degree": 4, "qt": 10, "dang": 0, "dangIndices": [0, 1], "boundary": true}
  ],
  "gooshehs": [
    {
      "name": "daramad",
      "ist": 1,
      "shahed": 3,
      "melody": [1, 2, 3, 4, 3, 2, 3, 5, 3, 2, 1],
      "touchedSet": [1, 2, 3, 4, 5]
    }
  ],
  "derived": {
    "intervalVector": [4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2, 4, 4, 4, 2],
    "rangeQt": 58
  }
}
```

Key changes from the initial draft:
- `schemaVersion` for forward compatibility
- `metadata` separates storage concerns from domain data
- `gaps`: `null` = default (4 qt), integer = explicitly written (enables lossless round-trip)
- `notes[].dangIndices`: array of dang affiliations (boundary notes belong to both)
- `notes[].boundary`: flag for dang boundary notes
- `gooshehs`: array of goosheh objects (ist, shahed, melody, touchedSet are per-goosheh)
- `melody: null` means "not provided, all notes touched". `melody: []` means "explicitly empty"
- `derived`: computed quantities grouped separately

---

## Architecture (5 Layers)

### Layer 0: Storage (filesystem)
```
data/
  maayehs/           # all .maayeh definitions (flat)
  radifs/             # collection directories with index.radif files
  dangs/              # optional named dang catalog
```

### Layer 1: Core Domain (Python, `src/maayeh/core/`)
Abstract dataclasses. No rendering, no I/O, no storage metadata.

Key types:
- `IntervalSequence`: tuple of positive ints
- `Dang`: IntervalSequence with span constraint (sum 9-11, length 3-4)
- `Note`: degree, qt, dang index, dangIndices (all affiliations), boundary flag
- `Maayeh`: dangs, gaps, notes (the scale structure only)
- `Goosheh`: reference to a Maayeh + ist, shahed, melody, touchedSet
- `Radif`: ordered list of (Maayeh, Goosheh) pairs

**Separation of concerns**: `MaayehDefinition` wraps a `Maayeh` domain object + `MaayehMetadata` (name, dastgah, radifs, tags). The core domain stays clean of storage concerns. The parser returns `MaayehDefinition`. The JSON exporter merges domain + metadata.

Abstraction strategy:
- Protocol classes at boundaries
- Factory functions for construction
- Derived quantities as `@property` or methods (computed/cached)
- No rendering state in domain objects

**Tuning assumption**: All values are integers (quarter-tones). This is a known limitation. A tuning system change would propagate beyond core (to JSON schema, TypeScript types, and SVG pixel calculations). If rational tuning becomes needed, use floats in JSON from that point.

### Layer 2: Parser (Python, `src/maayeh/parser/`)
- `parse_maayeh(text) -> MaayehDefinition` and `serialize_maayeh(d) -> str`
- Two-pass tokenizer for gap syntax (regex `\|(\d+)\|` for explicit gaps, then bare `|` for defaults)
- Handles `--- goosheh ---` blocks
- Tracks explicit vs. default gaps for lossless round-trip
- `parse_bulk(text) -> list[MaayehDefinition]` for multi-document import

**Interval line identification**: The first non-blank line after the metadata block that matches `^[\d\s|]+$` is the interval line. All subsequent non-blank lines before `--- goosheh ---` (or EOF) are annotation lines for a default goosheh.

### Layer 3: Analysis (Python, `src/maayeh/analysis/`)
- Interval content, melodic contour, modulation distance, dang similarity (spec section 6)
- Topology: adjacency graph + pairwise distance matrix + shared-dang incidence matrix
- Dang catalog: enumerate all valid interval sequences of length 3-4 summing to 9-11
- Column ordering: greedy nearest-neighbor traversal from a user-selected root, using the distance matrix. Multiple orderings available (by dastgah, by topological proximity, alphabetical, custom)

**Topology operates on domain objects, not JSON.** The CLI build command: (1) parses all `.maayeh` files into domain objects, (2) runs topology analysis on domain objects, (3) exports everything to JSON.

**Future topology extensions**: The adjacency graph is Phase 4's implementation. The data model stores enough raw data (distance matrix, shared-dang incidence) to support future extensions: simplicial complexes, persistent homology, metric space embeddings. The user (a mathematician) may want UMAP or force-directed layout for 2D visualization of the modal space.

### Layer 4: Visualization (TypeScript, `web/src/viz/`)
- `renderColumn(maayehJson, gooshehIndex)`: single column SVG renderer
- `renderStrip(maayehJsonList)`: horizontal scrollable strip of aligned columns
- Horizontal connectors between shared notes across adjacent columns (spec section 7.5)
- Configurable palette matching prototype colors

### Layer 5: Interactive UI (TypeScript, `web/src/ui/`)
- **Quick entry**: Text area for pasting `.maayeh` notation, instant preview via browser-side parser (no build step needed)
- **Database browser**: List/search/filter maayehs by name, dastgah, tags
- **Column viewer**: Primary radif visualization, horizontal strip with selectable goosheh overlays
- **Grid editor**: Blank column, click cells to toggle notes, real-time text notation display, "Save to database" downloads `.maayeh` file and feeds result directly into the strip view
- **Radif arranger**: Create new radif, add maayehs from database/search/grid editor, drag-and-drop reorder, export as `.radif` file
- **Discovery panel**: Show valid but uncataloged dangs/maayehs with "Add to database" button

**Deferred interactive features** (from spec section 7.6, not in initial phases):
- Hover tooltips (Phase 2, easy to add with SVG title elements)
- Audio playback (requires Web Audio API, deferred to post-Phase 7)
- Melody animation (deferred)
- Modulation animation (deferred)

---

## File Structure

```
persian_music_abstraction/
  maayeh-spec.md                    # existing spec
  daramad-mahur.html                # existing prototype (reference)
  plans/                            # this directory

  # Shared schema (single source of truth)
  schema/
    maayeh.schema.json              # JSON Schema for the bridge

  # Python core
  pyproject.toml
  src/
    maayeh/
      __init__.py
      cli.py                        # CLI: build, build --watch, validate, import
      core/
        __init__.py
        types.py                    # Protocols + dataclasses
        interval_sequence.py
        dang.py
        note.py
        maayeh.py                   # Scale structure (domain only)
        goosheh.py                  # Goosheh (role assignments + melody)
        radif.py
        definition.py               # MaayehDefinition = Maayeh + Metadata
      parser/
        __init__.py
        tokenizer.py                # Two-pass tokenizer for gap syntax
        maayeh_parser.py            # parse + serialize + parse_bulk
        radif_parser.py             # Parse .radif files
      analysis/
        __init__.py
        interval_content.py
        melodic_contour.py
        modulation.py
        dang_catalog.py             # Enumerate valid dangs
        topology.py                 # Adjacency, distance matrix, ordering
      export/
        __init__.py
        json_export.py              # MaayehDefinition -> JSON, validates against schema

  # TypeScript web UI
  web/
    package.json
    tsconfig.json
    vite.config.ts
    index.html
    src/
      types.ts                      # Generated from schema/maayeh.schema.json
      parser.ts                     # Lightweight browser-side parser for quick entry
      viz/
        palette.ts
        svg-utils.ts
        maayeh-column.ts            # Single column renderer
        pitch-axis.ts
        radif-strip.ts              # Multi-column with connectors
      ui/
        app.ts
        quick-entry.ts              # Paste-and-preview text area
        data-service.ts
        column-viewer.ts
        grid-editor.ts
        radif-arranger.ts
        database-browser.ts
        discovery-panel.ts
      styles.css

  # Human-readable database
  data/
    maayehs/
      daramad-mahur.maayeh
      shur.maayeh
    radifs/
      sample/
        index.radif

  # Build output (gitignored)
  build/
    data/                           # JSON from Python
    web/                            # Vite output

  tests/
    test_parser.py
    test_maayeh.py
    test_goosheh.py
    test_analysis.py
    test_schema.py                  # Validates JSON output against schema
    fixtures/
      daramad-mahur.maayeh          # Known-good test fixture
```

---

## Implementation Phases

### Phase 1: Core Library + Parser [DONE]
- [x] Python project setup (pyproject.toml, package structure)
- [x] JSON Schema file (`schema/maayeh.schema.json`)
- [x] Core domain types (types.py, factory.py: dataclasses + factory functions)
- [x] `MaayehDefinition` = `Maayeh` (domain) + `MaayehMetadata` (storage)
- [x] IntervalSequence, Dang, Note, Maayeh, Goosheh classes
- [x] Two-pass tokenizer (explicit gap regex, then bare `|` split)
- [x] Parser: `parse_maayeh`, `serialize_maayeh`, `parse_bulk`
- [x] Goosheh block parsing (`--- goosheh ---`)
- [x] Track explicit vs. default gaps for lossless round-trip
- [x] First data files (daramad-mahur.maayeh, shur.maayeh)
- [x] JSON export module (validates against schema)
- [x] CLI command: `python -m maayeh build` and `python -m maayeh import`
- [x] Tests: 50 tests passing (core, parser, tokenizer, serializer, export, schema)

**Verified**:
1. Parsed Daramad Mahur matches spec section 9 table exactly
2. Round-trip serialization preserves explicit vs. default gaps
3. JSON output validates against `schema/maayeh.schema.json`
4. Goosheh blocks parsed correctly (multiple gooshehs per maayeh)
5. Gap=0 boundary sharing works (7 notes instead of 8, boundary flag set)

### Phase 2: Single-Column Visualization [DONE]
- [x] Web project setup (package.json, tsconfig, vite config)
- [x] TypeScript types matching JSON Schema (web/src/types.ts)
- [x] SVG renderer: palette, svg-utils, maayeh-column (with goosheh selection)
- [x] Hover tooltips on note markers (degree, qt, dang, role)
- [x] Application shell (index.html, dark theme styles, app.ts)
- [x] Fetch pre-built JSON and render one column
- [x] Quick-entry text area with browser-side parser for instant preview
- [x] Browser-side parser (web/src/parser.ts) duplicating Python logic

**Verified**: Side-by-side screenshot comparison confirms visual match with prototype
(same colors, spacing, opacity, note count, dang grouping).

### Phase 3: Multi-Column View + Data Loading [DONE]
- [x] Radif parser (Python, `.radif` file format) with CLI and manifest export
- [x] Radif strip renderer (TypeScript) with shared pitch axis
- [x] Horizontal connectors between shared notes across adjacent columns
- [x] Horizontal scrolling (overflow-x: auto on strip container)
- [x] Data service for loading multiple maayehs (fetch from manifest, filter by dastgah)
- [x] Root note selector, view mode toggles (sparse/grid/stretched), dark/light theme
- [x] Note names on shared pitch axis (C, D, E, F#, Ak, Bb, etc.)
- [x] Three-tier visual hierarchy: active notes (solid) > scale notes (faint fill) > grid (dashed empty)
- [x] Role markers: O for ist, X for shahed (centered in squares, dang-colored)
- [x] Self-contained strip layout (columns never shift when toggling controls)
- [ ] Goosheh selector per column (deferred, needs UI design)

**Verified**: 5 Mahur maayehs rendered side by side with connectors, shared pitch axis, all view modes working.

### Phase 4: Analysis Layer [DONE]
- [x] Interval content (multiset of pairwise intervals, vector form)
- [x] Melodic contour (sign sequence, verified: + + + - - + + - - -)
- [x] Modulation distance (pivot-based, best_modulation finds minimum distance)
- [x] Dang catalog (enumerate all valid: length 3-4, sum 9-11, modal families)
- [x] Topology: adjacency graph + distance matrix + shared-dang incidence
- [x] Column ordering (nearest-neighbor greedy traversal)
- [x] 13 analysis tests all passing (63 total)

**Verified**: Interval content for Mahur touched set correct (10 pairs). Melodic contour matches spec. Modulation pivots at qt=0,10,14 for Mahur/Shur. Identical maayehs have distance 0.

### Phase 5: Grid Editor [DONE]
- [x] Blank column with 48 clickable quarter-tone cells (2 octaves)
- [x] Toggle notes on/off by clicking
- [x] Real-time dang validation (detects 9-11 qt spans, shows dang/partial status)
- [x] Real-time text notation display (auto-generates interval string with | separators)
- [x] Note names on left, dang coloring of active cells
- [x] Export as .maayeh file download
- [x] Clear button to reset
- [x] Responds to root note / palette / theme changes
- [ ] Click-drag for ranges (deferred)
- [ ] Common dang presets (deferred)
- [ ] localStorage persistence (deferred)

**Verified**: Clicking cells at C,D,E,F,G,A,B,C produces notation `4 4 2 | 4 4 4 2` with correct dang detection.

### Phase 6: Database Management + Radif Composition [DONE]
- [x] Database browser: search by name/dastgah/tag, dastgah filter chips
- [x] Drag-and-drop reorder maayehs in the list (updates strip in real time)
- [x] Export radif order as `.radif` file download
- [x] Filtering updates the strip visualization live
- [ ] Tagging and multi-radif membership (deferred, needs backend)

### Phase 7: Computational Discovery [DONE]
- [x] Enumerate all valid dangs (319 total: 81 span-9, 104 span-10, 130 span-11)
- [x] Compare against database (4 cataloged from 6 maayehs, 315 uncataloged)
- [x] Tabbed display: Uncataloged / In Database, grouped by span
- [x] Each entry shows interval sequence and which maayehs use it

---

## Known Challenges and Decisions

1. **Boundary notes when gap=0**: Shared notes assigned to next dang (matching prototype). `dangIndices` array preserves both affiliations. `boundary` flag marks these notes.

2. **Build step friction**: Mitigated three ways: (a) `--watch` mode for auto-rebuild, (b) browser-side parser for quick preview, (c) grid editor feeds directly into strip view without requiring rebuild.

3. **Topology at scale**: Shared-dang connections are cheap (O(n*d)). Distance matrix stored for future extensions. Modulation distances computed lazily for large databases.

4. **Grid editor saving**: Downloads `.maayeh` file to user's filesystem. Also feeds the created maayeh directly into the browser view. localStorage for session state.

5. **Tuning assumption**: All values are integers (quarter-tones). A change to rational/float tuning would propagate to JSON schema, TypeScript types, and SVG rendering. Documented as a known limitation.

6. **Goosheh-level topology**: The topology primarily operates at the maayeh (scale) level. Goosheh-level refinements (melodic profile similarity) can be layered on as edge weights in future phases.

---

## Critical Files

| File | Purpose |
|------|---------|
| `maayeh-spec.md` | Authoritative specification |
| `daramad-mahur.html` | Visual fidelity target for the renderer |
| `schema/maayeh.schema.json` | Single source of truth for the Python-TypeScript contract |
| `src/maayeh/core/types.py` | All protocols and dataclasses defining the domain |
| `src/maayeh/core/definition.py` | MaayehDefinition = domain + metadata separation |
| `src/maayeh/parser/maayeh_parser.py` | Bridge between .maayeh files and domain objects |
| `src/maayeh/export/json_export.py` | Bridge between Python domain and TypeScript UI |
| `web/src/viz/maayeh-column.ts` | SVG column renderer |
| `web/src/parser.ts` | Browser-side parser for quick entry |

---

## Review Issues Addressed

| # | Issue | Resolution |
|---|-------|------------|
| 1 | Goosheh absent from data model | Added `--- goosheh ---` blocks in file format, `gooshehs` array in JSON, goosheh-aware rendering |
| 2 | `\|N\|` gap parsing ambiguous | Two-pass tokenizer: regex extracts explicit gaps first, then bare `\|` split |
| 3 | No type contract enforcement | JSON Schema file as single source of truth, validated on both sides, TS types generated |
| 4 | Round-trip not lossless | Gaps stored as `int \| None` (explicit vs. default), serializer reproduces original notation |
| 5 | Static build step too slow for interaction | Browser-side parser for quick preview, `--watch` mode, grid editor feeds strip directly |
| 6 | No bulk import | `parse_bulk()` for multi-document files, `python -m maayeh import` CLI command |
| 7 | `.radif` format undefined | Defined: header + ordered list of maayeh names |
| 8 | No schema version | `schemaVersion: 1` in every JSON file |
| 9 | Topology needs more than adjacency graph | Distance matrix + shared-dang incidence stored, future extensions documented |
| 10 | Column ordering unspecified | Greedy nearest-neighbor default, multiple orderings available |
| 11 | Melody null semantics | `null` = not provided (all touched), `[]` = explicitly empty |
| 12 | Interactive features silently omitted | Hover tooltips in Phase 2, audio/animation explicitly deferred |
| 13 | Boundary notes not represented | `boundary` flag + `dangIndices` array on Note |
| 14 | Domain/metadata coupling | `MaayehDefinition` separates `Maayeh` (domain) from `MaayehMetadata` |
