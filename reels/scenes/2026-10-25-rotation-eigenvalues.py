from lib.reel import *

R = [[0, -1], [1, 0]]  # 90 degree rotation


class Reel(ReelScene):
    def construct(self):
        self.hook("This matrix has no eigenvectors. Or does it?")

        plane = NumberPlane(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=7, y_length=7,
            background_line_style={"stroke_color": BLUE_E, "stroke_width": 2, "stroke_opacity": 0.7},
        ).move_to([0, 0.4, 0])
        O = plane.c2p(0, 0)

        def arrow(x, y, color):
            return Arrow(O, plane.c2p(x, y), buff=0, color=color, stroke_width=8,
                         max_tip_length_to_length_ratio=0.18)

        def line_through(x, y, color):
            return DashedLine(plane.c2p(-3 * x, -3 * y), plane.c2p(3 * x, 3 * y), color=color, stroke_opacity=0.5)

        mat = MathTex(r"A=\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}", font_size=60).move_to([0, 5.0, 0])
        with self.say("Here's a matrix that rotates the whole plane a quarter turn.") as t:
            self.play(Create(plane), run_time=t.duration * 0.5)
            self.play(Write(mat), run_time=t.duration * 0.3)

        dirs = [(1, 0.5, ACCENT), (-0.5, 1, ACCENT2), (1, -1, ACCENT3), (0.4, 1.2, WARM)]
        arrows = VGroup(*[arrow(x, y, c) for x, y, c in dirs])
        lines = VGroup(*[line_through(x, y, c) for x, y, c in dirs])
        with self.say("An eigenvector should stay on its own line. Let's test a few arrows.") as t:
            self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2), run_time=t.duration * 0.45)
            self.play(Create(lines), run_time=t.duration * 0.35)

        with self.say("Every single one gets knocked off. No real arrow survives.") as t:
            self.play(ApplyMatrix(R, arrows, about_point=O), run_time=t.duration * 0.55)
            self.play(*[Indicate(a, color=BAD) for a in arrows], run_time=t.duration * 0.3)

        # do the algebra anyway
        self.clear_all()
        e1 = MathTex(r"\det(A - \lambda I) = 0", font_size=80).move_to([0, 4.4, 0])
        e2 = MathTex(r"\lambda^2 + 1 = 0", font_size=80).next_to(e1, DOWN, buff=0.7)
        e3 = MathTex(r"\lambda = i", r"\quad\text{or}\quad", r"\lambda = -i", font_size=80).next_to(e2, DOWN, buff=0.7)
        e3[0].set_color(ACCENT2)
        e3[2].set_color(ACCENT2)
        with self.say("So solve for the eigenvalues anyway, and watch what comes out.") as t:
            self.play(Write(e1), run_time=t.duration * 0.4)
            self.play(Write(e2), run_time=t.duration * 0.4)
        with self.say("Lambda squared equals minus one. The eigenvalues are i and minus i.") as t:
            self.play(Write(e3), run_time=t.duration * 0.5)
            self.play(Circumscribe(e3, color=ACCENT2), run_time=t.duration * 0.35)

        # i is a quarter turn
        self.play(VGroup(e1, e2, e3).animate.scale(0.6).move_to([0, 5.0, 0]), run_time=0.6)
        cp = ComplexPlane(x_range=[-2, 2, 1], y_range=[-2, 2, 1], x_length=5.6, y_length=5.6,
                          background_line_style={"stroke_color": BLUE_E, "stroke_opacity": 0.6}).move_to([0, 0.4, 0])
        C = cp.n2p(0)
        one = MathTex("1", font_size=56).next_to(cp.n2p(1), DR, buff=0.12)
        ii = MathTex("i", font_size=56, color=ACCENT2).next_to(cp.n2p(1j), UL, buff=0.12)
        z = Arrow(C, cp.n2p(1), buff=0, color=ACCENT, stroke_width=8, max_tip_length_to_length_ratio=0.2)
        arc = Arc(radius=cp.n2p(1)[0] - C[0], start_angle=0, angle=PI / 2, arc_center=C, color=ACCENT2)
        lbl = MathTex(r"\times i", color=ACCENT2, font_size=60).move_to(C + np.array([1.6, 1.6, 0]))
        with self.say("Now here's the twist. Multiplying by i is itself a quarter turn.") as t:
            self.play(Create(cp), FadeIn(one), run_time=t.duration * 0.3)
            self.play(GrowArrow(z), run_time=t.duration * 0.15)
            self.play(Rotate(z, PI / 2, about_point=C), Create(arc), FadeIn(ii), Write(lbl), run_time=t.duration * 0.4)

        with self.say("The rotation's stretch factor was never missing. It was hiding in the complex numbers.") as t:
            self.play(Indicate(e3, color=ACCENT2, scale_factor=1.15), run_time=t.duration * 0.4)
            self.play(Indicate(lbl, scale_factor=1.3), run_time=t.duration * 0.3)

        self.clear_all()
        rule = MathTex(r"\text{imaginary eigenvalues}", font_size=72, color=ACCENT2).move_to([0, 2.6, 0])
        arr = Arrow(UP, DOWN, color=DIM).next_to(rule, DOWN, buff=0.3)
        rot = MathTex(r"\text{the matrix rotates}", font_size=72, color=ACCENT).next_to(arr, DOWN, buff=0.3)
        with self.say("So whenever you see imaginary eigenvalues, think: this matrix rotates.") as t:
            self.play(Write(rule), run_time=t.duration * 0.35)
            self.play(GrowArrow(arr), run_time=t.duration * 0.15)
            self.play(Write(rot), run_time=t.duration * 0.35)

        self.outro()
