import math
import random
from OpenGL.GL import *
from OpenGL.GLUT import *

# =========================
# WINDOW
# =========================
WIDTH = 1600
HEIGHT = 900

time_value = 0.0

far_stars = []
mid_stars = []
near_stars = []

engine_particles = []
beam_particles = []


# =========================
# HELPERS
# =========================
def clamp(v, a, b):
    return max(a, min(b, v))


def draw_circle(cx, cy, r, segments=80, filled=True):
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            a = 2.0 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
        glEnd()
    else:
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
        glEnd()


def draw_ellipse(cx, cy, rx, ry, segments=120, filled=True):
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            a = 2.0 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
        glEnd()
    else:
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
        glEnd()


def draw_gradient_ellipse(cx, cy, rx, ry, inner_color, outer_color, segments=140):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*inner_color)
    glVertex2f(cx, cy)
    glColor4f(*outer_color)
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
    glEnd()


# =========================
# STARFIELD
# =========================
def init_stars():
    global far_stars, mid_stars, near_stars
    far_stars = []
    mid_stars = []
    near_stars = []

    for _ in range(1200):
        far_stars.append((
            random.uniform(-1.9, 1.9),
            random.uniform(-1.1, 1.1),
            random.uniform(0.2, 0.7),
            random.uniform(0.5, 1.2),
            random.uniform(0.75, 1.0)
        ))

    for _ in range(650):
        mid_stars.append((
            random.uniform(-1.9, 1.9),
            random.uniform(-1.1, 1.1),
            random.uniform(0.4, 0.9),
            random.uniform(1.0, 1.8),
            random.uniform(0.75, 1.0)
        ))

    for _ in range(250):
        near_stars.append((
            random.uniform(-1.9, 1.9),
            random.uniform(-1.1, 1.1),
            random.uniform(0.7, 1.0),
            random.uniform(1.5, 2.8),
            random.uniform(0.8, 1.0)
        ))


def draw_star_layer(stars, speed_mul):
    for x, y, brightness, size, warm in stars:
        twinkle = 0.85 + 0.15 * math.sin(time_value * (1.5 + speed_mul) + x * 9.0 + y * 13.0)
        glPointSize(size)
        glBegin(GL_POINTS)
        glColor3f(brightness * twinkle, brightness * twinkle, brightness * warm)
        glVertex2f(x, y)
        glEnd()


def draw_stars():
    draw_star_layer(far_stars, 0.3)
    draw_star_layer(mid_stars, 0.7)
    draw_star_layer(near_stars, 1.2)


# =========================
# PARTICLES
# =========================
def spawn_engine_particle():
    return {
        "x": random.uniform(-0.09, 0.09),
        "y": -0.07,
        "vx": random.uniform(-0.0025, 0.0025),
        "vy": random.uniform(-0.020, -0.006),
        "life": random.uniform(0.6, 1.0),
        "size": random.uniform(0.004, 0.015)
    }


def spawn_beam_particle():
    return {
        "x": random.uniform(-0.15, 0.15),
        "y": random.uniform(-0.05, -0.85),
        "vy": random.uniform(-0.004, -0.001),
        "life": random.uniform(0.4, 1.0),
        "size": random.uniform(0.003, 0.012)
    }


def init_particles():
    global engine_particles, beam_particles
    engine_particles = [spawn_engine_particle() for _ in range(140)]
    beam_particles = [spawn_beam_particle() for _ in range(120)]


def update_particles():
    global engine_particles, beam_particles

    for i, p in enumerate(engine_particles):
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 0.02
        if p["life"] <= 0 or p["y"] < -0.45:
            engine_particles[i] = spawn_engine_particle()

    for i, p in enumerate(beam_particles):
        p["y"] += p["vy"]
        p["life"] -= 0.01
        if p["life"] <= 0 or p["y"] < -0.95:
            beam_particles[i] = spawn_beam_particle()


# =========================
# BACKGROUND
# =========================
def draw_background():
    glBegin(GL_QUADS)
    glColor3f(0.01, 0.01, 0.03)
    glVertex2f(-2.0, -1.2)
    glVertex2f(2.0, -1.2)
    glColor3f(0.00, 0.02, 0.08)
    glVertex2f(2.0, 1.2)
    glVertex2f(-2.0, 1.2)
    glEnd()

    # subtle haze
    for i in range(14, 0, -1):
        a = 0.002 + i * 0.0015
        draw_gradient_ellipse(
            -0.8, 0.55,
            0.3 + i * 0.06,
            0.12 + i * 0.025,
            (0.15, 0.22, 0.45, a),
            (0.05, 0.05, 0.12, 0.0)
        )


# =========================
# UFO
# =========================



def draw_engine_fire(ship_x, ship_y):
    for p in engine_particles:
        px = ship_x + p["x"]
        py = ship_y + p["y"]

        glColor4f(1.0, 0.55, 0.10, 0.85 * p["life"])
        draw_circle(px, py, p["size"], 18, True)

        glColor4f(1.0, 0.9, 0.7, 0.22 * p["life"])
        draw_circle(px, py, p["size"] * 2.2, 18, True)


def draw_ufo(ship_x, ship_y):
    bob = 0.018 * math.sin(time_value * 2.1)
    tilt = 0.004 * math.sin(time_value * 1.4)
    x = ship_x
    y = ship_y + bob

    # outer cinematic glow
    for i in range(22, 0, -1):
        a = 0.002 + i * 0.0018
        draw_gradient_ellipse(
            x, y,
            0.22 + i * 0.012,
            0.065 + i * 0.004,
            (0.35, 0.90, 1.0, a),
            (0.05, 0.20, 0.50, 0.0)
        )

    # lower shadow
    glColor4f(0.08, 0.09, 0.12, 0.9)
    draw_ellipse(x, y - 0.005, 0.29, 0.08, 140, True)

    # metallic hull base
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.92, 0.93, 0.96, 1.0)
    glVertex2f(x, y + 0.006)
    for i in range(141):
        a = 2.0 * math.pi * i / 140
        px = x + math.cos(a) * 0.27
        py = y + math.sin(a) * 0.073
        shade = 0.65 + 0.35 * math.cos(a - math.pi * 0.35)
        glColor4f(0.55 * shade + 0.25, 0.58 * shade + 0.25, 0.65 * shade + 0.25, 1.0)
        glVertex2f(px, py)
    glEnd()

    # top reflective band
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.98, 0.99, 1.0, 0.95)
    glVertex2f(x, y + 0.015)
    for i in range(141):
        a = 2.0 * math.pi * i / 140
        px = x + math.cos(a) * 0.21
        py = y + 0.01 + math.sin(a) * 0.038
        shade = 0.75 + 0.25 * math.cos(a - math.pi * 0.2)
        glColor4f(0.72 * shade + 0.15, 0.78 * shade + 0.15, 0.88 * shade + 0.12, 0.98)
        glVertex2f(px, py)
    glEnd()

    # dome glow
    for i in range(14, 0, -1):
        draw_gradient_ellipse(
            x, y + 0.062,
            0.115 + i * 0.005,
            0.078 + i * 0.004,
            (0.55, 0.98, 1.0, 0.014 + i * 0.006),
            (0.10, 0.35, 0.55, 0.0)
        )

    # main dome
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.78, 0.98, 1.0, 0.85)
    glVertex2f(x, y + 0.07)
    for i in range(141):
        a = 2.0 * math.pi * i / 140
        px = x + math.cos(a) * 0.11
        py = y + 0.058 + math.sin(a) * 0.078
        shade = 0.75 + 0.25 * math.cos(a - 0.7)
        glColor4f(0.35 * shade + 0.35, 0.75 * shade + 0.20, 0.95 * shade + 0.05, 0.82)
        glVertex2f(px, py)
    glEnd()

    # dome highlight
    glColor4f(1.0, 1.0, 1.0, 0.3)
    draw_ellipse(x - 0.03, y + 0.09, 0.035, 0.02, 50, True)

    # rim lights
    for i in range(9):
        a = -math.pi * 0.85 + i * (math.pi * 1.7 / 8.0)
        lx = x + math.cos(a) * 0.21
        ly = y - 0.003 + math.sin(a) * 0.02
        pulse = 0.55 + 0.45 * math.sin(time_value * 5.2 + i * 0.8)
        glColor4f(1.0, 0.92, 0.35, 0.55 + 0.35 * pulse)
        draw_circle(lx, ly, 0.011, 20, True)
        glColor4f(1.0, 1.0, 0.7, 0.12 * pulse)
        draw_circle(lx, ly, 0.025, 20, True)

    # underside center light
    pulse = 0.8 + 0.2 * math.sin(time_value * 6.0)
    glColor4f(0.75, 1.0, 1.0, 0.65 * pulse)
    draw_circle(x, y - 0.012, 0.018, 30, True)
    glColor4f(0.9, 1.0, 1.0, 0.18 * pulse)
    draw_circle(x, y - 0.012, 0.045, 30, True)

    draw_engine_fire(x, y - 0.02)


# =========================
# DISPLAY
# =========================
def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    draw_background()
    draw_stars()

    ship_x = 0.48 * math.sin(time_value * 0.45)
    ship_y = 0.18 + 0.08 * math.sin(time_value * 0.9)


    draw_ufo(ship_x, ship_y)

    glutSwapBuffers()


def update(value):
    global time_value
    time_value += 0.016
    update_particles()
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)


def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    aspect = w / float(h if h != 0 else 1)
    if aspect >= 1:
        glOrtho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0)
    else:
        glOrtho(-1.0, 1.0, -1.0 / aspect, 1.0 / aspect, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)

    init_stars()
    init_particles()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"High Quality UFO / Spacecraft")

    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutTimerFunc(16, update, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()