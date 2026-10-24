# Script format

Every reel is one JSON file, `reels/queue/<id>.json`. `lib/build.py` turns it into the video using the
components in `lib/components.py`; `make.py` checks it first. Two complete working examples:
`reels/queue/2026-10-25-rotation-eigenvalues.json` (planes, vectors, matrices, equations) and
`reels/queue/2026-10-25-e-to-the-x.json` (axes, graphs, live trackers, morphing equations).
Once posted they move to `reels/posted/`; read a few there before writing a new one.

## Top level (comments below are for illustration only; JSON has none)

```json
{
 "id": "2026-10-26-fourier-series",          // YYYY-MM-DD-slug, same as the file name
 "topic": "fourier series",
 "subject": "math",                           // math, physics, chemistry, engineering, computing, biology, statistics
 "hook_type": "visual surprise",              // see STYLE.md
 "caption": "Instagram caption…\n\n#tags",
 "cover_at": 1.0,                             // seconds; the cover frame
 "hook": "Any shape can be drawn with spinning circles.",   // ≤ 14 words, shown big for ~2 s
 "sub": "Even this one.",                     // optional small line under the hook
 "beats": [ … ],
 "outro": "Follow for more ideas like this."  // optional
}
```
`make.py` adds `post_after`, `est_duration` and `approved`.

## Beats

```json
{"text": "One line the viewer reads, ≤ 24 words. Math in $...$ like $e^{i\\pi}$.",
 "do": [ step, step, … ]}
```
- The text stays up for its reading time (~3 words/s, min 2.2 s). Steps play one after another
  inside that time, sharing it. Give a step `"time": seconds` to control its length.
- A beat with no `text` is a quick transition (e.g. `{"do": [{"clear": true}]}`).
- JSON needs backslashes doubled: `"\\frac{a}{b}"`.

## Positions

- `"at": [x, y]` in screen units. The frame is 9 wide × 16 tall, center (0, 0).
  Keep visuals in x ∈ [-4, 4], y ∈ [-3.4, 6.2]; the caption lives below that.
- Spots: `"top"` (0, 5.2) · `"upper"` (0, 3.6) · `"mid"` (0, 1.6) · `"center"` (0, 0.4) · `"lower"` (0, -2.2).
- `"on": "P", "at": [1, 2]` → point (1, 2) in the coordinates of plane/axes `P`.
- `"next_to": "name", "side": "down", "buff": 0.4` → place beside something. Sides: up, down, left, right, ul, ur, dl, dr.

## Colors
`blue` (main idea) · `yellow` (the thing to notice) · `teal` · `brown` · `red` · `green` · `white` · `dim` ·
`purple` · `pink` · `orange`, or `"#rrggbb"`.

## Components: `{"make": "<kind>", "name": "...", …}`
Names must be unique (except after `clear`). Everything is animated in when made; add `"hidden": true`
to make something without showing it (e.g. a target for `transform`).

| kind | fields | notes |
| --- | --- | --- |
| `text` | `text`, `size` 60, `color`, `bold`, `width` 22, `write` | Short on-screen label (≤ 8 words). Math in `$...$`. |
| `tex` | `tex` (string or list of parts), `size` 84, `color`, `colors` | Equation. Split into parts to color them: `"tex": ["\\lambda", "= i"], "colors": {"0": "yellow"}`; or by content: `"colors": {"\\lambda": "yellow"}`. |
| `plane` | `range` [-3,3], `y_range`, `size` 7.2, `at` center, `complex` | Coordinate grid. `complex: true` for the complex plane. |
| `axes` | `x` [min,max,step], `y`, `size` [7.4, 6.0], `at`, `labels` ["x","y"], `numbers` | For graphs. |
| `graph` | `on` (axes), `fn` "sin(x) + x^2/4", `x` [a,b], `color` | Functions: sin cos tan exp log ln sqrt abs arctan sinh cosh tanh arcsin arccos floor sign maximum minimum pi e. |
| `curve` | `x` "cos(t)", `y` "sin(t)", `t` [0, 6.28], `on`, `color` | Parametric curve (orbits, spirals, Lissajous). |
| `vector` | `to` [x,y], `from` [0,0], `on`, `color`, `label` "\\vec v", `width` 9 | Glowing arrow. With `label`, the label is also `<name>.label`. |
| `span` | `on` (plane), `dir` [x,y], `color` | Dashed line through the origin along a direction, to the grid edge. |
| `dot` | `at`, `on`, `color`, `label`, `side` · or `follow` (graph) + `x` (tracker) · or `track` (tracker) + `on` + `y` "x^2" | Point. `follow` rides along a graph as the tracker moves. |
| `line` | `from`, `to`, `on`, `color`, `dashed`, `width` 4 | Segment. |
| `shape` | `kind` circle / arc / polygon / rect, `on`, `center`, `radius`, `start`/`angle` (deg), `points`, `w`/`h`, `color`, `fill` | Sizes in the units of `on` if given. |
| `box` | `around`, `color` yellow, `buff` 0.2 | Rounded glowing highlight box. |
| `brace` | `of`, `side` down, `text` or `tex`, `color` | Curly brace with a label. |
| `pointer` | `to` (name), `text` or `tex`, `side` right, `color` yellow, `buff` 1.2 | Label with an arrow pointing at something. |
| `numberline` | `range` [-3,3,1], `length` 7.6, `numbers` true, `at` | |
| `bars` | `values`, `labels`, `colors`, `max`, `step`, `size` [7.2, 5.0], `at` | Bar chart. |
| `tracker` | `name`, `value` | An invisible number to animate with `slide`. |
| `readout` | `tracker`, `fn` "x" (of the tracker), `label` "\\text{slope} =", `decimals` 2, `at` top, `color` | Live number. |
| `tangent` | `graph`, `x` (tracker), `length` 3, `color` | Tangent line that follows the tracker. |
| `area` | `graph`, `x` [a, b] (b may be a tracker name), `color`, `opacity` 0.35 | Shaded area under a graph. |
| `group` | `name`, `of` [names] | Bundle things to move/hide together (not animated). |

## Actions

| step | example | does |
| --- | --- | --- |
| `apply_matrix` | `{"apply_matrix": [[2,1],[1,2]], "to": ["v1","v2"], "on": "P"}` | Linear map about the plane's origin. Include the plane itself in `to` to warp the grid too (keep the matrix gentle or it leaves the frame). |
| `rotate` | `{"rotate": "z", "angle": 90, "on": "C", "about": [0,0]}` | Degrees, counter-clockwise. |
| `morph` | `{"morph": "eq", "into": {"make": "tex", "tex": "..."}}` | Equation becomes a new one; matching symbols glide over. The new one keeps the name. |
| `transform` | `{"transform": "a", "into": "b"}` | `a` becomes `b` (made earlier with `hidden`). |
| `move` | `{"move": "eqs", "to": [0, 4.9], "scale": 0.55}` / `"shift": [1, 0]` | |
| `slide` | `{"slide": "t", "to": 2.5, "time": 3}` | Animate a tracker; everything bound to it follows. |
| `indicate` | `{"indicate": ["a","b"], "color": "yellow"}` | Brief pulse. |
| `circle` | `{"circle": "eq"}` | Draws a ring around it once. |
| `flash` | `{"flash": "eq"}` | Burst of lines. |
| `wiggle` | `{"wiggle": "v"}` | |
| `recolor` | `{"recolor": "v", "color": "red"}` | |
| `hide` | `{"hide": ["a","b"]}` | Fade out and forget. |
| `trace` | `{"trace": "p", "color": "yellow"}` | Start drawing the path a dot leaves (pair with `slide`). |
| `together` | `{"together": [step, step], "lag": 0.2}` | Play steps at once (`lag` staggers them). |
| `clear` | `{"clear": true}` | Fade everything out (trackers survive). |
| `sfx` | `{"sfx": "ding"}` | pop · tick · whoosh · ding · chime · riser · thud. Pops on text, whooshes on clear, ding on the hook and chime on the outro are automatic. |
| `wait` | `{"wait": 0.5}` | ≤ 1.5 s. |

## Patterns that work
- **Build one picture and keep changing it.** Make a plane or axes in beat 1 and act on it for 3–4 beats before `clear`.
- **Equations stack then shrink:** write 2–3 lines under each other with `next_to`, `group` them, then
  `move` the group to `[0, 4.9]` with `scale: 0.55` and use the space below for a picture.
- **Remove a `box` before morphing** what it surrounds (`{"hide": "bx"}`), or it stays at the old size.
- **Live numbers:** `tracker` + `dot` (`follow`) + `readout` + `slide`; the viewer watches a number change.
- **Reveal:** `{"sfx": "riser"}` before writing the key result, `{"sfx": "ding"}` + `box` right after.
