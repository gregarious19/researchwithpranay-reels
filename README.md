# @researchwithpranay reels

Five reels a day explaining complex ideas in math, science and engineering through the math,
animated in the style of 3Blue1Brown with [Manim](https://www.manim.community). On-screen text and
original sound effects, no voice. Written, rendered and posted automatically.

```
Claude (daily scheduled task)                    GitHub Actions
  analyze.py → learn + plan 5 reels                render.yml   on push → Manim → MP4 + sheet → release reel-<id>
  write reels/queue/<id>.json (a script)           post.yml     11/15/19/23/02 IST → posts the next approved due reel
  make.py --preview → check the frames             insights.yml 07:00 IST → metrics → data/insights.json
  push → wait for render → approve                 (and refreshes the Instagram token every Monday)
```

**How a reel is made:** Claude writes a JSON *script* (lines of text plus steps like "make a plane",
"add a vector", "apply this matrix", "plot e^x", "slide the point"). `lib/build.py` plays it using the
component library in `lib/components.py`. See `SCRIPT_FORMAT.md`.

**Cost:** ₹0. GitHub Actions is free for public repos; every sound is synthesized in code.

## Steering it
- **Topics you want:** add a line to `TOPICS.md`. They go first.
- **Anything else** (tone, subjects to avoid, more physics, …): write it in `FEEDBACK.md`.
- **Hold one reel:** edit its `reels/queue/<id>.json` on GitHub and add `"hold": true`.
- **Pause everything:** add an empty file named `PAUSED` at the repo root. Delete it to resume.
- **Post one now:** Actions → Post reel to Instagram → Run workflow (optionally give a spec path).

## One-time setup

### 1. Instagram account
In the Instagram app on @researchwithpranay: Settings → *Account type and tools* → switch to a
**Creator** or **Business** account. The account must be public.

### 2. Meta app and token
If you already have the Meta app you made for Chalkwise reels, open it and skip to step 4.
1. Go to [developers.facebook.com](https://developers.facebook.com) and log in.
2. **My Apps → Create App.** Use case **Other** → type **Business** → any name.
3. On the app dashboard, find **Instagram** and click **Set up** ("API setup with Instagram login").
4. Under **Generate access tokens**, click **Add account** and log in as **@researchwithpranay**. Keep
   `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights` ticked.
5. Click **Generate token** next to @researchwithpranay and copy it. Note its Instagram **user ID** too.

The app can stay in development mode: it only posts to your own accounts.

### 3. GitHub secrets
Repo → Settings → *Secrets and variables* → Actions → **New repository secret**:

| Secret | Value | Needed for |
| --- | --- | --- |
| `IG_ACCESS_TOKEN` | the @researchwithpranay token from step 2.5 | posting, insights |
| `IG_USER_ID` | its Instagram user ID | posting, insights (optional, looked up if missing) |
| `GH_PAT` | a fine-grained GitHub token with **Secrets: read and write** on this repo | saving the refreshed Instagram token every Monday |

Optional *variables* (Variables tab): `IG_API_VERSION` (default `v24.0`), `REEL_HANDLE` (default `@researchwithpranay`).

### 4. Test
Actions → **Pull Instagram insights** → Run workflow. A green run means the token works.

## Files

| Path | What |
| --- | --- |
| `DAILY_RUN.md` | The exact daily steps Claude follows |
| `STYLE.md` | Account voice, topics, structure, look |
| `SCRIPT_FORMAT.md` | Every component and action a script can use |
| `lib/components.py` | The component library (makers and actions) |
| `lib/build.py` | Plays a script as a Manim scene |
| `lib/reel.py` | Look and frame: black, Inter, palette, timed text, hook, outro, encoding |
| `lib/sfx.py` | Synthesized sound effects and background pad |
| `make.py` | Checks a script, sets its slot, renders a local preview (`--preview`) |
| `setup_local.sh` | Local Manim for previews inside a Claude workspace |
| `finish.sh` | Loudness normalization for Instagram |
| `approve.py` / `analyze.py` / `ig.py` | Approve/hold/drop · performance plan · Instagram API |
| `reels/queue/` → `reels/posted/` | Scripts waiting to post, then posted (with permalink) |
| `data/insights.json` | Daily metric snapshots |
| `LEARNINGS.md` | What the data has taught so far (updated by the daily run) |
| `TOPICS.md` / `FEEDBACK.md` | Your requests and notes for Claude |
