"""
╔══════════════════════════════════════════════════════════════╗
║         FRACTAL UNIVERSE  —  OpenGL + Pygame                 ║
║  Mandelbrot & Julia Set with animated colors + zoom          ║
╚══════════════════════════════════════════════════════════════╝

Controls:
  SPACE           — Switch between Mandelbrot and Julia Set
  A / D           — Rotate Julia Set parameter (morphing shapes)
  W / S           — Zoom in / out (keyboard)
  Scroll Wheel    — Zoom in / out toward mouse cursor
  Right-click drag— Pan / move the fractal
  R               — Reset view
  UP / DOWN       — Increase / Decrease color speed
  F               — Toggle auto-zoom fly-in
  ESC             — Quit
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np
import time
import math
import sys

# ── Resolution ───────────────────────────────────────────────────────────────
WIDTH,  HEIGHT  = 1280, 720
MAX_ITER        = 256          # iteration depth (quality)

# ── Fractal state ─────────────────────────────────────────────────────────────
mode            = "mandelbrot"  # "mandelbrot" or "julia"
zoom            = 1.0
offset_x        = -0.5
offset_y        = 0.0
color_time      = 0.0
color_speed     = 0.4
auto_zoom       = True
auto_zoom_speed = 0.0018

julia_angle     = 0.0
julia_r         = 0.7885

# ── Mouse pan state ───────────────────────────────────────────────────────────
mouse_drag      = False
drag_last_x     = 0
drag_last_y     = 0

# Mandelbrot deep-zoom target (a beautiful spiral region)
TARGET_X = -0.7436438885706021
TARGET_Y =  0.1318259042053119


# ─────────────────────────────────────────────────────────────────────────────
#  GLSL Shader source
# ─────────────────────────────────────────────────────────────────────────────

VERTEX_SHADER = """
#version 120
void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

FRAGMENT_SHADER = """
#version 120

uniform vec2  u_resolution;
uniform float u_zoom;
uniform vec2  u_offset;
uniform float u_time;
uniform float u_color_speed;
uniform int   u_mode;       // 0 = Mandelbrot, 1 = Julia
uniform vec2  u_julia_c;
uniform int   u_max_iter;

// Smooth HSV → RGB
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    vec2 uv  = (gl_FragCoord.xy - u_resolution * 0.5) / min(u_resolution.x, u_resolution.y);
    uv      /= u_zoom;
    uv      += u_offset;

    vec2 z, c;

    if (u_mode == 0) {
        // Mandelbrot: c = pixel, z starts at 0
        z = vec2(0.0);
        c = uv;
    } else {
        // Julia: z = pixel, c = constant
        z = uv;
        c = u_julia_c;
    }

    int  iter = 0;
    float len2 = 0.0;

    for (int i = 0; i < 1024; i++) {
        if (i >= u_max_iter) break;
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        len2 = dot(z, z);
        if (len2 > 4.0) break;
        iter++;
    }

    if (iter == u_max_iter) {
        // Inside the set → deep black with slight blue shimmer
        gl_FragColor = vec4(0.0, 0.0, 0.04 + 0.02*sin(u_time*0.3), 1.0);
    } else {
        // Smooth colouring
        float smooth_iter = float(iter) - log2(log2(len2)) + 4.0;
        float t = smooth_iter / float(u_max_iter);

        // Animated colour cycling
        float hue = fract(t * 3.0 + u_time * u_color_speed);
        float sat = 0.85;
        float val = t < 0.02 ? t * 50.0 : 1.0;   // fade near-set edge

        // Three-layer colour blend for richness
        vec3 col1 = hsv2rgb(vec3(hue,          sat, val));
        vec3 col2 = hsv2rgb(vec3(hue + 0.33,   sat * 0.7, val));
        vec3 col3 = hsv2rgb(vec3(hue + 0.66,   sat * 0.5, val * 0.8));

        float w1 = smoothstep(0.0, 0.5, t);
        float w2 = smoothstep(0.3, 0.8, t);
        vec3  col = mix(col1, mix(col2, col3, w2), w1);

        // Subtle brightness pulse
        col *= 0.85 + 0.15 * sin(u_time * 1.2 + t * 20.0);

        gl_FragColor = vec4(col, 1.0);
    }
}
"""


# ─────────────────────────────────────────────────────────────────────────────
def compile_shader(src, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, src)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        print("Shader compile error:\n", glGetShaderInfoLog(shader).decode())
        sys.exit(1)
    return shader


def build_program():
    vs = compile_shader(VERTEX_SHADER,   GL_VERTEX_SHADER)
    fs = compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    if not glGetProgramiv(prog, GL_LINK_STATUS):
        print("Link error:\n", glGetProgramInfoLog(prog).decode())
        sys.exit(1)
    return prog


def draw_fullscreen_quad():
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-1, -1)
    glTexCoord2f(1, 0); glVertex2f( 1, -1)
    glTexCoord2f(1, 1); glVertex2f( 1,  1)
    glTexCoord2f(0, 1); glVertex2f(-1,  1)
    glEnd()


def draw_hud(screen_surf, font_big, font_small):
    """Render HUD text on a pygame overlay surface."""
    screen_surf.fill((0, 0, 0, 0))

    mode_text = "✦ MANDELBROT SET" if mode == "mandelbrot" else "✦ JULIA SET"
    col = (255, 220, 60) if mode == "mandelbrot" else (100, 220, 255)

    title = font_big.render(mode_text, True, col)
    screen_surf.blit(title, (20, 20))

    info_lines = [
        f"Zoom: {zoom:.4f}x",
        f"Color Speed: {color_speed:.2f}",
        f"Auto-Zoom: {'ON' if auto_zoom else 'OFF'}",
        "",
        "SPACE: Switch Mode   F: Auto-Zoom",
        "Scroll: Zoom   Right-drag: Pan",
        "A/D: Morph Julia   UP/DOWN: Color Speed",
        "R: Reset   ESC: Quit",
    ]
    for i, line in enumerate(info_lines):
        surf = font_small.render(line, True, (200, 200, 220))
        screen_surf.blit(surf, (20, 60 + i * 22))


# ─────────────────────────────────────────────────────────────────────────────
def main():
    global mode, zoom, offset_x, offset_y, color_time, color_speed
    global auto_zoom, julia_angle, julia_r
    global mouse_drag, drag_last_x, drag_last_y

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("✦  Fractal Universe  —  Mandelbrot & Julia Set  ✦")

    # ── Fonts for HUD ─────────────────────────────────────────────────────
    font_big   = pygame.font.SysFont("consolas", 26, bold=True)
    font_small = pygame.font.SysFont("consolas", 16)
    hud_surf   = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # ── OpenGL setup ──────────────────────────────────────────────────────
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    prog = build_program()

    # HUD texture
    hud_tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, hud_tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    clock    = pygame.time.Clock()
    start_t  = time.time()

    while True:
        dt = clock.tick(60) / 1000.0
        color_time = time.time() - start_t

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); return
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit(); return
                if event.key == K_SPACE:
                    mode = "julia" if mode == "mandelbrot" else "mandelbrot"
                    zoom, offset_x, offset_y = 1.0, 0.0, 0.0
                if event.key == K_r:
                    zoom = 1.0
                    offset_x = -0.5 if mode == "mandelbrot" else 0.0
                    offset_y = 0.0
                    julia_angle = 0.0
                if event.key == K_f:
                    auto_zoom = not auto_zoom
                if event.key == K_w:
                    zoom *= 1.2
                if event.key == K_s:
                    zoom = max(0.001, zoom / 1.2)
                if event.key == K_UP:
                    color_speed = min(5.0, color_speed + 0.1)
                if event.key == K_DOWN:
                    color_speed = max(0.0, color_speed - 0.1)

            # ── Right-click drag to pan ────────────────────────────────────
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mouse_drag  = True
                drag_last_x = event.pos[0]
                drag_last_y = event.pos[1]
                auto_zoom   = False   # disable auto-zoom while panning

            if event.type == MOUSEBUTTONUP and event.button == 3:
                mouse_drag = False

            if event.type == MOUSEMOTION and mouse_drag:
                dx = event.pos[0] - drag_last_x
                dy = event.pos[1] - drag_last_y
                drag_last_x = event.pos[0]
                drag_last_y = event.pos[1]
                # Convert pixel delta → fractal-space delta
                scale = 1.0 / (zoom * min(WIDTH, HEIGHT))
                offset_x -= dx * scale
                offset_y += dy * scale   # y flipped

            # ── Scroll wheel zoom toward mouse cursor ─────────────────────
            if event.type == MOUSEBUTTONDOWN and event.button in (4, 5):
                auto_zoom = False   # disable auto-zoom on manual scroll
                mx, my = pygame.mouse.get_pos()
                # Fractal-space position under cursor BEFORE zoom
                scale_before = 1.0 / (zoom * min(WIDTH, HEIGHT))
                fx = (mx - WIDTH  * 0.5) * scale_before + offset_x
                fy = (HEIGHT * 0.5 - my) * scale_before + offset_y

                if event.button == 4:    # scroll up → zoom in
                    zoom *= 1.15
                else:                    # scroll down → zoom out
                    zoom = max(0.001, zoom / 1.15)

                # Adjust offset so the point under cursor stays fixed
                scale_after = 1.0 / (zoom * min(WIDTH, HEIGHT))
                offset_x = fx - (mx - WIDTH  * 0.5) * scale_after
                offset_y = fy - (HEIGHT * 0.5 - my) * scale_after

        keys = pygame.key.get_pressed()
        if keys[K_a]:
            julia_angle -= 0.02
        if keys[K_d]:
            julia_angle += 0.02

        # ── Auto-zoom ─────────────────────────────────────────────────────
        if auto_zoom:
            zoom *= (1.0 + auto_zoom_speed * 60 * dt)
            if mode == "mandelbrot":
                # Smoothly nudge toward deep target
                offset_x += (TARGET_X - offset_x) * 0.001
                offset_y += (TARGET_Y - offset_y) * 0.001
            # Reset if zoomed too deep
            if zoom > 80000:
                zoom = 1.0
                offset_x = -0.5 if mode == "mandelbrot" else 0.0
                offset_y = 0.0

        # ── Julia c parameter ─────────────────────────────────────────────
        julia_c_x = julia_r * math.cos(julia_angle + color_time * 0.08)
        julia_c_y = julia_r * math.sin(julia_angle + color_time * 0.08)

        # ── Draw fractal (GLSL) ───────────────────────────────────────────
        glUseProgram(prog)
        glUniform2f(glGetUniformLocation(prog, "u_resolution"),  WIDTH, HEIGHT)
        glUniform1f(glGetUniformLocation(prog, "u_zoom"),         zoom)
        glUniform2f(glGetUniformLocation(prog, "u_offset"),       offset_x, offset_y)
        glUniform1f(glGetUniformLocation(prog, "u_time"),         color_time)
        glUniform1f(glGetUniformLocation(prog, "u_color_speed"),  color_speed)
        glUniform1i(glGetUniformLocation(prog, "u_mode"),         0 if mode == "mandelbrot" else 1)
        glUniform2f(glGetUniformLocation(prog, "u_julia_c"),      julia_c_x, julia_c_y)
        glUniform1i(glGetUniformLocation(prog, "u_max_iter"),     MAX_ITER)

        draw_fullscreen_quad()
        glUseProgram(0)

        # ── HUD overlay ───────────────────────────────────────────────────
        draw_hud(hud_surf, font_big, font_small)
        hud_data = pygame.image.tostring(hud_surf, "RGBA", True)

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, hud_data)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-1, -1)
        glTexCoord2f(1, 0); glVertex2f( 1, -1)
        glTexCoord2f(1, 1); glVertex2f( 1,  1)
        glTexCoord2f(0, 1); glVertex2f(-1,  1)
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

        pygame.display.flip()


if __name__ == "__main__":
    main()