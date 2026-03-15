from PIL import Image, ImageDraw
import math

OUTFILE = "colour_strip.png"

#size
STRIP_WIDTH_MM = 240.0
STRIP_HEIGHT_MM = 25.0

#Output resolution (ECF printers only go to 600 i think)
DPI = 600

# Brightness ripple to improve uniqueness, keep somewhat small
BRIGHTNESS_RIPPLE = 0.10
#Optional vertical brightness shaping
VERTICAL_BRIGHTNESS = 0.08

#labelling space
BOTTOM_MARGIN_MM = 20


# sensor works at the following channels: 450, 500, 550, 570, 600, 650 nm
# first value is div by 12
# rgb values after
#would probably be faster to have gpt generate these tbh, it's kinda tedious
ANCHORS = [
    (0.000, (180,  20,  20)),   # deep red
    (0.083, (220, 110,  20)),   # orange
    (0.167, (220, 200,  20)),   # yellow
    (0.250, ( 40, 170,  30)),   # green
    (0.333, ( 20, 170, 120)),   # green-cyan
    (0.417, ( 20, 150, 220)),   # cyan
    (0.500, ( 30,  70, 220)),   # blue
    (0.583, (100,  40, 200)),   # violet
    (0.667, (180,  30, 180)),   # magenta
    (0.750, (150,  20,  80)),   # crimson
    (0.833, (110,  20,  20)),   # dark red
    (0.917, (190,  60, 120)),   # red-magenta transition
    (1.000, (180,  20,  20)),   # repeat first for clean seam
]

# helper fcns
def mm_to_px(mm, dpi):
    return int(round(mm * dpi / 25.4))

#avoid overflow
def clamp255(x: float) -> int:
    return max(0, min(255, int(round(x))))

#interpolate
def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    return t * t * (3.0 - 2.0 * t)

#inerpolate between
def interpolate_rgb(x, anchors):
    x = x % 1.0

    for i in range(len(anchors) - 1):
        x0, c0 = anchors[i]
        x1, c1 = anchors[i + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return c0
            t = (x - x0) / (x1 - x0)
            t = smoothstep(t)
            return (
                clamp255(lerp(c0[0], c1[0], t)),
                clamp255(lerp(c0[1], c1[1], t)),
                clamp255(lerp(c0[2], c1[2], t)),
            )

    return anchors[-1][1]


def apply_brightness(rgb, factor):
    return tuple(clamp255(c * factor) for c in rgb)


def make_strip():
    width_px = mm_to_px(STRIP_WIDTH_MM, DPI)
    height_px = mm_to_px(STRIP_HEIGHT_MM, DPI)
    bottom_margin_px = mm_to_px(BOTTOM_MARGIN_MM, DPI)
    total_height_px = height_px + bottom_margin_px

    img = Image.new("RGB", (width_px, total_height_px), "white")
    draw = ImageDraw.Draw(img)

    #Draw strip
    for x in range(width_px):
        xf = x / max(1, width_px - 1)

        #Base channel-optimized color path
        rgb = interpolate_rgb(xf, ANCHORS)

        for y in range(height_px):
            yf = y / max(1, height_px - 1)

            #periodic brightness ripple across angle
            ripple = 1.0 + BRIGHTNESS_RIPPLE * math.sin(2.0 * math.pi * 3.0 * xf)

            #Slight vertical shaping so the patch is not perfectly flat
            vertical = 1.0 - VERTICAL_BRIGHTNESS * (0.5 - yf)

            rgb2 = apply_brightness(rgb, ripple * vertical)
            img.putpixel((x, y), rgb2)

    #Border
    draw.rectangle([0, 0, width_px - 1, height_px - 1], outline="black", width=2)

    img.save(OUTFILE, dpi=(DPI, DPI))
    print(f"Saved {OUTFILE}")
    print(f"Image size: {width_px} x {total_height_px} px")
    print(f"Print size: {STRIP_WIDTH_MM} mm x {STRIP_HEIGHT_MM + BOTTOM_MARGIN_MM} mm @ {DPI} DPI")


if __name__ == "__main__":
    make_strip()