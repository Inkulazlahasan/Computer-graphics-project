import math
import random
import time

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

WIDTH = 1280
HEIGHT = 720

cam_rot_x = 25.0
cam_rot_y = -20.0
cam_zoom = -65.0
mouse_down = False
last_mouse = (0, 0)

NUM_STARS = 1800
stars = [
    (random.uniform(-220, 220), random.uniform(-220, 220), random.uniform(-220, 220))
    for _ in range(NUM_STARS)
]

PLANETS = [
    {"name": "Sun",     "radius": 3.5,  "orbit": 0.0,  "speed": 0.0,  "color": (1.0, 0.82, 0.18)},
    {"name": "Mercury", "radius": 0.40, "orbit": 6.5,  "speed": 1.20, "color": (0.75, 0.70, 0.66)},
    {"name": "Venus",   "radius": 0.95, "orbit": 10.0, "speed": 0.90, "color": (0.92, 0.78, 0.50)},
    {"name": "Earth",   "radius": 1.00, "orbit": 14.5, "speed": 0.75, "color": (0.22, 0.55, 0.95)},
    {"name": "Mars",    "radius": 0.55, "orbit": 19.0, "speed": 0.60, "color": (0.80, 0.35, 0.20)},
    {"name": "Jupiter", "radius": 2.15, "orbit": 27.5, "speed": 0.35, "color": (0.85, 0.72, 0.55)},
    {"name": "Saturn",  "radius": 1.90, "orbit": 35.0, "speed": 0.24, "color": (0.92, 0.84, 0.62), "rings": True},
    {"name": "Uranus",  "radius": 1.35, "orbit": 42.5, "speed": 0.16, "color": (0.55, 0.88, 0.95)},
    {"name": "Neptune", "radius": 1.25, "orbit": 49.0, "speed": 0.12, "color": (0.25, 0.42, 0.95)},
]

angles = {p["name"]: random.uniform(0, 360) for p in PLANETS}
moon_angle = 0.0
sun_glow = 0.0


def draw_sphere(radius, slices=30, stacks=30):
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, radius, slices, stacks)
    gluDeleteQuadric(quad)


def draw_orbit_ring(radius, segments=100):
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        glVertex3f(math.cos(a) * radius, 0.0, math.sin(a) * radius)
    glEnd()


def draw_saturn_rings(inner_r, outer_r, segments=90):
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        c = math.cos(a)
        s = math.sin(a)
        glVertex3f(c * outer_r, 0.0, s * outer_r)
        glVertex3f(c * inner_r, 0.0, s * inner_r)
    glEnd()


def draw_stars():
    glPointSize(1.5)
    glBegin(GL_POINTS)
    glColor3f(1.0, 1.0, 1.0)
    for sx, sy, sz in stars:
        glVertex3f(sx, sy, sz)
    glEnd()


def draw_sun_glow(pulse):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    layers = [(4.2, 0.25), (5.0, 0.12), (6.2, 0.06)]
    for r, a in layers:
        glColor4f(1.0, 0.75 + 0.05 * pulse, 0.15, a)
        draw_sphere(r, 24, 24)

    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)


def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.85, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.04, 0.04, 0.06, 1.0])

    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 24.0)


def draw_scene(dt):
    global moon_angle, sun_glow

    for p in PLANETS:
        if p["name"] != "Sun":
            angles[p["name"]] = (angles[p["name"]] + p["speed"] * 40.0 * dt) % 360.0

    moon_angle = (moon_angle + 140.0 * dt) % 360.0
    sun_glow += dt * 2.0

    glDisable(GL_LIGHTING)
    draw_stars()

    glColor4f(0.35, 0.35, 0.55, 0.30)
    for p in PLANETS[1:]:
        draw_orbit_ring(p["orbit"])

    pulse = math.sin(time.time() * 2.0)

    glPushMatrix()
    glColor3f(*PLANETS[0]["color"])
    draw_sphere(PLANETS[0]["radius"], 36, 36)
    draw_sun_glow(pulse)
    glPopMatrix()

    glEnable(GL_LIGHTING)

    for p in PLANETS[1:]:
        angle = math.radians(angles[p["name"]])
        px = math.cos(angle) * p["orbit"]
        pz = math.sin(angle) * p["orbit"]

        glPushMatrix()
        glTranslatef(px, 0.0, pz)
        glColor3f(*p["color"])
        draw_sphere(p["radius"], 28, 28)

        if p.get("rings"):
            glPushMatrix()
            glRotatef(90.0, 1.0, 0.0, 0.0)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDepthMask(GL_FALSE)
            glColor4f(0.93, 0.85, 0.65, 0.48)
            draw_saturn_rings(p["radius"] * 1.45, p["radius"] * 2.25)
            glDepthMask(GL_TRUE)
            glDisable(GL_BLEND)
            glPopMatrix()

        if p["name"] == "Earth":
            ma = math.radians(moon_angle)
            mx = math.cos(ma) * 2.1
            mz = math.sin(ma) * 2.1
            glPushMatrix()
            glTranslatef(mx, 0.0, mz)
            glColor3f(0.82, 0.82, 0.80)
            draw_sphere(0.28, 18, 18)
            glPopMatrix()

        glPopMatrix()


def main():
    global cam_rot_x, cam_rot_y, cam_zoom, mouse_down, last_mouse

    pygame.init()
    pygame.display.set_caption("3D Solar System")
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WIDTH / HEIGHT, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    setup_lighting()

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                return
            if event.type == KEYDOWN and event.key == K_r:
                cam_rot_x, cam_rot_y, cam_zoom = 25.0, -20.0, -65.0

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
                cam_zoom += 2.5
            if event.type == MOUSEBUTTONDOWN and event.button == 5:
                cam_zoom -= 2.5

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, cam_zoom)
        glRotatef(cam_rot_x, 1.0, 0.0, 0.0)
        glRotatef(cam_rot_y, 0.0, 1.0, 0.0)
        draw_scene(dt)
        pygame.display.flip()


if __name__ == "__main__":
    main()
