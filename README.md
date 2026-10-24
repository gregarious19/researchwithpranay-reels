# Explainer reels

Four 30–60 second Instagram reels a day explaining math, physics, chemistry, statistics, biology and
computing ideas, animated with [Manim](https://www.manim.community) and narrated by a free voice
(Kokoro-82M). Made and posted automatically.

```
Claude (daily, scheduled task)              GitHub Actions
  analyze.py → plan 4 reels                   render.yml   on push → Manim + voice → MP4 + contact sheet → release reel-<id>
  write reels/scenes/<id>.py + queue/<id>.json post.yml     11/15/19/23 IST → posts the next approved due reel
  push → wait for render → check sheet         insights.yml 08:00 IST → metrics → data/insights.json
  approve                                      (and refreshes the Instagram token every Monday)
```

**Cost:** ₹0. GitHub Actions is free for public repos, and the voice runs inside Actions.

## Steering it
- **Topics you want:** add a line to `TOPICS.md`. They go first.
- **Anything else** (tone, voice, subjects to avoid): write it in `FEEDBACK.md`.
- **Hold one reel:** edit its `reels/queue/<id>.json` on GitHub and add `"hold": true`.
- **Pause everything:** add an empty file named `PAUSED` at the repo root. Delete it to resume.
- **Sound:** no voice; on-screen text plus original synthesized sound effects (`lib/sfx.py`).
- **Your handle on the outro:** repo variable `REEL_HANDLE`, e.g. `@yourhandle`.

## One-time setup

### 1. Instagram account
In the Instagram app: Settings → *Account type and tools* → switch to a **Creator** or **Business** account. The account must be public.

### 2. Meta developer app
1. Go to [developers.facebook.com](https://developers.facebook.com), log in with the Facebook account you want to own the app, and register as a developer if asked.
2. **My Apps → Create App.** Use case: **Other** → app type: **Business** → name it "Explainer Reels" and add your email.
3. On the app dashboard, find the **Instagram** product and click **Set up**. "API setup with Instagram login" is added automatically.
4. Under **Generate access tokens**, click **Add account** and log in to the new Instagram account. Keep these permissions ticked: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`.
5. Click **Generate token** next to the account and copy it. Also note the Instagram **user ID** shown next to the account.

The app can stay in development mode: it only ever posts to your own account, which already has a role on the app.

### 3. GitHub secrets
Repo → Settings → *Secrets and variables* → Actions → **New repository secret**:

| Secret | Value | Needed for |
| --- | --- | --- |
| `IG_ACCESS_TOKEN` | the token from step 2.5 | posting, insights |
| `IG_USER_ID` | the Instagram user ID | posting, insights (optional, looked up if missing) |
| `GH_PAT` | a fine-grained GitHub token with **Secrets: read and write** on this repo | saving the refreshed Instagram token every Monday |

Optional *variable* (same page, Variables tab): `IG_API_VERSION` (default `v24.0`).

### 4. Test
Actions → **Pull Instagram insights** → Run workflow. A green run means the token works.

## Files

| Path | What |
| --- | --- |
| `DAILY_RUN.md` | The exact daily steps Claude follows |
| `STYLE.md` | Look, structure, narration rules, metadata format |
| `lib/reel.py` | Shared Manim base: vertical frame, colors, voice, captions, hook, outro |
| `reels/scenes/<id>.py` | One Manim scene per reel |
| `reels/queue/<id>.json` | Its caption and posting slot; moves to `reels/posted/` once posted |
| `make.py` | Pre-push checks (length, caption size, structure) and slot assignment |
| `approve.py` | Approve / hold / drop a queued reel |
| `analyze.py` | Performance summary and today's plan |
| `ig.py` | Instagram API: check, publish, insights, token refresh |
| `TOPICS.md` / `FEEDBACK.md` | Your requests and notes for Claude |
