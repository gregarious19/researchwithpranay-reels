# Daily run (the scheduled task follows this exactly)

You make 4 reels for @researchwithpranay. They post today at 11:00, 15:00, 19:00 and 23:00 IST, one per slot.
Each reel is a JSON script; the library renders it. Never write Manim code for a reel.

1. **Set up.** `./setup_local.sh` (local Manim for previews; ~1 min the first time).
   `python3 analyze.py` (follow its plan; never estimate numbers yourself).
   Read `FEEDBACK.md` (Pranay's notes; they override everything), `TOPICS.md` (requested topics go first),
   `STYLE.md` and `SCRIPT_FORMAT.md` in full, and two scripts in `reels/posted/` (or `reels/queue/`).

2. **For each slot, in order 11 → 15 → 19 → 23** (have the 11:00 reel approved by ~10:30 IST):
   1. Pick a topic per the plan: not in the last 28 reels; mix subjects across the day.
   2. Work out the explanation and check every claim. If unsure of a fact, change the angle or topic.
   3. Write `reels/queue/<id>.json` (id = `YYYY-MM-DD-slug`, today's date).
   4. `python3 make.py <id> --slot <hour> --preview`. Fix until it prints PASS and the preview renders.
   5. Look at `out/<id>-sheet.png` with the Read tool. Check: nothing cut off or outside the frame,
      no text overlapping text or the picture, equations rendered (not raw code), each beat shows
      something new, the reveal is visible. If anything is off, fix the script and preview again.
   6. `git add reels/queue/<id>.json && git commit -m "Reel <id>" && git push`. This starts render.yml.
   7. Wait for it: `gh run list --workflow render.yml --limit 3`, then `gh run watch <run-id> --exit-status`.
      If it fails: `gh run view <run-id> --log-failed`, fix, push again. After 3 failures drop the reel
      (`python3 approve.py drop <id>`, commit, push), say so, and carry on.
   8. `python3 approve.py approve <id>`, then
      `git add -A && git commit -m "Approve <id> [skip ci]" && git push`.
      `[skip ci]` stops a needless re-render. post.yml posts approved reels at their slot.

   Never approve a reel whose preview you haven't looked at or whose render failed. Never post by hand.
   Respect a `PAUSED` file and any `"hold": true`.

3. **Clean up.** Remove used topics from `TOPICS.md`; commit and push with `[skip ci]`.

4. **Report** to Pranay in a few lines: each reel's topic, slot and preview link
   (`https://github.com/<owner>/<repo>/releases/tag/reel-<id>`), plus anything that broke and the fix.
   If something is broken that you can't fix in a few minutes (Instagram API error, expired token,
   Actions outage), say plainly what's wrong and what he needs to do. Don't guess.

**If a script needs something the library can't do**, don't hack around it in the script: pick a
different visual approach that the components support, and note the missing component in your report.
