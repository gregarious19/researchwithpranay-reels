"""Shared base for every reel: vertical 1080x1920 frame, dark Manim look, Kokoro narration
with burned-in captions, a hook and an outro.

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
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.base import SpeechService

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

VOICE = os.environ.get("REEL_VOICE", "am_michael")
SPEED = float(os.environ.get("REEL_SPEED", "0.95"))
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


def spoken(text):
    """Caption text -> what the voice should say (tidy symbols the TTS would mangle)."""
    t = text.replace("×", " times ").replace("≈", " about ").replace("→", " to ").replace("=", " equals ")
    t = t.replace("λ", " lambda ").replace("°", " degrees")
    t = re.sub(r"\be\^", "e to the ", t)
    return re.sub(r"\s+", " ", t).strip()


class KokoroService(SpeechService):
    """Free local voice (Kokoro-82M, ONNX). Model files come from KOKORO_DIR (default models/)."""

    def __init__(self, voice=VOICE, speed=SPEED, **kwargs):
        from kokoro_onnx import Kokoro
        d = Path(os.environ.get("KOKORO_DIR", "models"))
        self.kokoro = Kokoro(str(d / "kokoro-v1.0.onnx"), str(d / "voices-v1.0.bin"))
        self.voice, self.speed = voice, speed
        SpeechService.__init__(self, **kwargs)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        import soundfile as sf
        cache_dir = cache_dir or self.cache_dir
        input_data = {"input_text": text, "service": "kokoro", "voice": self.voice, "speed": self.speed}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = str(path) if path else self.get_audio_basename(input_data) + ".mp3"
        samples, sr = self.kokoro.create(spoken(text), voice=self.voice, speed=self.speed, lang="en-us")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, samples, sr)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f.name, "-b:a", "192k",
                            str(Path(cache_dir) / audio_path)], check=True)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


class ReelScene(VoiceoverScene):
    def setup(self):
        super().setup()
        self.set_speech_service(KokoroService())

    # ---- narration ----
    def caption(self, text):
        return txt(text, size=52, width=30).move_to([0, CAPTION_Y, 0])

    @contextmanager
    def say(self, text):
        """Narrate `text` with a caption. Animations inside the block should use t.duration
        (or fractions of it) so picture and voice stay in step."""
        cap = self.caption(text)
        self.add(cap)
        with self.voiceover(text=text) as tracker:
            yield tracker
        self.remove(cap)

    # ---- standard pieces ----
    def title(self, text, size=60, color=INK):
        """Big heading at the top of the safe zone."""
        return txt(text, size=size, color=color, bold=True).move_to([0, 5.3, 0])

    def hook(self, line, sub=None):
        """First ~2 s: the question that stops the scroll. Spoken and shown big."""
        big = txt(line, size=76, bold=True, width=18).move_to([0, 1.5, 0])
        grp = VGroup(big)
        if sub:
            grp.add(txt(sub, size=48, color=ACCENT2).next_to(big, DOWN, buff=0.5))
        with self.voiceover(text=line) as t:
            self.play(FadeIn(grp, shift=UP * 0.3), run_time=min(0.6, t.duration))
        self.play(FadeOut(grp), run_time=0.4)

    def outro(self, line="Follow for more ideas like this."):
        grp = VGroup(txt(line, size=68, bold=True, width=18).move_to([0, 1.0, 0]))
        if HANDLE:
            grp.add(txt(HANDLE, size=44, color=ACCENT).next_to(grp[0], DOWN, buff=0.4))
        self.clear_all(run_time=0.4)
        with self.voiceover(text=line):
            self.play(FadeIn(grp, shift=UP * 0.2), run_time=0.6)
        self.wait(0.6)

    def clear_all(self, run_time=0.5):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)
