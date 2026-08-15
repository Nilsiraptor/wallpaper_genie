from random import getrandbits, random

import numpy as np
from PIL import Image, ImageDraw
import spectra
import opensimplex
import matplotlib.pyplot as plt


WIDTH, HEIGHT = 2560, 1440

CLOUD_COLOR_LIGHT = "#3B4252"
CLOUD_COLOR_DARK = "#11141A"

LIGHTNING_COLORS = [
    "#00F0FF"
]

NUM_CLOUDS = 5
CLOUD_CIRCLES = 10
CLOUD_PUFFINESS = 1.0
CLOUD_PUFFINESS_VARIETY = 0.2
CLOUD_PUFFINESS_FREQUENCY = 2.0
CLOUD_NOISE_FREQUENCY = 3.0
CLOUD_NOISE_HEIGHT = 0.15

NUM_LIGHTNINGS = 1
LIGHTNING_BRANCHES = 1

LIGHTNING_ATTRACTION = 2.0

def create_cloud(seed=None):
    if seed is None:
        seed = getrandbits(16)

    xs = np.linspace(0, 1, WIDTH, True)

    opensimplex.seed(seed)
    baseline = opensimplex.noise2array(CLOUD_NOISE_FREQUENCY*xs, np.ones(1))
    baseline *= CLOUD_NOISE_HEIGHT

    circle_x, dist = np.linspace(0, 1, CLOUD_CIRCLES+1, True, True)
    circle_y = opensimplex.noise2array(circle_x*CLOUD_NOISE_FREQUENCY, np.ones(1))[0]
    circle_y *= CLOUD_NOISE_HEIGHT

    distances = np.hypot(np.diff(circle_x), np.diff(circle_y))
    max_dist = distances.max()

    radius_change = opensimplex.noise2array(CLOUD_PUFFINESS_FREQUENCY*circle_x, 40*np.ones(1))[0]

    radius_change -= radius_change.min()
    new_radius = 1 + CLOUD_PUFFINESS_VARIETY * radius_change
    scale = max_dist/2/CLOUD_PUFFINESS / new_radius.min()
    new_radius *= scale

    fig, ax = plt.subplots(figsize=(10, 5))

    for center, r in zip(zip(circle_x, circle_y), new_radius):
        circle = plt.Circle(center, r)
        ax.add_patch(circle)

    ax.fill_between(xs, baseline[0], 1)

    ax.set_xlim(0, 1)
    ax.set_ylim(baseline.min()-max_dist/CLOUD_PUFFINESS, baseline.max()+max_dist)
    ax.set_aspect("equal")
    plt.show()

def rotate(v):
    # rotates the vector v clockwise 90°
    return np.array([v[1], -v[0]])

def to_img(v):
    return v[0] + 1j*v[1]

def draw_arc(image_draw, start, end, puffiness=1.0):
    r0 = (start - end) / 2
    h = rotate(r0) * np.sqrt(1/puffiness**2 - 1)
    r = np.linalg.norm(r0)/puffiness

    center = (start + end) / 2 - h

    image_draw.circle(center, 2, fill="green")

    box = [
        [c - r for c in center],
        [c + r for c in center]
    ]

    print(box)

    start_angle = np.angle(to_img(start-center), deg=True)%360
    end_angle = np.angle(to_img(end-center), deg=True)%360

    if start_angle > end_angle:
        start_angle, end_angle = end_angle, start_angle

    print(start_angle, end_angle)

    image_draw.chord(box, start=start_angle, end=end_angle, fill="red")


if __name__ == "__main__":
    create_cloud()
