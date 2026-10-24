# Style and content guide

Read this before writing a reel. One reel = one idea from math, physics, chemistry, statistics,
biology or computing, explained visually in 30–60 seconds with a calm narrated voice.

## The look (Manim, not a whiteboard)
- Dark background, clean geometry, LaTeX math, smooth transforms. The picture *is* the explanation:
  show the thing changing, don't show text describing it.
- Colors from `lib/reel.py`: `ACCENT` blue = the main object, `ACCENT2` yellow = the thing to notice,
  `ACCENT3` teal and `WARM` brown = a second/contrasting object, `BAD`/`GOOD` sparingly, `DIM` for scaffolding.
- Prefer Manim's motion: `Transform`, `ReplacementTransform`, `TransformMatchingTex`, `ApplyMatrix`,
  `ValueTracker` + `always_redraw`, `Indicate`, `Circumscribe`. Every line of narration should move something.
- Equations: `MathTex`, split into parts so pieces can be colored and transformed. Big (≥ 70) — it's a phone.
- No characters, mascots or logos from anyone else's channel. Original visuals only.

## Frame and safe zone (9 wide × 16 tall, origin at center)
- Keep everything inside x ∈ [-4, 4], y ∈ [-3.4, 6.2]. Captions sit at y ≈ -4.9 (handled by `say`).
- Instagram covers the bottom ~15% and a strip on the right with buttons. Nothing important there.
- `self.title(...)` puts a heading at y ≈ 5.3. Main diagram centered around y ≈ 1.

## Structure (~40 s)
1. `self.hook("...")` — one line, ≤ 10 words, a question or surprise. No "Hey guys", no "In this video".
2. 5–8 `with self.say("...") as t:` lines, each ≤ 18 words, each paired with an animation timed
   to `t.duration`. Build ONE picture and keep changing it rather than cutting between many.
3. The payoff: the moment it clicks, shown visually. Then one line naming the idea formally.
4. `self.outro()`.

## Narration
- Write for the ear: short sentences, plain words, "you", "notice", "watch". Name the formal term
  only after the intuition has landed.
- Narration strings must be plain literals (make.py reads them). The voice reads symbols poorly:
  write "e to the x", "x squared", "times", not symbols, in `say` text.
- Accuracy first. If a simplification is a simplification, say "roughly" or "for nice cases".

## Hooks (analyze.py tracks these as `hook_type`)
curiosity jump · everyday mystery · myth bust · wrong-answer reveal · visual surprise · exam pain · what it really means

## Metadata: `reels/queue/<id>.json`
```json
{"id": "2026-10-25-eigenvectors", "topic": "eigenvectors", "subject": "math",
 "hook_type": "curiosity jump", "caption": "...", "cover_at": 1.0}
```
- `id` = `YYYY-MM-DD-slug`; `subject` ∈ math, physics, chemistry, computing, biology, statistics.
- `caption`: 1–2 plain sentences restating the payoff, a save/share nudge, then 6–10 relevant hashtags.
- `make.py` adds `post_after`, `est_duration`, `hook`, `approved`.

## The 70/30 rule
Each day `analyze.py` plans 4 reels: once a hook has 3+ reels older than 48 h, 3 slots reuse the best
hook (new topics) and 1 slot explores another hook. Topics never repeat within the last 28 reels.
