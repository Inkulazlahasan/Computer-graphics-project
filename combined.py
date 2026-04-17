"""
Fractal Universe Combiner
=========================
Five-fractal explorer with configurable scene triggers.

This file imports your real scene modules:
    - black_hole.py
    - solar_system.py
    - spaceship.py
    - supernova.py

This file keeps everything in the same window:
the fractal is the background, and imported scene modules render
in the same display. By default a triggered scene fills the window.

Edit `SCENE_TRIGGERS` yourself to choose the coordinate and zoom.
"""

import math
import os
import sys

import matplotlib.cm as cm
import numpy as np
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from numba import njit, prange


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

SCENE_IMPORT_ERRORS = {}

try:
    import black_hole
except Exception as exc:
    black_hole = None
    SCENE_IMPORT_ERRORS["black_hole"] = exc

try:
    import solar_system
except Exception as exc:
    solar_system = None
    SCENE_IMPORT_ERRORS["solar_system"] = exc

try:
    import spaceship
except Exception as exc:
    spaceship = None
    SCENE_IMPORT_ERRORS["spaceship"] = exc

try:
    import supernova
except Exception as exc:
    supernova = None
    SCENE_IMPORT_ERRORS["supernova"] = exc


LOG2 = math.log(2.0)


@njit(parallel=True, fastmath=True, cache=True)
def k_mandelbrot(W, H, xmin, xmax, ymin, ymax, max_iter):
    out = np.empty((H, W), dtype=np.float32)
    dx = (xmax - xmin) / W
    dy = (ymax - ymin) / H
    for j in prange(H):
        cy = ymin + j * dy
        for i in range(W):
            cx = xmin + i * dx
            zx = 0.0
            zy = 0.0
            n = 0
            while n < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 256.0:
                    break
                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                n += 1
            if n >= max_iter:
                out[j, i] = -1.0
            else:
                mag = math.sqrt(zx * zx + zy * zy)
                nu = math.log(math.log(mag) / LOG2) / LOG2
                out[j, i] = n + 1.0 - nu
    return out


@njit(parallel=True, fastmath=True, cache=True)
def k_julia(W, H, xmin, xmax, ymin, ymax, max_iter, cre, cim):
    out = np.empty((H, W), dtype=np.float32)
    dx = (xmax - xmin) / W
    dy = (ymax - ymin) / H
    for j in prange(H):
        zy0 = ymin + j * dy
        for i in range(W):
            zx = xmin + i * dx
            zy = zy0
            n = 0
            while n < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 256.0:
                    break
                zy = 2.0 * zx * zy + cim
                zx = zx2 - zy2 + cre
                n += 1
            if n >= max_iter:
                out[j, i] = -1.0
            else:
                mag = math.sqrt(zx * zx + zy * zy)
                nu = math.log(math.log(mag) / LOG2) / LOG2
                out[j, i] = n + 1.0 - nu
    return out


@njit(parallel=True, fastmath=True, cache=True)
def k_burning_ship(W, H, xmin, xmax, ymin, ymax, max_iter):
    out = np.empty((H, W), dtype=np.float32)
    dx = (xmax - xmin) / W
    dy = (ymax - ymin) / H
    for j in prange(H):
        cy = -(ymin + j * dy)
        for i in range(W):
            cx = xmin + i * dx
            zx = 0.0
            zy = 0.0
            n = 0
            while n < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 256.0:
                    break
                zy = 2.0 * abs(zx * zy) + cy
                zx = zx2 - zy2 + cx
                n += 1
            if n >= max_iter:
                out[j, i] = -1.0
            else:
                mag = math.sqrt(zx * zx + zy * zy)
                nu = math.log(math.log(mag) / LOG2) / LOG2
                out[j, i] = n + 1.0 - nu
    return out


@njit(parallel=True, fastmath=True, cache=True)
def k_tricorn(W, H, xmin, xmax, ymin, ymax, max_iter):
    out = np.empty((H, W), dtype=np.float32)
    dx = (xmax - xmin) / W
    dy = (ymax - ymin) / H
    for j in prange(H):
        cy = ymin + j * dy
        for i in range(W):
            cx = xmin + i * dx
            zx = 0.0
            zy = 0.0
            n = 0
            while n < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 256.0:
                    break
                zy = -2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                n += 1
            if n >= max_iter:
                out[j, i] = -1.0
            else:
                mag = math.sqrt(zx * zx + zy * zy)
                nu = math.log(math.log(mag) / LOG2) / LOG2
                out[j, i] = n + 1.0 - nu
    return out


@njit(parallel=True, fastmath=True, cache=True)
def k_newton(W, H, xmin, xmax, ymin, ymax, max_iter):
    out = np.empty((H, W), dtype=np.float32)
    dx = (xmax - xmin) / W
    dy = (ymax - ymin) / H
    r0x, r0y = 1.0, 0.0
    r1x, r1y = -0.5, 0.8660254037844386
    r2x, r2y = -0.5, -0.8660254037844386
    tol = 1e-6
    for j in prange(H):
        zy0 = ymin + j * dy
        for i in range(W):
            zx = xmin + i * dx
            zy = zy0
            n = 0
            root = -1
            while n < max_iter:
                zx2 = zx * zx - zy * zy
                zy2 = 2.0 * zx * zy
                fx = zx2 * zx - zy2 * zy - 1.0
                fy = zx2 * zy + zy2 * zx
                dfx = 3.0 * (zx * zx - zy * zy)
                dfy = 6.0 * zx * zy
                denom = dfx * dfx + dfy * dfy
                if denom == 0.0:
                    break
                zx -= (fx * dfx + fy * dfy) / denom
                zy -= (fy * dfx - fx * dfy) / denom
                d0 = (zx - r0x) ** 2 + (zy - r0y) ** 2
                d1 = (zx - r1x) ** 2 + (zy - r1y) ** 2
                d2 = (zx - r2x) ** 2 + (zy - r2y) ** 2
                if d0 < tol:
                    root = 0
                    break
                if d1 < tol:
                    root = 1
                    break
                if d2 < tol:
                    root = 2
                    break
                n += 1
            if root < 0:
                out[j, i] = -1.0
            else:
                out[j, i] = root * 64.0 + min(n, 63)
    return out


@njit(parallel=True, fastmath=True, cache=True)
def colorize(values, lut, vmax):
    H, W = values.shape
    n_lut = lut.shape[0]
    out = np.empty((H, W, 3), dtype=np.uint8)
    for j in prange(H):
        for i in range(W):
            v = values[j, i]
            if v < 0.0:
                out[j, i, 0] = 0
                out[j, i, 1] = 0
                out[j, i, 2] = 0
            else:
                t = math.sqrt(v / vmax) if vmax > 0 else 0.0
                if t < 0.0:
                    t = 0.0
                if t > 1.0:
                    t = 1.0
                idx = int(t * (n_lut - 1))
                out[j, i, 0] = lut[idx, 0]
                out[j, i, 1] = lut[idx, 1]
                out[j, i, 2] = lut[idx, 2]
    return out


def make_lut(name, n=512):
    cmap = cm.get_cmap(name)
    arr = (cmap(np.linspace(0.0, 1.0, n))[:, :3] * 255).astype(np.uint8)
    return arr


FRACTALS = [
    ("Mandelbrot", "mandelbrot", k_mandelbrot, (-2.5, 1.0, -1.25, 1.25)),
    ("Julia", "julia", k_julia, (-1.6, 1.6, -1.2, 1.2)),
    ("Burning Ship", "burning_ship", k_burning_ship, (-2.0, 1.5, -2.0, 1.0)),
    ("Tricorn", "tricorn", k_tricorn, (-2.0, 2.0, -2.0, 2.0)),
    ("Newton z^3-1", "newton", k_newton, (-2.0, 2.0, -2.0, 2.0)),
]

CMAP_NAMES = [
    "twilight_shifted",
    "inferno",
    "magma",
    "plasma",
    "viridis",
    "turbo",
]

SCENE_LIBRARY = {
    "black_hole": {
        "label": "Black Hole",
        "module": black_hole,
        "script_name": "black_hole.py",
        "color": (255, 120, 60),
    },
    "solar_system": {
        "label": "Solar System",
        "module": solar_system,
        "script_name": "solar_system.py",
        "color": (255, 220, 110),
    },
    "spaceship": {
        "label": "Spaceship",
        "module": spaceship,
        "script_name": "spaceship.py",
        "color": (120, 220, 255),
    },
    "supernova": {
        "label": "Supernova",
        "module": supernova,
        "script_name": "supernova.py",
        "color": (190, 150, 255),
    },
}

# Edit these entries to place each scene at your chosen coordinates and zoom.
SCENE_TRIGGERS = [
    {
        "label": "Black Hole",
        "scene": "black_hole",
        "fractal": "mandelbrot",
        "enabled": True,
        "display_mode": "fullscreen",
        "anchor_mode": "center",
        "target": (-0.559264210703, -0.643893785194),
        "zoom": 3.201281e+05,
        "position_tolerance_px": 90,
        "sticky_position_tolerance_px": 140,
        "zoom_ratio_tolerance": 2.5,
        "sticky_zoom_ratio_tolerance": 4.5,
        "auto_launch": True,
    },
    {
        "label": "Solar System",
        "scene": "solar_system",
        "fractal": "mandelbrot",
        "enabled": True,
        "display_mode": "fullscreen",
        "anchor_mode": "center",
        "target": (-0.298145369573,  0.657346742247),
        "zoom": 3.766213e5,
        "position_tolerance_px": 90,
        "sticky_position_tolerance_px": 140,
        "zoom_ratio_tolerance": 3.0,
        "sticky_zoom_ratio_tolerance": 4.0,
        "auto_launch": True,
    },
    {
        "label": "Spaceship",
        "scene": "spaceship",
        "fractal": "julia",
        "enabled": True,
        "display_mode": "fullscreen",
        "anchor_mode": "center",
        "target": (0.468815534549, -0.480299920155),
        "zoom": 7.891276e5,
        "position_tolerance_px": 90,
        "sticky_position_tolerance_px": 140,
        "zoom_ratio_tolerance": 3.0,
        "sticky_zoom_ratio_tolerance": 4.0,
        "auto_launch": True,
    },
    {
        "label": "Supernova",
        "scene": "supernova",
        "fractal": "julia",
        "enabled": True,
        "display_mode": "fullscreen",
        "anchor_mode": "center",
        "target": (-0.331700930140, -0.204996062524),
        "zoom": 4.715623e6,
        "position_tolerance_px": 90,
        "sticky_position_tolerance_px": 140,
        "zoom_ratio_tolerance": 3.0,
        "sticky_zoom_ratio_tolerance": 4.0,
        "auto_launch": True,
    },
]


def clamp(v, a, b):
    return max(a, min(b, v))


def pixel_to_world(mx, my, xmin, xmax, ymin, ymax, width, height):
    wx = xmin + (mx / width) * (xmax - xmin)
    wy = ymin + (my / height) * (ymax - ymin)
    return wx, wy


def world_to_pixel(wx, wy, xmin, xmax, ymin, ymax, width, height):
    if xmax == xmin or ymax == ymin:
        return None
    px = int(round((wx - xmin) / (xmax - xmin) * width))
    py = int(round((wy - ymin) / (ymax - ymin) * height))
    return px, py


def current_zoom(xmin, xmax):
    return 3.5 / max(xmax - xmin, 1e-300)


def format_complex(z):
    return f"({z[0]: .12f}, {z[1]: .12f})"


def get_scene_color(scene_key):
    return SCENE_LIBRARY.get(scene_key, {}).get("color", (255, 255, 255))


def get_scene_module(scene_key):
    return SCENE_LIBRARY.get(scene_key, {}).get("module")


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_trigger_configured(trigger):
    if not trigger.get("enabled", False):
        return False
    target = trigger.get("target")
    zoom = trigger.get("zoom")
    if not isinstance(target, (list, tuple)) or len(target) != 2:
        return False
    if not is_number(target[0]) or not is_number(target[1]):
        return False
    if not is_number(zoom) or zoom <= 0:
        return False
    return True


def count_configured_triggers():
    return sum(1 for trigger in SCENE_TRIGGERS if is_trigger_configured(trigger))


def create_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return texture


def upload_surface_texture(texture, surface, fmt):
    width, height = surface.get_size()
    # Keep the surface in normal top-left screen orientation so the
    # fractal, HUD text, markers, and mouse coordinates all line up.
    pixels = pygame.image.tostring(surface, fmt, False)
    gl_format = GL_RGBA if fmt == "RGBA" else GL_RGB
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        gl_format,
        width,
        height,
        0,
        gl_format,
        GL_UNSIGNED_BYTE,
        pixels,
    )


def begin_2d(width, height):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()


def end_2d():
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()


def draw_texture_fullscreen(texture, width, height, alpha=1.0):
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 1.0, 1.0, alpha)
    begin_2d(width, height)
    glBindTexture(GL_TEXTURE_2D, texture)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0, 0)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(width, 0)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(width, height)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(0, height)
    glEnd()
    end_2d()
    glDisable(GL_TEXTURE_2D)


def set_ortho_projection(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = width / float(height if height != 0 else 1)
    if aspect >= 1.0:
        glOrtho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0)
    else:
        glOrtho(-1.0, 1.0, -1.0 / aspect, 1.0 / aspect, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def set_perspective_projection(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width / float(height if height != 0 else 1), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def compute_portal_rect(trigger, xmin, xmax, ymin, ymax, width, height):
    if trigger.get("display_mode", "fullscreen") != "portal":
        return pygame.Rect(0, 0, width, height)

    size = int(trigger.get("portal_size_px", 260))
    size = max(140, min(size, min(width, height) - 20))
    marker = world_to_pixel(trigger["target"][0], trigger["target"][1], xmin, xmax, ymin, ymax, width, height)
    if marker is None:
        return None
    center_x, center_y = marker
    left = max(10, min(center_x - size // 2, width - size - 10))
    top = max(10, min(center_y - size // 2, height - size - 10))
    return pygame.Rect(left, top, size, size)


def ensure_scene_initialized(scene_key, scene_runtime):
    state = scene_runtime[scene_key]
    if state["initialized"]:
        return True

    module = get_scene_module(scene_key)
    if module is None:
        error = SCENE_IMPORT_ERRORS.get(scene_key)
        state["last_error"] = str(error) if error is not None else "module import failed"
        return False

    try:
        if scene_key == "black_hole":
            black_hole.init()
        elif scene_key == "spaceship":
            spaceship.init()
        elif scene_key == "supernova":
            supernova.init()
        elif scene_key == "solar_system":
            glEnable(GL_DEPTH_TEST)
            glShadeModel(GL_SMOOTH)
            solar_system.setup_lighting()
        state["initialized"] = True
        state["last_error"] = None
        return True
    except Exception as exc:
        state["last_error"] = str(exc)
        return False


def render_black_hole_inline(dt, width, height):
    black_hole.time_value += dt
    black_hole.disk_rotation += 0.18 * (dt / 0.016)
    black_hole.update_particles()
    black_hole.planet_angle += 0.01 * (dt / 0.016)
    black_hole.planet_radius -= 0.00025 * (dt / 0.016)
    if black_hole.planet_radius < 0.34:
        black_hole.planet_radius = 0.62
        black_hole.planet_angle = black_hole.random.uniform(0, 2 * math.pi)

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(2)
    set_ortho_projection(width, height)
    black_hole.draw_background()
    black_hole.draw_nebula()
    black_hole.draw_stars()
    black_hole.draw_outer_glow()
    black_hole.draw_disk()
    black_hole.draw_chunk_trail_layer_first()
    black_hole.draw_particle_trail_layer_first()
    black_hole.draw_lensing()
    black_hole.draw_photon_ring()
    black_hole.draw_chunks()
    black_hole.draw_particles()
    black_hole.draw_event_horizon()
    black_hole.draw_small_planet()


def render_spaceship_inline(dt, width, height):
    spaceship.time_value += dt
    spaceship.update_particles()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    set_ortho_projection(width, height)
    spaceship.draw_background()
    spaceship.draw_stars()
    ship_x = 0.48 * math.sin(spaceship.time_value * 0.45)
    ship_y = 0.18 + 0.08 * math.sin(spaceship.time_value * 0.9)
    spaceship.draw_ufo(ship_x, ship_y)


def render_supernova_inline(dt, width, height):
    supernova.time_value += dt
    supernova.update_supernova()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    set_ortho_projection(width, height)
    supernova.draw_background()
    supernova.draw_stars()
    supernova.draw_nebula_glow()
    supernova.draw_beams()
    supernova.draw_bipolar_shells()
    supernova.draw_rings()
    supernova.draw_particles()
    supernova.draw_core()


def render_solar_system_inline(dt, width, height):
    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    set_perspective_projection(width, height)
    glTranslatef(0.0, 0.0, solar_system.cam_zoom)
    glRotatef(solar_system.cam_rot_x, 1.0, 0.0, 0.0)
    glRotatef(solar_system.cam_rot_y, 0.0, 1.0, 0.0)
    solar_system.draw_scene(dt)


def render_scene_portal(trigger, scene_runtime, portal_rect, dt, full_width, full_height):
    scene_key = trigger["scene"]
    if not ensure_scene_initialized(scene_key, scene_runtime):
        return "import-failed"

    gl_x = int(portal_rect.x)
    gl_y = int(full_height - portal_rect.y - portal_rect.height)
    gl_w = int(portal_rect.width)
    gl_h = int(portal_rect.height)

    glEnable(GL_SCISSOR_TEST)
    glScissor(gl_x, gl_y, gl_w, gl_h)
    glViewport(gl_x, gl_y, gl_w, gl_h)
    glClear(GL_DEPTH_BUFFER_BIT)

    try:
        if scene_key == "black_hole":
            render_black_hole_inline(dt, gl_w, gl_h)
        elif scene_key == "solar_system":
            render_solar_system_inline(dt, gl_w, gl_h)
        elif scene_key == "spaceship":
            render_spaceship_inline(dt, gl_w, gl_h)
        elif scene_key == "supernova":
            render_supernova_inline(dt, gl_w, gl_h)
        status = "inline"
    except Exception as exc:
        scene_runtime[scene_key]["last_error"] = str(exc)
        status = "render-failed"

    glDisable(GL_SCISSOR_TEST)
    glViewport(0, 0, full_width, full_height)
    return status


def scene_import_status_lines():
    lines = []
    for scene_key, scene_info in SCENE_LIBRARY.items():
        module = scene_info["module"]
        if module is None:
            error = SCENE_IMPORT_ERRORS.get(scene_key)
            lines.append(f'- {scene_info["label"]}: import failed ({error})')
        else:
            lines.append(f'- {scene_info["label"]}: imported {os.path.basename(module.__file__)}')
    return lines


def evaluate_trigger(trigger, mouse_px, center_px, zoom, xmin, xmax, ymin, ymax, width, height, sticky=False):
    target_px = world_to_pixel(trigger["target"][0], trigger["target"][1], xmin, xmax, ymin, ymax, width, height)
    if target_px is None:
        return 0.0

    if trigger.get("anchor_mode", "mouse") == "center":
        anchor_px = center_px
    else:
        anchor_px = mouse_px

    tol_key = "sticky_position_tolerance_px" if sticky else "position_tolerance_px"
    tol_px = max(trigger.get(tol_key, trigger.get("position_tolerance_px", 90)), 1)
    distance_px = math.hypot(anchor_px[0] - target_px[0], anchor_px[1] - target_px[1])
    position_score = 1.0 - distance_px / tol_px

    zoom_target = max(trigger.get("zoom", 1.0), 1e-15)
    zoom_key = "sticky_zoom_ratio_tolerance" if sticky else "zoom_ratio_tolerance"
    zoom_ratio_tol = max(trigger.get(zoom_key, trigger.get("zoom_ratio_tolerance", 3.0)), 1.01)
    zoom_span = math.log(zoom_ratio_tol)
    zoom_distance = abs(math.log(max(zoom, 1e-15) / zoom_target))
    zoom_score = 1.0 - zoom_distance / zoom_span if zoom_span > 0 else 0.0

    return clamp(min(position_score, zoom_score), 0.0, 1.0)


def find_active_trigger(fractal_key, mouse_px, center_px, zoom, xmin, xmax, ymin, ymax, width, height, previous_trigger=None):
    best_trigger = None
    best_score = 0.0
    for trigger in SCENE_TRIGGERS:
        if trigger["fractal"] != fractal_key:
            continue
        if not is_trigger_configured(trigger):
            continue
        sticky = trigger is previous_trigger
        score = evaluate_trigger(trigger, mouse_px, center_px, zoom, xmin, xmax, ymin, ymax, width, height, sticky=sticky)
        if score > best_score:
            best_trigger = trigger
            best_score = score
    return best_trigger, best_score


def print_snapshot(fractal_name, fractal_key, mouse_px, mouse_world, center_world, zoom, trigger=None):
    print()
    print("=== Fractal Universe Snapshot ===")
    print(f"Fractal: {fractal_name} ({fractal_key})")
    print(f"Mouse px: {mouse_px}")
    print(f"Mouse world: {format_complex(mouse_world)}")
    print(f"View center: {format_complex(center_world)}")
    print(f"Zoom: {zoom:.6e}x")
    if trigger is not None:
        print(f'Current trigger match: {trigger["label"]}')
    print("Paste these lines into the scene entry you want:")
    print('    "enabled": True,')
    print(f'    "fractal": "{fractal_key}",')
    print('    "anchor_mode": "mouse",')
    print(f'    "target": ({mouse_world[0]:.12f}, {mouse_world[1]:.12f}),')
    print(f'    "zoom": {zoom:.6e},')
    print('    "position_tolerance_px": 90,')
    print('    "sticky_position_tolerance_px": 140,')
    print('    "zoom_ratio_tolerance": 3.0,')
    print('    "sticky_zoom_ratio_tolerance": 4.0,')


def draw_trigger_markers(screen, font, fractal_key, xmin, xmax, ymin, ymax):
    width, height = screen.get_size()
    for trigger in SCENE_TRIGGERS:
        if trigger["fractal"] != fractal_key:
            continue
        if not is_trigger_configured(trigger):
            continue
        marker = world_to_pixel(trigger["target"][0], trigger["target"][1], xmin, xmax, ymin, ymax, width, height)
        if marker is None:
            continue
        mx, my = marker
        if mx < -30 or mx > width + 30 or my < -30 or my > height + 30:
            continue
        color = get_scene_color(trigger["scene"])
        pygame.draw.circle(screen, color, (mx, my), 3)
        pygame.draw.circle(screen, color, (mx, my), 10, 2)
        pygame.draw.line(screen, color, (mx - 14, my), (mx - 6, my), 1)
        pygame.draw.line(screen, color, (mx + 6, my), (mx + 14, my), 1)
        pygame.draw.line(screen, color, (mx, my - 14), (mx, my - 6), 1)
        pygame.draw.line(screen, color, (mx, my + 6), (mx, my + 14), 1)
        label = font.render(trigger["label"], True, color)
        screen.blit(label, (mx + 12, my - 12))


def draw_portal_frame(screen, portal_rect, trigger):
    if trigger.get("display_mode", "fullscreen") != "portal":
        return

    color = get_scene_color(trigger["scene"])
    shadow_rect = portal_rect.inflate(8, 8)
    pygame.draw.rect(screen, (0, 0, 0, 90), shadow_rect, border_radius=12)
    pygame.draw.rect(screen, (*color, 210), portal_rect, 3, border_radius=10)
    inner_rect = portal_rect.inflate(-10, -10)
    pygame.draw.rect(screen, (*color, 80), inner_rect, 1, border_radius=8)


def draw_mouse_crosshair(screen, mouse_px):
    mx, my = mouse_px
    color = (255, 255, 255)
    pygame.draw.circle(screen, color, (mx, my), 10, 1)
    pygame.draw.line(screen, color, (mx - 16, my), (mx - 4, my), 1)
    pygame.draw.line(screen, color, (mx + 4, my), (mx + 16, my), 1)
    pygame.draw.line(screen, color, (mx, my - 16), (mx, my - 4), 1)
    pygame.draw.line(screen, color, (mx, my + 4), (mx, my + 16), 1)


def blit_hud_lines(screen, font, lines):
    for idx, line in enumerate(lines):
        shadow = font.render(line, True, (0, 0, 0))
        text = font.render(line, True, (255, 255, 255))
        y = 10 + idx * 18
        screen.blit(shadow, (11, y + 1))
        screen.blit(text, (10, y))


def save_opengl_screenshot(width, height, filename):
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    shot = pygame.image.fromstring(pixels, (width, height), "RGB", True)
    pygame.image.save(shot, filename)


def run():
    pygame.init()
    pygame.display.set_caption("Fractal Universe (Mandelbrot + Julia)")

    width, height = 960, 700
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,monospace", 15)
    small_font = pygame.font.SysFont("consolas,monospace", 13)
    fractal_texture = create_texture()
    overlay_texture = create_texture()

    fractal_idx = 0
    cmap_idx = 0
    luts = [make_lut(name) for name in CMAP_NAMES]
    max_iter = 220
    julia_c = [-0.7, 0.27015]
    show_hud = True
    last_scene_label = None
    previous_active_trigger = None
    scene_runtime = {
        scene_key: {"initialized": False, "last_error": None}
        for scene_key in SCENE_LIBRARY
    }
    pending_screenshot = None
    dt = 1.0 / 60.0

    glViewport(0, 0, width, height)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def reset_view():
        nonlocal xmin, xmax, ymin, ymax
        _, _, _, init_view = FRACTALS[fractal_idx]
        xmin, xmax, y0, y1 = init_view
        cy = (y0 + y1) / 2.0
        half_h = (xmax - xmin) * height / width / 2.0
        ymin, ymax = cy - half_h, cy + half_h

    _, _, _, init_view = FRACTALS[fractal_idx]
    xmin, xmax, y0, y1 = init_view
    cy = (y0 + y1) / 2.0
    half_h = (xmax - xmin) * height / width / 2.0
    ymin, ymax = cy - half_h, cy + half_h

    dragging = False
    drag_anchor = None

    print("Compiling fractal kernels (first run only)...")
    for _, _, kernel, _ in FRACTALS:
        if kernel is k_julia:
            kernel(32, 32, -1.0, 1.0, -1.0, 1.0, 30, julia_c[0], julia_c[1])
        else:
            kernel(32, 32, -1.0, 1.0, -1.0, 1.0, 30)
    colorize(np.zeros((4, 4), dtype=np.float32), luts[0], 1.0)
    print("Ready.")
    print("Scene module status:")
    for line in scene_import_status_lines():
        print(line)
    print("Scenes now render inside the fractal window.")
    print("Press P to print the current mouse world-point and zoom.")
    print("Then paste those values into SCENE_TRIGGERS.")

    while True:
        dt = clock.tick(120) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_r:
                    reset_view()
                elif event.key == pygame.K_c:
                    cmap_idx = (cmap_idx + 1) % len(CMAP_NAMES)
                elif event.key == pygame.K_h:
                    show_hud = not show_hud
                elif event.key == pygame.K_UP:
                    max_iter = min(4000, int(max_iter * 1.25) + 1)
                elif event.key == pygame.K_DOWN:
                    max_iter = max(30, int(max_iter / 1.25))
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                    fractal_idx = event.key - pygame.K_1
                    reset_view()
                    last_scene_label = None
                elif event.key == pygame.K_s:
                    fractal_name = FRACTALS[fractal_idx][0].replace(" ", "_")
                    pending_screenshot = f"combined_{fractal_name}.png"
                elif event.key == pygame.K_p:
                    mx, my = pygame.mouse.get_pos()
                    mouse_world = pixel_to_world(mx, my, xmin, xmax, ymin, ymax, width, height)
                    center_world = ((xmin + xmax) * 0.5, (ymin + ymax) * 0.5)
                    fractal_name, fractal_key, _, _ = FRACTALS[fractal_idx]
                    zoom = current_zoom(xmin, xmax)
                    trigger, _ = find_active_trigger(
                        fractal_key,
                        (mx, my),
                        (width // 2, height // 2),
                        zoom,
                        xmin,
                        xmax,
                        ymin,
                        ymax,
                        width,
                        height,
                        previous_active_trigger,
                    )
                    print_snapshot(fractal_name, fractal_key, (mx, my), mouse_world, center_world, zoom, trigger)

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                cx, cy = pixel_to_world(mx, my, xmin, xmax, ymin, ymax, width, height)
                factor = 0.85 if event.y > 0 else 1.0 / 0.85
                xmin = cx + (xmin - cx) * factor
                xmax = cx + (xmax - cx) * factor
                ymin = cy + (ymin - cy) * factor
                ymax = cy + (ymax - cy) * factor

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                drag_anchor = (event.pos[0], event.pos[1], xmin, xmax, ymin, ymax)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                ax_mx, ax_my, ax_xmin, ax_xmax, ax_ymin, ax_ymax = drag_anchor
                dxd = (mx - ax_mx) / width * (ax_xmax - ax_xmin)
                dyd = (my - ax_my) / height * (ax_ymax - ax_ymin)
                xmin = ax_xmin - dxd
                xmax = ax_xmax - dxd
                ymin = ax_ymin - dyd
                ymax = ax_ymax - dyd

        fractal_name, fractal_key, kernel, _ = FRACTALS[fractal_idx]
        if kernel is k_julia:
            data = kernel(width, height, xmin, xmax, ymin, ymax, max_iter, julia_c[0], julia_c[1])
        else:
            data = kernel(width, height, xmin, xmax, ymin, ymax, max_iter)

        rgb = colorize(data, luts[cmap_idx], float(max_iter))
        fractal_surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))

        mouse_px = pygame.mouse.get_pos()
        mouse_world = pixel_to_world(mouse_px[0], mouse_px[1], xmin, xmax, ymin, ymax, width, height)
        center_world = ((xmin + xmax) * 0.5, (ymin + ymax) * 0.5)
        zoom = current_zoom(xmin, xmax)

        active_trigger, scene_strength = find_active_trigger(
            fractal_key,
            mouse_px,
            (width // 2, height // 2),
            zoom,
            xmin,
            xmax,
            ymin,
            ymax,
            width,
            height,
            previous_active_trigger,
        )

        render_status = "idle"
        active_file = "-"
        portal_rect = None
        if active_trigger is not None:
            active_file = SCENE_LIBRARY[active_trigger["scene"]]["script_name"]
            portal_rect = compute_portal_rect(active_trigger, xmin, xmax, ymin, ymax, width, height)
            if active_trigger["label"] != last_scene_label:
                print(
                    f'Trigger matched {active_trigger["label"]}: '
                    f'mouse={format_complex(mouse_world)} zoom={zoom:.6e}x'
                )
                last_scene_label = active_trigger["label"]
            previous_active_trigger = active_trigger
        else:
            last_scene_label = None
            previous_active_trigger = None

        overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if portal_rect is not None:
            draw_portal_frame(overlay_surface, portal_rect, active_trigger)
        draw_trigger_markers(overlay_surface, small_font, fractal_key, xmin, xmax, ymin, ymax)
        draw_mouse_crosshair(overlay_surface, mouse_px)

        if show_hud:
            configured_count = count_configured_triggers()
            if active_trigger is None:
                scene_line = f"Scene trigger: none   configured={configured_count}/{len(SCENE_TRIGGERS)}"
                target_line = "Set target+zoom in SCENE_TRIGGERS, then use P to capture values"
                file_line = "Scene source: -"
            else:
                scene_line = (
                    f'Scene trigger: {active_trigger["label"]} '
                    f'score={scene_strength:.2f} render=pending'
                )
                target_line = (
                    f'Target: {format_complex(active_trigger["target"])} '
                    f'@ {active_trigger["zoom"]:.2e}x'
                )
                file_line = f"Scene source: {active_file}"

            lines = [
                f"FPS: {clock.get_fps():5.1f}    {width}x{height}",
                f"Fractal: {fractal_name}   [1-5]",
                f"Iterations: {max_iter}   [Up/Dn]",
                f"Colormap: {CMAP_NAMES[cmap_idx]}   [C]",
                f"Zoom: {zoom:.6e}x",
                f"Mouse px: ({mouse_px[0]}, {mouse_px[1]})",
                f"Mouse world: {format_complex(mouse_world)}",
                f"View center: {format_complex(center_world)}",
                scene_line,
                target_line,
                file_line,
                "Wheel zoom   Drag pan   P print point+zoom   R reset   S save   H hide",
            ]
            blit_hud_lines(overlay_surface, font, lines)

        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        upload_surface_texture(fractal_texture, fractal_surface, "RGB")
        draw_texture_fullscreen(fractal_texture, width, height)

        if active_trigger is not None and portal_rect is not None:
            render_status = render_scene_portal(active_trigger, scene_runtime, portal_rect, dt, width, height)
        elif active_trigger is not None:
            render_status = "offscreen"

        if show_hud and active_trigger is not None:
            lines = [
                f"FPS: {clock.get_fps():5.1f}    {width}x{height}",
                f"Fractal: {fractal_name}   [1-5]",
                f"Iterations: {max_iter}   [Up/Dn]",
                f"Colormap: {CMAP_NAMES[cmap_idx]}   [C]",
                f"Zoom: {zoom:.6e}x",
                f"Mouse px: ({mouse_px[0]}, {mouse_px[1]})",
                f"Mouse world: {format_complex(mouse_world)}",
                f"View center: {format_complex(center_world)}",
                f'Scene trigger: {active_trigger["label"]} score={scene_strength:.2f} render={render_status}',
                f'Target: {format_complex(active_trigger["target"])} @ {active_trigger["zoom"]:.2e}x',
                f"Scene source: {active_file}",
                "Wheel zoom   Drag pan   P print point+zoom   R reset   S save   H hide",
            ]
            overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            if portal_rect is not None:
                draw_portal_frame(overlay_surface, portal_rect, active_trigger)
            draw_trigger_markers(overlay_surface, small_font, fractal_key, xmin, xmax, ymin, ymax)
            draw_mouse_crosshair(overlay_surface, mouse_px)
            blit_hud_lines(overlay_surface, font, lines)

        upload_surface_texture(overlay_texture, overlay_surface, "RGBA")
        draw_texture_fullscreen(overlay_texture, width, height)

        if pending_screenshot is not None:
            save_opengl_screenshot(width, height, pending_screenshot)
            print(f"Saved {os.path.abspath(pending_screenshot)}")
            pending_screenshot = None

        pygame.display.flip()


if __name__ == "__main__":
    run()
