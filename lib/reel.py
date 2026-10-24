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

Everything visual stays inside the SAFE zone (see STYLE.md): x in [-4, 4], y in [-3.4, 6.2].
Captions live below it; Instagram's buttons cover the bottom and right edges.
"""
import os, re, subprocess, tempfile
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
FONT = "DejaVu Sans"

SAFE_TOP, SAFE_BOTTOM, SAFE_X = 6.2, -3.4, 4.0
CAPTION_Y = -4.9

VOICE = os.environ.get("REEL_VOICE", "am_michael")
SPEED = float(os.environ.get("REEL_SPEED", "1.05"))
HANDLE = os.environ.get("REEL_HANDLE", "")  # e.g. "@yourhandle"; set as a repo variable


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
        audio_path = path or self.get_audio_basename(input_data) + ".mp3"
        samples, sr = self.kokoro.create(spoken(text), voice=self.voice, speed=self.speed, lang="en-us")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, samples, sr)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f.name, "-b:a", "192k",
                            str(Path(cache_dir) / audio_path)], check=True)
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


def spoken(text):
    """Caption text -> what the voice should say (tidy symbols the TTS would mangle)."""
    t = text.replace("×", " times ").replace("≈", " about ").replace("→", " to ").replace("=", " equals ")
    t = re.sub(r"\be\^", "e to the ", t)
    return re.sub(r"\s+", " ", t).strip()


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
    return "\n".join(lines)


class ReelScene(VoiceoverScene):
    def setup(self):
        super().setup()
        self.set_speech_service(KokoroService())

    # ---- narration ----
    def caption(self, text):
        cap = Text(wrap(text), font=FONT, font_size=40, color=INK, line_spacing=0.9)
        cap.move_to([0, CAPTION_Y, 0])
        box = BackgroundRectangle(cap, color=BLACK, fill_opacity=0.55, buff=0.18, corner_radius=0.12)
        return VGroup(box, cap)

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
        return Text(text, font=FONT, font_size=size, color=color, weight=BOLD).move_to([0, 5.3, 0])

    def hook(self, line, sub=None):
        """First ~2 s: the question that stops the scroll. Spoken and shown big."""
        big = Text(wrap(line, 18), font=FONT, font_size=72, color=INK, weight=BOLD, line_spacing=0.9)
        big.move_to([0, 1.5, 0])
        grp = VGroup(big)
        if sub:
            grp.add(Text(sub, font=FONT, font_size=40, color=ACCENT2).next_to(big, DOWN, buff=0.5))
        with self.voiceover(text=line) as t:
            self.play(FadeIn(grp, shift=UP * 0.3), run_time=min(0.6, t.duration))
        self.play(FadeOut(grp), run_time=0.4)

    def outro(self, line="Follow for one idea a day."):
        txt = Text(line, font=FONT, font_size=46, color=INK).move_to([0, 1.0, 0])
        grp = VGroup(txt)
        if HANDLE:
            grp.add(Text(HANDLE, font=FONT, font_size=40, color=ACCENT).next_to(txt, DOWN, buff=0.4))
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.4)
        with self.voiceover(text=line):
            self.play(FadeIn(grp, shift=UP * 0.2), run_time=0.6)
        self.wait(0.6)

    def clear_all(self, run_time=0.5):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)
