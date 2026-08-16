from itertools import pairwise
from random import getrandbits

from coloraide import Color
import numpy as np
import opensimplex
from PIL import Image, ImageDraw


WIDTH, HEIGHT = 2560, 1440

CLOUD_COLOR_LIGHT = Color("#3B4252")
CLOUD_COLOR_DARK = Color("#000000")
CLOUD_GAMMA = 1.2

LIGHTNING_COLOR = Color("#7DF9FF")

NUM_CLOUDS = 7
CLOUD_CIRCLES = 15
CLOUD_PUFFINESS = 0.9
CLOUD_PUFFINESS_VARIETY = 1.0
CLOUD_NOISE_FREQUENCY = 3.0
CLOUD_NOISE_HEIGHT = 1.0
CLOUD_VARIETY = 0.3

NUM_LIGHTNINGS = 1
LIGHTNING_BREAKTHROUGH = 2
LIGHTNING_BRANCHES = 1

LIGHTNING_STEP_RATIO = 0.1
LIGHTNING_MOMENTUM = 0.3

LIGHTNING_ROUGHNESS = 1.0
LIGHTNING_MIN_SEGMENT = 2

LIGHTNING_HALO_WIDTH = 25

LIGHTNING_ORIGIN = None
LIGHTNING_TARGET = None

SEED = getrandbits(16)

RNG = np.random.default_rng(SEED)


def get_rgb(color, fit=False):
    new_color = color.convert("srgb")

    if fit:
        new_color.fit()
    else:
        new_color.clip()

    return tuple(int(255 * c) for c in new_color.coords())


def get_rgba(color, fit=False):
    new_color = color.convert("srgb")

    if fit:
        new_color.fit()
    else:
        new_color.clip()

    rgb = [int(255 * c) for c in new_color.coords()]
    a = int(255 * new_color[-1])
    return *rgb, a


def create_wallpaper():
    img = Image.new("RGBA", (WIDTH, HEIGHT), get_rgb(CLOUD_COLOR_DARK))
    pen = ImageDraw.Draw(img)

    offsets, height = np.linspace(0, 1, NUM_CLOUDS, False, True)
    gradient = Color.interpolate(
        [CLOUD_COLOR_LIGHT, CLOUD_COLOR_DARK], space="oklch", out_space="srgb"
    )
    for o in reversed(offsets[LIGHTNING_BREAKTHROUGH:]):
        draw_cloud_band(pen, o, height * CLOUD_NOISE_HEIGHT, gradient(o**CLOUD_GAMMA))

    draw_lightning(img)

    for o in reversed(offsets[:LIGHTNING_BREAKTHROUGH]):
        draw_cloud_band(pen, o, height * CLOUD_NOISE_HEIGHT, gradient(o**CLOUD_GAMMA))

    img.save(f"{SEED}.png")
    print(f"Saved wallpaper to {SEED}.png")


def draw_lightning(og_image):
    global LIGHTNING_ORIGIN, LIGHTNING_TARGET
    image = Image.new("RGBA", og_image.size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)

    if LIGHTNING_ORIGIN is None:
        LIGHTNING_ORIGIN = RNG.random(2).mean() * WIDTH
    if LIGHTNING_TARGET is None:
        if LIGHTNING_ORIGIN < WIDTH / 2:
            LIGHTNING_TARGET = WIDTH * RNG.random(2).mean() / 2
        else:
            LIGHTNING_TARGET = WIDTH + (0.5 * RNG.random(2).mean() / 2)

    light = generate_lightning(x=LIGHTNING_ORIGIN, target=[LIGHTNING_TARGET, HEIGHT])

    transparent = Color(LIGHTNING_COLOR)
    transparent[-1] = 0.0

    halo = np.linspace(0, 1, LIGHTNING_HALO_WIDTH, True)

    gradient = Color.interpolate([transparent, LIGHTNING_COLOR], out_space="srgb")

    for w, t in enumerate(halo):
        # print(w, t, get_rgba(gradient(t)))
        pen.line(
            light,
            fill=get_rgba(gradient(t**2)),
            width=1 + LIGHTNING_HALO_WIDTH - w,
            joint="curve",
        )

    pen.line(light, fill="white", width=2)

    og_image.alpha_composite(image)


def generate_skeleton(x, direction, target):
    """Coarse random walk with large steps. This alone decides the macro
    shape of the bolt (overall bend toward the target, big direction
    changes) — fine texture is added afterwards by midpoint displacement."""
    pos = np.array([x, 0.0])
    skeleton = [pos.tolist()]

    intended_dir = direction
    step_size = HEIGHT * LIGHTNING_STEP_RATIO
    kappa = 5

    while pos[1] < HEIGHT:
        to_target = np.arctan2(target[1] - pos[1], target[0] - pos[0])
        intended_dir = LIGHTNING_MOMENTUM * intended_dir + (1 - LIGHTNING_MOMENTUM) * to_target

        step_dir = RNG.vonmises(intended_dir, kappa)
        intended_dir = step_dir

        pos += step_size * np.array([np.cos(step_dir), np.sin(step_dir)])
        skeleton.append(pos.tolist())

    return skeleton


def displace_segment(p0, p1):
    """Recursively subdivide the segment p0->p1, displacing each new
    midpoint perpendicular to the segment by a shrinking random amount
    (classic 1D midpoint-displacement / fractional Brownian bridge).
    Returns the list of points from just after p0 up to and including p1."""
    length = np.linalg.norm(p1 - p0)
    if length <= LIGHTNING_MIN_SEGMENT:
        return [p1.tolist()]

    mid = (p0 + p1) / 2
    direction = p1 - p0
    perpendicular = rotate(direction)
    displacement = RNG.random(2).mean() - 0.5
    displacement *= LIGHTNING_ROUGHNESS
    mid = mid + perpendicular * displacement

    left = displace_segment(p0, mid)
    right = displace_segment(mid, p1)
    return left + right


def generate_lightning(x=WIDTH / 2, direction=np.pi / 2, target=None):
    if target is None:
        target = np.array([WIDTH / 2, HEIGHT])

    skeleton = generate_skeleton(x, direction, target)

    lightning = [skeleton[0]]
    for p0, p1 in pairwise(skeleton):
        p0, p1 = np.array(p0), np.array(p1)
        lightning += displace_segment(p0, p1)

    return lightning


def draw_cloud_band(pen, baseline, height, color):
    opensimplex.seed(SEED)

    start = RNG.random() / (-CLOUD_CIRCLES)

    circle_x = [start]

    while circle_x[-1] < 1:
        step = np.abs(
            RNG.normal(
                loc=1 / CLOUD_CIRCLES,
                scale=0.5 * CLOUD_PUFFINESS_VARIETY / CLOUD_CIRCLES,
            )
        )
        step += 1 / CLOUD_CIRCLES / 2
        new_circle = circle_x[-1] + step
        circle_x.append(new_circle)

    circle_x = np.array(circle_x)

    circle_y = opensimplex.noise2array(
        circle_x * CLOUD_NOISE_FREQUENCY, baseline / height * CLOUD_VARIETY * np.ones(1)
    )[0]
    circle_y *= height
    circle_y += baseline

    circle_x *= WIDTH
    circle_y *= HEIGHT

    cloud = np.stack([circle_x, circle_y], axis=1).tolist()
    cloud.append([WIDTH, 0])
    cloud.append([0, 0])

    pen.polygon(cloud, fill=get_rgb(color))

    for x, y, a, b in zip(circle_x, circle_y, circle_x[1:], circle_y[1:]):
        draw_bubble(pen, np.array([x, y]), np.array([a, b]), color, CLOUD_PUFFINESS)


def rotate(v):
    # rotates the vector v clockwise 90°
    return np.array([v[1], -v[0]])


def to_img(v):
    return v[0] + 1j * v[1]


def draw_bubble(image_draw, start, end, color, puffiness=1.0):
    r0 = (start - end) / 2
    h = rotate(r0) * np.sqrt(1 / puffiness**2 - 1)
    r = np.linalg.norm(r0) / puffiness

    center = (start + end) / 2 - h

    image_draw.circle(center, r, fill=get_rgb(color))


if __name__ == "__main__":
    create_wallpaper()
