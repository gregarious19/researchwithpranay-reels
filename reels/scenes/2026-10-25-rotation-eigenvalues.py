from lib.reel import *

R = [[0, -1], [1, 0]]  # 90 degree rotation
GRID = {"stroke_color": BLUE_D, "stroke_width": 3, "stroke_opacity": 0.55}


class Reel(ReelScene):
    def construct(self):
        self.hook("Here's a matrix with no eigenvectors. At least, no real ones.")

        plane = NumberPlane(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=7.2, y_length=7.2,
            background_line_style=GRID, axis_config={"stroke_width": 4, "stroke_color": INK},
        ).move_to([0, 0.4, 0])
        O = plane.c2p(0, 0)

        def arrow(x, y, color):
            return Arrow(O, plane.c2p(x, y), buff=0, color=color, stroke_width=14,
                         max_tip_length_to_length_ratio=0.22, max_stroke_width_to_length_ratio=12)

        def line_through(x, y, color):
            k = 3 / max(abs(x), abs(y))  # stop at the edge of the grid
            return DashedLine(plane.c2p(-k * x, -k * y), plane.c2p(k * x, k * y), color=color,
                              stroke_width=4, dash_length=0.18)

        mat = MathTex(r"A=\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}", font_size=68).move_to([0, 5.2, 0])
        with self.say("This matrix rotates every vector by ninety degrees.") as t:
            self.play(Create(plane), run_time=t.duration * 0.5)
            self.play(Write(mat), run_time=t.duration * 0.3)

        dirs = [(1, 0.5, ACCENT), (-0.5, 1, ACCENT2), (1, -1, ACCENT3), (0.4, 1.2, WARM)]
        arrows = VGroup(*[arrow(x, y, c) for x, y, c in dirs])
        lines = VGroup(*[line_through(x, y, c) for x, y, c in dirs])
        with self.say("Remember, an eigenvector stays on its own span. It just gets stretched or squished.") as t:
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2), run_time=t.duration * 0.45)
            self.play(Create(lines), run_time=t.duration * 0.35)

        with self.say("But under a rotation, every vector gets knocked off its span. Not one survives.") as t:
            self.play(ApplyMatrix(R, arrows, about_point=O), run_time=t.duration * 0.55)
            self.play(*[Indicate(a, color=BAD) for a in arrows], run_time=t.duration * 0.3)

        # do the algebra anyway
        self.clear_all()
        e1 = MathTex(r"\det(A - \lambda I) = 0", font_size=92).move_to([0, 3.6, 0])
        e2 = MathTex(r"\lambda^2 + 1 = 0", font_size=92).next_to(e1, DOWN, buff=0.9)
        e3 = MathTex(r"\lambda = i", r"\quad\text{or}\quad", r"\lambda = -i", font_size=92).next_to(e2, DOWN, buff=0.9)
        e3[0].set_color(ACCENT2)
        e3[2].set_color(ACCENT2)
        with self.say("And yet, if you dutifully compute the eigenvalues anyway...") as t:
            self.play(Write(e1), run_time=t.duration * 0.4)
            self.play(Write(e2), run_time=t.duration * 0.4)
        with self.say("you find lambda squared equals negative one. So lambda is i, or negative i.") as t:
            self.play(Write(e3), run_time=t.duration * 0.5)
            self.play(Circumscribe(e3, color=ACCENT2, stroke_width=6), run_time=t.duration * 0.35)

        # i is a quarter turn
        self.play(VGroup(e1, e2, e3).animate.scale(0.55).move_to([0, 4.9, 0]), run_time=0.6)
        cp = ComplexPlane(x_range=[-2, 2, 1], y_range=[-2, 2, 1], x_length=6.6, y_length=6.6,
                          background_line_style=GRID, axis_config={"stroke_width": 4, "stroke_color": INK}
                          ).move_to([0, 0.0, 0])
        C = cp.n2p(0)
        one = MathTex("1", font_size=72).next_to(cp.n2p(1), DR, buff=0.15)
        ii = MathTex("i", font_size=72, color=ACCENT2).next_to(cp.n2p(1j), UL, buff=0.15)
        z = Arrow(C, cp.n2p(1), buff=0, color=ACCENT, stroke_width=14, max_tip_length_to_length_ratio=0.25,
                  max_stroke_width_to_length_ratio=12)
        arc = Arc(radius=cp.n2p(1)[0] - C[0], start_angle=0, angle=PI / 2, arc_center=C, color=ACCENT2, stroke_width=6)
        lbl = MathTex(r"\times i", color=ACCENT2, font_size=84).move_to(C + np.array([2.0, 2.0, 0]))
        with self.say("Is the algebra just giving nonsense? Not at all. Multiplying by i is itself a quarter turn.") as t:
            self.play(Create(cp), FadeIn(one), run_time=t.duration * 0.3)
            self.play(GrowArrow(z), run_time=t.duration * 0.15)
            self.play(Rotate(z, PI / 2, about_point=C), Create(arc), FadeIn(ii), Write(lbl), run_time=t.duration * 0.4)

        with self.say("So the algebra was telling you something real. The scaling factor is a rotation.") as t:
            self.play(Indicate(e3, color=ACCENT2, scale_factor=1.15), run_time=t.duration * 0.4)
            self.play(Indicate(lbl, scale_factor=1.3), run_time=t.duration * 0.3)

        self.clear_all()
        rule = txt("imaginary eigenvalues", size=70, color=ACCENT2, bold=True).move_to([0, 3.0, 0])
        arr = Arrow(UP, DOWN, color=INK, stroke_width=10).scale(1.3).next_to(rule, DOWN, buff=0.5)
        rot = txt("rotation", size=96, color=ACCENT, bold=True).next_to(arr, DOWN, buff=0.5)
        with self.say("In general, imaginary eigenvalues are the signature of some kind of rotation.") as t:
            self.play(Write(rule), run_time=t.duration * 0.35)
            self.play(GrowArrow(arr), run_time=t.duration * 0.15)
            self.play(Write(rot), run_time=t.duration * 0.35)

        self.outro()
