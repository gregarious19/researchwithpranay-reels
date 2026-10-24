#!/usr/bin/env bash
# Set up a local Manim for `make.py --preview` in a Claude workspace (or any Linux box with LaTeX).
# Usage: ./setup_local.sh [venv_dir]      (default ~/mvenv; make.py looks there)
#
# Why the odd steps: the workspace has Cairo and LaTeX but no Pango headers and no dvisvgm.
# - Python 3.12 venv via uv (wheels exist for 3.12)
# - Manim 0.19 installed without ManimPango; a tiny stand-in module replaces it (reels never use Text())
# - PyAV < 14 (Manim 0.19's requirement)
# - lib/reel.py converts LaTeX through pdftocairo when dvisvgm is missing
set -euo pipefail
V="${1:-$HOME/mvenv}"
export NO_PROXY= no_proxy=   # PyPI must go through the workspace proxy
for t in uv pdftocairo xelatex pdflatex ffmpeg; do
  command -v "$t" >/dev/null || { echo "missing $t"; exit 1; }
done
fc-list | grep -qi "Inter" || echo "warning: Inter font not found; words will fall back to the default sans font"

if [ -x "$V/bin/python" ] && "$V/bin/python" -c "import manim, soundfile, av" 2>/dev/null; then
  echo "already set up: $V"; exit 0
fi
uv python install 3.12 >/dev/null
uv venv -q -p 3.12 "$V"
export VIRTUAL_ENV="$V"
uv pip install -q --no-deps "manim==0.19.0"
uv pip install -q "av>=9,<14" soundfile pycairo "numpy>=2.1" scipy pillow click cloup decorator isosurfaces \
  mapbox-earcut "moderngl>=5,<6" moderngl-window networkx pydub pygments rich screeninfo skia-pathops srt \
  svgelements tqdm typing-extensions watchdog beautifulsoup4
SP=$("$V/bin/python" -c "import site; print(site.getsitepackages()[0])")
cat > "$SP/manimpango.py" <<'EOF'
"""Local stand-in for ManimPango (no Pango headers here). Reels render all words through LaTeX."""
__version__ = "0.0-stub"
class _Unavailable:
    def __init__(self, *a, **k): raise RuntimeError("Pango unavailable here: use txt() from lib.reel, not Text()")
MarkupUtils = PangoUtils = TextSetting = _Unavailable
def list_fonts(): return []
def text2svg(*a, **k): raise RuntimeError("Pango unavailable here: use txt() from lib.reel, not Text()")
def register_font(*a, **k): return True
def unregister_font(*a, **k): return True
EOF
(cd /tmp && "$V/bin/python" -c "import manim, av; print('manim', manim.__version__, '| av', av.__version__)")
echo "ready: $V   (make.py --preview finds it at ~/mvenv, or set MANIM_PY=$V/bin/python)"
