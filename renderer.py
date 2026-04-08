from OpenGL.GL import *
import numpy as np


def draw_circle(x, y, radius, segments=50, filled=False):
    mode = GL_POLYGON if filled else GL_LINE_LOOP
    glBegin(mode)
    for i in range(segments):
        theta = 2.0 * np.pi * i / segments
        dx = radius * np.cos(theta)
        dy = radius * np.sin(theta)
        glVertex2f(x + dx, y + dy)
    glEnd()


def draw_line(x1, y1, x2, y2, width=2):
    glLineWidth(width)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()


def draw_grid(width, height, spacing=50):
    glColor3f(0.2, 0.2, 0.2)
    glLineWidth(1)
    glBegin(GL_LINES)

    for x in range(-width, width, spacing):
        glVertex2f(x, -height)
        glVertex2f(x, height)

    for y in range(-height, height, spacing):
        glVertex2f(-width, y)
        glVertex2f(width, y)

    glEnd()


# ✅ NEW: Gradient Background
def draw_background(width, height):
    glBegin(GL_QUADS)

    # Top color
    glColor3f(0.05, 0.05, 0.15)
    glVertex2f(-width, height)
    glVertex2f(width, height)

    # Bottom color
    glColor3f(0, 0, 0)
    glVertex2f(width, -height)
    glVertex2f(-width, -height)

    glEnd()