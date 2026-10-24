# Daily run (the scheduled task follows this exactly)

You make 4 reels. They post today at 11:00, 15:00, 19:00 and 23:00 IST, one per slot.
Rendering happens on GitHub Actions; you write the scene, push, wait for the render, look at it, approve.

1. **Read the room.** `python3 analyze.py` (follow its plan; never estimate numbers yourself).
   Read `FEEDBACK.md` (Pranay's notes, they override everything) and `TOPICS.md` (requested topics
   go first). Read `STYLE.md` fully. Look at one existing scene in `reels/scenes/` for the pattern.

2. **For each slot, in order 11 → 15 → 19 → 23**, have the 11:00 reel approved by ~10:30 IST:
   1. Pick a topic per the plan: not used in the last 28 reels; mix subjects across the day.
   2. Check the content is correct. If you're not sure of a fact, pick a different angle or topic.
   3. Write `reels/scenes/<id>.py` and `reels/queue/<id>.json` (STYLE.md).
   4. `python3 make.py <id> --slot <hour>` until it prints PASS.
   5. `git add -A && git commit -m "Reel <id>" && git push`. This starts render.yml.
   6. Wait for the render: `gh run list --workflow render.yml --limit 3`, then
      `gh run watch <run-id> --exit-status`. It takes several minutes.
   7. If it failed: `gh run view <run-id> --log-failed`, fix the scene, make.py again, push again.
      Give up on a reel after 3 failed renders: drop it (`approve.py drop <id>`), say so, carry on.
   8. Download the contact sheet: `gh release download reel-<id> -p '*-sheet.png' -D /tmp/sheets --clobber`
      and look at it with the Read tool. Check: nothing cut off or outside the frame, no text overlapping
      other text or the diagram, captions readable, the payoff visible, equations rendered (not raw code).
      If anything is off, fix and push again (back to step 6).

3. **Approve** each reel only after it rendered and its sheet is right:
   `python3 approve.py approve <id>`, then `git add -A && git commit -m "Approve <id> [skip ci]" && git push`.
   `[skip ci]` matters: it stops a needless re-render. post.yml posts approved reels at their slot.
   Never approve a reel that failed or that you haven't looked at. Never post by hand.
   Respect a `PAUSED` file and any `"hold": true`.

4. **Clean up.** Remove topics you used from `TOPICS.md`. Commit and push (`[skip ci]`).

5. **Report** to Pranay in a few lines: each reel's topic, slot and preview link
   (`https://github.com/<owner>/<repo>/releases/tag/reel-<id>`), plus anything that broke and the fix.
   If something is broken that you can't fix in a few minutes (Instagram API error, expired token,
   Actions outage), say plainly what's wrong and what he needs to do. Don't guess.
