import numpy as np
from OpenGL.GL import *
from renderer import draw_circle, draw_line


class AnimationSystem:
    def __init__(self):
        self.time = 0

    def update(self):
        self.time += 0.02

    def draw(self):
        t = self.time

        # =========================
        # 🌈 COLOR TRANSITION
        # =========================
        r = (np.sin(t) + 1) / 2
        g = (np.sin(t + 2) + 1) / 2
        b = (np.sin(t + 4) + 1) / 2

        # =========================
        # 🔥 GLOW TRAIL EFFECT (FAKE)
        # =========================
        glColor4f(0, 0, 0, 0.1)
        glBegin(GL_QUADS)
        glVertex2f(-2000, -2000)
        glVertex2f(2000, -2000)
        glVertex2f(2000, 2000)
        glVertex2f(-2000, 2000)
        glEnd()

        # =========================
        # 🔺 ROTATING TRIANGLE
        # =========================
        glColor3f(r, g, b)
        self.draw_polygon(3, 120, t)

        # =========================
        # 🔷 ROTATING HEXAGON
        # =========================
        glColor3f(b, r, g)
        self.draw_polygon(6, 200, -t * 0.7)

        # =========================
        # 🌀 ORBITING PARTICLES
        # =========================
        for i in range(20):
            angle = i * (2 * np.pi / 20) + t
            radius = 150 + np.sin(t * 2 + i) * 20

            x = np.cos(angle) * radius
            y = np.sin(angle) * radius

            glColor3f(1, g, r)
            draw_circle(x, y, 5, filled=True)

        # =========================
        # 🎵 BEAT PULSE CIRCLE
        # =========================
        pulse = abs(np.sin(t * 3)) * 80 + 20
        glColor3f(1, 1, 1)
        draw_circle(0, 0, pulse, filled=False)

        # =========================
        # 🌊 WAVE LINE
        # =========================
        glColor3f(0.5, 1, 0.7)
        for x in range(-400, 400, 15):
            y = np.sin(x * 0.05 + t * 3) * 40 - 250
            draw_circle(x, y, 3, filled=True)

    # -------------------------
    # Helper: Draw polygon
    # -------------------------
    def draw_polygon(self, sides, radius, rotation):
        glBegin(GL_LINE_LOOP)
        for i in range(sides):
            angle = i * (2 * np.pi / sides) + rotation
            x = np.cos(angle) * radius
            y = np.sin(angle) * radius
            glVertex2f(x, y)
        glEnd()