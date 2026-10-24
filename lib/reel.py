"""Shared base for every reel: vertical 1080x1920 frame, dark Manim look, on-screen text
timed for reading, original sound effects, a hook and an outro. No voice.

A reel's scene file (reels/scenes/<id>.py) looks like:

    from lib.reel import *

    class Reel(ReelScene):
        def construct(self):
            self.hook("Why does ice float?")
            with self.say("Almost every solid sinks in its own liquid.") as t:
                self.play(Create(thing), run_time=t.duration)
            ...
            self.outro()

All words on screen go through LaTeX: use txt("...") for words and MathTex for math.
Never use manim's Text() (it needs Pango, and the LaTeX look is the house style).
Everything visual stays inside the SAFE zone (see STYLE.md): x in [-4, 4], y in [-3.4, 6.2].
Captions live below it; Instagram's buttons cover the bottom and right edges.
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

# ---------- look ----------
BG = "#0E1117"
config.background_color = BG
INK = "#ECECEC"          # main text
DIM = "#8B93A1"          # secondary text
ACCENT = BLUE_C          # main idea
ACCENT2 = YELLOW_C       # the thing to notice
ACCENT3 = TEAL_C
WARM = "#C08A5B"         # brown accent
BAD = RED_C
GOOD = GREEN_C

SAFE_TOP, SAFE_BOTTOM, SAFE_X = 6.2, -3.4, 4.0
CAPTION_Y = -4.6

READ_WPS = 3.0     # comfortable reading speed for on-screen text, words per second
HANDLE = os.environ.get("REEL_HANDLE", "")  # e.g. "@yourhandle"; set as a repo variable

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


# ---------- words ----------
_ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
        "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        "×": r"$\times$", "°": r"$^\circ$", "→": r"$\to$", "≈": r"$\approx$", "λ": r"$\lambda$"}


def _esc(s):
    return "".join(_ESC.get(c, c) for c in s)


def wrap(text, width=26):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def txt(text, size=48, color=INK, bold=False, width=None):
    """Words on screen, set in LaTeX sans-serif. `width` = max characters per line (wraps)."""
    lines = wrap(text, width) if width else text.split("\n")
    body = r" \\ ".join(_esc(l) for l in lines)
    body = r"\textbf{" + body + "}" if bold else body
    return Tex(r"\textsf{" + body + "}", font_size=size, color=color)


def read_time(text):
    """Seconds a line stays up: enough to read it comfortably."""
    return max(2.2, len(text.split()) / READ_WPS + 0.9)


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
        return txt(text, size=58, width=26).move_to([0, CAPTION_Y, 0])

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
