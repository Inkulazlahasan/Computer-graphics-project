import math
import random
from OpenGL.GL import *
from OpenGL.GLUT import *

# =========================
# WINDOW
# =========================
WIDTH = 1400
HEIGHT = 850

# black hole position
BH_X = 0.78
BH_Y = 0.02

time_value = 0.0
disk_rotation = 0.0

stars = []
dust = []
particles = []
chunks = []


# =========================
# INIT DATA
# =========================
def init_stars():
    global stars
    stars = []
    for _ in range(1600):
        x = random.uniform(-1.8, 1.8)
        y = random.uniform(-1.1, 1.1)
        b = random.uniform(0.25, 1.0)
        s = random.uniform(0.6, 2.0)
        warm = random.uniform(0.7, 1.0)
        stars.append((x, y, b, s, warm))


def init_dust():
    global dust
    dust = []
    for _ in range(350):
        x = random.uniform(-1.7, 0.3)
        y = random.uniform(-0.9, 0.9)
        r = random.uniform(0.01, 0.04)
        a = random.uniform(0.005, 0.03)
        dust.append((x, y, r, a))


def spawn_particle():
    side = random.choice(["left_stream", "orbit"])
    if side == "left_stream":
        x = random.uniform(-1.6, -0.4)
        y = random.uniform(-0.7, 0.15)
        vx = random.uniform(0.002, 0.006)
        vy = random.uniform(-0.001, 0.001)
    else:
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0.55, 1.15)
        x = BH_X + math.cos(angle) * r
        y = BH_Y + math.sin(angle) * r * 0.55
        vx = 0.0
        vy = 0.0

    size = random.uniform(0.003, 0.01)
    heat = random.uniform(0.5, 1.0)

    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "size": size,
        "heat": heat,
        "trail": []
    }


def spawn_chunk():
    x = random.uniform(-1.5, -0.6)
    y = random.uniform(-0.55, 0.45)
    vx = random.uniform(0.0008, 0.0025)
    vy = random.uniform(-0.001, 0.001)
    size = random.uniform(0.012, 0.028)
    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "size": size,
        "trail": []
    }


def init_particles():
    global particles, chunks
    particles = [spawn_particle() for _ in range(900)]
    chunks = [spawn_chunk() for _ in range(18)]


# =========================
# HELPERS
# =========================
def draw_circle(cx, cy, r, segments=80, filled=True):
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            a = 2 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
        glEnd()
    else:
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            a = 2 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
        glEnd()


def draw_ellipse(cx, cy, rx, ry, segments=120, filled=False):
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            a = 2 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
        glEnd()
    else:
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            a = 2 * math.pi * i / segments
            glVertex2f(cx + math.cos(a) * rx, cy + math.sin(a) * ry)
        glEnd()


def clamp(v, a, b):
    return max(a, min(b, v))


# =========================
# BACKGROUND
# =========================
def draw_background():
    glBegin(GL_QUADS)
    glColor3f(0.01, 0.01, 0.03)
    glVertex2f(-2.0, -1.2)
    glVertex2f(2.0, -1.2)
    glColor3f(0.05, 0.00, 0.08)
    glVertex2f(2.0, 1.2)
    glVertex2f(-2.0, 1.2)
    glEnd()


def draw_nebula():
    for x, y, r, a in dust:
        glColor4f(1.0, 0.25, 0.08, a)
        draw_circle(x, y, r, 40, True)

    for i in range(18):
        rr = 0.08 + i * 0.05
        aa = 0.012 - i * 0.0005
        glColor4f(0.8, 0.08, 0.18, max(aa, 0.002))
        draw_ellipse(-1.0, 0.55, rr * 1.7, rr * 0.7, 100, True)


def draw_stars():
    for x, y, b, s, warm in stars:
        glPointSize(s)
        glBegin(GL_POINTS)
        glColor3f(b, b * warm, b * 0.7)
        glVertex2f(x, y)
        glEnd()


# =========================
# BLACK HOLE
# =========================
def draw_outer_glow():
    for i in range(28, 0, -1):
        r = 0.23 + i * 0.016
        a = 0.004 + i * 0.0011
        glColor4f(1.0, 0.22, 0.02, a)
        draw_circle(BH_X, BH_Y, r, 100, True)

    for i in range(16, 0, -1):
        r = 0.23 + i * 0.012
        a = 0.003 + i * 0.0010
        glColor4f(1.0, 0.85, 0.6, a)
        draw_circle(BH_X, BH_Y, r, 100, True)


def draw_lensing():
    glLineWidth(2.0)
    for i in range(7):
        r = 0.29 + i * 0.03
        a = 0.11 - i * 0.012
        glColor4f(1.0, 0.9, 0.75, max(a, 0.01))
        draw_ellipse(BH_X, BH_Y, r * 1.05, r * 0.96, 140, False)


def draw_photon_ring():
    for i in range(8):
        r = 0.218 + i * 0.004
        glColor4f(1.0, 0.95, 0.82, 0.18 - i * 0.016)
        draw_ellipse(BH_X, BH_Y, r * 1.03, r * 0.98, 160, False)


def draw_event_horizon():
    for i in range(15, 0, -1):
        r = 0.205 + i * 0.008
        glColor4f(0.0, 0.0, 0.0, 0.008)
        draw_circle(BH_X, BH_Y, r, 100, True)

    glColor3f(0.0, 0.0, 0.0)
    draw_circle(BH_X, BH_Y, 0.21, 140, True)


def draw_disk():
    global disk_rotation, time_value

    # left stream
    glPushMatrix()
    glTranslatef(BH_X, BH_Y, 0.0)
    glRotatef(-11, 0, 0, 1)

    for i in range(120):
        t = i / 120.0
        x1 = -1.65 + t * 2.05
        x2 = x1 + 0.035

        ymid = -0.56 + t * 0.30 + 0.025 * math.sin(12 * t + time_value * 4.0)
        thick = 0.028 + 0.05 * (1.0 - t)

        a = 0.04 + 0.16 * (1.0 - abs(t - 0.8))
        glBegin(GL_QUADS)
        glColor4f(1.0, 0.2 + 0.7 * (1 - t), 0.02 + 0.08 * t, a * 0.35)
        glVertex2f(x1, ymid - thick)
        glVertex2f(x2, ymid - thick * 0.8)
        glColor4f(1.0, 0.95, 0.8, a)
        glVertex2f(x2, ymid + thick * 0.8)
        glVertex2f(x1, ymid + thick)
        glEnd()

    glPopMatrix()

    # spinning accretion disk
    glPushMatrix()
    glTranslatef(BH_X, BH_Y, 0.0)
    glRotatef(disk_rotation, 0, 0, 1)

    layers = 120
    for i in range(layers):
        t = i / float(layers)
        r1 = 0.27 + t * 0.55
        r2 = r1 + 0.010 + t * 0.004

        squash = 0.42 + 0.04 * math.sin(time_value + t * 5.0)

        red = 1.0
        green = 0.22 + 0.78 * (1.0 - t)
        blue = 0.03 + 0.20 * t
        alpha = 0.22 * (1.0 - t) + 0.015

        glBegin(GL_QUAD_STRIP)
        for j in range(220):
            a = 2 * math.pi * j / 219.0
            wave = 0.012 * math.sin(7 * a + time_value * 4 + t * 8)
            bend = 0.04 * math.exp(-((a - math.pi * 1.6) ** 2) / 0.25)

            x1 = math.cos(a) * (r1 + wave)
            y1 = math.sin(a) * (r1 + wave) * squash

            x2 = math.cos(a) * (r2 + wave)
            y2 = math.sin(a) * (r2 + wave) * squash

            boost = 1.0
            if 0.15 < a < 2.8:
                boost = 1.45

            glColor4f(
                min(red * boost, 1.0),
                min(green * boost, 1.0),
                min(blue * boost + 0.04, 1.0),
                alpha
            )
            glVertex2f(x1, y1 + bend)
            glVertex2f(x2, y2 + bend)
        glEnd()

    glPopMatrix()


# =========================
# SUCKING PARTICLES
# =========================
def draw_particle_trail(p):
    trail = p["trail"]
    if len(trail) < 2:
        return

    glBegin(GL_LINE_STRIP)
    for i, (tx, ty) in enumerate(trail):
        t = i / float(len(trail))
        alpha = t * 0.35
        glColor4f(1.0, 0.5 + 0.4 * t, 0.1, alpha)
        glVertex2f(tx, ty)
    glEnd()


def draw_particles():
    for p in particles:
        draw_particle_trail(p)

        x = p["x"]
        y = p["y"]
        size = p["size"]
        heat = p["heat"]

        dx = x - BH_X
        dy = y - BH_Y
        dist = math.sqrt(dx * dx + dy * dy)

        hot = clamp(1.35 - dist, 0.0, 1.0)

        glColor4f(1.0, 0.35 + 0.55 * heat + 0.25 * hot, 0.08 + 0.15 * hot, 0.9)
        draw_circle(x, y, size, 18, True)

        if dist < 0.42:
            glColor4f(1.0, 0.95, 0.8, 0.25)
            draw_circle(x, y, size * 2.2, 18, True)


def draw_chunk_trail(c):
    trail = c["trail"]
    if len(trail) < 2:
        return

    glBegin(GL_LINE_STRIP)
    for i, (tx, ty) in enumerate(trail):
        t = i / float(len(trail))
        glColor4f(1.0, 0.7, 0.3, t * 0.28)
        glVertex2f(tx, ty)
    glEnd()


def draw_chunks():
    for c in chunks:
        draw_chunk_trail(c)

        x = c["x"]
        y = c["y"]
        s = c["size"]

        glColor4f(1.0, 0.45, 0.10, 0.85)
        draw_circle(x, y, s, 20, True)
        glColor4f(1.0, 0.9, 0.7, 0.22)
        draw_circle(x, y, s * 1.9, 20, True)


# =========================
# MOTION
# =========================
def update_particles():
    global particles, chunks

    for i, p in enumerate(particles):
        dx = BH_X - p["x"]
        dy = BH_Y - p["y"]

        dist2 = dx * dx + dy * dy + 0.0001
        dist = math.sqrt(dist2)

        # gravity pull
        gravity = 0.00012 / dist2
        p["vx"] += dx * gravity
        p["vy"] += dy * gravity

        # swirl
        tangent_x = -dy
        tangent_y = dx
        swirl = 0.00008 / (dist + 0.03)
        p["vx"] += tangent_x * swirl
        p["vy"] += tangent_y * swirl

        # disk pull flattening
        p["vy"] *= 0.997

        # move
        p["x"] += p["vx"]
        p["y"] += p["vy"]

        # heat increase near center
        p["heat"] = clamp(p["heat"] + 0.002 * (1.2 - dist), 0.3, 1.4)

        # trail
        p["trail"].append((p["x"], p["y"]))
        if len(p["trail"]) > 14:
            p["trail"].pop(0)

        # respawn if swallowed or outside
        if dist < 0.22 or abs(p["x"]) > 2.2 or abs(p["y"]) > 1.4:
            particles[i] = spawn_particle()

    for i, c in enumerate(chunks):
        dx = BH_X - c["x"]
        dy = BH_Y - c["y"]

        dist2 = dx * dx + dy * dy + 0.0001
        dist = math.sqrt(dist2)

        gravity = 0.00028 / dist2
        c["vx"] += dx * gravity
        c["vy"] += dy * gravity

        tangent_x = -dy
        tangent_y = dx
        swirl = 0.00011 / (dist + 0.02)
        c["vx"] += tangent_x * swirl
        c["vy"] += tangent_y * swirl

        c["x"] += c["vx"]
        c["y"] += c["vy"]

        c["trail"].append((c["x"], c["y"]))
        if len(c["trail"]) > 20:
            c["trail"].pop(0)

        if dist < 0.24:
            chunks[i] = spawn_chunk()


# =========================
# SMALL PLANET
# =========================
planet_angle = 2.8
planet_radius = 0.62

def draw_small_planet():
    px = BH_X + math.cos(planet_angle) * planet_radius
    py = BH_Y + math.sin(planet_angle) * planet_radius * 0.55

    glColor3f(0.03, 0.03, 0.06)
    draw_circle(px, py, 0.045, 60, True)
    glColor4f(0.9, 0.85, 0.6, 0.35)
    draw_circle(px + 0.02, py + 0.01, 0.011, 20, True)


# =========================
# DISPLAY
# =========================
def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    draw_background()
    draw_nebula()
    draw_stars()

    draw_outer_glow()
    draw_disk()

    draw_chunk_trail_layer_first()
    draw_particle_trail_layer_first()

    draw_lensing()
    draw_photon_ring()

    draw_chunks()
    draw_particles()

    draw_event_horizon()
    draw_small_planet()

    glutSwapBuffers()


def draw_particle_trail_layer_first():
    for p in particles:
        draw_particle_trail(p)


def draw_chunk_trail_layer_first():
    for c in chunks:
        draw_chunk_trail(c)


# =========================
# LOOP
# =========================
def update(value):
    global time_value, disk_rotation, planet_angle, planet_radius

    time_value += 0.016
    disk_rotation += 0.18

    update_particles()

    # small planet slowly spirals inward
    planet_angle += 0.01
    planet_radius -= 0.00025
    if planet_radius < 0.34:
        planet_radius = 0.62
        planet_angle = random.uniform(0, 2 * math.pi)

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)


# =========================
# RESHAPE
# =========================
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


# =========================
# OPENGL INIT
# =========================
def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)
    glLineWidth(2)

    init_stars()
    init_dust()
    init_particles()


# =========================
# MAIN
# =========================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"Animated Black Hole Sucking Objects")

    init()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutTimerFunc(16, update, 0)

    glutMainLoop()


if __name__ == "__main__":
    main()