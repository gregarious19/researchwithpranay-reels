"""Render a JSON reel script:  REEL_SPEC=reels/queue/<id>.json manim render lib/build.py Reel"""
import json, os
from lib.reel import *
from lib.components import World, run_steps


class Reel(ReelScene):
    def construct(self):
        spec = json.load(open(os.environ["REEL_SPEC"]))
        w = World(self)
        self.hook(spec["hook"], spec.get("sub"))
        for i, beat in enumerate(spec["beats"]):
            try:
                if beat.get("text"):
                    with self.say(beat["text"]) as t:
                        run_steps(self, w, beat.get("do", []), t.duration)
                else:
                    run_steps(self, w, beat.get("do", []))
            except Exception as e:
                raise RuntimeError(f"beat {i + 1} ({beat.get('text', '')[:40]!r}): {e}") from e
        self.outro(spec.get("outro", "Follow for more ideas like this."))
