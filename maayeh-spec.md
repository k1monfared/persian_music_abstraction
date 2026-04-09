# Maayeh Representation System
## A Specification for Mathematical, Computational, and Visual Representation of Persian Modal Structures

---

## 1. Scope

This document defines a complete representation system for Persian classical music modal structures (*maayeh*, *dastgah*, *dang*), intended for a mathematician-musician who wants to:

- Input melodies and modal structures in a compact notation
- Produce formal mathematical representations
- Work with those representations computationally
- Perform analysis (interval content, modulation, melodic profile)
- Visualize results for print, web, and interactive use

The system is designed to be implementation-agnostic. The reader should be able to build it in any language or framework.

---

## 2. Primitive: The Quarter-Tone

The fundamental unit is the **quarter-tone** (qt), one quarter of a Western whole tone.

- 1 semitone = 2 qt
- 1 whole tone = 4 qt
- 1 perfect fourth ≈ 10–11 qt (depending on tuning)
- 1 octave = 24 qt (in equal quarter-tone temperament)

All intervals, positions, and distances in this system are expressed as non-negative integers in quarter-tones. Absolute pitch is never required; the system is always relative to a root.

---

## 3. Mathematical Objects

### 3.1 Interval Sequence

An **interval sequence** is a finite ordered list of positive integers:

```
I = (i₁, i₂, ..., iₙ)   where each iₖ ∈ ℤ⁺
```

Each element is the distance in quarter-tones from one note to the next.

### 3.2 Dang

A **dang** is an interval sequence of length 3 or 4, spanning approximately a perfect fourth (9–11 qt). The dang is the irreducible modal unit.

```
D = (i₁, i₂, ..., iₖ)   k ∈ {3, 4},   Σiₖ ∈ [9, 11]
```

### 3.3 Note Set

Given a dang D with root at position 0, the **note set** is the cumulative sum sequence:

```
N(D) = (0, i₁, i₁+i₂, ..., Σiₖ)
```

This is a sequence of k+1 absolute positions in qt, always starting at 0.

### 3.4 Maayeh

A **maayeh** is an ordered list of dangs with a defined gap between consecutive dangs:

```
M = (D₁, g₁, D₂, g₂, ..., Dₘ)
```

Where each gⱼ ∈ ℤ⁺ is the gap in qt from the last note of Dⱼ to the first note of Dⱼ₊₁.

The **full note set** of a maayeh is constructed by concatenating note sets with gaps applied, assigning each note a dang index. Boundary notes (the last note of Dⱼ and first of Dⱼ₊₁ when gap = 0) are shared; when gap > 0 they are distinct.

### 3.5 Degree

A **degree** is a 1-based index into the full note set of a maayeh. Degree 1 is always the root (position 0).

### 3.6 Role Assignment

Two special degrees are defined per maayeh per gusheh:

- **ist**: the tonal center / resting tone (an integer degree)
- **shahed**: the characteristic emphasized tone (an integer degree)

These are properties of a gusheh within a maayeh, not of the maayeh itself.

### 3.7 Melodic Profile

A **melodic profile** is an ordered sequence of degrees:

```
P = (d₁, d₂, ..., dₙ)   each dₖ ∈ {1, ..., |N(M)|}
```

The **touched set** T(P) ⊆ {1, ..., |N(M)|} is the set of unique degrees that appear in P.

---

## 4. Canonical Text Notation

The text notation is the input layer. It must be human-writable and machine-parseable.

### 4.1 Maayeh String

```
<dang> | <dang> | ...
```

- Each `<dang>` is a space-separated list of positive integers (interval sizes in qt)
- `|` is the dang separator
- The gap between dangs is always 4 qt unless explicitly overridden with `|<n>|` where n is the gap size
- Whitespace around `|` is ignored

Examples:
```
4 4 2 | 4 4 2
4 4 2 |6| 4 4 2
4 3 3 | 4 3 3
```

### 4.2 Annotation Block

Annotations follow the maayeh string as key-value pairs:

```
ist: <degree>
shahed: <degree>
melody: <degree> <degree> ...
name: <string>
```

All fields are optional. If `melody` is omitted, all notes are considered touched.

### 4.3 Full Input Example

```
4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
name: daramad mahur
```

---

## 5. Computational Representation

### 5.1 Note Object

```
Note {
  degree:   int          // 1-based index in full note set
  qt:       int          // absolute position in quarter-tones from root
  dang:     int          // 0-based dang index
  role:     'ist' | 'shahed' | null
  touched:  bool         // appears in melody
}
```

### 5.2 Maayeh Object

```
Maayeh {
  name:     string
  dangs:    int[][]      // each inner array is a dang's interval list
  gaps:     int[]        // gaps[i] = qt gap between dang i and dang i+1
  notes:    Note[]       // full ordered note set, 0-indexed (degree = index + 1)
  ist:      int          // degree (1-based)
  shahed:   int          // degree (1-based)
  melody:   int[]        // sequence of degrees
}
```

### 5.3 Parse Algorithm

```
function parse(input):
  parts = split input.intervals by '|'
  notes = []
  qt = 0
  for each (dang_intervals, dang_index) in parts:
    if notes is empty or notes.last.qt != qt:
      notes.append(Note(qt, dang_index))
    for each interval in dang_intervals:
      qt += interval
      notes.append(Note(qt, dang_index))
    if not last dang:
      qt += gap  // default 4
  assign degree = index + 1 for each note
  tag ist, shahed, touched from annotations
  return Maayeh
```

### 5.4 Derived Quantities

From a Maayeh object the following are directly computable:

- **interval_vector**: consecutive differences of qt values across all notes
- **touched_set**: set of degrees appearing in melody
- **range_qt**: qt of last note minus qt of first note
- **dang_span(i)**: sum of intervals in dang i
- **degree_to_qt(d)**: notes[d-1].qt
- **qt_to_degree(q)**: reverse lookup, null if q is not a note position

---

## 6. Analysis Operations

These are the operations a mathematician-musician would want to perform:

### 6.1 Interval Content

The **interval content** of a maayeh is the multiset of all pairwise intervals between notes in the touched set:

```
IC(M, T) = { |qt(a) - qt(b)| : a,b ∈ T, a ≠ b }
```

Useful for comparing modal color across maayehs.

### 6.2 Melodic Contour

The contour of a melody P is the sign sequence of consecutive differences:

```
C(P) = (sign(qt(d₂)-qt(d₁)), sign(qt(d₃)-qt(d₂)), ...)
```

Where sign ∈ {-1, 0, +1}. This abstracts the shape of the phrase independently of interval size.

### 6.3 Modulation

A **modulation** from maayeh M₁ to maayeh M₂ is defined by a **pivot degree**: a degree d₁ in M₁ and degree d₂ in M₂ such that qt(d₁) = qt(d₂) (same absolute pitch used as transition point).

The **modulation distance** is the minimum number of notes that must change between the two full note sets when aligned at the pivot.

### 6.4 Dang Similarity

Two dangs are **identical** if their interval sequences are equal. They are **transpositions** of each other always (since all positions are relative). A **modal family** is a set of maayehs that share at least one dang type.

---

## 7. Visual Representation

### 7.1 Coordinate System

The vertical axis is pitch, measured in quarter-tones, with 0 at the bottom (root). Each qt unit maps to a fixed pixel height `h` (recommended: 12–16px). The visual height of the full column is `range_qt × h`.

There is no required horizontal axis for the maayeh column alone. When a melody is shown, the horizontal axis is ordinal (event index), not temporal.

### 7.2 The Maayeh Column

The maayeh is represented as a vertical column of **note markers**. Each marker:

- Is a square of side `h - padding` (padding = 1–2px)
- Is centered horizontally in the column
- Is positioned so its bottom edge sits at `qt × h` from the bottom of the canvas
- Carries a color encoding (see §7.3)
- Carries an opacity encoding (see §7.4)

No grid lines are required. The spacing between markers encodes the interval visually.

### 7.3 Color Encoding

Color communicates dang membership and role. These two override each other: **role takes priority over dang**.

**Dang colors** should form an ordinal sequence — a gradient from warm to cool, or dark to light, that conveys register (low = warm, high = cool):

| Dang | Suggested Character |
|------|---------------------|
| 1    | warm / amber        |
| 2    | neutral-warm / olive|
| 3    | cool / slate        |
| 4    | deep / purple       |

**Role colors** must be visually distinct from all dang colors and from each other:

| Role   | Character                        |
|--------|----------------------------------|
| ist    | bright neutral (white or cream)  |
| shahed | bright warm accent (coral / red) |

### 7.4 Opacity Encoding

- Touched notes (appear in melody): opacity = 1.0
- Untouched notes (in maayeh but not melody): opacity = 0.4–0.6

If no melody is provided, all notes are fully opaque.

### 7.5 Multiple Columns

To compare two maayehs or show modulation, place columns side by side with a shared vertical axis. Align them at the pivot note (same qt position). Notes that exist in both are visually bridged with a horizontal connector.

### 7.6 Interactive Extensions

For web/interactive contexts:

- Hovering a note marker reveals: degree, qt position, dang index, role
- Clicking a note plays its pitch (if audio is available)
- A melody playback mode highlights notes sequentially as the melody progresses
- A modulation view allows selecting two maayehs and animating the transition between columns

### 7.7 Print Considerations

For print (color):
- Use fully opaque colors; avoid transparency
- Represent untouched notes with an outline-only style (no fill) rather than reduced opacity
- Ensure dang colors are distinguishable in CMYK

---

## 8. Completeness Constraints

An implementation is complete if it satisfies:

1. Any valid maayeh string (§4.1) can be parsed into a Maayeh object (§5.2)
2. The Maayeh object can reproduce the original interval string losslessly
3. All derived quantities (§5.4) are computable from the Maayeh object alone
4. The visual column (§7.2) can be rendered from the Maayeh object without additional input
5. Two Maayeh objects can be compared for modulation (§6.3) given a shared pitch reference

---

## 9. Examples

### Example 1: Daramad Mahur

```
4 4 2 | 4 4 2 | 4 4 2 | 4 4 2
ist: 1
shahed: 3
melody: 1 2 3 4 3 2 3 5 3 2 1
name: daramad mahur
```

**Parsed note set (first two dangs):**

| Degree | qt | Dang | Role    | Touched |
|--------|----|------|---------|---------|
| 1      | 0  | 0    | ist     | yes     |
| 2      | 4  | 0    |         | yes     |
| 3      | 8  | 0    | shahed  | yes     |
| 4      | 10 | 0    |         | yes     |
| 5      | 14 | 1    |         | yes     |
| 6      | 18 | 1    |         | no      |
| 7      | 22 | 1    |         | no      |
| 8      | 24 | 1    |         | no      |
| ...    |    |      |         |         |

**Interval vector:** `4 4 2 4 4 4 2 4 4 4 2 4 4 4 2`  
**Melodic contour:** `+ + + - - + + - - -`  
**Touched set:** `{1, 2, 3, 4, 5}`

---

### Example 2: Modulation from Mahur to Shur

Shur input:
```
3 4 3 | 4 3 4
ist: 1
shahed: 5
name: shur
```

Mahur's degree 5 (G, qt=14) and Shur's degree 1 (G, qt=0 when rooted on G) are the same absolute pitch. This is the pivot. The modulation distance is the number of note positions that differ between the two scales when aligned at G — in this case, degrees 2 and 3 change (D→D-koron, E→E-koron), giving a modulation distance of 2.
