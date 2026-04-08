import glfw
import pymunk
import random
from OpenGL.GL import *
from OpenGL.GLU import *

from stickman import Stickman
from renderer import draw_grid, draw_circle, draw_line, draw_background
from effects import create_explosion, update_particles, draw_particles
from animation import AnimationSystem

WIDTH, HEIGHT = 1280, 720

# -----------------------------
# Physics Setup
# -----------------------------
space = pymunk.Space()
space.gravity = (0, -900)

floor = pymunk.Segment(space.static_body, (-WIDTH/2, -300), (WIDTH/2, -300), 5)
floor.elasticity = 0.6
space.add(floor)

phys_circles = []

mouse_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
mouse_joint = None

# Mode: 0 = physics, 1 = animation
mode = 1

# -----------------------------
# Create Physics Circle
# -----------------------------
def create_circle(x, y):
    mass = 1
    radius = random.randint(15, 30)

    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (x, y)

    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.8
    shape.friction = 0.5

    color = (random.random(), random.random(), random.random())

    space.add(body, shape)
    phys_circles.append((shape, color))


# -----------------------------
# Mouse Position
# -----------------------------
def get_mouse_world(window):
    mx, my = glfw.get_cursor_pos(window)
    return mx - WIDTH/2, (HEIGHT/2) - my


# -----------------------------
# Mouse Input
# -----------------------------
def mouse_button_callback(window, button, action, mods):
    global mouse_joint

    mx, my = get_mouse_world(window)

    if mode == 0:  # only physics mode interaction
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                for shape, _ in phys_circles:
                    if shape.point_query((mx, my)).distance <= 0:
                        mouse_body.position = (mx, my)
                        mouse_joint = pymunk.PivotJoint(mouse_body, shape.body, (0,0), (0,0))
                        mouse_joint.max_force = 50000
                        space.add(mouse_joint)
                        return

                create_circle(mx, my)

            elif action == glfw.RELEASE:
                if mouse_joint:
                    space.remove(mouse_joint)
                    mouse_joint = None

        # Right click = explosion
        if button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
            create_explosion(mx, my)

            for shape, _ in phys_circles:
                dx = shape.body.position.x - mx
                dy = shape.body.position.y - my
                dist = (dx**2 + dy**2) ** 0.5

                if dist < 200:
                    force = 90000 / (dist + 1)
                    shape.body.apply_impulse_at_local_point((dx * force, dy * force))


# -----------------------------
# Keyboard Input
# -----------------------------
def key_callback(window, key, scancode, action, mods):
    global mode

    if action == glfw.PRESS:

        if key == glfw.KEY_TAB:
            mode = 1 - mode   # 🔥 SWITCH MODES

        if key == glfw.KEY_R:
            for shape, _ in phys_circles:
                space.remove(shape, shape.body)
            phys_circles.clear()

        if key == glfw.KEY_SPACE:
            for _ in range(10):
                create_circle(random.randint(-200, 200), random.randint(0, 300))


# -----------------------------
# MAIN
# -----------------------------
def main():
    if not glfw.init():
        return

    window = glfw.create_window(WIDTH, HEIGHT, "Final CG Project", None, None)
    glfw.make_context_current(window)

    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_key_callback(window, key_callback)

    glMatrixMode(GL_PROJECTION)
    gluOrtho2D(-WIDTH/2, WIDTH/2, -HEIGHT/2, HEIGHT/2)
    glMatrixMode(GL_MODELVIEW)

    glClearColor(0, 0, 0, 1)

    character = Stickman(0, 0)
    animation = AnimationSystem()

    dt = 1/60

    while not glfw.window_should_close(window):

        # =========================
        # TRAIL / CLEAR EFFECT
        # =========================
        if mode == 1:
            # Trail effect (animation mode)
            glColor4f(0, 0, 0, 0.08)
            glBegin(GL_QUADS)
            glVertex2f(-WIDTH, -HEIGHT)
            glVertex2f(WIDTH, -HEIGHT)
            glVertex2f(WIDTH, HEIGHT)
            glVertex2f(-WIDTH, HEIGHT)
            glEnd()
        else:
            # Full clear (physics mode)
            glClear(GL_COLOR_BUFFER_BIT)
            draw_background(WIDTH, HEIGHT)

        mx, my = get_mouse_world(window)

        # =========================
        # MODE SWITCH
        # =========================
        if mode == 0:
            # PHYSICS MODE
            space.step(dt)
            mouse_body.position = (mx, my)

            draw_grid(WIDTH, HEIGHT)

            glColor3f(0.6, 0.6, 0.6)
            draw_line(-WIDTH/2, -300, WIDTH/2, -300, 5)

            for shape, color in phys_circles:
                glColor3f(*color)
                pos = shape.body.position
                draw_circle(pos.x, pos.y, shape.radius, filled=True)

            update_particles()
            draw_particles()

            character.draw(mx, my)

        else:
            # ANIMATION MODE
            animation.update()
            animation.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()