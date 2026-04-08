"""
3D Solar System Animation - OpenGL + Pygame
============================================
Controls:
  - Mouse drag (Left Button): Rotate the solar system
  - Scroll Wheel: Zoom in/out
  - R key: Reset camera
  - ESC: Quit
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

# ── Window ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720

# ── Camera state ─────────────────────────────────────────────────────────────
cam_rot_x   = 20.0
cam_rot_y   = 0.0
cam_zoom    = -55.0
mouse_down  = False
last_mouse  = (0, 0)

# ── Stars ────────────────────────────────────────────────────────────────────
NUM_STARS = 1500
stars = [(random.uniform(-200, 200),
          random.uniform(-200, 200),
          random.uniform(-200, 200)) for _ in range(NUM_STARS)]

# ── Planet definitions ────────────────────────────────────────────────────────
#   name,  radius, orbit_r, speed(°/s), color(RGB 0-1), tilt, moons
PLANETS = [
    # Sun (special – no orbit)
    {"name": "Sun",     "radius": 3.5,  "orbit": 0,    "speed": 0,
     "color": (1.0, 0.85, 0.2),  "tilt": 0,  "emissive": True},

    {"name": "Mercury", "radius": 0.38, "orbit": 6.5,  "speed": 87,
     "color": (0.76, 0.70, 0.65), "tilt": 0,  "emissive": False},

    {"name": "Venus",   "radius": 0.95, "orbit": 10.0, "speed": 34,
     "color": (0.93, 0.80, 0.55), "tilt": 3,  "emissive": False},

    {"name": "Earth",   "radius": 1.0,  "orbit": 14.5, "speed": 21,
     "color": (0.25, 0.55, 0.90), "tilt": 23, "emissive": False,
     "moon": {"radius": 0.27, "orbit": 2.0, "speed": 180,
              "color": (0.80, 0.80, 0.78)}},

    {"name": "Mars",    "radius": 0.53, "orbit": 19.5, "speed": 11,
     "color": (0.78, 0.35, 0.20), "tilt": 25, "emissive": False},

    {"name": "Jupiter", "radius": 2.2,  "orbit": 27.0, "speed": 1.8,
     "color": (0.85, 0.72, 0.55), "tilt": 3,  "emissive": False},

    {"name": "Saturn",  "radius": 1.85, "orbit": 35.0, "speed": 0.75,
     "color": (0.91, 0.84, 0.62), "tilt": 27, "emissive": False,
     "rings": True},

    {"name": "Uranus",  "radius": 1.3,  "orbit": 42.0, "speed": 0.26,
     "color": (0.55, 0.88, 0.95), "tilt": 98, "emissive": False},

    {"name": "Neptune", "radius": 1.25, "orbit": 49.0, "speed": 0.13,
     "color": (0.25, 0.40, 0.95), "tilt": 28, "emissive": False},
]

# ── Angle state ───────────────────────────────────────────────────────────────
angles = {p["name"]: random.uniform(0, 360) for p in PLANETS}
moon_angle = 0.0
sun_glow   = 0.0   # oscillating glow


# ─────────────────────────────────────────────────────────────────────────────
def draw_sphere(radius, slices=32, stacks=32):
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, radius, slices, stacks)
    gluDeleteQuadric(quad)


def draw_orbit_ring(orbit_r, segments=120):
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        glVertex3f(orbit_r * math.cos(angle), 0, orbit_r * math.sin(angle))
    glEnd()


def draw_saturn_rings(inner, outer, segments=80):
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        c, s = math.cos(angle), math.sin(angle)
        glVertex3f(outer * c, 0, outer * s)
        glVertex3f(inner * c, 0, inner * s)
    glEnd()


def draw_stars():
    glPointSize(1.5)
    glBegin(GL_POINTS)
    glColor3f(1, 1, 1)
    for (x, y, z) in stars:
        glVertex3f(x, y, z)
    glEnd()


def draw_sun_glow(radius, pulse):
    """Simple layered transparent spheres to simulate glow."""
    layers = [
        (radius * 1.05, 0.35),
        (radius * 1.15, 0.18),
        (radius * 1.30, 0.07),
    ]
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    for (r, alpha) in layers:
        glColor4f(1.0, 0.80 + 0.05 * pulse, 0.1, alpha)
        draw_sphere(r, 24, 24)
    glDisable(GL_BLEND)
    glDepthMask(GL_TRUE)


def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])  # point light at sun
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 0.95, 0.85, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0,  1.0,  1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.05, 0.05, 0.08, 1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    glMaterialfv(GL_FRONT, GL_SPECULAR,  [0.4, 0.4, 0.4, 1.0])
    glMaterialf (GL_FRONT, GL_SHININESS, 30.0)


# ─────────────────────────────────────────────────────────────────────────────
def draw_scene(dt):
    global sun_glow, moon_angle

    sun_glow += dt * 1.5
    pulse = math.sin(sun_glow)

    # Update angles
    for p in PLANETS:
        if p["speed"] > 0:
            angles[p["name"]] = (angles[p["name"]] + p["speed"] * dt) % 360
    moon_angle = (moon_angle + 180 * dt) % 360

    # ── Stars (no lighting) ───────────────────────────────────────────────
    glDisable(GL_LIGHTING)
    draw_stars()

    # ── Orbit rings ───────────────────────────────────────────────────────
    glColor4f(0.4, 0.4, 0.6, 0.25)
    for p in PLANETS[1:]:
        draw_orbit_ring(p["orbit"])

    # ── Sun ───────────────────────────────────────────────────────────────
    glDisable(GL_LIGHTING)
    sun = PLANETS[0]
    glColor3f(*sun["color"])
    draw_sphere(sun["radius"])
    draw_sun_glow(sun["radius"], pulse)
    glEnable(GL_LIGHTING)

    # ── Planets ───────────────────────────────────────────────────────────
    for p in PLANETS[1:]:
        angle_rad = math.radians(angles[p["name"]])
        px = p["orbit"] * math.cos(angle_rad)
        pz = p["orbit"] * math.sin(angle_rad)

        glPushMatrix()
        glTranslatef(px, 0, pz)
        glRotatef(p["tilt"], 0, 0, 1)

        # Planet body
        glColor3f(*p["color"])
        draw_sphere(p["radius"])

        # Saturn rings
        if p.get("rings"):
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDepthMask(GL_FALSE)
            glColor4f(0.91, 0.84, 0.62, 0.50)
            draw_saturn_rings(p["radius"] * 1.35, p["radius"] * 2.2)
            glDepthMask(GL_TRUE)
            glDisable(GL_BLEND)
            glPopMatrix()

        # Moon
        if p.get("moon"):
            m = p["moon"]
            ma_rad = math.radians(moon_angle)
            mx = m["orbit"] * math.cos(ma_rad)
            mz = m["orbit"] * math.sin(ma_rad)
            glPushMatrix()
            glTranslatef(mx, 0, mz)
            glColor3f(*m["color"])
            draw_sphere(m["radius"], 16, 16)
            glPopMatrix()

        glPopMatrix()


# ─────────────────────────────────────────────────────────────────────────────
def main():
    global cam_rot_x, cam_rot_y, cam_zoom, mouse_down, last_mouse

    pygame.init()
    pygame.display.set_caption("☀  3D Solar System  |  Drag to rotate  |  Scroll to zoom")
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    icon = pygame.Surface((32, 32))
    icon.fill((255, 220, 50))
    pygame.display.set_icon(icon)

    # OpenGL setup
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    setup_lighting()

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0   # seconds per frame

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit(); return
            if event.type == KEYDOWN and event.key == K_r:
                cam_rot_x, cam_rot_y, cam_zoom = 20.0, 0.0, -55.0

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                last_mouse = event.pos
            if event.type == MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
            if event.type == MOUSEMOTION and mouse_down:
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                cam_rot_y += dx * 0.4
                cam_rot_x += dy * 0.4
                cam_rot_x = max(-89, min(89, cam_rot_x))
                last_mouse = event.pos

            if event.type == MOUSEBUTTONDOWN and event.button == 4:
                cam_zoom = min(-5, cam_zoom + 2)
            if event.type == MOUSEBUTTONDOWN and event.button == 5:
                cam_zoom = max(-150, cam_zoom - 2)

        # ── Render ────────────────────────────────────────────────────────
        glClearColor(0.01, 0.01, 0.06, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0, 0, cam_zoom)
        glRotatef(cam_rot_x, 1, 0, 0)
        glRotatef(cam_rot_y, 0, 1, 0)

        draw_scene(dt)

        pygame.display.flip()


if __name__ == "__main__":
    main()
