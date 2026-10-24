#!/usr/bin/env python3
"""Check a reel before pushing it, and set its posting slot.

    python3 make.py <id> [--slot 11|15|19|23]

Needs reels/scenes/<id>.py (class Reel(ReelScene)) and reels/queue/<id>.json (see STYLE.md).
Checks the scene parses, estimates narration length from the self.hook/self.say lines, and checks
each caption is short enough to read. Prints PASS or what to fix. Rendering happens on GitHub
Actions (render.yml) after you push; its contact sheet is the visual check.
"""
import argparse, ast, datetime, glob, json, os, re, sys

SLOTS = (11, 15, 19, 23)  # IST; must match post.yml and analyze.py
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
WORDS_PER_SEC = 2.6        # Kokoro at speed 1.05, measured roughly
GAP_PER_LINE = 0.9         # animation time between/after lines
MIN_S, MAX_S = 28, 58
MAX_WORDS_PER_LINE = 18
FIELDS = ("id", "topic", "subject", "hook_type", "caption")
SUBJECTS = ("math", "physics", "chemistry", "computing", "biology", "statistics")


def narration(src):
    lines = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("say", "hook", "outro") and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                lines.append(a.value)
            else:
                lines.append(None)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "outro" and not node.args:
            lines.append("Follow for one idea a day.")
    return lines


def next_slot(taken):
    now = datetime.datetime.now(IST)
    for day in range(0, 7):
        d = (now + datetime.timedelta(days=day)).date()
        for h in SLOTS:
            t = datetime.datetime(d.year, d.month, d.day, h, tzinfo=IST)
            if t > now + datetime.timedelta(minutes=45) and t.isoformat() not in taken:
                return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--slot", type=int, choices=SLOTS)
    a = ap.parse_args()
    scene_p, meta_p = f"reels/scenes/{a.id}.py", f"reels/queue/{a.id}.json"
    problems = []
    if not os.path.exists(scene_p):
        raise SystemExit(f"FAIL: {scene_p} missing")
    if not os.path.exists(meta_p):
        raise SystemExit(f"FAIL: {meta_p} missing")
    meta = json.load(open(meta_p))
    src = open(scene_p).read()

    for f in FIELDS:
        if not meta.get(f):
            problems.append(f"meta: '{f}' is missing")
    if meta.get("id") != a.id:
        problems.append(f"meta: id must be {a.id!r}")
    if meta.get("subject") and meta["subject"] not in SUBJECTS:
        problems.append(f"meta: subject must be one of {SUBJECTS}")
    if len(meta.get("caption", "")) > 2000:
        problems.append("meta: caption over 2000 characters")

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"FAIL: {scene_p} line {e.lineno}: {e.msg}")
    if not any(isinstance(n, ast.ClassDef) and n.name == "Reel" for n in tree.body):
        problems.append("scene: needs `class Reel(ReelScene)`")
    if "from lib.reel import *" not in src:
        problems.append("scene: must start with `from lib.reel import *`")
    if "self.hook(" not in src:
        problems.append("scene: open with self.hook(...) — the first 2 seconds decide everything")
    if "self.outro(" not in src:
        problems.append("scene: end with self.outro()")
    for m in re.finditer(r"self\.wait\(\s*([\d.]+)", src):
        if float(m.group(1)) > 1.5:
            problems.append(f"scene: self.wait({m.group(1)}) is a dead pause; keep waits ≤ 1.5 s")

    lines = narration(src)
    if any(l is None for l in lines):
        problems.append("scene: narration must be plain string literals (needed for the length estimate)")
    lines = [l for l in lines if l]
    words = sum(len(l.split()) for l in lines)
    est = words / WORDS_PER_SEC + GAP_PER_LINE * len(lines)
    for l in lines:
        n = len(l.split())
        if n > MAX_WORDS_PER_LINE:
            problems.append(f"line too long for one caption ({n} words, max {MAX_WORDS_PER_LINE}): {l!r}")
    if not MIN_S <= est <= MAX_S:
        problems.append(f"estimated length {est:.0f}s; aim for {MIN_S}-{MAX_S}s ({words} words in {len(lines)} lines)")

    if problems:
        print("FAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    taken = {json.load(open(p)).get("post_after") for p in glob.glob("reels/queue/*.json") if not p.endswith(f"{a.id}.json")}
    if a.slot:
        d = datetime.datetime.now(IST).date()
        t = datetime.datetime(d.year, d.month, d.day, a.slot, tzinfo=IST)
        if t <= datetime.datetime.now(IST):
            t += datetime.timedelta(days=1)
    else:
        t = next_slot(taken)
    meta["post_after"] = t.isoformat()
    meta["est_duration"] = round(est)
    meta["hook"] = lines[0]
    meta.setdefault("approved", False)
    json.dump(meta, open(meta_p, "w"), indent=1, ensure_ascii=False)
    print(f"PASS  {a.id}: ~{est:.0f}s, {len(lines)} lines, posts after {meta['post_after']}")
    print("Next: commit + push; render.yml renders it and attaches the MP4 and sheet.png to release reel-" + a.id)


if __name__ == "__main__":
    main()
