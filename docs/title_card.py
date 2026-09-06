#!/usr/bin/env python3
"""Render a post's title card: motif + the market's own price action + the headline.

    python3 docs/title_card.py 2026-08-15-paid-to-wait --motif grains --chart corn.png
    python3 docs/title_card.py 2026-06-11-spacex-ipo  --motif softs --no-chart

Writes assets/posts/<slug>/title.jpg and title.webp, both 1280x720. The WebP is what
the page loads; the JPEG twin exists for the same reason every card gets one — share
card crawlers are the one audience whose WebP support is not worth betting on — but
this card is JPEG rather than PNG because it is a PHOTOGRAPH: q86 JPEG holds a
photographic scene at a fraction of PNG's size (the nine cards ran 8.5MB as PNG,
1.1MB as JPEG), where PNG's lossless encoding is mostly spent on grain it doesn't
need to preserve. The chart cards under assets/posts/*/cards/ stay PNG on purpose —
they are flat line art (solid fills, hard edges, text), the case PNG is actually
built for, where JPEG would introduce ringing around every line for no size win.

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
import datetime
import os
import pathlib
import statistics
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
    # A crowd of traders bidding, hands up. Catalogued as a wheat pit, but nothing
    # agricultural is visible in the frame and no institution is named on it — which
    # makes it the one motif that carries "a bid" rather than a market, and the reason
    # it is registered separately instead of under "grains" (taken by the elevators).
    "pit":      "thumb-arch-wheat-pit-1920.jpg",
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


def panel_ground(gray: Image.Image, w: int, h: int, inset: int = 2, n: int = 9) -> float:
    """Median of a border ring of samples, not the mean of 4 corner pixels.

    Four single pixels let one gridline, axis tick or crosshair dash near a corner
    decide which way the *entire* band renders (a stray dark corner reads as "dark
    ground", flips the whole formula, and keys the actual background in as ink). A
    ring of points along all four edges, reduced with a median instead of a mean,
    shrugs off that one contaminated sample instead of baking it into the average —
    the background is still the majority of any edge, even a busy one."""
    xs = [round(inset + i * (w - 1 - 2 * inset) / (n - 1)) for i in range(n)]
    ys = [round(inset + i * (h - 1 - 2 * inset) / (n - 1)) for i in range(n)]
    pts = ([gray.getpixel((x, inset)) for x in xs] +
           [gray.getpixel((x, h - 1 - inset)) for x in xs] +
           [gray.getpixel((inset, y)) for y in ys] +
           [gray.getpixel((w - 1 - inset, y)) for y in ys])
    return statistics.median(pts)


def kursband(img: Image.Image, chart: pathlib.Path) -> Image.Image:
    """Key the candles out of the card and colour them by direction.

    The card draws rising candles blue and falling ones red, so direction is
    recoverable from hue: compare the red and blue channels. Anything near the card's
    ground drops out, so only the trace survives.

    The ground is DETECTED, not assumed white: the dashboard has a dark theme of its
    own, so a chart card exported from it can arrive on navy instead of white. An
    earlier version of this function sampled the ground only to pick one of two
    hardcoded cutoffs (220 on white, 35 on black) — the sampled value never
    recalibrated anything, so a card whose ground sits somewhere in between (say
    grey, ~140) still ran the white-paper cutoff of 220, which is nowhere near where
    that ground actually falls, and read almost the entire panel as ink. That is
    the solid-colour wash that shipped once, just generalised to any ground the
    corpus hasn't seen yet rather than the one dark chart that first hit it.

    So the cutoff is now DERIVED from the sampled ground, not chosen from it:
    `cutoff = ground - MARGIN` on a light ground, mirrored (`ground + MARGIN`) on a
    dark one — ink is whatever sits meaningfully further from the ground than
    MARGIN, in the one direction the ground is not. MARGIN=8 is the slack the one
    real dark card in the corpus already needed (its ground measures 27, 8 short of
    the old hardcoded 35), reused for both directions rather than inventing a second
    constant. The derived cutoff is then clamped back to the old constant (`min(...,
    220)` / `max(..., 35)`) so a near-paper or near-navy ground — everything actually
    seen so far — keys identically to before: on this corpus every measured ground
    sits far enough from 128 that the clamp is what fires, at exactly 220 or 35, so
    all eight existing white-ground cards and the one dark-ground card are unchanged
    down to the byte. The clamp only yields to the derived value once the ground is
    genuinely in between, which is exactly the case that broke before.

    Two things this does NOT fix, honestly: it still only looks for ink on the one
    side of the ground the >=128/<128 branch commits to, so a light stroke on a
    light ground (or a dark stroke on a dark ground) still drops out as background —
    the same one-directional assumption the old code made, now just correctly
    calibrated rather than incorrectly calibrated. And the two branches still meet
    at a step, not a curve: a ground of 127 and 129 pick cutoffs on opposite sides of
    the mirror rather than converging. Untested in practice, because no real ground
    in the corpus has ever landed near 128 — dashboard exports are paper-white or
    navy-black, nothing between."""
    MARGIN = 8
    panel = price_panel(chart).convert("RGB")
    bh = int(H * BAND)
    panel = panel.resize((W, bh), Image.LANCZOS)
    r, _g, b = panel.split()
    gray = panel.convert("L")
    ground = panel_ground(gray, W, bh)
    if ground >= 128:
        cutoff = min(220, ground - MARGIN)
        ink = gray.point(lambda v: 0 if v > cutoff else min(255, int((cutoff - v) * 2.6)))
    else:
        cutoff = max(35, ground + MARGIN)
        ink = gray.point(lambda v: 0 if v < cutoff else min(255, int((v - cutoff) * 2.6)))
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
    # A post that pins its publication TIME (to break a same-day tie on the cover)
    # writes `2026-08-20 09:00:00 +0200`, which PyYAML's timestamp pattern does not
    # match — the zone offset has no colon — so it arrives here as a plain string.
    # Take the leading date either way rather than demanding one shape.
    date = fm["date"]
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date.split()[0])
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
    out.save(dest / "title.jpg", "JPEG", quality=86, optimize=True, progressive=True)
    out.save(dest / "title.webp", "WEBP", quality=84, method=6)
    print(f"  {slug}  ->  title.jpg + title.webp   ({motif}"
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
