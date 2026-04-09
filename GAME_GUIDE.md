# Mandelbrot Portal Solar System

## What This Game Is

This is an exploration game built inside a Mandelbrot fractal world.

You move around the fractal, zoom into hidden portal locations, and reveal special space scenes. There are 4 portals to discover:

- Solar System
- Black Hole
- Spaceship
- Supernova

The goal is to discover all 4 portals.

## Main Goal

Find every hidden portal in the fractal and zoom in deep enough to reveal its scene.

You win when all 4 portals have been discovered.

## How The Game Works

Each portal has a hidden position inside the fractal.

To discover one:

1. Move around the fractal.
2. Zoom toward a portal location.
3. When you are close enough, the game recognizes that you are near a target.
4. Keep zooming in until the portal reveal level is reached.
5. The portal becomes discovered and its scene appears.

## Controls

- `Mouse Wheel`: Zoom in and out
- `Left Drag`: Move around the fractal
- `H`: Turn on the pointer hint
- `Tab`: Hide or show the info panel
- `G`: Randomize fractal colors
- `R`: Reset the whole game
- `Esc`: Quit the game

## Important Rule About The Hint

The `H` key enables the pointer hint system.

The pointer can help you find portal directions, but it comes with a penalty:

- If you press `H` before all 4 portals are discovered, the game enters `Game Over`
- The game still runs, but you lose the challenge condition

So if you want to play properly and avoid losing, do not use the hint early.

## Win Condition

You win by discovering all 4 portals.

When that happens, the game shows:

- `ALL PORTALS DISCOVERED`

## Lose Condition

You lose the challenge if you activate the pointer hint before discovering every portal.

When that happens, the game shows:

- `GAME OVER`

## What The Info Panel Shows

The panel on the screen shows useful live information:

- How many portals are discovered
- Which portal is nearby
- Whether the pointer hint is on or off
- Whether the game is over
- Your last discovered portal
- Your current zoom level
- Whether you are near a target

It also shows the main controls.

If you want a full clear view of the fractal, press `Tab` to hide the panel.

## Best Way To Play

- Start by exploring without using the hint
- Zoom slowly and carefully when you think you are near something
- Watch the `Nearby Portal` and `Near Target` information
- Keep zooming once you are near a portal
- Use `R` if you want to restart a clean run
- Use `G` if you want a different color style while playing

## Suggested Player Strategy

Try this approach:

1. Pan across the fractal using left drag.
2. Use the mouse wheel to inspect interesting regions.
3. Watch for the nearby target status in the panel.
4. Once you are close, keep zooming until the hidden scene appears.
5. Repeat until all portals are discovered.

## How To Start The Game

Run:

```bash
python main.py
```

`main.py` launches the main game in `combined.py`.

## Notes

- The game begins with the info panel visible.
- The game begins with the pointer hint turned off.
- The game starts at normal zoom and a default fractal position.
- The portal scenes are part of the discovery system, not separate levels you select from a menu.
