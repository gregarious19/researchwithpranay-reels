"""Original sound effects, synthesized with numpy (no samples, no licensing questions).

    path = sfx.get("pop")              # cached WAV, made on first use
    path = sfx.pad(seconds)            # soft background chord of exactly that length

Kinds: pop (text appears), tick (small motion), whoosh (scene change), ding (reveal),
       chime (outro / gentle accent), riser (build-up before a reveal), thud (something fails).
"""
import os, hashlib
from pathlib import Path
import numpy as np
import soundfile as sf

SR = 44100
CACHE = Path(os.environ.get("SFX_DIR", "media/sfx"))
_rng = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(SR * sec)) / SR


def _env(n, attack=0.005, decay=0.2):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def _lowpass(x, cutoff):
    # one-pole low-pass, good enough for softening noise
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def _norm(x, peak=0.8):
    m = np.max(np.abs(x)) or 1
    return (x / m * peak).astype(np.float32)


def _stereo(x, width=0.0):
    return np.stack([x, x if not width else np.roll(x, int(SR * width))], axis=1)


def pop():
    t = _t(0.09)
    f = 950 * np.exp(-t * 18) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.03)
    return _norm(x, 0.7)


def tick():
    t = _t(0.035)
    x = (np.sin(2 * np.pi * 2600 * t) + 0.4 * np.sin(2 * np.pi * 5200 * t)) * _env(len(t), 0.0005, 0.006)
    return _norm(x, 0.5)


def whoosh():
    n = int(SR * 0.45)
    noise = _rng.standard_normal(n)
    t = np.arange(n) / SR
    body = _lowpass(noise, 1800) - _lowpass(noise, 250)
    env = np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 2
    return _norm(body * env, 0.55)


def ding():
    t = _t(1.6)
    f0 = 1046.5  # C6
    x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d)
            for r, a, d in [(1, 1, 2.2), (2.76, 0.35, 4.0), (5.4, 0.12, 7.0), (0.5, 0.25, 1.6)])
    return _norm(x * np.clip(t / 0.003, 0, 1), 0.6)


def chime():
    t = _t(2.0)
    x = np.zeros_like(t)
    for k, f in enumerate([523.25, 659.25, 783.99]):  # C E G, slightly staggered
        s = np.clip(t - 0.09 * k, 0, None)
        x += np.sin(2 * np.pi * f * s) * np.exp(-s * 2.0) * (s > 0)
    return _norm(x, 0.5)


def riser():
    t = _t(1.2)
    noise = _lowpass(_rng.standard_normal(len(t)), 3000)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 600 * (t / t[-1]) ** 2) / SR)
    env = (t / t[-1]) ** 2
    return _norm((0.6 * noise + 0.4 * tone) * env, 0.45)


def thud():
    t = _t(0.35)
    f = 120 * np.exp(-t * 6) + 45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.09)
    return _norm(x, 0.7)


KINDS = {"pop": pop, "tick": tick, "whoosh": whoosh, "ding": ding, "chime": chime, "riser": riser, "thud": thud}


def get(kind):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{kind}.wav"
    if not p.exists():
        sf.write(p, _stereo(KINDS[kind]()), SR)
    return str(p)


def pad(seconds, seed="pad"):
    """Soft evolving chord bed (A minor add9 → F major 7 → C → G, 8 s each), faded in and out."""
    CACHE.mkdir(parents=True, exist_ok=True)
    seconds = round(seconds, 1)
    p = CACHE / f"pad-{hashlib.md5(f'{seed}{seconds}'.encode()).hexdigest()[:8]}.wav"
    if p.exists():
        return str(p)
    t = _t(seconds)
    chords = [[220.0, 261.63, 329.63, 493.88], [174.61, 220.0, 261.63, 329.63],
              [196.0, 261.63, 329.63, 392.0], [196.0, 246.94, 293.66, 392.0]]
    seg = 8.0
    x = np.zeros_like(t)
    for i, ch in enumerate(chords * int(np.ceil(seconds / (seg * len(chords))) + 1)):
        start = i * seg - 1.5
        if start > seconds:
            break
        local = t - start
        w = np.clip(local / 2.5, 0, 1) * np.clip((seg + 1.5 - local) / 2.5, 0, 1)  # crossfade
        for f in ch:
            lfo = 1 + 0.003 * np.sin(2 * np.pi * 0.2 * t + f)
            x += w * (np.sin(2 * np.pi * f * lfo * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) / len(ch)
    x *= np.clip(t / 2.0, 0, 1) * np.clip((seconds - t) / 2.0, 0, 1)
    sf.write(p, _stereo(_norm(x, 0.5), width=0.012), SR)
    return str(p)
