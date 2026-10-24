#!/usr/bin/env python3
"""Change a queued reel's status. The daily run approves a reel itself once make.py prints PASS and the
contact sheet looks right (see DAILY_RUN.md).

    python3 approve.py list                 show the queue
    python3 approve.py approve <id>         it posts at its slot (post_after), or the next free one
    python3 approve.py hold <id>            keep it in the queue, don't post
    python3 approve.py unhold <id>
    python3 approve.py drop <id>            you rejected it -> delete the spec (brief stays)

Then commit and push.
"""
import datetime, glob, json, os, sys


def when(p):
    """Sort key: the reel's post_after as a real time (specs mix +00:00 and +05:30 offsets)."""
    pa = json.load(open(p)).get("post_after")
    try:
        return datetime.datetime.fromisoformat(pa).timestamp() if pa else 0, p
    except ValueError:
        return 0, p


def path(i):
    p = f"reels/queue/{i}.json"
    if not os.path.exists(p):
        raise SystemExit(f"no queued reel {i!r}. Queue: " + ", ".join(os.path.basename(x)[:-5] for x in sorted(glob.glob('reels/queue/*.json'))))
    return p


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        for p in sorted(glob.glob("reels/queue/*.json"), key=when):
            s = json.load(open(p))
            state = "HOLD" if s.get("hold") else ("APPROVED" if s.get("approved") is True else "not approved yet")
            print(f"{s['id']}: {state}; posts after {s.get('post_after')}; ~{s.get('duration') or s.get('est_duration')}s; topic {s.get('topic')}")
        return
    cmd, i = sys.argv[1], sys.argv[2]
    p = path(i)
    if cmd == "drop":
        os.remove(p)
        print(f"removed {p}")
        return
    s = json.load(open(p))
    if cmd == "approve":
        s["approved"] = True
        s.pop("hold", None)
    elif cmd == "hold":
        s["hold"] = True
    elif cmd == "unhold":
        s.pop("hold", None)
    else:
        raise SystemExit(__doc__)
    json.dump(s, open(p, "w"), indent=1, ensure_ascii=False)
    print(f"{i}: {cmd} done. Now: git add -A && git commit -m '{cmd.capitalize()} {i} [skip ci]' && git push")


if __name__ == "__main__":
    main()
