# Daily run (the scheduled task follows this exactly)

You make 5 reels for @researchwithpranay. They post at 11:00, 15:00, 19:00, 23:00 IST today and 02:00 IST
tonight (the night after), one per slot. Each reel is a JSON script; the library renders it.
Never write Manim code for a reel.

1. **Set up.** `./setup_local.sh` (local Manim for previews; ~1 min the first time).
   `git pull`, then check `data/insights.json` was updated today (insights.yml pulls it at 07:00 IST).
   If not, start it yourself with the GitHub MCP tool `actions_run_trigger` (method `run_workflow`,
   workflow `insights.yml`, ref `main`), wait for that run to finish, `git pull`, and check again.
   If it still isn't there, carry on and mention it in your report.

2. **Learn from the past.** `python3 analyze.py` and read all of it. Never estimate numbers yourself.
   - Open the scripts of the best and worst reels it lists (`reels/posted/<id>.json`) and compare them:
     hook wording, first beat, how fast the picture appears, where the reveal lands, text per beat, visuals.
   - Update `LEARNINGS.md`: add at most 2 new lessons, each tied to numbers analyze.py printed and the reels
     that show it; remove or correct any lesson the data now contradicts. Keep it under ~40 lines.
   - Read `LEARNINGS.md`, `FEEDBACK.md` (Pranay's notes; they override everything), `TOPICS.md` (requested
     topics go first), `STYLE.md` and `SCRIPT_FORMAT.md` in full.
   - Today's reels follow analyze.py's plan (which hook / visual / length to keep in exploit slots, what to test
     in the explore slot, how to spread subjects) and the lessons in LEARNINGS.md.

   `python3 approve.py list`: a slot that already holds a queued reel (approved or not) is taken;
   make reels only for the free slots, and leave existing queued reels alone (Pranay may have put them there).

3. **For each free slot, in order 11 → 15 → 19 → 23 → 02** (have the 11:00 reel approved by ~10:30 IST):
   1. Pick a topic per the plan and LEARNINGS.md: not in the last 28 reels; mix subjects across the day.
      Set `hook_type` and `subject` honestly; they are what analyze.py learns from.
   2. Work out the explanation and check every claim. If unsure of a fact, change the angle or topic.
   3. Write `reels/queue/<id>.json` (id = `YYYY-MM-DD-slug`, today's date).
   4. `python3 make.py <id> --slot <hour> --preview`. Fix until it prints PASS and the preview renders.
   5. Look at `out/<id>-sheet.png` with the Read tool. Check: nothing cut off or outside the frame,
      no text overlapping text or the picture, equations rendered (not raw code), each beat shows
      something new, the reveal is visible. If anything is off, fix the script and preview again.
   6. `git add reels/queue/<id>.json && git commit -m "Reel <id>" && git push`. This starts render.yml.
   7. Wait for it: `gh run list --workflow render.yml --limit 3`, then `gh run watch <run-id> --exit-status`
      (run it in the background; a render takes ~5–10 min, so script the next reel meanwhile).
      Use `gh api` (REST) for anything else; `gh release …`/`gh workflow run` don't work from sessions.
      Confirm the release has both files:
      `gh api repos/<owner>/<repo>/releases/tags/reel-<id> --jq '[.assets[].name]'`.
      If it fails: `gh api repos/<owner>/<repo>/actions/runs/<run-id>/jobs --jq '.jobs[].steps[] | "\(.name)=\(.conclusion)"'`
      shows the failing step; reproduce it locally with `make.py <id> --preview`, fix, push again.
      After 3 failures drop the reel (`python3 approve.py drop <id>`, commit, push), say so, and carry on.
   8. `python3 approve.py approve <id>`, then
      `git add -A && git commit -m "Approve <id> [skip ci]" && git push`.
      `[skip ci]` stops a needless re-render. post.yml posts approved reels at their slot.

   Never approve a reel whose preview you haven't looked at or whose render failed. Never post by hand.
   Respect a `PAUSED` file and any `"hold": true`.

4. **Clean up.** Remove used topics from `TOPICS.md`. Commit `TOPICS.md` and `LEARNINGS.md` and push with `[skip ci]`.

5. **Report** to Pranay in a few lines: what the data says is working (one line, with numbers), each reel's topic, slot and preview link
   (`https://github.com/<owner>/<repo>/releases/tag/reel-<id>`), plus anything that broke and the fix.
   If something is broken that you can't fix in a few minutes (Instagram API error, expired token,
   Actions outage), say plainly what's wrong and what he needs to do. Don't guess.

**If a script needs something the library can't do**, don't hack around it in the script: pick a
different visual approach that the components support, and note the missing component in your report.
