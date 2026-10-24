# Style and content guide: @researchwithpranay

Read this before writing a reel. Then read SCRIPT_FORMAT.md for how to build it.

## What this account is
Complex ideas from math, physics, chemistry, engineering, computing, statistics and biology,
**explained through the math**, in the visual style of 3Blue1Brown. One reel = one idea, 30–90 s
(quality over brevity). No voice: the viewer reads short lines while the picture does the explaining,
with sound effects for rhythm.

Audience: university students, engineers and researchers who know some math and want to *see why*
something is true. Don't dumb it down; make it clear. Assume high-school calculus and basic linear
algebra; introduce anything beyond that in a line.

## Topic ideas (one idea each, never a survey)
- Math: eigenvectors, determinants as area, complex multiplication as rotation, Fourier series, Taylor
  series, why e is special, convolution, the central limit theorem, gradient as steepest ascent.
- Physics: why orbits are ellipses, simple harmonic motion as a rotating vector, wave interference,
  entropy counting, special relativity's light clock, Schrödinger's equation as rotation in time.
- Engineering: transfer functions and poles, why bridges resonate, PID control, signal sampling and
  aliasing, Fourier transforms in filters, stress and strain, the Kalman filter's idea.
- Computing / ML: gradient descent on a loss surface, attention as weighted averages, why neural nets
  need nonlinearity, PCA as finding the stretch directions, hashing, the FFT's trick.
- Chemistry / biology: half-life as e^(-kt), equilibrium as balancing rates, diffusion as random walks,
  logistic population growth.
Pick angles where a picture changes your understanding, not just decorates it.

## The look (built into lib/: don't fight it)
- Pure black background, Inter for words, LaTeX for math, glowing slim arrows, fine grids.
- Colors carry meaning: `blue` = main object, `yellow` = the thing to notice, `teal`/`brown` = second and
  third objects, `red` = failure/contradiction, `green` = success. Same object keeps its color throughout.
- Prefer motion that *is* the explanation: `apply_matrix`, `rotate`, `slide` a tracker, `morph` equations.
  Every beat should change something on screen.

## Structure
1. **Hook** (≤ 14 words): a surprising claim or question. No "Did you know", no "In this video".
2. **Set up** the object (1–2 beats): show it, name it.
3. **Recall** the one definition the viewer needs ("Remember, an eigenvector stays on its own span.").
4. **Tension**: show the naive expectation failing, or a surprising fact.
5. **Reveal**: the key insight, shown visually, with `riser` → result → `ding` + `box`.
6. **Generalize** in one line: what this means beyond the example.
Typical: 7–11 beats.

## Writing the lines (Grant Sanderson's teaching tone, in text)
- Calm, curious, precise. Invite the viewer to notice: "Watch what happens to…", "Notice that…",
  "And yet, if you dutifully compute…", "Is that nonsense? Not at all."
- Intuition before formalism; name the formal term only after the idea has landed.
- Use exact words (span, linear, proportional) but explain them the first time.
- Short clauses, one idea per line, ≤ 24 words. Math inline as `$...$`.
- **Accuracy first.** If something is a simplification, say "roughly" or "in the simplest case".
  If you are not sure a claim is exactly right, choose a different angle or topic.

## Hooks (`hook_type`, tracked by analyze.py)
curiosity jump · everyday mystery · myth bust · wrong-answer reveal · visual surprise · exam pain · what it really means

## Caption
1–2 plain sentences restating the payoff, one save/share nudge, then 6–10 relevant hashtags
(e.g. #math #physics #engineering #linearalgebra #calculus #stem #machinelearning #science).

## The 70/30 rule
Each day `analyze.py` plans 4 reels. Once a hook has 3+ reels older than 48 h, 3 slots reuse the best
hook (new topics) and 1 slot explores another hook. Topics never repeat within the last 28 reels.
Mix subjects across the day.
