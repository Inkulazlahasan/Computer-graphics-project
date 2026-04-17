# Fractal Explorer / Fractal Universe

Interactive fractal viewers built with Python, Numba, Pygame, and OpenGL.

This project now has two main entry points:

- `fractal_explorer.py` - the original fractal viewer
- `combined.py` - the fractal universe version that can render scene modules such as `black_hole.py`, `solar_system.py`, `spaceship.py`, and `supernova.py` inside the same window when a trigger matches

## Features

- 5 fractals: Mandelbrot, Julia, Burning Ship, Tricorn, Newton `z^3 - 1`
- Real-time zoom and pan
- Multiple colormaps
- Numba-accelerated CPU fractal rendering
- OpenGL-backed display path in `combined.py`
- Configurable scene triggers based on fractal, coordinate, zoom, and tolerance
- On-screen HUD with mouse position, world coordinate, zoom, and trigger info
- Screenshot export

## Requirements

Use Python 3.12 if possible.

Install dependencies:

```bash
py -3.12 -m pip install numpy numba pygame matplotlib PyOpenGL
```

If `py -3.12` is not available, use your local Python command:

```bash
pip install numpy numba pygame matplotlib PyOpenGL
```

## Run

Run the original viewer:

```bash
py -3.12 fractal_explorer.py
```

Run the combined fractal universe viewer:

```bash
py -3.12 combined.py
```

## Files

- `fractal_explorer.py` - original standalone fractal viewer
- `combined.py` - fractal universe viewer with scene triggers
- `black_hole.py` - black hole scene module
- `solar_system.py` - solar system scene module
- `spaceship.py` - spaceship scene module
- `supernova.py` - supernova scene module

## Controls

These controls are used in `combined.py`:

| Key / Input | Action |
|---|---|
| Mouse wheel | Zoom in / out |
| Left drag | Pan |
| `1 2 3 4 5` | Switch fractal |
| `C` | Cycle colormap |
| `Up / Down` | Increase / decrease iterations |
| `R` | Reset current fractal view |
| `P` | Print snapshot with point and zoom |
| `S` | Save screenshot |
| `H` | Show / hide HUD |
| `Esc` | Quit |

## Scene Trigger Setup

`combined.py` uses a list named `SCENE_TRIGGERS` to decide when a scene should appear.

Each trigger entry looks like this:

```python
{
    "label": "Black Hole",
    "scene": "black_hole",
    "fractal": "mandelbrot",
    "enabled": True,
    "display_mode": "fullscreen",
    "anchor_mode": "mouse",
    "target": (-0.559263844063, -0.643894886232),
    "zoom": 7.414709e4,
    "position_tolerance_px": 90,
    "sticky_position_tolerance_px": 140,
    "zoom_ratio_tolerance": 3.0,
    "sticky_zoom_ratio_tolerance": 4.0,
    "auto_launch": True,
}
```

### Trigger fields

- `label` - display name in the HUD
- `scene` - which imported scene module to render
- `fractal` - which fractal this trigger belongs to: `mandelbrot`, `julia`, `burning_ship`, `tricorn`, or `newton`
- `enabled` - turn the trigger on or off
- `display_mode` - `"fullscreen"` or `"portal"`
- `anchor_mode` - `"mouse"` or `"center"`
- `target` - fractal world coordinate where the trigger should match
- `zoom` - target zoom level
- `position_tolerance_px` - how near the mouse/center must be before the scene starts
- `sticky_position_tolerance_px` - how far it can move after the scene already appeared
- `zoom_ratio_tolerance` - how near the zoom must be before the scene starts
- `sticky_zoom_ratio_tolerance` - how much zoom can change after the scene already appeared
- `auto_launch` - allow the scene to activate automatically

## Mouse vs Center

This is the most important setup rule:

- `anchor_mode: "mouse"` -> use `Mouse world` from the `P` snapshot
- `anchor_mode: "center"` -> use `View center` from the `P` snapshot

If you use `"center"` but keep a `target` copied from `Mouse world`, the trigger may not match.

## How To Capture A New Trigger

1. Open `combined.py`
2. Go to the fractal you want
3. Zoom to the place where the scene should appear
4. Press `P`
5. Copy the printed values into the correct entry in `SCENE_TRIGGERS`

The snapshot prints:

- `Mouse px`
- `Mouse world`
- `View center`
- `Zoom`

### For mouse-based triggers

Use:

```python
"anchor_mode": "mouse",
"target": (copy Mouse world here),
```

### For center-based triggers

Use:

```python
"anchor_mode": "center",
"target": (copy View center here),
```

## How Range Works

A scene appears only when both conditions match:

- the position is close enough to the target
- the zoom is close enough to the target zoom

### Position range

`position_tolerance_px` is measured in screen pixels.

Example:

```python
"position_tolerance_px": 90,
```

This means the mouse or center must be within about 90 pixels of the target marker.

### Zoom range

`zoom_ratio_tolerance` works like a multiplier.

Example:

```python
"zoom": 7.414709e4,
"zoom_ratio_tolerance": 3.0,
```

This means the scene can start showing roughly between:

- `7.414709e4 / 3`
- `7.414709e4 * 3`

### Sticky range

The sticky values are used after the scene already appears.

They are useful when:

- you do not want the scene to disappear immediately
- you move the mouse a little
- you zoom a little while the scene is active

Example:

```python
"position_tolerance_px": 90,
"sticky_position_tolerance_px": 400,
"zoom_ratio_tolerance": 1.8,
"sticky_zoom_ratio_tolerance": 3.0,
```

This setup makes the scene start only near the correct location, but stay active more easily once it is already visible.

## Recommended Trigger Presets

### Tight

```python
"position_tolerance_px": 60,
"sticky_position_tolerance_px": 100,
"zoom_ratio_tolerance": 1.8,
"sticky_zoom_ratio_tolerance": 2.2,
```

### Medium

```python
"position_tolerance_px": 120,
"sticky_position_tolerance_px": 180,
"zoom_ratio_tolerance": 3.0,
"sticky_zoom_ratio_tolerance": 4.0,
```

### Loose

```python
"position_tolerance_px": 250,
"sticky_position_tolerance_px": 500,
"zoom_ratio_tolerance": 5.0,
"sticky_zoom_ratio_tolerance": 7.0,
```

## Common Fixes

### The scene shows too early

Make the zoom range smaller:

```python
"zoom_ratio_tolerance": 1.5,
```

You can also reduce:

```python
"position_tolerance_px"
```

### The scene disappears when I move the mouse

If you are using:

```python
"anchor_mode": "mouse",
```

increase:

```python
"sticky_position_tolerance_px"
```

For example:

```python
"sticky_position_tolerance_px": 2000,
```

### I want mouse movement to not matter

Use:

```python
"anchor_mode": "center",
```

and copy the value from `View center` into `target`.

### The scene is not showing at all

Check these first:

- `enabled` is `True`
- `fractal` matches the current fractal
- `target` was copied from the correct snapshot field
- `zoom` is near the current zoom
- tolerances are not too small

## Notes About Rendering

- `combined.py` keeps the fractal and scene in the same window
- scenes do not open in a separate display anymore
- `display_mode: "fullscreen"` makes the scene fill the window when triggered
- `display_mode: "portal"` can be used if you want a framed portal effect instead

## Project Structure

```text
Fractal-Explorer-main/
|-- README.md
|-- fractal_explorer.py
|-- combined.py
|-- black_hole.py
|-- solar_system.py
|-- spaceship.py
`-- supernova.py
```
