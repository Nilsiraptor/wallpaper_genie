"""
Generate a "Primrose's Field" style wallpaper at 2560x1440, inspired by
Akiyoshi Kitaoka's illusion: a checkerboard of rounded green squares whose
corner gaps reveal small diamond-shaped "primroses" that alternate between
white and magenta at each grid intersection. The alternating high/low
contrast junctions (green-to-white vs. green-to-magenta) are what drive the
illusory shimmer/movement effect.
"""

from math import ceil

from PIL import Image, ImageDraw


# Canvas
CANVAS_W, CANVAS_H = 2560, 1440

# Grid
X_OFFSET, Y_OFFSET = 0, -3

WIDTH, HEIGHT = 75, 98

RADIUS_PERC = 40
RADIUS = round(min(WIDTH, HEIGHT) / 200 * RADIUS_PERC)

print(WIDTH, HEIGHT, RADIUS)

THEME = "pool"

BG_COLOR = "#ffffff"  # fallback background color (mostly covered by primroses)

# Primrose (intersection marker) colors
PRIMROSE_A = "#ffffff"
PRIMROSE_B = "#000000"

# Colors

if THEME == "original":
    COLOR_A = "#4fbb80"  # dark squares
    COLOR_B = "#a0d733"  # light squares
    BG_COLOR = "#ffffff"  # fallback background color (mostly covered by primroses)

    # Primrose (intersection marker) colors - these alternate at each grid vertex
    PRIMROSE_A = "#ffffff"
    PRIMROSE_B = "#cc0099"
elif THEME == "pool":
    COLOR_A = "#01a0c0"  # dark squares
    COLOR_B = "#abe1fd"  # light squares
else:
    pass
    # derive colors from hex code and make it lighter or darker using okLCH
    # make diamonds/primroses white and black

# Half-size (in px) of the diamond drawn at each intersection. Roughly matches
# the corner cutout left behind by the rounded rectangles so the primroses
# fill the gaps neatly; tweak to taste.
PRIMROSE_HALF = min(WIDTH, HEIGHT) // 2


def draw_primrose(draw, cx, cy, half, color):
    """Draw a small diamond ('primrose') centered at (cx, cy)."""
    diamond = [
        (cx, cy - half),
        (cx + half, cy),
        (cx, cy + half),
        (cx - half, cy),
    ]
    draw.polygon(diamond, fill=color, width=0)


def rose_color_seq(i):
    if i >= 8 or i < 0:
        return rose_color_seq(i % 8)
    if i >= 4:
        return not rose_color_seq(i - 4)
    if i == 1:
        return False
    return True


def get_color(i, j):
    index = i - j
    if rose_color_seq(index):
        return PRIMROSE_A
    else:
        return PRIMROSE_B


def main():
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    n_rows = ceil(CANVAS_H / HEIGHT)
    n_cols = ceil(CANVAS_W / WIDTH)

    # Draw primroses first, at every grid vertex (intersection of 4 cells),
    # alternating color in a checkerboard pattern of their own.
    for row in range(n_rows + 1):
        for col in range(n_cols + 1):
            cx = X_OFFSET + col * WIDTH
            cy = Y_OFFSET + row * HEIGHT
            color = get_color(row, col)
            draw_primrose(draw, cx, cy, PRIMROSE_HALF, color)

    # Draw the rounded checkerboard squares on top, leaving the primroses
    # peeking through at the rounded corners.
    for row in range(n_rows):
        for col in range(n_cols):
            x0 = X_OFFSET + col * WIDTH
            y0 = Y_OFFSET + row * HEIGHT
            x1 = x0 + WIDTH
            y1 = y0 + HEIGHT

            color = COLOR_A if (row + col) % 2 == 0 else COLOR_B
            draw.rounded_rectangle([x0, y0, x1, y1], radius=RADIUS, fill=color, width=0)

    img.save("primroses_field.png")
    print("Saved primroses_field.png")


if __name__ == "__main__":
    main()
