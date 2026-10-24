from lib.reel import *

A = [[2, 1], [1, 2]]


class Reel(ReelScene):
    def construct(self):
        self.hook("Some arrows survive a matrix without turning.", sub="Which ones?")

        plane = NumberPlane(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=7, y_length=7,
            background_line_style={"stroke_color": BLUE_E, "stroke_width": 2, "stroke_opacity": 0.7},
        ).move_to([0, 1.0, 0])
        O = plane.c2p(0, 0)

        def arrow(x, y, color):
            return Arrow(O, plane.c2p(x, y), buff=0, color=color, stroke_width=8,
                         max_tip_length_to_length_ratio=0.18)

        title = self.title("What a matrix does")
        with self.say("A matrix is a rule that moves every arrow in the plane.") as t:
            self.play(Create(plane), Write(title), run_time=t.duration * 0.8)

        # a generic arrow gets knocked off its line
        g = arrow(1.2, -0.4, ACCENT2)
        gline = DashedLine(plane.c2p(-3, 1), plane.c2p(3, -1), color=ACCENT2, stroke_opacity=0.6)
        with self.say("Take this arrow, and the line it points along.") as t:
            self.play(GrowArrow(g), run_time=t.duration * 0.4)
            self.play(Create(gline), run_time=t.duration * 0.4)

        sq = Polygon(*[plane.c2p(*p) for p in [(0, 0), (1, 0), (1, 1), (0, 1)]],
                     color=ACCENT, fill_opacity=0.25, stroke_width=4)
        with self.say("Now apply the matrix. The arrow gets knocked right off its line.") as t:
            self.play(FadeIn(sq), run_time=0.4)
            self.play(ApplyMatrix(A, VGroup(sq, g), about_point=O), run_time=t.duration * 0.6)
        self.play(FadeOut(g, gline, sq), run_time=0.4)

        # the eigenvector along the diagonal only stretches
        e = arrow(1, 1, ACCENT3)
        eline = DashedLine(plane.c2p(-3, -3), plane.c2p(3, 3), color=ACCENT3, stroke_opacity=0.6)
        with self.say("But this arrow, along the diagonal, stays on its line. It only stretches.") as t:
            self.play(GrowArrow(e), Create(eline), run_time=t.duration * 0.35)
            self.play(ApplyMatrix(A, e, about_point=O), run_time=t.duration * 0.5)
        x3 = MathTex(r"\times 3", color=ACCENT3, font_size=60).next_to(plane.c2p(3, 3), LEFT, buff=0.3)
        self.play(Write(x3), run_time=0.5)

        f = arrow(1, -1, WARM)
        fline = DashedLine(plane.c2p(-3, 3), plane.c2p(3, -3), color=WARM, stroke_opacity=0.6)
        with self.say("And the other diagonal? It doesn't move at all.") as t:
            self.play(GrowArrow(f), Create(fline), run_time=t.duration * 0.35)
            self.play(ApplyMatrix(A, f, about_point=O), run_time=t.duration * 0.45)
        x1 = MathTex(r"\times 1", color=WARM, font_size=60).next_to(plane.c2p(1, -1), RIGHT, buff=0.3)
        self.play(Write(x1), run_time=0.5)

        # name it
        self.clear_all()
        eq = MathTex("A", r"\vec{v}", "=", r"\lambda", r"\vec{v}", font_size=110).move_to([0, 2.0, 0])
        eq[1].set_color(ACCENT3)
        eq[4].set_color(ACCENT3)
        eq[3].set_color(ACCENT2)
        vec_lbl = txt("eigenvector", size=44, color=ACCENT3).next_to(eq[1], DOWN, buff=0.6)
        val_lbl = txt("eigenvalue", size=44, color=ACCENT2).next_to(eq[3], UP, buff=0.6)
        with self.say("Arrows that only stretch are eigenvectors. The stretch factor is the eigenvalue.") as t:
            self.play(Write(eq), run_time=t.duration * 0.35)
            self.play(FadeIn(vec_lbl, shift=UP * 0.2), run_time=t.duration * 0.2)
            self.play(FadeIn(val_lbl, shift=DOWN * 0.2), run_time=t.duration * 0.2)

        # payoff
        self.clear_all()
        m = MathTex(r"\begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}", font_size=90).move_to([0, 3.6, 0])
        arr = Arrow(UP, DOWN, color=DIM).next_to(m, DOWN, buff=0.3)
        l1 = MathTex(r"\times 3 \text{ along } \nearrow", color=ACCENT3, font_size=70)
        l2 = MathTex(r"\times 1 \text{ along } \searrow", color=WARM, font_size=70)
        lines = VGroup(l1, l2).arrange(DOWN, buff=0.5).next_to(arr, DOWN, buff=0.4)
        with self.say("Find them, and a messy matrix becomes simple stretching along a few directions.") as t:
            self.play(Write(m), run_time=t.duration * 0.3)
            self.play(GrowArrow(arr), run_time=t.duration * 0.15)
            self.play(Write(lines), run_time=t.duration * 0.35)

        self.outro()
