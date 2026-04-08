from OpenGL.GL import *
from renderer import draw_circle, draw_line
import numpy as np


class Stickman:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.head_radius = 15

    def draw(self, mouse_x, mouse_y):
        # Smooth follow
        self.x += (mouse_x - self.x) * 0.08
        self.y += (mouse_y - 120 - self.y) * 0.08

        glColor3f(1, 1, 1)

        # Head
        draw_circle(self.x, self.y + 60, self.head_radius, filled=True)

        # Body
        draw_line(self.x, self.y + 45, self.x, self.y)

        # Arms
        draw_line(self.x, self.y + 35, mouse_x, mouse_y)
        draw_line(self.x, self.y + 35, self.x - 30, self.y + 10)

        # Walking legs animation
        walk = np.sin(self.x * 0.05) * 10
        draw_line(self.x, self.y, self.x - 15 + walk, self.y - 40)
        draw_line(self.x, self.y, self.x + 15 - walk, self.y - 40)