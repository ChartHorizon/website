"""Render the ChartHorizon OG default card (1200x630) as a masthead nameplate.

Replicates the site masthead from _layouts/default.html / blog.css:
horizon mark + CHARTHORIZON wordmark + sub-line + tramline + motto, on paper.
"""
import sys
from io import BytesIO

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

PAPER = (245, 244, 241)
INK = (23, 21, 15)
GOLD = (200, 162, 74)
MUTED = (107, 99, 86)

SITE = "/Users/notwoalike/charthorizon/website"
OUT = SITE + "/assets/og-default.png"

SS = 2  # supersample factor for crisp strokes
W, H = 1200 * SS, 630 * SS


def instanced(woff2_path, wght):
    f = TTFont(woff2_path)
    instantiateVariableFont(f, {"wght": wght, "opsz": 72})
    buf = BytesIO()
    f.flags = getattr(f, "flags", None)
    f.save(buf)
    buf.seek(0)
    return buf


roman = instanced(SITE + "/assets/fonts/newsreader.woff2", 600)
italic = instanced(SITE + "/assets/fonts/newsreader-italic.woff2", 400)

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)


def tracked_width(draw, text, font, tracking):
    widths = [draw.textlength(c, font=font) for c in text]
    return sum(widths) + tracking * (len(text) - 1), widths


def draw_tracked(draw, x, y, text, font, tracking, fill):
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + tracking


# --- fit the wordmark ---------------------------------------------------
WORD = "CHARTHORIZON"
size = 104 * SS
while True:
    word_font = ImageFont.truetype(roman, size)
    roman.seek(0)
    tracking = 0.10 * size
    word_w, _ = tracked_width(d, WORD, word_font, tracking)
    word_bbox = d.textbbox((0, 0), "H", font=word_font)
    cap_top, cap_bot = word_bbox[1], word_bbox[3]
    cap_h = cap_bot - cap_top
    # the drawn mark spans 48 of 100 viewBox units (ray tips to horizon line)
    mark_scale = cap_h * 1.15 / 48.0
    mark_w = int(72 * mark_scale)
    gap = int(size * 0.24)
    if word_w + gap + mark_w <= 1000 * SS:
        break
    size -= 2 * SS

sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(13 * SS * 2))
motto_font = ImageFont.truetype(italic, 33 * SS)

SUB = "THE WEEKLY TAPE · FUTURES DESK"
sub_tracking = 0.26 * sub_font.size
sub_w, _ = tracked_width(d, SUB, sub_font, sub_tracking)
sub_h = d.textbbox((0, 0), SUB, font=sub_font)[3]

MOTTO = "Positioning, not predictions."
motto_w = d.textlength(MOTTO, font=motto_font)
motto_h = d.textbbox((0, 0), MOTTO, font=motto_font)[3]

# --- vertical stack -----------------------------------------------------
g1, g2, g3 = int(40 * SS), int(34 * SS), int(30 * SS)
tram_h = int(9 * SS)
total = cap_h + g1 + sub_h + g2 + tram_h + g3 + motto_h
top = (H - total) // 2

# --- brand row: mark + wordmark ----------------------------------------
row_w = mark_w + gap + word_w
row_x = (W - row_w) // 2
word_x = row_x + mark_w + gap
word_y = top - cap_top  # so the cap top lands exactly on `top`
draw_tracked(d, word_x, word_y, WORD, word_font, tracking, INK)

# horizon mark, geometry from the masthead SVG (viewBox 100, g translate(0,3));
# its horizon line (unit y=64, +3 translate) sits on the wordmark baseline
s = mark_scale
baseline_y = top + cap_h
mx = row_x - 14 * s  # drawn content starts at unit x=14
my = baseline_y - 67 * s
def P(x, y):
    return (mx + x * s, my + (y + 3) * s)
lw_ink = max(2, int(2.6 * s))
lw_gold = max(3, int(5.2 * s))
d.line([P(14, 64), P(86, 64)], fill=INK, width=lw_ink)
r = 17 * s
cx, cy = P(50, 64)
d.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=GOLD, width=lw_gold)
d.line([P(50, 19), P(50, 28)], fill=GOLD, width=lw_gold)
d.line([P(26.4, 35.6), P(32, 41.3)], fill=GOLD, width=lw_gold)
d.line([P(73.6, 35.6), P(68, 41.3)], fill=GOLD, width=lw_gold)

# --- sub-line ------------------------------------------------------------
y = top + cap_h + g1
draw_tracked(d, (W - sub_w) // 2, y, SUB, sub_font, sub_tracking, MUTED)

# --- tramline: thick rule with a hairline riding beneath -----------------
y = top + cap_h + g1 + sub_h + g2
margin = 110 * SS
d.rectangle([margin, y, W - margin, y + 5 * SS], fill=INK)
d.rectangle([margin, y + 7 * SS, W - margin, y + 7 * SS + 1 * SS], fill=INK)

# --- motto ----------------------------------------------------------------
y = top + cap_h + g1 + sub_h + g2 + tram_h + g3
d.text(((W - motto_w) // 2, y), MOTTO, font=motto_font, fill=MUTED)

img = img.resize((1200, 630), Image.LANCZOS)
img.save(OUT, optimize=True)
print("wrote", OUT, img.size)
