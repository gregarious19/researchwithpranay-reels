"""The look and frame every reel shares: vertical 1080x1920, pure black, Inter words, LaTeX math,
refined grids and glowing arrows, text timed for reading, sound effects, hook and outro.

Reels are JSON scripts played by lib/build.py with the components in lib/components.py (see
SCRIPT_FORMAT.md); this file is the foundation those build on. All words go through LaTeX: use txt()
for words (math inside $...$) and MathTex for equations, never manim's Text().
"""
import os, re, shutil, subprocess, tempfile
from contextlib import contextmanager
from pathlib import Path

from manim import *
from types import SimpleNamespace
from lib import sfx

# ---------- frame: 9:16, 9 units wide x 16 tall ----------
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 30

if os.environ.get("REEL_PREVIEW"):  # quick local check: half size, 15 fps
    config.pixel_width, config.pixel_height, config.frame_rate = 540, 960, 15

# ---------- look ----------
BG = "#000000"
config.background_color = BG
INK = "#F2F2F2"          # main text
DIM = "#7C8494"          # secondary text, scaffolding
ACCENT = "#58C4DD"       # main idea (blue)
ACCENT2 = "#FFD45E"      # the thing to notice (warm yellow)
ACCENT3 = "#5FD3B5"      # second object (teal)
WARM = "#D49A66"         # contrasting object (brown)
BAD = "#FF6B6B"
GOOD = "#7BE495"
GRID_COLOR = "#2E6F8E"

SAFE_TOP, SAFE_BOTTOM, SAFE_X = 6.2, -3.4, 4.0
CAPTION_Y = -4.6

READ_WPS = 3.0     # comfortable reading speed for on-screen text, words per second
HANDLE = os.environ.get("REEL_HANDLE", "@researchwithpranay")

# ---------- encoding: Manim's default (CRF 23) smears thin colored lines on dark backgrounds ----------
import av as _av
import manim.scene.scene_file_writer as _sfw

X264 = {"crf": os.environ.get("REEL_CRF", "12"), "preset": "slow", "tune": "animation"}


class _Container:
    """Wraps an av output container so every libx264 stream gets X264 quality settings."""

    def __init__(self, c):
        self._c = c

    def __getattr__(self, name):
        return getattr(self._c, name)

    def __enter__(self):
        self._c.__enter__()
        return self

    def __exit__(self, *exc):
        return self._c.__exit__(*exc)

    def add_stream(self, codec_name=None, *args, options=None, **kwargs):
        if codec_name == "libx264":
            options = {**(options or {}), **X264}
        return self._c.add_stream(codec_name, *args, options=options, **kwargs)


class _AV:
    def __getattr__(self, name):
        return getattr(_av, name)

    def open(self, *args, **kwargs):
        c = _av.open(*args, **kwargs)
        return _Container(c) if kwargs.get("mode") == "w" or (len(args) > 1 and args[1] == "w") else c


_sfw.av = _AV()

# ---------- LaTeX without dvisvgm (some machines lack it): compile to PDF, convert with pdftocairo ----------
if shutil.which("dvisvgm") is None and shutil.which("pdftocairo"):
    import manim.utils.tex_file_writing as _tfw

    def _pdf_to_svg(dvi_file, extension, page=1):
        out = Path(dvi_file).with_suffix(".svg")
        if not out.exists():
            subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(dvi_file), str(out)],
                           check=True, capture_output=True)
        return out

    _tfw.convert_to_svg = _pdf_to_svg
    config.tex_template.tex_compiler = "pdflatex"
    config.tex_template.output_format = ".pdf"


# ---------- words: Inter via XeLaTeX (math inside $...$ stays Computer Modern) ----------
WORDS = TexTemplate(tex_compiler="xelatex",
                    output_format=".pdf" if shutil.which("dvisvgm") is None else ".xdv")
WORDS.add_to_preamble(r"\usepackage{fontspec}\setsansfont{Inter}[UprightFont=*-Medium,BoldFont=*-Bold]"
                      r"\renewcommand{\familydefault}{\sfdefault}")

_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "×": r"$\times$", "°": r"$^\circ$", "→": r"$\to$", "≈": r"$\approx$", "λ": r"$\lambda$"}
_MATH = re.compile(r"(\$[^$]+\$)")
NBSP = " "


def _esc(s):
    """Escape LaTeX specials outside $...$; math segments pass through untouched."""
    return "".join(part if _MATH.fullmatch(part) else "".join(_ESC.get(c, c) for c in part)
                   for part in _MATH.split(s))


def plain(text):
    """Roughly how a line reads on screen (math collapsed), for wrapping and reading time."""
    return _MATH.sub(lambda m: re.sub(r"\\[a-zA-Z]+|[{}^_$\\]", "x", m.group(1)).replace(" ", ""), text)


def wrap(text, width=26):
    """Wrap on spaces, never inside $...$."""
    protected = _MATH.sub(lambda m: m.group(1).replace(" ", NBSP), text)
    lines, cur = [], ""
    for w in [w for w in protected.split(" ") if w]:  # split(" "), not split(): NBSP must survive
        if cur and len(plain(cur.replace(NBSP, " "))) + 1 + len(plain(w.replace(NBSP, " "))) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return [l.replace(NBSP, " ") for l in lines]


def txt(text, size=48, color=INK, bold=False, width=None):
    """Words on screen in Inter; put math in $...$. `width` = max characters per line (wraps)."""
    lines = wrap(text, width) if width else text.split("\n")
    body = r" \\ ".join(_esc(l) for l in lines)
    body = r"\textbf{" + body + "}" if bold else body
    return Tex(body, font_size=size, color=color, tex_template=WORDS)


# ---------- refined building blocks ----------
def grid(size=7.2, center=(0, 0.4, 0), x_range=(-3, 3, 1), y_range=None, plane=NumberPlane):
    """Fine main grid lines, a faint half-step subgrid, crisp axes."""
    y_range = y_range or x_range
    g = plane(x_range=list(x_range), y_range=list(y_range), x_length=size, y_length=size,
              background_line_style={"stroke_color": GRID_COLOR, "stroke_width": 2, "stroke_opacity": 0.75},
              faded_line_style={"stroke_color": GRID_COLOR, "stroke_width": 1, "stroke_opacity": 0.3},
              faded_line_ratio=2, axis_config={"stroke_width": 3, "stroke_color": INK, "stroke_opacity": 0.9})
    return g.move_to(center)


def vec(start, end, color=ACCENT, width=9):
    """Arrow with a slim body, sharp tip and a soft glow behind it."""
    a = Arrow(start, end, buff=0, color=color, stroke_width=width, tip_length=0.3,
              max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=20)
    a.set_stroke(color, width=width * 2.6, opacity=0.22, background=True, family=False)  # glow on the body only
    return a


def span_line(p1, p2, color, opacity=0.65):
    return DashedLine(p1, p2, color=color, stroke_width=2.5, stroke_opacity=opacity, dash_length=0.14,
                      dashed_ratio=0.55)


def glow(mob, color=None, width=18, opacity=0.2):
    """Soft halo behind any stroked shape (arcs, curves)."""
    mob.set_stroke(color or mob.get_color(), width=width, opacity=opacity, background=True)
    return mob


def read_time(text):
    """Seconds a line stays up: enough to read it comfortably."""
    return max(2.2, len(plain(text).split()) / READ_WPS + 0.9)


class ReelScene(Scene):
    """Sounds are added automatically: pop when a line appears, whoosh on clear_all, ding on the hook,
    chime on the outro, and a soft pad under everything. Call self.sfx("tick"|"ding"|"riser"|"thud"|...)
    for extra accents on key moments (sparingly: 1-3 per reel)."""

    SFX_GAIN = {"pop": -14, "tick": -16, "whoosh": -15, "ding": -10, "chime": -11, "riser": -14, "thud": -10}
    PAD_GAIN = -26

    def sfx(self, kind, offset=0.0, gain=None):
        self.add_sound(sfx.get(kind), time_offset=offset, gain=self.SFX_GAIN.get(kind, -14) if gain is None else gain)

    def tear_down(self):
        # background pad spanning the whole reel, added last so its length is exact
        total = self.renderer.time
        if total > 1:
            self.add_sound(sfx.pad(total), time_offset=-total, gain=self.PAD_GAIN)
        super().tear_down()

    # ---- narration (on-screen text) ----
    def caption(self, text):
        return txt(text, size=50, width=26).move_to([-0.15, CAPTION_Y, 0])

    @contextmanager
    def say(self, text):
        """Show `text` for its reading time. Animations inside the block should use t.duration
        (or fractions of it); any time left over is waited out before the text leaves."""
        cap = self.caption(text)
        dur = read_time(text)
        self.sfx("pop")
        self.play(FadeIn(cap, shift=UP * 0.12), run_time=0.25)
        start = self.renderer.time
        yield SimpleNamespace(duration=dur)
        left = dur - (self.renderer.time - start)
        if left > 0.05:
            self.wait(left)
        self.play(FadeOut(cap), run_time=0.2)

    # ---- standard pieces ----
    def title(self, text, size=60, color=INK):
        """Big heading at the top of the safe zone."""
        return txt(text, size=size, color=color, bold=True).move_to([0, 5.3, 0])

    def hook(self, line, sub=None):
        """First seconds: the question that stops the scroll, shown big."""
        big = txt(line, size=80, bold=True, width=18).move_to([0, 1.5, 0])
        grp = VGroup(big)
        if sub:
            grp.add(txt(sub, size=52, color=ACCENT2).next_to(big, DOWN, buff=0.5))
        self.sfx("ding")
        self.play(FadeIn(grp, shift=UP * 0.3), run_time=0.5)
        self.wait(max(1.2, read_time(line) - 0.6))
        self.sfx("whoosh")
        self.play(FadeOut(grp, shift=UP * 0.3), run_time=0.4)

    def outro(self, line="Follow for more ideas like this."):
        grp = VGroup(txt(line, size=68, bold=True, width=18).move_to([0, 1.0, 0]))
        if HANDLE:
            grp.add(txt(HANDLE, size=48, color=ACCENT).next_to(grp[0], DOWN, buff=0.4))
        self.clear_all(run_time=0.4)
        self.sfx("chime")
        self.play(FadeIn(grp, shift=UP * 0.2), run_time=0.6)
        self.wait(2.0)

    def clear_all(self, run_time=0.5):
        if self.mobjects:
            self.sfx("whoosh")
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)
