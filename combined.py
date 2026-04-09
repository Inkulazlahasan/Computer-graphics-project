import math
import random
import sys
import time

import black_hole
import pygame
import solar_system
import spaceship
import supernova
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

WIDTH = 1280
HEIGHT = 720

VERTEX_SHADER = """
#version 120
void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

FRAGMENT_SHADER = """
#version 120

uniform vec2  u_resolution;
uniform float u_zoom;
uniform vec2  u_offset;
uniform float u_time;
uniform int   u_max_iter;
uniform float u_palette_seed;

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - u_resolution * 0.5) / min(u_resolution.x, u_resolution.y);
    uv /= u_zoom;
    uv += u_offset;

    vec2 z = vec2(0.0);
    vec2 c = uv;

    int iter = 0;
    float len2 = 0.0;

    for (int i = 0; i < 1024; i++) {
        if (i >= u_max_iter) break;
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        len2 = dot(z, z);
        if (len2 > 4.0) break;
        iter++;
    }

    if (iter == u_max_iter) {
        vec3 core = vec3(0.010, 0.013, 0.030);
        float haze = 0.025 * exp(-7.0 * dot(uv, uv));
        gl_FragColor = vec4(core + haze, 1.0);
    } else {
        float safe_len2 = max(len2, 1.000001);
        float smooth_iter = float(iter);
        if (iter > 0 && iter < u_max_iter) {
            smooth_iter = float(iter) - log2(log2(safe_len2)) + 4.0;
        }

        float t = smooth_iter / float(u_max_iter);
        float hue = fract(t * 1.35 + u_time * 0.025 + u_palette_seed);
        vec3 col = hsv2rgb(vec3(hue, 0.85, 1.0));
        col *= 0.90 + 0.10 * sin(u_time * 0.28 + t * 9.0 + u_palette_seed * 6.2831);

        gl_FragColor = vec4(col, 1.0);
    }
}
"""

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

stars = [
    (random.uniform(-220, 220), random.uniform(-220, 220), random.uniform(-220, 220))
    for _ in range(1800)
]

angles = {}
moon_angle = 0.0

cam_rot_x = 25.0
cam_rot_y = -20.0
cam_zoom = -65.0

fractal_prog = None
hud_tex = None
start_time = 0.0
font = None
title_font = None
small_font = None
tiny_font = None
DEFAULT_PALETTE_SEED = 0.0
palette_seed = DEFAULT_PALETTE_SEED
RANDOM_BUTTON_RECT = pygame.Rect(0, 0, 0, 0)

zoom = 1.0
offset_x = -0.5
offset_y = 0.0
max_iter = 320

PORTALS = [
    {"name": "Solar System", "point": (-0.655030428732103, 0.4169064792377491), "scene": "solar"},
    {"name": "Black Hole", "point": (0.18366980606447902, 0.5853828621610686), "scene": "black_hole"},
    {"name": "Spaceship", "point": (0.3707430686664573, 0.0916287245391974), "scene": "spaceship"},
    {"name": "Supernova", "point": (-0.3011318316732259, -0.6547660793655354), "scene": "supernova"},
]

current_point_index = -1
selected_x, selected_y = PORTALS[0]["point"]
TARGET_MARKER_MARGIN_NDC = 0.12
PORTAL_REVEAL_ZOOM = 250000.0
TARGET_RADIUS_X_PIXELS = 220.0
TARGET_RADIUS_Y_PIXELS = 220.0
pointer_enabled = False
game_over = False
overlay_visible = True
discovered_portals = set()
last_discovery = ""


def compile_shader(src, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, src)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        print(glGetShaderInfoLog(shader).decode())
        sys.exit(1)
    return shader


def build_program():
    vs = compile_shader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fs = compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    if not glGetProgramiv(prog, GL_LINK_STATUS):
        print(glGetProgramInfoLog(prog).decode())
        sys.exit(1)
    return prog


def set_2d():
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def draw_fullscreen_quad():
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -1.0)
    glVertex2f(1.0, -1.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(-1.0, 1.0)
    glEnd()


def draw_circle_2d(x, y, radius, segments=100, filled=False):
    mode = GL_TRIANGLE_FAN if filled else GL_LINE_LOOP
    glBegin(mode)
    if filled:
        glVertex2f(x, y)
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        glVertex2f(x + math.cos(a) * radius, y + math.sin(a) * radius)
    glEnd()


def screen_to_fractal(mx, my):
    scale = 1.0 / (zoom * min(WIDTH, HEIGHT))
    fx = (mx - WIDTH * 0.5) * scale + offset_x
    fy = (HEIGHT * 0.5 - my) * scale + offset_y
    return fx, fy


def fractal_to_screen(px, py):
    scale = min(WIDTH, HEIGHT)
    sx = ((px - offset_x) * zoom) * scale + WIDTH * 0.5
    sy = HEIGHT * 0.5 - ((py - offset_y) * zoom) * scale
    return sx, sy


def screen_to_ndc(sx, sy):
    nx = (sx / WIDTH) * 2.0 - 1.0
    ny = 1.0 - (sy / HEIGHT) * 2.0
    return nx, ny


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def draw_point_marker(px, py, is_selected):
    sx, sy = fractal_to_screen(px, py)
    nx, ny = screen_to_ndc(sx, sy)
    marker_x = clamp(nx, -1.0 + TARGET_MARKER_MARGIN_NDC, 1.0 - TARGET_MARKER_MARGIN_NDC)
    marker_y = clamp(ny, -1.0 + TARGET_MARKER_MARGIN_NDC, 1.0 - TARGET_MARKER_MARGIN_NDC)
    target_visible = marker_x == nx and marker_y == ny
    base_radius = 0.035 if is_selected else 0.025
    pulse = base_radius + 0.008 * math.sin(time.time() * 4.0)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    if is_selected:
        glow_color = (1.0, 1.0, 1.0, 0.18)
        main_color = (1.0, 0.95, 0.2, 1.0) if target_visible else (1.0, 0.45, 0.2, 1.0)
    else:
        glow_color = (0.55, 0.95, 1.0, 0.14)
        main_color = (0.45, 0.95, 1.0, 0.95) if target_visible else (0.4, 0.7, 1.0, 0.95)

    glColor4f(*glow_color)
    draw_circle_2d(marker_x, marker_y, pulse * 1.8, filled=True)

    glColor4f(*main_color)
    draw_circle_2d(marker_x, marker_y, pulse, filled=False)

    glBegin(GL_LINES)
    glVertex2f(marker_x - pulse * 1.8, marker_y)
    glVertex2f(marker_x + pulse * 1.8, marker_y)
    glVertex2f(marker_x, marker_y - pulse * 1.8)
    glVertex2f(marker_x, marker_y + pulse * 1.8)
    glEnd()

    if not target_visible:
        dir_x = nx - marker_x
        dir_y = ny - marker_y
        length = math.hypot(dir_x, dir_y)
        if length > 0.0:
            dir_x /= length
            dir_y /= length
            tail = pulse * 2.2
            head = pulse * 3.8

            glBegin(GL_LINES)
            glVertex2f(marker_x, marker_y)
            glVertex2f(marker_x + dir_x * tail, marker_y + dir_y * tail)
            glEnd()

            side_x = -dir_y
            side_y = dir_x
            tip_x = marker_x + dir_x * head
            tip_y = marker_y + dir_y * head
            wing = pulse * 0.8

            glBegin(GL_TRIANGLES)
            glVertex2f(tip_x, tip_y)
            glVertex2f(
                marker_x + dir_x * tail + side_x * wing,
                marker_y + dir_y * tail + side_y * wing,
            )
            glVertex2f(
                marker_x + dir_x * tail - side_x * wing,
                marker_y + dir_y * tail - side_y * wing,
            )
            glEnd()


def draw_target_markers():
    for index, portal in enumerate(PORTALS):
        px, py = portal["point"]
        draw_point_marker(px, py, index == current_point_index)

    glDisable(GL_BLEND)


def draw_fractal():
    glUseProgram(fractal_prog)
    glUniform2f(glGetUniformLocation(fractal_prog, "u_resolution"), float(WIDTH), float(HEIGHT))
    glUniform1f(glGetUniformLocation(fractal_prog, "u_zoom"), float(zoom))
    glUniform2f(glGetUniformLocation(fractal_prog, "u_offset"), float(offset_x), float(offset_y))
    glUniform1f(glGetUniformLocation(fractal_prog, "u_time"), float(time.time() - start_time))
    glUniform1i(glGetUniformLocation(fractal_prog, "u_max_iter"), int(max_iter))
    glUniform1f(glGetUniformLocation(fractal_prog, "u_palette_seed"), float(palette_seed))
    draw_fullscreen_quad()
    glUseProgram(0)


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


def draw_solar_system(dt):
    global moon_angle

    for p in PLANETS:
        if p["name"] != "Sun":
            angles[p["name"]] = (angles[p["name"]] + p["speed"] * 40.0 * dt) % 360.0

    moon_angle = (moon_angle + 140.0 * dt) % 360.0

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

def is_selected_point_allowed():
    tolerance = 0.002

    for portal in PORTALS:
        px, py = portal["point"]
        dx = selected_x - px
        dy = selected_y - py
        if math.sqrt(dx * dx + dy * dy) < tolerance:
            return True
    return False


def load_selected_point(index):
    global selected_x, selected_y, current_point_index
    global offset_x, offset_y, zoom

    if 0 <= index < len(PORTALS):
        selected_x, selected_y = PORTALS[index]["point"]
        current_point_index = index

        # Center the viewport on the selected point so the target is fully visible.
        offset_x = selected_x
        offset_y = selected_y
        zoom = 60.0

        print("Loaded point:", current_point_index, selected_x, selected_y)


def find_near_target_index():
    scale = zoom * min(WIDTH, HEIGHT)
    radius_x = TARGET_RADIUS_X_PIXELS / scale
    radius_y = TARGET_RADIUS_Y_PIXELS / scale

    nearest_index = -1
    nearest_dist2 = float("inf")

    for index, portal in enumerate(PORTALS):
        px, py = portal["point"]
        dx = offset_x - px
        dy = offset_y - py
        if abs(dx) <= radius_x and abs(dy) <= radius_y:
            dist2 = dx * dx + dy * dy
            if dist2 < nearest_dist2:
                nearest_dist2 = dist2
                nearest_index = index

    return nearest_index


def is_near_target():
    return find_near_target_index() != -1


def should_reveal_solar():
    return current_point_index != -1 and zoom >= PORTAL_REVEAL_ZOOM


def reset_all():
    global zoom, offset_x, offset_y, current_point_index
    global cam_rot_x, cam_rot_y, cam_zoom, moon_angle
    global pointer_enabled, game_over, last_discovery, palette_seed, overlay_visible

    zoom = 1.0
    offset_x = -0.5
    offset_y = 0.0
    current_point_index = -1
    pointer_enabled = False
    game_over = False
    overlay_visible = True
    last_discovery = ""
    palette_seed = DEFAULT_PALETTE_SEED
    discovered_portals.clear()

    cam_rot_x = 25.0
    cam_rot_y = -20.0
    cam_zoom = -65.0
    moon_angle = 0.0
    solar_system.cam_rot_x = 25.0
    solar_system.cam_rot_y = -20.0
    solar_system.cam_zoom = -65.0
    solar_system.sun_glow = 0.0
    solar_system.moon_angle = 0.0
    solar_system.angles = {p["name"]: random.uniform(0, 360) for p in solar_system.PLANETS}

    for p in PLANETS:
        angles[p["name"]] = random.uniform(0.0, 360.0)


def zoom_at(mx, my, zoom_factor):
    global zoom, offset_x, offset_y, current_point_index

    scale_before = 1.0 / (zoom * min(WIDTH, HEIGHT))
    fx = (mx - WIDTH * 0.5) * scale_before + offset_x
    fy = (HEIGHT * 0.5 - my) * scale_before + offset_y

    zoom *= zoom_factor
    if zoom < 1.0:
        zoom = 1.0

    scale_after = 1.0 / (zoom * min(WIDTH, HEIGHT))
    offset_x = fx - (mx - WIDTH * 0.5) * scale_after
    offset_y = fy - (HEIGHT * 0.5 - my) * scale_after


def draw_status_banner(overlay, title, subtitle, accent_color, danger=False):
    pulse = 0.84 + 0.16 * math.sin((time.time() - start_time) * 2.2)
    card = pygame.Surface((760, 82), pygame.SRCALPHA)
    pygame.draw.rect(card, (8, 12, 20, 205), card.get_rect(), border_radius=18)
    pygame.draw.rect(card, (*accent_color, int(120 * pulse)), card.get_rect(), width=2, border_radius=18)

    title_surf = title_font.render(title, True, (245, 248, 255))
    subtitle_surf = small_font.render(subtitle, True, (208, 215, 228))
    title_x = 24
    title_y = 14
    subtitle_x = 24
    subtitle_y = 48
    accent_width = min(max(title_surf.get_width() + 18, 72), 180)
    accent_rect = pygame.Rect(title_x, title_y - 8, accent_width, 5)
    pygame.draw.rect(card, (*accent_color, int(95 * pulse)), accent_rect, border_radius=3)

    if danger:
        warning_glow = pygame.Surface((accent_width + 28, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(warning_glow, (*accent_color, 36), warning_glow.get_rect())
        card.blit(warning_glow, (title_x - 14, title_y - 16))

    card.blit(title_surf, (title_x, title_y))
    card.blit(subtitle_surf, (subtitle_x, subtitle_y))

    overlay.blit(card, (WIDTH // 2 - card.get_width() // 2, HEIGHT - 108))


def draw_info_overlay():
    global RANDOM_BUTTON_RECT

    if not overlay_visible:
        RANDOM_BUTTON_RECT = pygame.Rect(0, 0, 0, 0)
        return

    nearby_name = PORTALS[current_point_index]["name"] if current_point_index != -1 else "NONE"
    pointer_status = "ON" if pointer_enabled else "OFF"
    discovered_count = len(discovered_portals)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    panel = pygame.Surface((320, 380), pygame.SRCALPHA)
    panel_rect = panel.get_rect()
    pygame.draw.rect(panel, (8, 12, 22, 210), panel_rect, border_radius=24)
    pygame.draw.rect(panel, (82, 129, 181, 170), panel_rect, width=2, border_radius=24)
    pygame.draw.rect(panel, (120, 196, 255, 120), pygame.Rect(20, 14, 86, 6), border_radius=4)
    pygame.draw.rect(panel, (255, 184, 88, 85), pygame.Rect(20, 24, 58, 3), border_radius=3)

    lines = [
        ("PORTAL DISCOVERY", (255, 242, 184)),
        (f"Discovered: {discovered_count}/{len(PORTALS)}", (245, 248, 255)),
        (f"Nearby Portal: {nearby_name}", (255, 220, 80) if current_point_index != -1 else (180, 180, 180)),
        (f"Pointer Hint: {pointer_status}", (255, 136, 120) if pointer_enabled else (160, 220, 255)),
        (f"Game Over: {'YES' if game_over else 'NO'}", (255, 120, 120) if game_over else (120, 255, 190)),
        (f"Last Discovery: {last_discovery if last_discovery else 'NONE'}", (120, 255, 200)),
        (f"Zoom: {zoom:.1f}", (245, 248, 255)),
        (f"Near Target: {'YES' if is_near_target() else 'NO'}",
         (120, 255, 190) if is_near_target() else (255, 120, 120)),
        ("Mouse Wheel = zoom", (220, 228, 240)),
        ("Left Drag = move fractal", (220, 228, 240)),
        ("H = pointer hint", (220, 228, 240)),
        ("TAB = hide panel", (220, 228, 240)),
        ("R = reset", (220, 228, 240)),
        ("ESC = quit", (220, 228, 240)),
    ]

    y = 34
    for text, color in lines:
        current_font = title_font if text == "PORTAL DISCOVERY" else font
        if text in ("Mouse Wheel = zoom", "Left Drag = move fractal", "H = pointer hint", "TAB = hide panel", "R = reset", "ESC = quit"):
            current_font = tiny_font
        shadow = current_font.render(text, True, (0, 0, 0))
        surf = current_font.render(text, True, color)
        panel.blit(shadow, (23, y + 2))
        panel.blit(surf, (20, y))
        y += 28 if current_font == title_font else 20

    button_rect = pygame.Rect(20, y + 12, 136, 28)
    pygame.draw.rect(panel, (18, 32, 28, 225), button_rect, border_radius=12)
    pygame.draw.rect(panel, (154, 220, 120, 200), button_rect, width=2, border_radius=12)
    button_text = tiny_font.render("Random Colors", True, (240, 248, 232))
    panel.blit(
        button_text,
        (button_rect.x + button_rect.width // 2 - button_text.get_width() // 2,
         button_rect.y + button_rect.height // 2 - button_text.get_height() // 2),
    )

    panel_pos = (18, 18)
    RANDOM_BUTTON_RECT = button_rect.move(panel_pos)
    overlay.blit(panel, panel_pos)

    if game_over:
        draw_status_banner(
            overlay,
            "GAME OVER",
            "Pointer hint was used before every portal was discovered.",
            (255, 96, 96),
            danger=True,
        )
    elif discovered_count == len(PORTALS):
        draw_status_banner(
            overlay,
            "ALL PORTALS DISCOVERED",
            "Every hidden scene has been found. The cosmos is fully mapped.",
            (110, 255, 188),
            danger=False,
        )

    overlay_data = pygame.image.tostring(overlay, "RGBA", True)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glBindTexture(GL_TEXTURE_2D, hud_tex)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT,
        0, GL_RGBA, GL_UNSIGNED_BYTE, overlay_data
    )

    glColor4f(1.0, 1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-1, -1)
    glTexCoord2f(1, 0); glVertex2f( 1, -1)
    glTexCoord2f(1, 1); glVertex2f( 1,  1)
    glTexCoord2f(0, 1); glVertex2f(-1,  1)
    glEnd()

    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)


def draw_solar_portal(dt):
    glEnable(GL_DEPTH_TEST)
    glClear(GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, WIDTH / HEIGHT, 0.1, 500.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, cam_zoom)
    glRotatef(cam_rot_x, 1.0, 0.0, 0.0)
    glRotatef(cam_rot_y, 0.0, 1.0, 0.0)

    solar_system.setup_lighting()
    solar_system.draw_scene(dt)

    set_2d()


def set_flat_scene_projection():
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = WIDTH / float(HEIGHT if HEIGHT != 0 else 1)
    if aspect >= 1.0:
        glOrtho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0)
    else:
        glOrtho(-1.0, 1.0, -1.0 / aspect, 1.0 / aspect, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def init_portal_scenes():
    solar_system.sun_glow = 0.0
    solar_system.moon_angle = 0.0
    solar_system.angles = {p["name"]: random.uniform(0, 360) for p in solar_system.PLANETS}

    black_hole.init_stars()
    black_hole.init_dust()
    black_hole.init_particles()
    black_hole.time_value = 0.0
    black_hole.disk_rotation = 0.0
    black_hole.planet_angle = 2.8
    black_hole.planet_radius = 0.62

    spaceship.init_stars()
    spaceship.init_particles()
    spaceship.time_value = 0.0

    supernova.init_stars()
    supernova.init_supernova()
    supernova.time_value = 0.0


def update_portal_scenes():
    black_hole.time_value += 0.016
    black_hole.disk_rotation += 0.18
    black_hole.update_particles()
    black_hole.planet_angle += 0.01
    black_hole.planet_radius -= 0.00025
    if black_hole.planet_radius < 0.34:
        black_hole.planet_radius = 0.62
        black_hole.planet_angle = random.uniform(0, 2 * math.pi)

    spaceship.time_value += 0.016
    spaceship.update_particles()

    supernova.time_value += 0.016
    supernova.update_supernova()


def draw_black_hole_scene():
    set_flat_scene_projection()
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
    set_2d()


def draw_spaceship_scene():
    set_flat_scene_projection()
    spaceship.draw_background()
    spaceship.draw_stars()
    ship_x = 0.48 * math.sin(spaceship.time_value * 0.45)
    ship_y = 0.18 + 0.08 * math.sin(spaceship.time_value * 0.9)
    spaceship.draw_ufo(ship_x, ship_y)
    set_2d()


def draw_supernova_scene():
    set_flat_scene_projection()
    supernova.draw_background()
    supernova.draw_stars()
    supernova.draw_nebula_glow()
    supernova.draw_beams()
    supernova.draw_bipolar_shells()
    supernova.draw_rings()
    supernova.draw_particles()
    supernova.draw_core()
    set_2d()


def draw_active_portal(dt):
    scene = PORTALS[current_point_index]["scene"]
    if scene == "solar":
        draw_solar_portal(dt)
    elif scene == "black_hole":
        draw_black_hole_scene()
    elif scene == "spaceship":
        draw_spaceship_scene()
    elif scene == "supernova":
        draw_supernova_scene()


def register_discovery():
    global last_discovery

    if current_point_index != -1 and current_point_index not in discovered_portals:
        discovered_portals.add(current_point_index)
        last_discovery = PORTALS[current_point_index]["name"]


def randomize_fractal_palette():
    global palette_seed
    palette_seed = random.random()


def main():
    global fractal_prog, hud_tex, start_time, font, title_font, small_font, tiny_font
    global offset_x, offset_y
    global selected_x, selected_y, current_point_index, pointer_enabled, game_over, overlay_visible

    pygame.init()
    title_font = pygame.font.SysFont("trebuchetms", 26, bold=True)
    font = pygame.font.SysFont("trebuchetms", 18, bold=True)
    small_font = pygame.font.SysFont("trebuchetms", 15)
    tiny_font = pygame.font.SysFont("trebuchetms", 13)
    pygame.display.set_caption("Mandelbrot Portal Solar System")
    pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)

    glClearColor(0.0, 0.0, 0.0, 1.0)

    fractal_prog = build_program()
    start_time = time.time()

    hud_tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, hud_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    setup_lighting()
    init_portal_scenes()
    reset_all()

    fractal_drag = False
    fractal_last = (0, 0)

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_r:
                    init_portal_scenes()
                    reset_all()
                elif event.key == K_c:
                    mx, my = pygame.mouse.get_pos()
                    fx, fy = screen_to_fractal(mx, my)
                    selected_x = fx
                    selected_y = fy
                    current_point_index = -1
                    print("selected_x =", repr(selected_x))
                    print("selected_y =", repr(selected_y))
                elif event.key == K_h:
                    pointer_enabled = True
                    if len(discovered_portals) < len(PORTALS):
                        game_over = True
                elif event.key == K_TAB:
                    overlay_visible = not overlay_visible
                elif event.key == K_g:
                    randomize_fractal_palette()

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if RANDOM_BUTTON_RECT.collidepoint(event.pos):
                        randomize_fractal_palette()
                        continue
                    fractal_drag = True
                    fractal_last = event.pos
                elif event.button == 2:
                    fx, fy = screen_to_fractal(event.pos[0], event.pos[1])
                    selected_x = fx
                    selected_y = fy
                    current_point_index = -1
                    print("selected_x =", repr(selected_x))
                    print("selected_y =", repr(selected_y))
                elif event.button == 4:
                    zoom_at(event.pos[0], event.pos[1], 1.15)
                elif event.button == 5:
                    zoom_at(event.pos[0], event.pos[1], 1.0 / 1.15)

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    fractal_drag = False

            elif event.type == MOUSEMOTION and fractal_drag:
                dx = event.pos[0] - fractal_last[0]
                dy = event.pos[1] - fractal_last[1]
                fractal_last = event.pos

                scale = 1.0 / (zoom * min(WIDTH, HEIGHT))
                offset_x -= dx * scale
                offset_y += dy * scale

        update_portal_scenes()
        current_point_index = find_near_target_index()
        if current_point_index != -1:
            selected_x, selected_y = PORTALS[current_point_index]["point"]
            if should_reveal_solar():
                register_discovery()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        set_2d()
        draw_fractal()
        if pointer_enabled:
            draw_target_markers()

        if should_reveal_solar():
            draw_active_portal(dt)

        draw_info_overlay()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
