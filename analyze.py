#!/usr/bin/env python3
"""What's working, from the numbers. Prints markdown; changes nothing.

    python3 analyze.py

Reads data/insights.json (pulled daily at 07:00 IST) and reels/posted/*.json. For every posted reel:
views, hold rate (avg watch time / length), share+save rate and comment rate. Then:
- best and worst reels (with their hooks), to learn from concretely
- averages by hook type, subject, visual style, length, number of beats and posting slot
  (only reels at least 48 h old count; a group needs 3+ reels before it's called a winner)
- a plan for today's 5 reels: 4 exploit what works, 1 explores something new (rotating what's tested)
"""
import datetime, glob, json, os

from make import SLOTS, IST, visual_style

HOOKS = ["curiosity jump", "everyday mystery", "myth bust", "wrong-answer reveal", "visual surprise",
         "exam pain", "what it really means"]
SUBJECTS = ["math", "physics", "engineering", "computing", "statistics", "chemistry", "biology"]
VISUALS = ["geometry", "graph", "equations", "data"]
MIN_N = 3          # reels per group before it can be called best
MATURE_H = 48      # hours before a reel's numbers count


def slot_of(ts):
    """Posting slot a reel went out in: the latest slot at or before its IST post time."""
    h = ts.astimezone(IST).hour
    past = sorted(x for x in SLOTS if x <= h)
    return f"{(past[-1] if past else max(SLOTS)):02d}:00"


def bucket_len(d):
    return "<45s" if d < 45 else ("45-59s" if d < 60 else ("60-74s" if d < 75 else "75s+"))


def bucket_beats(n):
    return "≤7 beats" if n <= 7 else ("8-10 beats" if n <= 10 else "11+ beats")


def load():
    db = json.load(open("data/insights.json")) if os.path.exists("data/insights.json") else {}
    now = datetime.datetime.now(datetime.timezone.utc)
    rows = []
    for p in sorted(glob.glob("reels/posted/*.json")):
        s = json.load(open(p))
        lat = db.get(s["id"], {}).get("latest", {})
        ts = (s.get("posted") or {}).get("timestamp")
        age_h = slot = None
        if ts:
            try:
                t = datetime.datetime.fromisoformat(ts.replace("+0000", "+00:00"))
                age_h, slot = (now - t).total_seconds() / 3600, slot_of(t)
            except ValueError:
                pass
        dur = s.get("duration") or s.get("est_duration") or 0
        reach = lat.get("reach") or 0
        awt = lat.get("ig_reels_avg_watch_time")
        beats = len([b for b in s.get("beats", []) if b.get("text")])
        rows.append({
            "id": s["id"], "topic": s.get("topic"), "hook": s.get("hook", ""), "hook_type": s.get("hook_type"),
            "subject": s.get("subject"), "visual": s.get("visual") or visual_style(s), "duration": dur,
            "length": bucket_len(dur), "beats": bucket_beats(beats), "age_h": age_h, "slot": slot,
            "views": lat.get("views"), "reach": reach,
            "hold": (awt / 1000 / dur) if (awt and dur) else None,
            "share_save": ((lat.get("shares") or 0) + (lat.get("saved") or 0)) / reach if reach else None,
            "comment": (lat.get("comments") or 0) / reach if reach else None,
            "has_data": bool(lat),
            "errors": [e for snap in db.get(s["id"], {}).get("snapshots", [])[-1:] for e in snap.get("_errors", [])],
        })
    return rows, db.get("_account", [])


def pct(x):
    return "–" if x is None else f"{x * 100:.1f}%"


def main():
    rows, acct = load()
    mature = [r for r in rows if r["has_data"] and (r["age_h"] or 0) >= MATURE_H and r["hold"] is not None]

    print("## Account\n")
    if acct:
        a = acct[-1]
        first = next((x.get("followers_count") for x in acct if x.get("followers_count") is not None), None)
        print(f"@{a.get('username', '?')}: {a.get('followers_count', '–')} followers "
              f"(first record {first}), {a.get('media_count', '–')} posts.")
        if a.get("account_error") or a.get("token_error"):
            print(f"\n**API problem:** {a.get('token_error') or a.get('account_error')}")
    else:
        print("No account data yet.")
    print()

    print(f"## Reels ({len(rows)} posted, {len(mature)} at least {MATURE_H} h old)\n")
    if rows:
        print("| reel | hook type | subject | visual | len | slot | age | views | hold | share+save | comments |")
        print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in rows[-20:]:
            age = "–" if r["age_h"] is None else f"{r['age_h']:.0f}h"
            v = "no data yet" if not r["has_data"] else (r["views"] if r["views"] is not None else "–")
            print(f"| {r['id']} | {r['hook_type']} | {r['subject']} | {r['visual']} | {r['duration']:.0f}s | "
                  f"{r['slot'] or '–'} | {age} | {v} | {pct(r['hold'])} | {pct(r['share_save'])} | {pct(r['comment'])} |")
        print()
    errs = [(r["id"], e) for r in rows for e in r["errors"]]
    if errs:
        print("**API problems:** " + "; ".join(f"{i}: {e}" for i, e in errs[:5]) + "\n")

    if len(mature) >= 4:
        ranked = sorted(mature, key=lambda r: r["hold"], reverse=True)
        print("## Learn from these (by hold rate)\n")
        for label, group in (("Best", ranked[:3]), ("Worst", ranked[-3:][::-1])):
            print(f"**{label}:**")
            for r in group:
                print(f"- {pct(r['hold'])} hold, {pct(r['share_save'])} share+save, {r['views']} views — "
                      f"*{r['topic']}* ({r['subject']}, {r['visual']}, {r['hook_type']}, {r['duration']:.0f}s, "
                      f"{r['beats']}, {r['slot']}). Hook: \"{r['hook']}\"")
            print()
        print("Open the best and worst scripts in reels/posted/ and compare: hook wording, first beat, "
              "where the reveal lands, how much text per beat.\n")

    print(f"## What works (groups with {MIN_N}+ mature reels can win)\n")
    best = {}
    for key in ("hook_type", "subject", "visual", "length", "beats", "slot"):
        groups = {}
        for r in mature:
            groups.setdefault(r[key], []).append(r)
        if not groups:
            continue
        print(f"**By {key.replace('_', ' ')}**\n")
        print("| value | reels | avg hold | avg share+save | avg comments |")
        print("| --- | --- | --- | --- | --- |")
        ranked = []
        for k, g in sorted(groups.items(), key=lambda kv: -sum(x["hold"] for x in kv[1]) / len(kv[1])):
            avg = lambda f: sum(x[f] or 0 for x in g) / len(g)
            ranked.append((avg("hold"), k, len(g)))
            note = "" if len(g) >= MIN_N else " (too early)"
            print(f"| {k}{note} | {len(g)} | {pct(avg('hold'))} | {pct(avg('share_save'))} | {pct(avg('comment'))} |")
        print()
        ok = [x for x in ranked if x[2] >= MIN_N]
        if ok:
            best[key] = max(ok)[1]
    if not mature:
        print(f"Not enough data yet (reels need {MATURE_H} h). Explore widely: different hooks, subjects and visuals.\n")

    # ---- plan ----
    print(f"## Plan for today's {len(SLOTS)} reels\n")
    day = datetime.date.today().toordinal()
    dims = [("hook_type", HOOKS), ("subject", SUBJECTS), ("visual", VISUALS)]
    test_dim, options = dims[day % len(dims)]          # rotate what gets tested
    n_explore = max(1, len(SLOTS) // 4)                 # about a quarter of the slots test, at least 1
    explore_slots = {SLOTS[(day + k * (len(SLOTS) // n_explore)) % len(SLOTS)] for k in range(n_explore)}
    counts = {o: sum(1 for r in rows if r[test_dim] == o) for o in options}
    untried = sorted(options, key=lambda o: (counts[o], options.index(o)))
    keep = ", ".join(f"{k.replace('_', ' ')} **{v}**" for k, v in best.items() if k in ("hook_type", "visual", "length", "beats"))
    used_subjects = []
    for i, h in enumerate(SLOTS):
        if best and h not in explore_slots:
            print(f"- **{h:02d}:00 IST** — EXPLOIT: keep what works ({keep or 'no winners yet'}); new topic.")
        else:
            cands = [o for o in untried if o != best.get(test_dim)] if best else []
            pick = cands[len(used_subjects) % len(cands)] if cands else None  # a different test per explore slot
            used_subjects.append(pick)
            if not best:
                # no winners yet: spread hooks and subjects across the day
                hook, subj = HOOKS[(day + i) % len(HOOKS)], SUBJECTS[(day + i) % len(SUBJECTS)]
                vis = VISUALS[(day + i) % len(VISUALS)]
                print(f"- **{h:02d}:00 IST** — EXPLORE: hook **{hook}**, subject **{subj}**, visual **{vis}**.")
                used_subjects.append(subj)
            else:
                print(f"- **{h:02d}:00 IST** — EXPLORE {test_dim.replace('_', ' ')}: try **{pick}** "
                      f"(used {counts[pick]}×); keep everything else as in the exploit slots.")
    if "subject" in best:
        print(f"\nSubjects: **{best['subject']}** works best so far; give it 2 of today's slots and spread the "
              f"rest over other subjects (never all one subject).")
    else:
        print("\nSubjects: mix them; at least 3 different subjects today, never two of the same subject in a row.")
    if "slot" in best:
        print(f"\nBest posting slot so far: **{best['slot']}** IST.")
    recent = [r["topic"] for r in rows[-28:] if r["topic"]]
    print(f"\n- Don't repeat these recent topics: {', '.join(recent) or 'none yet'}.")
    print("- Update LEARNINGS.md with at most 2 new lessons, each tied to a number above "
          "(e.g. \"graph reels hold 41% vs 33% for equation-only, 4 reels each\"). Never invent numbers.")


if __name__ == "__main__":
    main()
