"""
Generate a checkerboard wallpaper at 2560x1440 using a 34x14 grid (Case A).

Grid: 34 columns x 14 rows
Cell size: 52 x 101 px
Padding: 24px horizontal, 2px vertical (only between cells, no outer border)
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

# Colors
COLOR_A = "darkgreen"  # dark squares
COLOR_B = "green"  # light squares
BG_COLOR = "whitesmoke"  # padding/background color


def main():
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    for row in range(ceil(CANVAS_H / HEIGHT)):
        for col in range(ceil(CANVAS_W / WIDTH)):
            x0 = X_OFFSET + col * WIDTH
            y0 = Y_OFFSET + row * HEIGHT
            x1 = x0 + WIDTH
            y1 = y0 + HEIGHT

            color = COLOR_A if (row + col) % 2 == 0 else COLOR_B
            draw.rounded_rectangle([x0, y0, x1, y1], radius=RADIUS, fill=color, width=0)

    img.save("checkerboard_wallpaper.png")
    print("Saved checkerboard_wallpaper.png")


if __name__ == "__main__":
    main()
