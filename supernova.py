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

stars = []
ejecta_particles = []
rings = []


# =========================
# HELPERS
# =========================
def clamp(v, a, b):
    return max(a, min(b, v))


def draw_circle(cx, cy, r, segments=90, filled=True):
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


def draw_gradient_circle(cx, cy, r, inner_color, outer_color, segments=140):
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*inner_color)
    glVertex2f(cx, cy)
    glColor4f(*outer_color)
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
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
# STARS
# =========================
def init_stars():
    global stars
    stars = []
    for _ in range(2400):
        stars.append((
            random.uniform(-1.9, 1.9),
            random.uniform(-1.1, 1.1),
            random.uniform(0.25, 1.0),
            random.uniform(0.7, 2.0),
            random.uniform(0.85, 1.0)
        ))


def draw_stars():
    for x, y, b, s, blue in stars:
        tw = 0.82 + 0.18 * math.sin(time_value * 1.6 + x * 8.0 + y * 12.0)
        glPointSize(s)
        glBegin(GL_POINTS)
        glColor3f(b * tw, b * tw, min(1.0, b * blue + 0.1))
        glVertex2f(x, y)
        glEnd()


# =========================
# SUPERNOVA DATA
# =========================
def spawn_particle():
    angle = random.uniform(0, 2.0 * math.pi)
    speed = random.uniform(0.0025, 0.014)

    # prefer bipolar directions a bit
    if random.random() < 0.5:
        angle = random.choice([
            random.uniform(math.pi / 3, 2 * math.pi / 3),
            random.uniform(-2 * math.pi / 3, -math.pi / 3)
        ])
        speed *= 1.2

    return {
        "x": 0.0,
        "y": 0.0,
        "vx": math.cos(angle) * speed,
        "vy": math.sin(angle) * speed,
        "life": random.uniform(0.65, 1.0),
        "size": random.uniform(0.003, 0.010),
        "trail": []
    }


def spawn_ring():
    return {
        "r": random.uniform(0.03, 0.08),
        "alpha": random.uniform(0.35, 0.65),
        "speed": random.uniform(0.0035, 0.0075),
        "ratio": random.uniform(1.35, 1.85)
    }


def init_supernova():
    global ejecta_particles, rings
    ejecta_particles = [spawn_particle() for _ in range(1100)]
    rings = [spawn_ring() for _ in range(8)]


def update_supernova():
    global ejecta_particles, rings

    for i, p in enumerate(ejecta_particles):
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # small drift
        p["vx"] *= 1.0005
        p["vy"] *= 1.0005

        p["life"] -= 0.0035

        p["trail"].append((p["x"], p["y"]))
        if len(p["trail"]) > 18:
            p["trail"].pop(0)

        if abs(p["x"]) > 2.0 or abs(p["y"]) > 1.25 or p["life"] <= 0:
            ejecta_particles[i] = spawn_particle()

    for i, ring in enumerate(rings):
        ring["r"] += ring["speed"]
        ring["alpha"] -= 0.0028
        if ring["alpha"] <= 0:
            rings[i] = spawn_ring()


# =========================
# DRAW SUPERNOVA
# =========================
def draw_background():
    glBegin(GL_QUADS)
    glColor3f(0.00, 0.01, 0.05)
    glVertex2f(-2.0, -1.2)
    glVertex2f(2.0, -1.2)
    glColor3f(0.00, 0.08, 0.18)
    glVertex2f(2.0, 1.2)
    glVertex2f(-2.0, 1.2)
    glEnd()


def draw_nebula_glow():
    # central blue wash
    for i in range(22, 0, -1):
        a = 0.003 + i * 0.0018
        draw_gradient_circle(
            0.0, 0.0,
            0.14 + i * 0.05,
            (0.25, 0.65, 1.0, a),
            (0.05, 0.15, 0.45, 0.0)
        )

    # broad bipolar lobes
    for i in range(18, 0, -1):
        a = 0.002 + i * 0.0016
        draw_gradient_ellipse(
            -0.33, -0.10,
            0.18 + i * 0.028,
            0.26 + i * 0.05,
            (0.85, 0.65, 0.9, a),
            (0.2, 0.2, 0.4, 0.0)
        )
        draw_gradient_ellipse(
            0.36, 0.13,
            0.18 + i * 0.03,
            0.28 + i * 0.05,
            (0.85, 0.65, 0.9, a),
            (0.2, 0.2, 0.4, 0.0)
        )


def draw_core():
    pulse = 1.0 + 0.08 * math.sin(time_value * 4.2)

    for i in range(18, 0, -1):
        draw_gradient_ellipse(
            0.0, 0.0,
            (0.03 + i * 0.010) * pulse,
            (0.07 + i * 0.018) * pulse,
            (1.0, 0.95, 1.0, 0.03 + i * 0.012),
            (0.5, 0.8, 1.0, 0.0)
        )

    glColor4f(1.0, 1.0, 1.0, 0.98)
    draw_ellipse(0.0, 0.0, 0.028 * pulse, 0.060 * pulse, 100, True)


def draw_beams():
    beam_count = 40
    for i in range(beam_count):
        a = i * (2.0 * math.pi / beam_count) + time_value * 0.12
        width = 0.018
        length = 0.35 + 0.22 * (0.5 + 0.5 * math.sin(time_value * 2.6 + i * 0.9))

        x1 = math.cos(a - width) * 0.05
        y1 = math.sin(a - width) * 0.05
        x2 = math.cos(a + width) * 0.05
        y2 = math.sin(a + width) * 0.05
        x3 = math.cos(a) * length
        y3 = math.sin(a) * length

        glBegin(GL_TRIANGLES)
        glColor4f(0.55, 0.82, 1.0, 0.11)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glColor4f(0.20, 0.45, 1.0, 0.0)
        glVertex2f(x3, y3)
        glEnd()


def draw_rings():
    for ring in rings:
        for i in range(5):
            alpha = ring["alpha"] - i * 0.045
            if alpha <= 0:
                continue
            glColor4f(1.0, 0.78, 0.90, alpha)
            draw_ellipse(0.0, 0.0, ring["r"] + i * 0.01, (ring["r"] + i * 0.01) * ring["ratio"], 160, False)


def draw_particle_trail(p):
    if len(p["trail"]) < 2:
        return

    glBegin(GL_LINE_STRIP)
    for i, (tx, ty) in enumerate(p["trail"]):
        t = i / float(len(p["trail"]))
        glColor4f(1.0, 0.75, 0.92, t * 0.30 * p["life"])
        glVertex2f(tx, ty)
    glEnd()


def draw_particles():
    for p in ejecta_particles:
        draw_particle_trail(p)

        glColor4f(1.0, 0.78, 0.92, 0.82 * p["life"])
        draw_circle(p["x"], p["y"], p["size"], 18, True)

        glColor4f(1.0, 0.95, 1.0, 0.16 * p["life"])
        draw_circle(p["x"], p["y"], p["size"] * 2.4, 18, True)


def draw_bipolar_shells():
    # left shell
    for i in range(3):
        alpha = 0.12 - i * 0.03
        glColor4f(1.0, 0.78, 0.88, alpha)
        glBegin(GL_LINE_STRIP)
        for t in range(120):
            u = t / 119.0
            ang = math.pi * 0.15 + u * math.pi * 1.55
            r = 0.32 + 0.07 * math.sin(u * math.pi)
            x = -0.34 + math.cos(ang) * r * 0.62
            y = -0.10 + math.sin(ang) * r * 1.35
            glVertex2f(x, y)
        glEnd()

    # right shell
    for i in range(3):
        alpha = 0.12 - i * 0.03
        glColor4f(1.0, 0.78, 0.88, alpha)
        glBegin(GL_LINE_STRIP)
        for t in range(120):
            u = t / 119.0
            ang = -math.pi * 0.55 + u * math.pi * 1.55
            r = 0.32 + 0.07 * math.sin(u * math.pi)
            x = 0.36 + math.cos(ang) * r * 0.65
            y = 0.14 + math.sin(ang) * r * 1.38
            glVertex2f(x, y)
        glEnd()


# =========================
# DISPLAY
# =========================
def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    draw_background()
    draw_stars()
    draw_nebula_glow()
    draw_beams()
    draw_bipolar_shells()
    draw_rings()
    draw_particles()
    draw_core()

    glutSwapBuffers()


def update(value):
    global time_value
    time_value += 0.016
    update_supernova()
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
    init_supernova()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"High Quality Supernova")

    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutTimerFunc(16, update, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()