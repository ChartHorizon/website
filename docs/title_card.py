#!/usr/bin/env python3
"""Render a post's title card: motif + the market's own price action + the headline.

    python3 docs/title_card.py 2026-08-15-paid-to-wait --motif grains --chart corn.png
    python3 docs/title_card.py 2026-06-11-spacex-ipo  --motif softs --no-chart

Writes assets/posts/<slug>/title.png and title.webp, both 1280x720. The PNG is the
share image (card crawlers are the one audience whose WebP support is not worth
betting on); the WebP is what the page loads.

WHY A PICTURE CARD AT ALL
    The chart cards are drawn on near-white and glare on the night press run — the
    front page had to dim them with brightness(.92). A card built dark from the start
    needs no correction and reads the same on paper and on navy. The chart is not lost:
    it is drawn INTO the card, which is also why two posts sharing a motif never share
    a card — the price action differs every week.

WHERE THE MOTIFS LIVE
    In the sibling PRIVATE content repo, resolved through $CH_CONTENT. Only the
    finished card is committed here, so this public repo never carries the masters and
    never depends on a sibling repo at build time.

Title and date come from the post's own front matter. They are deliberately not
arguments: a card whose headline has drifted from the page is worse than no card.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
from io import BytesIO

import yaml
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont, ImageOps

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTENT = pathlib.Path(os.environ.get("CH_CONTENT", pathlib.Path.home() / "charthorizon/content"))
SCENES = CONTENT / "assets/brand/thumb-scenes"

# --- palette: assets/css/blog.css -----------------------------------------
CREAM = (243, 246, 250)          # --ink in the dark edition
NAVY = (11, 19, 29)              # --paper in the dark edition
GOLD_LIFT = (214, 178, 100)      # --gold-ink in the dark edition, #d6b264.
                                 # NOT the paper gold #c8a24a: that measures 2.19:1 on
                                 # paper and was visibly weak on the card.
BULL = (126, 201, 150)           # --bull #6fae83, lifted — the token value vanishes
BEAR = (232, 148, 126)           # --bear #d98a76, lifted   against a near-black ground

# The video narrative pool (scene-*.jpg) is deliberately absent: it is a recurring
# character in colour, and a recurring face over every post reads as a byline, which
# /about/ makes a point of the desk not having.
MOTIFS = {
    "grains":   "thumb-scene-1.png",                 # grain elevators
    "metals":   "thumb-scene-3.png",                 # foundry
    "fx":       "thumb-scene-5.png",                 # freighter at the dock
    "softs":    "thumb-scene-7.png",                 # cotton bales
    "equities": "thumb-arch-nyse-floor-1920.jpg",
    "macro":    "thumb-arch-exchange-facade-1928.jpg",
    "rates":    "thumb-arch-trading-posts-1922.jpg",
}

SS = 2                                    # supersample, then downsample once at the end
W, H = 1280 * SS, 720 * SS
BAND = 0.72                               # the price band covers two thirds of the frame
HELV = "/System/Library/Fonts/Supplemental/Helvetica.ttc"


def instanced(path: pathlib.Path, wght: int) -> BytesIO:
    """Newsreader is a variable font; PIL needs a static instance."""
    f = TTFont(str(path))
    instantiateVariableFont(f, {"wght": wght, "opsz": 72})
    buf = BytesIO()
    f.save(buf)
    buf.seek(0)
    return buf


ROMAN = instanced(REPO / "assets/fonts/newsreader.woff2", 700)   # 700 is the axis maximum


def rfont(size: int) -> ImageFont.FreeTypeFont:
    ROMAN.seek(0)
    return ImageFont.truetype(ROMAN, size)


def cover(im: Image.Image, w: int, h: int) -> Image.Image:
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def base_photo(motif: str) -> Image.Image:
    """Luminance duotone, navy to cream. Colour in the source is discarded, so a warm
    and a cold photograph of the same subject come out alike — the same treatment the
    video pipeline's Thumbnail.tsx applies, for the same reason."""
    path = SCENES / MOTIFS[motif]
    if not path.exists():
        sys.exit(f"!! motif not found: {path}\n   set $CH_CONTENT if the content repo is elsewhere")
    im = cover(Image.open(path).convert("RGB"), W, H)
    im = ImageOps.colorize(ImageOps.grayscale(im), NAVY, CREAM)
    return ImageEnhance.Brightness(im).enhance(0.82)


def price_panel(chart: pathlib.Path) -> Image.Image:
    """ONLY the plot area of the chart card's price panel. Its header and axis labels
    duplicate the kicker and wordmark this card draws itself, and read as noise."""
    c = Image.open(chart)
    w, h = c.size
    return c.crop((int(w * 0.05), int(h * 0.105), int(w * 0.915), int(h * 0.54)))


def kursband(img: Image.Image, chart: pathlib.Path) -> Image.Image:
    """Key the candles out of the card and colour them by direction.

    The card draws rising candles blue and falling ones red, so direction is
    recoverable from hue: compare the red and blue channels. Anything near the card's
    white ground drops out, so only the trace survives."""
    panel = price_panel(chart).convert("RGB")
    bh = int(H * BAND)
    panel = panel.resize((W, bh), Image.LANCZOS)
    r, _g, b = panel.split()
    ink = panel.convert("L").point(lambda v: 0 if v > 220 else min(255, int((220 - v) * 2.6)))
    bear_sel = ImageChops.subtract(r, b, 1, 0).point(lambda v: 255 if v > 8 else 0)
    bull_sel = bear_sel.point(lambda v: 255 - v)
    out = img
    for sel, colour in ((bull_sel, BULL), (bear_sel, BEAR)):
        m = ImageChops.multiply(ink, sel)
        full = Image.new("L", (W, H), 0)
        full.paste(m, (0, H - bh))
        out = Image.composite(Image.new("RGB", (W, H), colour), out, full)
    return out


def scrim(img: Image.Image, floor=0.72, strength=0.92, start=0.06) -> Image.Image:
    """Darken the whole frame, hardest at the foot.

    Legibility on a photograph is a GROUND problem before it is a colour problem: the
    first draft put the kicker on a bright sky, where no gold holds. Fixing the ground
    is what makes the lifted gold work — do not "fix" this by brightening the ink."""
    img = ImageEnhance.Brightness(img).enhance(floor)
    grad = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y / H - start) / (1 - start))
        grad.putpixel((0, y), round(255 * (t ** 1.25) * strength))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, grad.resize((W, H)))


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for word in words:
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def tracked(d, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def front_matter(slug: str) -> dict:
    p = REPO / "_posts" / f"{slug}.md"
    if not p.exists():
        sys.exit(f"!! no such post: {p}")
    text = p.read_text(encoding="utf-8")
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


def render(slug: str, motif: str, chart: pathlib.Path | None) -> None:
    fm = front_matter(slug)
    title = str(fm["title"])
    date = fm["date"]
    kicker = f"WEEKLY TAPE  ·  {date.strftime('%B %-d, %Y').upper()}"

    img = base_photo(motif)
    if chart is not None:
        img = kursband(img, chart)
    img = scrim(img)

    d = ImageDraw.Draw(img)
    m = 74 * SS
    maxw = W - 2 * m

    up = title.upper()
    size = 96 * SS
    f = rfont(size)
    lines = wrap(d, up, f, maxw)
    while len(lines) > 3 and size > 52 * SS:
        size -= 6 * SS
        f = rfont(size)
        lines = wrap(d, up, f, maxw)
    lh = int(size * 1.02)

    y = H - m - lh * len(lines) - 22 * SS
    tracked(d, (m, y - 52 * SS), kicker, ImageFont.truetype(HELV, 25 * SS), GOLD_LIFT, 2.2 * SS)
    for i, ln in enumerate(lines):
        d.text((m, y + i * lh), ln, font=f, fill=CREAM)
    d.line([(m, H - m - 4 * SS), (m + 150 * SS, H - m - 4 * SS)], fill=GOLD_LIFT, width=5 * SS)

    wf = ImageFont.truetype(HELV, 17 * SS)
    wb = d.textbbox((0, 0), "CHARTHORIZON", font=wf)
    d.text((W - m - (wb[2] - wb[0]), m), "CHARTHORIZON", font=wf, fill=CREAM)

    out = img.resize((1280, 720), Image.LANCZOS)
    dest = REPO / "assets/posts" / slug
    dest.mkdir(parents=True, exist_ok=True)
    out.save(dest / "title.png")
    out.save(dest / "title.webp", "WEBP", quality=84, method=6)
    print(f"  {slug}  ->  title.png + title.webp   ({motif}"
          f"{', no chart' if chart is None else ', ' + chart.name})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("slug", help="post slug, e.g. 2026-08-15-paid-to-wait")
    ap.add_argument("--motif", required=True, choices=sorted(MOTIFS))
    ap.add_argument("--chart", help="file under assets/posts/<slug>/cards/, e.g. corn.png")
    ap.add_argument("--no-chart", action="store_true",
                    help="omit the price band (for a post that has no chart card)")
    a = ap.parse_args()

    if a.no_chart and a.chart:
        sys.exit("!! --chart and --no-chart are mutually exclusive")
    if not a.no_chart and not a.chart:
        sys.exit("!! pass --chart <file>, or --no-chart if the post has none")

    chart = None
    if a.chart:
        chart = REPO / "assets/posts" / a.slug / "cards" / a.chart
        if not chart.exists():
            sys.exit(f"!! chart card not found: {chart}")
    render(a.slug, a.motif, chart)


if __name__ == "__main__":
    main()
