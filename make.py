#!/usr/bin/env python3
"""Check a reel script, set its posting slot, and optionally render a quick local preview.

    python3 make.py <id> [--slot 11|15|19|23] [--preview]

The script is reels/queue/<id>.json (format: SCRIPT_FORMAT.md). Checks everything that can be checked
without rendering: fields, steps, component names, references to things on screen, colors, functions,
text length and total length. Prints PASS or a list of what to fix.

--preview renders at half resolution with the local Manim setup (./setup_local.sh) and writes
out/<id>-sheet.png, a 12-frame contact sheet to look at before pushing. GitHub Actions renders the
real thing after you push.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys

SLOTS = (11, 15, 19, 23, 2)  # IST posting hours (02:00 is the night after); must match post.yml
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
READ_WPS = 3.0            # must match lib/reel.py
MIN_S, MAX_S = 28, 90
MAX_WORDS_PER_LINE = 24
FIELDS = ("id", "topic", "subject", "hook_type", "caption", "hook", "beats")
SUBJECTS = ("math", "physics", "chemistry", "engineering", "computing", "biology", "statistics")
COLORS = {"blue", "yellow", "teal", "brown", "red", "green", "white", "dim", "grid", "purple", "pink", "orange"}
SPOTS = {"top", "upper", "mid", "center", "lower"}
SIDES = {"up", "down", "left", "right", "ul", "ur", "dl", "dr"}
SFX = {"pop", "tick", "whoosh", "ding", "chime", "riser", "thud"}
SAFE_FN = {"sin", "cos", "tan", "exp", "log", "sqrt", "abs", "arctan", "sinh", "cosh", "tanh", "arcsin", "arccos",
           "floor", "sign", "maximum", "minimum", "pi", "e", "ln"}

# component -> required fields
MAKE = {"text": ["text"], "tex": ["tex"], "plane": [], "axes": [], "graph": ["on", "fn"], "curve": ["x", "y"],
        "vector": ["to"], "span": ["on", "dir"], "dot": [], "line": ["from", "to"], "shape": [], "box": ["around"],
        "brace": ["of"], "pointer": ["to"], "numberline": [], "bars": ["values"], "tracker": ["name"],
        "readout": ["tracker"], "tangent": ["graph", "x"], "area": ["graph"], "group": ["of", "name"]}
# fields that name something already on screen
REF_FIELDS = {"on", "around", "of", "next_to", "graph", "follow"}
ACTIONS = {"apply_matrix": ["to", "on"], "rotate": [], "transform": ["into"], "morph": ["into"], "move": [],
           "indicate": [], "circle": [], "flash": [], "wiggle": [], "recolor": ["color"], "hide": [],
           "slide": ["to"], "trace": []}


def words(text):
    return len(re.sub(r"\$[^$]+\$", "x", text).split())


def read_time(text):
    return max(2.2, words(text) / READ_WPS + 0.9)


def check_fn(expr, var, where, problems):
    for name in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", expr):
        if name not in SAFE_FN and name != var:
            problems.append(f"{where}: function {expr!r} uses {name!r}; allowed: {sorted(SAFE_FN)} and {var}")


def check_tex(tex, where, problems):
    for t in (tex if isinstance(tex, list) else [tex]):
        if t.count("{") != t.count("}"):
            problems.append(f"{where}: unbalanced braces in {t!r}")
        if "$" in t:
            problems.append(f"{where}: no $ inside tex (it's already math): {t!r}")


def check_step(step, names, trackers, where, problems):
    if not isinstance(step, dict):
        problems.append(f"{where}: each step must be an object, got {step!r}")
        return
    if "together" in step:
        for j, sub in enumerate(step["together"]):
            check_step(sub, names, trackers, f"{where} together[{j + 1}]", problems)
        return
    if "sfx" in step:
        if step["sfx"] not in SFX:
            problems.append(f"{where}: unknown sfx {step['sfx']!r}; use {sorted(SFX)}")
        return
    if "wait" in step:
        if float(step["wait"]) > 1.5:
            problems.append(f"{where}: wait {step['wait']} s is a dead pause; keep ≤ 1.5")
        return
    if "clear" in step:
        names.clear()
        return

    def ref(n, what="name"):
        if isinstance(n, list):
            for x in n:
                ref(x, what)
            return
        if not isinstance(n, str) or n not in names:
            problems.append(f"{where}: {what} {n!r} isn't on screen (have: {', '.join(sorted(names)) or 'nothing'})")

    if "color" in step and step["color"] not in COLORS and not str(step["color"]).startswith("#"):
        problems.append(f"{where}: unknown color {step['color']!r}; use {sorted(COLORS)}")

    if "make" in step:
        kind = step["make"]
        if kind not in MAKE:
            problems.append(f"{where}: unknown component {kind!r}; available: {sorted(MAKE)}")
            return
        for f in MAKE[kind]:
            if f not in step:
                problems.append(f"{where}: {kind} needs {f!r}")
        for f in REF_FIELDS & step.keys():
            ref(step[f], f)
        if kind == "pointer":
            ref(step["to"], "pointer target")
        if kind == "readout" and step.get("tracker") not in trackers:
            problems.append(f"{where}: no tracker {step.get('tracker')!r}")
        if kind in ("tangent", "dot") and isinstance(step.get("x"), str) and step["x"] not in trackers:
            problems.append(f"{where}: no tracker {step['x']!r}")
        if kind == "dot" and step.get("track") and step["track"] not in trackers:
            problems.append(f"{where}: no tracker {step['track']!r}")
        if kind == "area" and isinstance((step.get("x") or [0, 1])[1], str) and step["x"][1] not in trackers:
            problems.append(f"{where}: no tracker {step['x'][1]!r}")
        if kind == "graph":
            check_fn(step.get("fn", ""), "x", where, problems)
        if kind == "curve":
            check_fn(step.get("x", ""), "t", where, problems)
            check_fn(step.get("y", ""), "t", where, problems)
        if kind == "readout" and step.get("fn"):
            check_fn(step["fn"], "x", where, problems)
        if kind == "tex":
            check_tex(step.get("tex", ""), where, problems)
            for k, c in (step.get("colors") or {}).items():
                if c not in COLORS and not str(c).startswith("#"):
                    problems.append(f"{where}: unknown color {c!r} in colors; use {sorted(COLORS)}")
        if isinstance(step.get("at"), str) and step["at"] not in SPOTS:
            problems.append(f"{where}: unknown spot {step['at']!r}; use {sorted(SPOTS)} or [x, y]")
        if step.get("side") and step["side"] not in SIDES:
            problems.append(f"{where}: unknown side {step['side']!r}; use {sorted(SIDES)}")
        if kind == "text" and words(step.get("text", "")) > 8:
            problems.append(f"{where}: on-screen label {step['text']!r} is long; labels ≤ 8 words (the caption explains)")
        name = step.get("name")
        if kind == "tracker":
            trackers.add(name)
        elif name:
            if name in names:
                problems.append(f"{where}: name {name!r} already used; pick a new one")
            names.add(name)
            if kind == "vector" and step.get("label"):
                names.add(name + ".label")
        return

    key = next((k for k in ACTIONS if k in step), None)
    if key is None:
        problems.append(f"{where}: step does nothing I know: {step}")
        return
    for f in ACTIONS[key]:
        if f not in step:
            problems.append(f"{where}: {key} needs {f!r}")
    if key == "slide":
        if step["slide"] not in trackers:
            problems.append(f"{where}: no tracker {step['slide']!r}")
        return
    if key == "apply_matrix":
        ref(step["to"])
        ref(step["on"], "plane")
        m = step["apply_matrix"]
        if not (isinstance(m, list) and len(m) == 2 and all(len(r) == 2 for r in m)):
            problems.append(f"{where}: apply_matrix must be a 2x2 list like [[0,-1],[1,0]]")
        return
    target = step[key]
    ref(target)
    if key == "morph":
        into = step["into"]
        if isinstance(into, dict):
            check_step({**into, "name": into.get("name", f"{target}_next")}, names, trackers, where + " into", problems)
        else:
            ref(into)
    if key == "transform":
        ref(step["into"])
    if key == "hide":
        for n in (target if isinstance(target, list) else [target]):
            names.discard(n)
    if key == "trace":
        names.add(step.get("name", f"{target}.path"))


def validate(spec, rid):
    problems = []
    for f in FIELDS:
        if not spec.get(f):
            problems.append(f"'{f}' is missing")
    if spec.get("id") != rid:
        problems.append(f"id must be {rid!r}")
    if spec.get("subject") and spec["subject"] not in SUBJECTS:
        problems.append(f"subject must be one of {SUBJECTS}")
    if len(spec.get("caption", "")) > 2000:
        problems.append("caption over 2000 characters")
    if words(spec.get("hook", "")) > 14:
        problems.append("hook over 14 words; it has to land in two seconds")
    names, trackers = set(), set()
    total = max(1.2, read_time(spec.get("hook", ""))) + 1.0
    texts = 0
    for i, beat in enumerate(spec.get("beats") or [], 1):
        where = f"beat {i}"
        text = beat.get("text")
        if text:
            texts += 1
            if words(text) > MAX_WORDS_PER_LINE:
                problems.append(f"{where}: {words(text)} words; keep each line ≤ {MAX_WORDS_PER_LINE}")
            if text.count("$") % 2:
                problems.append(f"{where}: unmatched $ in text")
            total += read_time(text) + 0.45
        for j, step in enumerate(beat.get("do", []), 1):
            check_step(step, names, trackers, f"{where} step {j}", problems)
            if not text:
                total += 0.8
    if texts < 4:
        problems.append(f"only {texts} lines of text; a reel needs at least 4 beats to explain anything")
    total += 3.2  # outro
    if not MIN_S <= total <= MAX_S:
        problems.append(f"estimated length {total:.0f}s; aim for {MIN_S}-{MAX_S}s")
    return problems, total


def slot_time(h, now=None):
    """Next occurrence of posting hour h (IST) that is still ahead."""
    now = now or datetime.datetime.now(IST)
    t = datetime.datetime(now.year, now.month, now.day, h, tzinfo=IST)
    return t if t > now else t + datetime.timedelta(days=1)


def next_slot(taken):
    now = datetime.datetime.now(IST)
    cands = sorted(datetime.datetime(d.year, d.month, d.day, h, tzinfo=IST)
                   for d in [(now + datetime.timedelta(days=k)).date() for k in range(8)] for h in SLOTS)
    for t in cands:
        if t > now + datetime.timedelta(minutes=45) and t.isoformat() not in taken:
            return t


def visual_style(spec):
    """What the reel mostly shows: geometry, graph, equations or data (for analyze.py)."""
    groups = {"geometry": {"plane", "vector", "span", "shape"}, "graph": {"axes", "graph", "curve", "tangent", "area"},
              "data": {"bars", "numberline"}}
    counts = {g: 0 for g in groups}

    def walk(steps):
        for st in steps:
            if "together" in st:
                walk(st["together"])
            for g, kinds in groups.items():
                if st.get("make") in kinds or (g == "geometry" and ("apply_matrix" in st or "rotate" in st)):
                    counts[g] += 1
    for b in spec.get("beats", []):
        walk(b.get("do", []))
    top = max(counts, key=counts.get)
    return top if counts[top] else "equations"


def preview(rid):
    py = os.environ.get("MANIM_PY", os.path.expanduser("~/mvenv/bin/python"))
    if not os.path.exists(py):
        py = "/home/claude/mvenv/bin/python"
    if not os.path.exists(py):
        print("(no local Manim; run ./setup_local.sh for previews. GitHub Actions will render it anyway.)")
        return
    os.makedirs("out", exist_ok=True)
    env = {**os.environ, "PYTHONPATH": os.getcwd(), "REEL_SPEC": f"reels/queue/{rid}.json", "REEL_PREVIEW": "1",
           "SFX_DIR": "out/sfx"}
    r = subprocess.run([py, "-m", "manim", "render", "--disable_caching", "--media_dir", "out/preview",
                        "-o", rid, "lib/build.py", "Reel"], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        tail = [l for l in (r.stdout + r.stderr).splitlines() if "Error" in l or "beat " in l or "│ ❱" in l][-8:]
        print("PREVIEW FAILED\n" + "\n".join(tail))
        sys.exit(1)
    mp4 = next(iter(glob.glob(f"out/preview/videos/**/{rid}.mp4", recursive=True)), None)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout or 0)
    sheet = f"out/{rid}-sheet.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf",
                    f"fps=12/{dur},scale=270:-1,tile=6x2:padding=6:color=gray", "-frames:v", "1", sheet], check=True)
    print(f"preview: {mp4} ({dur:.1f}s)\nsheet:   {sheet}  <- look at this before pushing")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--slot", type=int, choices=SLOTS)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    path = f"reels/queue/{a.id}.json"
    if not os.path.exists(path):
        raise SystemExit(f"FAIL: {path} missing")
    try:
        spec = json.load(open(path))
    except json.JSONDecodeError as e:
        raise SystemExit(f"FAIL: {path} is not valid JSON: {e}")
    problems, est = validate(spec, a.id)
    if problems:
        print("FAIL")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    taken = {json.load(open(p)).get("post_after") for p in glob.glob("reels/queue/*.json") if not p.endswith(f"{a.id}.json")}
    if a.slot is not None:
        t = slot_time(a.slot)
    elif spec.get("post_after"):
        t = datetime.datetime.fromisoformat(spec["post_after"])
    else:
        t = next_slot(taken)
    spec["post_after"] = t.isoformat()
    spec["est_duration"] = round(est)
    spec["visual"] = visual_style(spec)
    spec.setdefault("approved", False)
    json.dump(spec, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"PASS  {a.id}: ~{est:.0f}s, {len(spec['beats'])} beats, {spec['visual']}, posts after {spec['post_after']}")
    if a.preview:
        preview(a.id)


if __name__ == "__main__":
    main()
