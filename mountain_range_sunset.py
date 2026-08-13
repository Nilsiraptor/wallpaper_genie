"""
Procedural Wallpaper Generator
===============================
Generates a wallpaper with:
  - a vertical color gradient background (red/pink at bottom -> yellow at top)
  - several layers of "mountains" (filled area under a 1D noise curve),
    drawn back-to-front, getting darker the lower/closer they are.

Everything you'd want to tweak lives in the CONFIG section below:
colors, number of mountains, noise shape/roughness, image size, etc.

Requires: numpy, Pillow
    pip install numpy pillow
"""

from random import getrandbits

import numpy as np
from PIL import Image, ImageDraw
import spectra
import opensimplex

# ============================================================
# CONFIG - tweak everything here
# ============================================================

WIDTH, HEIGHT = 2560, 1440

# --- Background gradient colors (RGB 0-255) ---
SKY_BOTTOM_COLOR = spectra.html("#FF0000").to("lch")
SKY_MID_COLOR = spectra.html("#FF5A78").to("lch")
SKY_TOP_COLOR = spectra.html("#FFDC5A").to("lch")

# --- Mountain layer colors ---
# The farthest-back (topmost, smallest) mountain uses MOUNTAIN_COLOR_FAR,
# the frontmost (lowest, largest) mountain uses MOUNTAIN_COLOR_NEAR.
# Every layer in between is linearly interpolated, so the mountains get
# progressively darker as they get lower/closer to the viewer.
MOUNTAIN_COLOR_FAR = spectra.html("#005d98").to("lch")
MOUNTAIN_COLOR_NEAR = spectra.html("#01225e").to("lch")

# --- Mountain shape / layout ---
NUM_MOUNTAINS = 4          # how many mountain layers to stack

# Each mountain's silhouette is built from fractal ("fBm") noise.
NOISE_OCTAVES = 8          # more octaves = more fine detail/roughness
NOISE_PERSISTENCE = 0.5    # how quickly amplitude shrinks per octave (0-1)
NOISE_LACUNARITY = 2.0     # how quickly frequency grows per octave
NOISE_BASE_FREQUENCY = 3 # base "zoominess" of the noise (higher = more bumps)

# Where the mountains sit vertically, as a fraction of image height (0=top, 1=bottom).
# The first value is for the farthest-back mountain, the last for the closest.
MOUNTAIN_BASE_Y = np.linspace(0.5, 0.95, NUM_MOUNTAINS, True)

# How tall each mountain's noise silhouette is, as a fraction of image height.
# The first value is for the farthest-back mountain, the last for the closest.
MOUNTAIN_AMPLITUDE = np.linspace(0.3, 0.2, NUM_MOUNTAINS, True)

OUTPUT_PATH = "wallpaper.png"

# ============================================================
# NOISE GENERATION
# ============================================================

def fractal_noise_1d(width, seed=None, octaves=5, persistence=0.5, lacunarity=2.0,
                      base_frequency=2.0):
    """
    Fractal Brownian Motion (fBm): sums several octaves of value noise
    at increasing frequency / decreasing amplitude for a natural,
    rough silhouette. Returns an array of length `width` normalized to [-1, 1].
    """

    if seed is None:
        seed = getrandbits(16)

    xs = np.linspace(0, base_frequency, width, False)
    total = np.zeros(width)
    amplitude = 1.0
    frequency = 1.0
    max_amplitude = 0

    opensimplex.seed(seed)

    for octave in range(octaves):
        total += np.array([opensimplex.noise2(x=x * frequency, y=128*octave) * amplitude for x in xs])
        max_amplitude += amplitude
        amplitude *= persistence
        frequency *= lacunarity

    total /= max_amplitude  # normalize to roughly [-1, 1]
    return total


# ============================================================
# DRAWING
# ============================================================

def make_background(width, height, colors):
    """Create a vertical gradient image: top_color at y=0, bottom_color at y=height."""
    gradient = spectra.range(colors, height)

    colors = 255 * np.array([[c.clamped_rgb] for c in gradient])

    background = np.tile(colors, (1, width, 1)).astype(np.uint8)

    return Image.fromarray(background, mode="RGB")


def draw_mountain(draw, width, height, base_y_frac, amplitude_frac, color, seed):
    """
    Draw a single mountain layer: the region under a noise curve,
    filled down to the bottom of the image.
    """
    noise = fractal_noise_1d(
        width,
        seed=seed,
        octaves=NOISE_OCTAVES,
        persistence=NOISE_PERSISTENCE,
        lacunarity=NOISE_LACUNARITY,
        base_frequency=NOISE_BASE_FREQUENCY,
    )

    base_y = base_y_frac * height
    amplitude = amplitude_frac * height
    ridge_y = base_y - noise * amplitude  # noise pushes the ridge line upward

    points = [(x, ridge_y[x]) for x in range(width)]
    points.append((width, height))
    points.append((0, height))

    color_tuple = tuple((int(255*c) for c in color.rgb))

    draw.polygon(points, fill=color_tuple)


def generate_wallpaper(seed=None):
    if seed is None:
        seed = getrandbits(16)

    img = make_background(WIDTH, HEIGHT, [
        SKY_TOP_COLOR,
        SKY_MID_COLOR,
        SKY_BOTTOM_COLOR,
    ])
    draw = ImageDraw.Draw(img)

    for i in range(NUM_MOUNTAINS):
        t = i / max(NUM_MOUNTAINS - 1, 1)  # 0 = farthest, 1 = closest
        color = MOUNTAIN_COLOR_FAR.blend(MOUNTAIN_COLOR_NEAR, t)
        draw_mountain(
            draw,
            WIDTH,
            HEIGHT,
            base_y_frac=MOUNTAIN_BASE_Y[i],
            amplitude_frac=MOUNTAIN_AMPLITUDE[i],
            color=color,
            seed=seed + i,
        )

    img.save(f"{seed}.png")
    print(f"Saved wallpaper to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_wallpaper()
