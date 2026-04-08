import random
from OpenGL.GL import *

particles = []

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = random.uniform(0.5, 1.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.2
        self.life -= 0.02

    def draw(self):
        glColor3f(1, random.random(), 0)
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex2f(self.x, self.y)
        glEnd()


def create_explosion(x, y):
    for _ in range(50):
        particles.append(Particle(x, y))


def update_particles():
    global particles
    for p in particles:
        p.update()
    particles = [p for p in particles if p.life > 0]


def draw_particles():
    for p in particles:
        p.draw()