"""Elementary components and actions that turn a JSON reel script into Manim.

A script is a list of beats. Each beat shows one line of text (timed for reading) and runs a list
of steps: `make` steps create something and animate it in; action steps change what's on screen.
SCRIPT_FORMAT.md documents every step with examples; this file is the implementation.
"""
import math
import numpy as np
from lib.reel import *

COLORS = {"blue": ACCENT, "yellow": ACCENT2, "teal": ACCENT3, "brown": WARM, "red": BAD, "green": GOOD,
          "white": INK, "dim": DIM, "grid": GRID_COLOR, "purple": "#B58CFF", "pink": "#FF8FC7",
          "orange": "#FF9F4A"}
SPOTS = {"top": (0, 5.2), "upper": (0, 3.6), "mid": (0, 1.6), "center": (0, 0.4), "lower": (0, -2.2)}
SIDES = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT, "ul": UL, "ur": UR, "dl": DL, "dr": DR}
SAFE_FN = {k: getattr(np, k) for k in ("sin", "cos", "tan", "exp", "log", "sqrt", "abs", "arctan", "sinh",
                                        "cosh", "tanh", "arcsin", "arccos", "floor", "sign", "maximum", "minimum")}
SAFE_FN.update(pi=np.pi, e=np.e, ln=np.log)


class ScriptError(Exception):
    pass


def col(c, default=None):
    if c is None:
        return default
    if c in COLORS:
        return COLORS[c]
    if isinstance(c, str) and c.startswith("#"):
        return c
    raise ScriptError(f"unknown color {c!r}; use one of {sorted(COLORS)} or #hex")


def fn(expr, var="x"):
    """Compile a math expression like 'sin(x) + x**2/4' into a numpy function."""
    code = compile(expr.replace("^", "**"), "<fn>", "eval")
    for name in code.co_names:
        if name not in SAFE_FN and name != var:
            raise ScriptError(f"function {expr!r} uses {name!r}; allowed: {sorted(SAFE_FN)} and {var}")
    return lambda v: eval(code, {"__builtins__": {}, **SAFE_FN}, {var: v})


class World:
    """Everything the script has made, by name, plus coordinate helpers."""

    def __init__(self, scene):
        self.scene = scene
        self.objs, self.kind, self.trackers, self.meta = {}, {}, {}, {}

    def get(self, name):
        if name in self.objs:
            return self.objs[name]
        raise ScriptError(f"nothing called {name!r} on screen (made so far: {sorted(self.objs)})")

    def pt(self, at, on=None, default="center"):
        """Scene point from [x, y] (scene units, or the coordinates of plane/axes `on`) or a spot name."""
        at = default if at is None else at
        if isinstance(at, str):
            if at not in SPOTS:
                raise ScriptError(f"unknown spot {at!r}; use {sorted(SPOTS)} or [x, y]")
            return np.array([*SPOTS[at], 0.0])
        if on:
            sys_ = self.get(on)
            if isinstance(sys_, NumberLine) and not isinstance(sys_, Axes):
                return sys_.n2p(at if np.isscalar(at) else at[0])
            return sys_.c2p(*at[:2])
        return np.array([at[0], at[1], 0.0])

    def place(self, mob, a, default="center"):
        if a.get("next_to"):
            mob.next_to(self.get(a["next_to"]), SIDES[a.get("side", "down")], buff=a.get("buff", 0.4))
        else:
            mob.move_to(self.pt(a.get("at"), a.get("on"), default))
        return mob


# ------------------------------------------------------------------ makers
# each returns (mobject, intro animation or None)

def m_text(w, a):
    t = txt(a["text"], size=a.get("size", 60), color=col(a.get("color"), INK), bold=a.get("bold", False),
            width=a.get("width", 22))
    return w.place(t, a, "upper"), Write(t) if a.get("write") else FadeIn(t, shift=UP * 0.15)


def m_tex(w, a):
    parts = a["tex"] if isinstance(a["tex"], list) else [a["tex"]]
    t = MathTex(*parts, font_size=a.get("size", 84), color=col(a.get("color"), INK))
    for idx, c in (a.get("colors") or {}).items():
        if str(idx).isdigit():
            t[int(idx)].set_color(col(c))
        else:
            t.set_color_by_tex(idx, col(c))
    return w.place(t, a, "upper"), Write(t)


def _rng(r, step=1):
    return [r[0], r[1], r[2] if len(r) > 2 else step]


def m_plane(w, a):
    r = a.get("range", [-3, 3])
    p = grid(size=a.get("size", 7.2), center=w.pt(a.get("at"), None, "center"), x_range=_rng(r),
             y_range=_rng(a["y_range"]) if a.get("y_range") else None,
             plane=ComplexPlane if a.get("complex") else NumberPlane)
    w.meta[a["name"]] = {"range": _rng(r), "y_range": _rng(a.get("y_range", r))}
    return p, Create(p, lag_ratio=0.05)


def m_axes(w, a):
    xr, yr = _rng(a.get("x", [-1, 5])), _rng(a.get("y", [-1, 4]))
    size = a.get("size", [7.4, 6.0])
    ax = Axes(x_range=xr, y_range=yr, x_length=size[0], y_length=size[1], tips=True,
              axis_config={"stroke_color": INK, "stroke_width": 3, "tip_width": 0.22, "tip_height": 0.22,
                           "include_numbers": a.get("numbers", False), "font_size": 30})
    ax.move_to(w.pt(a.get("at"), None, "center"))
    grp = VGroup(ax)
    labels = a.get("labels")
    if labels:
        lx = MathTex(labels[0], font_size=60, color=INK).next_to(ax.x_axis.get_end(), DOWN, buff=0.2)
        ly = MathTex(labels[1], font_size=60, color=INK).next_to(ax.y_axis.get_end(), LEFT, buff=0.2)
        grp.add(lx, ly)
    w.meta[a["name"]] = {"x": xr, "y": yr}
    w.objs[a["name"] + ".labels"] = VGroup(*grp[1:])
    return ax, (Create(grp, lag_ratio=0.1) if labels else Create(ax))


def m_graph(w, a):
    ax = w.get(a["on"])
    f = fn(a["fn"])
    xr = a.get("x") or w.meta[a["on"]]["x"][:2]
    g = ax.plot(f, x_range=[xr[0], xr[1], (xr[1] - xr[0]) / 300], color=col(a.get("color"), ACCENT),
                stroke_width=a.get("width", 5), use_smoothing=False)
    glow(g, width=a.get("width", 5) * 3, opacity=0.18)
    w.meta[a["name"]] = {"f": f, "on": a["on"]}
    return g, Create(g)


def m_curve(w, a):
    """Parametric curve: {"x": "cos(t)", "y": "sin(t)", "t": [0, 6.28]} in the coordinates of `on`."""
    fx, fy = fn(a["x"], "t"), fn(a["y"], "t")
    t0, t1 = a.get("t", [0, 2 * math.pi])
    if a.get("on"):
        sys_ = w.get(a["on"])
        func = lambda t: sys_.c2p(fx(t), fy(t))
    else:
        func = lambda t: np.array([fx(t), fy(t), 0])
    c = ParametricFunction(func, t_range=[t0, t1, (t1 - t0) / 300], color=col(a.get("color"), ACCENT),
                           stroke_width=a.get("width", 5), use_smoothing=False)
    glow(c, width=a.get("width", 5) * 3, opacity=0.18)
    return c, Create(c)


def m_vector(w, a):
    on = a.get("on")
    v = vec(w.pt(a.get("from", [0, 0]), on), w.pt(a["to"], on), col(a.get("color"), ACCENT), width=a.get("width", 9))
    if a.get("label"):
        d = v.get_end() - v.get_start()
        d = d / (np.linalg.norm(d) or 1)
        lab = MathTex(a["label"], font_size=a.get("label_size", 60), color=col(a.get("color"), ACCENT))
        lab.move_to(v.get_end() + d * 0.45 + np.array([-d[1], d[0], 0]) * 0.25)
        w.objs[a["name"] + ".label"] = lab
        return VGroup(v, lab), AnimationGroup(GrowArrow(v), FadeIn(lab), lag_ratio=0.5)
    return v, GrowArrow(v)


def m_span(w, a):
    p = w.get(a["on"])
    r, yr = w.meta[a["on"]]["range"], w.meta[a["on"]]["y_range"]
    x, y = a["dir"]
    k = min(r[1] / abs(x) if x else 1e9, yr[1] / abs(y) if y else 1e9)
    s = span_line(p.c2p(-k * x, -k * y), p.c2p(k * x, k * y), col(a.get("color"), ACCENT))
    return s, Create(s)


def m_dot(w, a):
    color = col(a.get("color"), ACCENT2)
    if a.get("follow"):
        g = w.meta[a["follow"]]
        ax, f, tr = w.get(g["on"]), g["f"], w.trackers[a["x"]]
        d = always_redraw(lambda: Dot(ax.c2p(tr.get_value(), f(tr.get_value())), radius=0.11, color=color))
    elif a.get("track"):
        # dot at (tracker, value) on plane/axes `on`: {"track": "t", "on": "ax", "y": "t**2"}
        sys_, tr, fy = w.get(a["on"]), w.trackers[a["track"]], fn(a.get("y", "0"))
        d = always_redraw(lambda: Dot(sys_.c2p(tr.get_value(), fy(tr.get_value())), radius=0.11, color=color))
    else:
        d = Dot(w.pt(a.get("at", [0, 0]), a.get("on")), radius=a.get("radius", 0.11), color=color)
    d.set_stroke(color, width=14, opacity=0.25, background=True)
    if a.get("label") and not (a.get("follow") or a.get("track")):
        lab = MathTex(a["label"], font_size=56, color=color).next_to(d, SIDES[a.get("side", "ur")], buff=0.12)
        return VGroup(d, lab), FadeIn(VGroup(d, lab), scale=0.5)
    return d, FadeIn(d, scale=0.5)


def m_line(w, a):
    on = a.get("on")
    cls = DashedLine if a.get("dashed") else Line
    l = cls(w.pt(a["from"], on), w.pt(a["to"], on), color=col(a.get("color"), INK), stroke_width=a.get("width", 4))
    return l, Create(l)


def m_shape(w, a):
    on, kind, color = a.get("on"), a.get("kind", "circle"), col(a.get("color"), ACCENT)
    unit = (w.get(on).c2p(1, 0)[0] - w.get(on).c2p(0, 0)[0]) if on else 1
    if kind == "circle":
        s = Circle(radius=a.get("radius", 1) * unit, color=color).move_to(w.pt(a.get("center", [0, 0]), on))
    elif kind == "arc":
        s = Arc(radius=a.get("radius", 1) * unit, start_angle=a.get("start", 0) * DEGREES,
                angle=a.get("angle", 90) * DEGREES, arc_center=w.pt(a.get("center", [0, 0]), on), color=color)
    elif kind == "polygon":
        s = Polygon(*[w.pt(p, on) for p in a["points"]], color=color)
    elif kind == "rect":
        s = Rectangle(width=a.get("w", 2) * unit, height=a.get("h", 1) * unit, color=color).move_to(
            w.pt(a.get("center", [0, 0]), on))
    else:
        raise ScriptError(f"unknown shape kind {kind!r}; use circle, arc, polygon, rect")
    s.set_stroke(width=a.get("width", 4))
    if a.get("fill"):
        s.set_fill(color, opacity=a.get("fill") if isinstance(a.get("fill"), (int, float)) else 0.25)
    glow(s, width=a.get("width", 4) * 3, opacity=0.15)
    return s, Create(s)


def m_box(w, a):
    b = SurroundingRectangle(w.get(a["around"]), color=col(a.get("color"), ACCENT2), buff=a.get("buff", 0.2),
                             corner_radius=0.15, stroke_width=3)
    glow(b)
    return b, Create(b)


def m_brace(w, a):
    t = w.get(a["of"])
    side = SIDES[a.get("side", "down")]
    br = Brace(t, direction=side, color=col(a.get("color"), DIM))
    lab = (MathTex(a["tex"], font_size=a.get("size", 56)) if a.get("tex")
           else txt(a.get("text", ""), size=a.get("size", 52), width=18))
    lab.set_color(col(a.get("color"), INK if a.get("text") else ACCENT2))
    br.put_at_tip(lab)
    return VGroup(br, lab), AnimationGroup(GrowFromCenter(br), FadeIn(lab), lag_ratio=0.4)


def m_pointer(w, a):
    """A short label with an arrow pointing at something."""
    t = w.get(a["at_obj"] if a.get("at_obj") else a["to"])
    side = SIDES[a.get("side", "right")]
    lab = (MathTex(a["tex"], font_size=a.get("size", 56)) if a.get("tex")
           else txt(a["text"], size=a.get("size", 44), width=14))
    lab.set_color(col(a.get("color"), ACCENT2))
    lab.next_to(t, side, buff=a.get("buff", 1.2))
    arr = vec(lab.get_edge_center(-side), t.get_edge_center(side) + side * 0.12, col(a.get("color"), ACCENT2), width=5)
    return VGroup(lab, arr), AnimationGroup(FadeIn(lab), GrowArrow(arr), lag_ratio=0.4)


def m_numberline(w, a):
    r = _rng(a.get("range", [-3, 3]))
    nl = NumberLine(x_range=r, length=a.get("length", 7.6), color=INK, stroke_width=3,
                    include_numbers=a.get("numbers", True), font_size=36)
    return w.place(nl, a, "center"), Create(nl)


def m_bars(w, a):
    vals = a["values"]
    colors = [col(c) for c in a.get("colors", ["blue", "teal", "yellow", "brown", "purple", "pink"])]
    top = a.get("max", max(vals) * 1.15 if max(vals) > 0 else 1)
    ch = BarChart(vals, bar_names=a.get("labels"), y_range=[0, top, a.get("step", top / 4)],
                  x_length=a.get("size", [7.2, 5.0])[0], y_length=a.get("size", [7.2, 5.0])[1],
                  bar_colors=colors, bar_fill_opacity=0.85, bar_stroke_width=0,
                  x_axis_config={"font_size": 32, "stroke_color": INK},
                  y_axis_config={"font_size": 28, "stroke_color": INK})
    return w.place(ch, a, "center"), Create(ch)


def m_tracker(w, a):
    w.trackers[a["name"]] = ValueTracker(a.get("value", 0))
    return None, None


def m_readout(w, a):
    """Live number from a tracker: {"tracker": "t", "label": "x =", "decimals": 2}."""
    tr = w.trackers[a["tracker"]]
    f = fn(a.get("fn", "x"))
    label = MathTex(a.get("label", ""), font_size=a.get("size", 64), color=col(a.get("color"), INK))
    num = DecimalNumber(f(tr.get_value()), num_decimal_places=a.get("decimals", 2), font_size=a.get("size", 64),
                        color=col(a.get("color"), INK))
    grp = VGroup(label, num).arrange(RIGHT, buff=0.2)
    w.place(grp, a, "top")
    num.add_updater(lambda m: m.set_value(f(tr.get_value())).next_to(label, RIGHT, buff=0.2))
    return grp, FadeIn(grp)


def m_tangent(w, a):
    """Tangent line to a graph at a tracker's x: {"graph": "g", "x": "t", "length": 3}."""
    g = w.meta[a["graph"]]
    ax, f, tr = w.get(g["on"]), g["f"], w.trackers[a["x"]]
    color, L = col(a.get("color"), ACCENT2), a.get("length", 3)

    def draw():
        x0, h = tr.get_value(), 1e-4
        s = (f(x0 + h) - f(x0 - h)) / (2 * h)
        p0, p1 = ax.c2p(x0, f(x0)), ax.c2p(x0 + 1, f(x0) + s)
        d = (p1 - p0) / (np.linalg.norm(p1 - p0) or 1)
        return Line(p0 - d * L / 2, p0 + d * L / 2, color=color, stroke_width=4)
    t = always_redraw(draw)
    return t, Create(t)


def m_area(w, a):
    """Shaded area under a graph between x values (numbers or a tracker name for the right edge)."""
    g = w.meta[a["graph"]]
    ax, graph = w.get(g["on"]), w.get(a["graph"])
    x0, x1 = a.get("x", [0, 1])
    color, op = col(a.get("color"), ACCENT), a.get("opacity", 0.35)
    if isinstance(x1, str):
        tr = w.trackers[x1]
        ar = always_redraw(lambda: ax.get_area(graph, x_range=[x0, max(x0 + 1e-3, tr.get_value())], color=color,
                                               opacity=op))
    else:
        ar = ax.get_area(graph, x_range=[x0, x1], color=color, opacity=op)
    return ar, FadeIn(ar)


def m_group(w, a):
    return VGroup(*[w.get(n) for n in a["of"]]), None


MAKERS = {"text": m_text, "tex": m_tex, "plane": m_plane, "axes": m_axes, "graph": m_graph, "curve": m_curve,
          "vector": m_vector, "span": m_span, "dot": m_dot, "line": m_line, "shape": m_shape, "box": m_box,
          "brace": m_brace, "pointer": m_pointer, "numberline": m_numberline, "bars": m_bars,
          "tracker": m_tracker, "readout": m_readout, "tangent": m_tangent, "area": m_area, "group": m_group}


# ------------------------------------------------------------------ actions
# each returns a list of animations (possibly empty) and may change the world

def a_make(w, a):
    kind = a["make"]
    if kind not in MAKERS:
        raise ScriptError(f"unknown component {kind!r}; available: {sorted(MAKERS)}")
    if "name" not in a:
        a = {**a, "name": f"_{kind}{len(w.objs)}"}
    mob, intro = MAKERS[kind](w, a)
    if mob is None:
        return []
    w.objs[a["name"]], w.kind[a["name"]] = mob, kind
    if a.get("hidden"):
        return []
    if intro is None:
        w.scene.add(mob)
        return []
    return [intro]


def _objs(w, names):
    names = names if isinstance(names, list) else [names]
    return [w.get(n) for n in names]


def a_apply_matrix(w, a):
    p = w.get(a["on"])
    return [ApplyMatrix(a["apply_matrix"], VGroup(*_objs(w, a["to"])), about_point=p.c2p(0, 0))]


def a_rotate(w, a):
    about = w.pt(a.get("about", [0, 0]), a.get("on"))
    return [Rotate(VGroup(*_objs(w, a["rotate"])), a.get("angle", 90) * DEGREES, about_point=about)]


def a_transform(w, a):
    src, dst = w.get(a["transform"]), w.get(a["into"])
    w.objs[a["transform"]] = dst
    return [ReplacementTransform(src, dst)]


def a_morph(w, a):
    """Morph an equation into a new one, moving matching pieces: {"morph": "eq", "into": {"make": "tex", ...}}.
    The new one takes the old one's place unless it gives its own "at"/"next_to"."""
    src = w.get(a["morph"])
    into = a["into"]
    if isinstance(into, dict):
        spec = {**into, "hidden": True, "name": into.get("name", a["morph"] + "_next")}
        a_make(w, spec)
        if into.get("at") is None and not into.get("next_to"):
            w.get(spec["name"]).move_to(src)
        into = spec["name"]
    dst = w.get(into)
    w.objs[a["morph"]] = dst
    if isinstance(src, MathTex) and isinstance(dst, MathTex):
        return [TransformMatchingTex(src, dst)]
    return [ReplacementTransform(src, dst)]


def a_move(w, a):
    m = w.get(a["move"])
    anim = m.animate
    if a.get("scale"):
        anim = anim.scale(a["scale"])
    if a.get("to") is not None:
        anim = anim.move_to(w.pt(a["to"], a.get("on")))
    if a.get("shift"):
        anim = anim.shift(np.array([*a["shift"], 0]))
    return [anim]


def a_indicate(w, a):
    return [Indicate(m, color=col(a.get("color"), ACCENT2), scale_factor=a.get("scale", 1.15)) for m in _objs(w, a["indicate"])]


def a_circle(w, a):
    return [Circumscribe(m, color=col(a.get("color"), ACCENT2), stroke_width=5) for m in _objs(w, a["circle"])]


def a_flash(w, a):
    return [Flash(m.get_center(), color=col(a.get("color"), ACCENT2), line_length=0.35, num_lines=12,
                  flash_radius=max(m.width, m.height) / 2 + 0.2) for m in _objs(w, a["flash"])]


def a_wiggle(w, a):
    return [Wiggle(m) for m in _objs(w, a["wiggle"])]


def a_recolor(w, a):
    return [m.animate.set_color(col(a["color"])) for m in _objs(w, a["recolor"])]


def a_hide(w, a):
    ms = _objs(w, a["hide"])
    for n in (a["hide"] if isinstance(a["hide"], list) else [a["hide"]]):
        w.objs.pop(n, None)
    return [FadeOut(m) for m in ms]


def a_slide(w, a):
    tr = w.trackers.get(a["slide"])
    if tr is None:
        raise ScriptError(f"no tracker {a['slide']!r}")
    return [tr.animate.set_value(a["to"])]


def a_trace(w, a):
    m = w.get(a["trace"])
    path = TracedPath(m.get_center, stroke_color=col(a.get("color"), ACCENT2), stroke_width=4)
    w.scene.add(path)
    w.objs[a.get("name", a["trace"] + ".path")] = path
    return []


ACTIONS = {"make": a_make, "apply_matrix": a_apply_matrix, "rotate": a_rotate, "transform": a_transform,
           "morph": a_morph, "move": a_move, "indicate": a_indicate, "circle": a_circle, "flash": a_flash,
           "wiggle": a_wiggle, "recolor": a_recolor, "hide": a_hide, "slide": a_slide, "trace": a_trace}
TIMELESS = ("sfx", "wait", "clear", "trace")


def step_key(step):
    for k in ("together", *TIMELESS, *ACTIONS):
        if k in step:
            return k
    raise ScriptError(f"step does nothing I know: {step}. Steps: make, {', '.join(k for k in ACTIONS if k != 'make')}, "
                      f"together, sfx, wait, clear")


def run_steps(scene, w, steps, duration=None):
    """Play steps in order. Run times share the beat's reading time unless a step sets "time" (seconds)."""
    timed = [s for s in steps if step_key(s) not in TIMELESS]
    share = (0.85 * duration / max(1, len(timed))) if duration else 0.8
    for s in steps:
        k = step_key(s)
        if k == "sfx":
            scene.sfx(s["sfx"])
            continue
        if k == "wait":
            scene.wait(min(float(s["wait"]), 1.5))
            continue
        if k == "clear":
            scene.clear_all()
            keep = {n: o for n, o in w.objs.items() if o in scene.mobjects}
            w.objs = keep
            continue
        if k == "trace":
            a_trace(w, s)
            continue
        if k == "together":
            anims = [an for sub in s["together"] for an in ACTIONS[step_key(sub)](w, sub)]
        else:
            anims = ACTIONS[k](w, s)
        if anims:
            rt = s.get("time", min(1.8, share))
            if s.get("lag"):
                scene.play(LaggedStart(*anims, lag_ratio=s["lag"]), run_time=rt)
            else:
                scene.play(*anims, run_time=rt)
