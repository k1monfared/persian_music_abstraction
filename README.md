# Maayeh (مایه)

**Status**: 🟡 MVP | **Mode**: 🤖 Claude Code | **Updated**: 2026-04-08

**[Live Demo](https://k1monfared.github.io/persian_music_abstraction/)**

A system for mathematical, computational, and visual representation of Persian classical music modal structures (maayeh, dastgah, dang). Input melodies and modal structures in a compact notation, compute formal mathematical representations, and visualize results as interactive side-by-side columns.

## Overview

Persian classical music is built on a system of modes (dastgah) composed of tetrachordal units (dang). Each dang is a sequence of 3-4 intervals measured in quarter-tones that spans roughly a perfect fourth. Maayehs (modal structures) are built by stacking dangs with gaps between them.

This system provides:

- A **human-readable text notation** for defining maayehs (`.maayeh` files)
- A **Python core library** for parsing, computation, and analysis
- An **interactive web visualization** showing maayehs as vertical columns of colored squares
- **Mathematical analysis** tools: interval content, melodic contour, modulation distance, topology
- A **grid editor** for creating new maayehs visually
- A **discovery panel** that enumerates all valid dang structures and identifies uncataloged ones

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### Installation

```bash
# Install Python package
pip install -e ".[dev]"

# Install web dependencies
cd web && npm install && cd ..
```

### Build and Run

```bash
# Build JSON data from .maayeh files
python -m maayeh build

# Start the web visualization
cd web && npx vite
```

Open `http://localhost:5173` in your browser.

## The .maayeh Text Format

Each maayeh is a human-readable text file. The interval line uses space-separated integers (quarter-tones) with `|` separating dangs:

```
--- maayeh ---
name: daramad-mahur
dastgah: mahur
tags: daramad, tetrachord

4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
```

### Format details

- **Header**: `--- maayeh ---` identifies the file type
- **Metadata**: key-value pairs (name, dastgah, radifs, tags) before the interval line
- **Interval line**: the first line of only digits, spaces, and pipes. Each group between `|` is one dang. Default gap between dangs is 4 qt. Use `|N|` for an explicit gap of N qt (e.g., `|6|`)
- **Annotations**: ist (tonal center degree), shahed (emphasized tone degree), melody (degree sequence)
- **Goosheh blocks**: multiple `--- goosheh ---` sections can follow, each with its own ist/shahed/melody

### Quarter-tone system

The fundamental unit is the quarter-tone (qt): 1/4 of a Western whole tone.

| Interval | Quarter-tones |
|----------|---------------|
| Semitone | 2 qt |
| Neutral tone (koron) | 3 qt |
| Whole tone | 4 qt |
| Perfect fourth | ~10 qt |
| Octave | 24 qt |

### Dang constraints

A valid dang has 3 or 4 intervals, each a positive integer, summing to 9, 10, or 11 qt. Common examples:

| Name | Intervals | Span |
|------|-----------|------|
| Mahur (major) | 4 4 2 | 10 qt |
| Shur | 3 4 3 | 10 qt |
| Chahargah | 2 6 2 | 10 qt |

## CLI Commands

```bash
# Parse all .maayeh files and export JSON
python -m maayeh build

# Build with radif index support
python -m maayeh build --radifs-dir data/radifs

# Validate a single file
python -m maayeh validate data/maayehs/daramad-mahur.maayeh

# Import a bulk file (multiple --- maayeh --- blocks) into individual files
python -m maayeh import bulk-input.txt --output-dir data/maayehs
```

## Web Visualization

The web UI shows maayehs as vertical columns of colored squares, where each square is a note and vertical position represents pitch.

### Controls

- **Root**: select the root note (C, D, E, F, G, A, B) to see note names
- **View mode**: three display modes
  - **Sparse**: only note positions shown, gaps empty
  - **Grid**: dashed empty squares at every quarter-tone position
  - **Stretched**: notes stretch vertically to fill the interval space
- **A B C**: toggle note names on the pitch axis
- **Light/Dark**: theme toggle

### Visual encoding

- **Dang colors**: warm-to-cool gradient (amber, olive, blue, purple) indicating register
- **Active notes**: solid fill at full opacity (appear in the melody)
- **Scale notes**: faint fill (in the maayeh but not in the melody)
- **Grid positions**: dashed outline, dang-colored at very low opacity
- **Ist (tonal center)**: circle marker (O) inside the square
- **Shahed (characteristic tone)**: cross marker (X) inside the square
- **Connectors**: thin lines between adjacent columns at shared pitch positions
- **Note names**: shown on the pitch axis with Persian accidentals (koron, sori)

### Sections

1. **Dastgah-e Mahur**: the main strip showing maayeh columns side by side
2. **Database**: search, filter, and drag-to-reorder maayehs. Export as `.radif` file.
3. **Editor**: click quarter-tone cells to build a new maayeh visually. See real-time notation and export as `.maayeh` file.
4. **Discovery**: browse all 319 valid dang structures. See which are in the database (4) and which are uncataloged (315).

## Project Structure

```
persian_music_abstraction/
  src/maayeh/               # Python core library
    core/                   # Domain types (Dang, Note, Maayeh, Goosheh)
    parser/                 # .maayeh and .radif text parsers
    analysis/               # Interval content, contour, modulation, topology
    export/                 # JSON export with schema validation
    cli.py                  # CLI entry point

  web/                      # TypeScript web UI
    src/
      viz/                  # SVG renderers (column, pitch axis, connectors)
      ui/                   # App, database browser, grid editor, discovery
      parser.ts             # Browser-side .maayeh parser
      types.ts              # JSON schema types

  data/                     # Human-readable database
    maayehs/                # .maayeh files (one per maayeh)
    radifs/                 # Radif index directories

  schema/                   # JSON Schema (Python-TypeScript contract)
  tests/                    # Python tests (63 passing)
  plans/                    # Implementation plan
```

## Architecture

The system has two sides connected by JSON:

```
.maayeh files --> Python parser --> JSON files --> TypeScript UI --> SVG
  (human)          (build step)     (computed)     (static site)    (visual)
```

- **Python** handles all parsing, domain logic, mathematical analysis, and JSON export
- **TypeScript** handles all rendering, interaction, and browser-side features
- **JSON Schema** (`schema/maayeh.schema.json`) is the single source of truth for the data contract between the two languages

### Abstraction strategy

- Domain objects (`Maayeh`, `Dang`, `Note`, `Goosheh`) are immutable dataclasses with no rendering state
- `MaayehDefinition` separates the musical domain from storage metadata
- Derived quantities (interval vector, range, touched set) are computed properties
- The analysis layer operates on domain objects, never on JSON
- The visualization layer reads JSON and produces SVG, with configurable palettes and layouts

## Analysis Operations

The Python analysis layer (spec section 6) provides:

- **Interval content**: multiset of all pairwise intervals between notes in the touched set
- **Melodic contour**: sign sequence (+/-/0) of consecutive pitch changes, abstracting phrase shape
- **Modulation distance**: number of differing note positions when two maayehs are aligned at a pivot
- **Dang catalog**: enumeration of all valid dang interval sequences (319 total)
- **Modal families**: grouping maayehs by shared dang types
- **Topology graph**: adjacency graph with distance matrix and nearest-neighbor ordering

## Data Files

The repository includes 6 maayeh definitions:

| Name | Dastgah | Dangs | Notes | Description |
|------|---------|-------|-------|-------------|
| daramad-mahur | mahur | 4 | 16 | Full Mahur scale, 4 major tetrachords |
| kereshmeh-mahur | mahur | 2 | 8 | Rhythmic pattern, lower register |
| dadgah-mahur | mahur | 2 | 8 | Dominant-centered, same intervals |
| delkash | mahur | 2 | 8 | Modulation to Shur-like upper tetrachord (3 3 4) |
| rak-mahur | mahur | 3 | 12 | Upper register, 3 major tetrachords |
| shur | shur | 2 | 8 | Base Shur scale (3 4 3, 4 3 4) |

## Testing

```bash
# Run all Python tests
python -m pytest tests/ -v

# Type-check TypeScript
cd web && npx tsc --noEmit
```

63 Python tests covering: core domain types, parser (tokenizer, round-trip serialization, goosheh blocks, bulk parsing), JSON export with schema validation, and analysis operations (interval content, contour, modulation, dang catalog, topology).

## Specification

The formal specification is in `maayeh-spec.md`. It defines the mathematical objects, text notation, computational representation, analysis operations, and visual encoding used throughout the system.

## License

MIT
