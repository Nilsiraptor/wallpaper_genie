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

import numpy as np
from PIL import Image, ImageDraw

# ============================================================
# CONFIG - tweak everything here
# ============================================================

WIDTH, HEIGHT = 2560, 1440

# --- Background gradient colors (RGB 0-255) ---
SKY_BOTTOM_COLOR = (255, 90, 120)     # red/pink at the bottom
SKY_TOP_COLOR = (255, 220, 90)        # yellow at the top

# --- Mountain layer colors ---
# The farthest-back (topmost, smallest) mountain uses MOUNTAIN_COLOR_FAR,
# the frontmost (lowest, largest) mountain uses MOUNTAIN_COLOR_NEAR.
# Every layer in between is linearly interpolated, so the mountains get
# progressively darker as they get lower/closer to the viewer.
MOUNTAIN_COLOR_FAR = (110, 130, 200)   # lighter blue, farthest mountain
MOUNTAIN_COLOR_NEAR = (10, 15, 45)     # near-black blue, closest mountain

# --- Mountain shape / layout ---
NUM_MOUNTAINS = 4          # how many mountain layers to stack
SEED = 42                  # change for a totally different layout

# Each mountain's silhouette is built from fractal ("fBm") noise.
NOISE_OCTAVES = 6          # more octaves = more fine detail/roughness
NOISE_PERSISTENCE = 0.5    # how quickly amplitude shrinks per octave (0-1)
NOISE_LACUNARITY = 2.0     # how quickly frequency grows per octave
NOISE_BASE_FREQUENCY = 2.5 # base "zoominess" of the noise (higher = more bumps)

# Where the mountains sit vertically, as a fraction of image height (0=top, 1=bottom).
# The first value is for the farthest-back mountain, the last for the closest.
MOUNTAIN_BASE_Y = np.linspace(0.55, 0.85, NUM_MOUNTAINS)

# How tall each mountain's noise silhouette is, as a fraction of image height.
# The first value is for the farthest-back mountain, the last for the closest.
MOUNTAIN_AMPLITUDE = np.linspace(0.10, 0.22, NUM_MOUNTAINS)

OUTPUT_PATH = "wallpaper.png"

# ============================================================
# NOISE GENERATION
# ============================================================


def smoothstep(t):
    """Smooth interpolation curve (ease in/out), used to soften value noise."""
    return t * t * (3 - 2 * t)


def value_noise_1d(x, seed):
    """
    1D value noise: random values pinned to integer coordinates,
    smoothly interpolated in between. x can be any float array.
    """
    x0 = np.floor(x).astype(int)
    x1 = x0 + 1
    t = smoothstep(x - x0)

    def rand_at(i):
        # Deterministic pseudo-random value per integer coordinate + seed
        rng_input = (i.astype(np.int64) * 374761393 + seed * 668265263) & 0xFFFFFFFF
        rng_input = (rng_input ^ (rng_input >> 13)) * 1274126177 & 0xFFFFFFFF
        rng_input = rng_input ^ (rng_input >> 16)
        return (rng_input / 0xFFFFFFFF) * 2 - 1  # range [-1, 1]

    v0 = rand_at(x0)
    v1 = rand_at(x1)
    return v0 + t * (v1 - v0)


def fractal_noise_1d(width, seed, octaves=5, persistence=0.5, lacunarity=2.0,
                      base_frequency=2.0):
    """
    Fractal Brownian Motion (fBm): sums several octaves of value noise
    at increasing frequency / decreasing amplitude for a natural,
    rough silhouette. Returns an array of length `width` normalized to [0, 1].
    """
    xs = np.linspace(0, base_frequency, width)
    total = np.zeros(width)
    amplitude = 1.0
    frequency = 1.0
    max_amplitude = 0.0

    for octave in range(octaves):
        total += value_noise_1d(xs * frequency, seed=seed + octave * 101) * amplitude
        max_amplitude += amplitude
        amplitude *= persistence
        frequency *= lacunarity

    total /= max_amplitude  # normalize to roughly [-1, 1]
    return (total + 1) / 2  # normalize to [0, 1]


# ============================================================
# DRAWING
# ============================================================


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def make_background(width, height, bottom_color, top_color):
    """Create a vertical gradient image: top_color at y=0, bottom_color at y=height."""
    t = np.linspace(0, 1, height).reshape(height, 1)
    top = np.array(top_color, dtype=float).reshape(1, 1, 3)
    bottom = np.array(bottom_color, dtype=float).reshape(1, 1, 3)
    gradient = top + (bottom - top) * t.reshape(height, 1, 1)
    gradient = np.repeat(gradient, width, axis=1).astype(np.uint8)
    return Image.fromarray(gradient, mode="RGB")


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

    draw.polygon(points, fill=color)


def generate_wallpaper():
    img = make_background(WIDTH, HEIGHT, SKY_BOTTOM_COLOR, SKY_TOP_COLOR)
    draw = ImageDraw.Draw(img)

    for i in range(NUM_MOUNTAINS):
        t = i / max(NUM_MOUNTAINS - 1, 1)  # 0 = farthest, 1 = closest
        color = lerp_color(MOUNTAIN_COLOR_FAR, MOUNTAIN_COLOR_NEAR, t)
        draw_mountain(
            draw,
            WIDTH,
            HEIGHT,
            base_y_frac=MOUNTAIN_BASE_Y[i],
            amplitude_frac=MOUNTAIN_AMPLITUDE[i],
            color=color,
            seed=SEED + i * 977,  # different seed per layer -> different silhouette
        )

    img.save(OUTPUT_PATH)
    print(f"Saved wallpaper to {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_wallpaper()
