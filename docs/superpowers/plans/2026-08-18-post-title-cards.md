# Post Title Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the nine Weekly Tape posts a dark photographic title card with the market's own price action drawn across it and the headline set into the image, and make the cover show it.

**Architecture:** One generator script in `docs/` (never shipped — `docs/` is in the build's exclude list) composites a motif from the private content repo, the post's own chart card, and the site's type into a 1280×720 card written to `assets/posts/<slug>/title.{png,webp}`. Each Tape post's `image:` then points at that card, so it is both the cover's lead figure and the share image. One CSS line changes the lead figure's crop from 2:1 to 16:9.

**Tech Stack:** Python 3.9 (system), Pillow, fontTools + brotli (to instance the site's Newsreader variable woff2), PyYAML. Jekyll 3.10 for the build. No new runtime dependency — nothing here runs at page-render time.

**Spec:** `docs/superpowers/specs/2026-08-18-post-title-cards-design.md`

## Global Constraints

Copied from the spec. Every task's requirements implicitly include these.

- **Public repo:** no link to dashboard source, installers or GitHub releases anywhere.
- **Zero third-party requests on content pages.** Cards are committed local files; nothing is fetched at render time.
- **No file outside this repo is written.** `$CH_CONTENT` (default `~/charthorizon/content`) is read-only, and no absolute local path may be committed — a committed plan leaked `/Users/<name>/…` the day before and it was a review finding.
- **No paid image generation.** The motif pool is what already exists.
- **The Hedgers' Ledger is untouched** — its posts keep their chart cards, on purpose, so the two editions look different.
- **`_data/*` is untouched.**
- `assets/css/blog.css` is the single source of truth for the look. Three house rules: both muted tones clear 4.5:1 on every surface; `:focus-visible` is one ink ring defined once, add none; prose stays capped at `--measure`.
- **Keep `CNAME` intact.** Bump `css_version` when `blog.css` changes — this branch takes it 12 → 13.
- `.preview/` is gitignored and must never be `git add`ed.

## Workspace

Worktree `~/charthorizon/website/.worktrees/title-cards`, branch `title-cards`, **branched from `video-rail`, not from `main`** — the unmerged video-rail work touches the same `index.html` and `blog.css`, so building on `main` would write the 16:9 change against stale code.

Every build is `REPO="$PWD" ~/charthorizon/ops/website-build.sh` from the worktree root. A bare `ops/website-build.sh` builds the main checkout instead and reports green while doing it.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `docs/title_card.py` | **new** — the generator: motif + chart + type → one card. Not shipped. | 1 |
| `.preview/check-cards.py` | **new, gitignored** — asserts every Tape card exists, is 1280×720 in both twins, and is actually dark | 1 |
| `assets/posts/<slug>/title.{png,webp}` | **new** — nine cards, committed | 2 |
| `_posts/<nine Tape posts>.md` | `image:` / `image_alt:` repointed at the card | 2 |
| `assets/css/blog.css` | `.lead-figure` crop 2:1 → 16:9 | 3 |
| `_config.yml` | `css_version` 12 → 13 | 3 |
| `CLAUDE.md` | documents the card, the generator and the motif rule | 3 |

---

### Task 1: The generator

**Files:**
- Create: `docs/title_card.py`
- Create: `.preview/check-cards.py`

**Interfaces:**
- Produces: `python3 docs/title_card.py <slug> --motif <key> [--chart <file>] [--no-chart]`, writing `assets/posts/<slug>/title.png` and `title.webp`, both exactly 1280×720. Task 2 calls it nine times.
- Produces: `python3 .preview/check-cards.py`, exit 1 on any failure. Task 4 runs it.
- Title and date are read from the post's own front matter, never passed in — so the headline on the card can never drift from the headline on the page.

- [ ] **Step 1: Write the failing check**

Create `.preview/check-cards.py`:

```python
#!/usr/bin/env python3
"""Every Weekly Tape post has a title card, and that card is actually dark.

Lives under .preview/ (gitignored AND in the build's exclude list) so it is
neither committed nor published.

The darkness assertion is not cosmetic. The entire reason for a photographic card
is that it works in BOTH editions without correction — the chart cards had to be
dimmed with brightness(.92) in the dark edition precisely because they are drawn on
near-white. A bright card would silently reintroduce that problem, and nothing else
here would catch it.

    python3 .preview/check-cards.py
"""
from __future__ import annotations

import pathlib
import sys

import yaml
from PIL import Image, ImageStat

REPO = pathlib.Path(__file__).resolve().parent.parent
POSTS = REPO / "_posts"

MAX_MEAN_LUMA = 100      # out of 255; the agreed recipe lands near 60
fail: list[str] = []


def front_matter(p: pathlib.Path) -> dict:
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}


tape = []
for p in sorted(POSTS.glob("*.md")):
    fm = front_matter(p)
    title = str(fm.get("title", ""))
    edition = str(fm.get("edition", ""))
    is_ledger = "Hedgers" in edition if edition else "Hedgers" in title
    if not is_ledger:
        tape.append((p, fm))

print(f"  weekly tape posts: {len(tape)}")

for p, fm in tape:
    slug = p.stem
    img = str(fm.get("image", ""))
    want = f"/assets/posts/{slug}/title.png"
    if img != want:
        fail.append(f"{slug}: image is {img!r}, expected {want!r}")
        continue
    if not str(fm.get("image_alt", "")).strip():
        fail.append(f"{slug}: image_alt is empty")
    png = REPO / img.lstrip("/")
    webp = png.with_suffix(".webp")
    for f in (png, webp):
        if not f.exists():
            fail.append(f"{slug}: missing {f.relative_to(REPO)}")
            continue
        im = Image.open(f)
        if im.size != (1280, 720):
            fail.append(f"{slug}: {f.name} is {im.size}, expected (1280, 720)")
        luma = ImageStat.Stat(im.convert("L")).mean[0]
        if luma > MAX_MEAN_LUMA:
            fail.append(f"{slug}: {f.name} mean luminance {luma:.0f} > {MAX_MEAN_LUMA} "
                        "— the card must be dark enough to need no dimming in the night edition")

if fail:
    print("\nCARD CHECKS FAILED:")
    for f in fail:
        print("  !!", f)
    sys.exit(1)
print("  cards:             all present, 1280x720, dark in both twins")
print("\n  card checks passed")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website/.worktrees/title-cards && python3 .preview/check-cards.py
```

Expected: FAIL, nine lines of `image is '/assets/posts/…/cards/<market>.png', expected '…/title.png'`. That is the point — no card exists yet.

- [ ] **Step 3: Write the generator**

Create `docs/title_card.py`:

```python
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
```

- [ ] **Step 4: Render one card and look at it**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
python3 docs/title_card.py 2026-08-15-paid-to-wait --motif grains --chart corn.png
```

Expected: one line naming both outputs. Then **open `assets/posts/2026-08-15-paid-to-wait/title.png` and look at it.** It must show: grain elevators darkened almost to silhouette, green and red candles across the lower two thirds, `WEEKLY TAPE · AUGUST 15, 2026` in gold, `PAID TO WAIT` in cream serif caps, a short gold rule, `CHARTHORIZON` top right. If the kicker is hard to read, the ground is too bright — adjust `scrim(floor=…)`, never the ink colour.

- [ ] **Step 5: Prove the darkness assertion is real**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
python3 - <<'PY'
from PIL import Image, ImageStat, ImageEnhance
p = "assets/posts/2026-08-15-paid-to-wait/title.png"
im = Image.open(p)
print("mean luminance:", round(ImageStat.Stat(im.convert("L")).mean[0]))
bright = ImageEnhance.Brightness(im).enhance(2.6)
bright.save("/tmp/too-bright.png")
print("bright copy mean:", round(ImageStat.Stat(bright.convert("L")).mean[0]))
PY
```

Expected: the real card well under 100, the deliberately brightened copy well over it. This shows the check in Step 1 would actually fire on a card that lost its darkness — the property the whole design rests on.

- [ ] **Step 6: Commit**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
git add docs/title_card.py
git commit -m "cards: a generator for post title cards"
```

`.preview/check-cards.py` is gitignored — there is nothing to add for it, and that is expected. The one rendered card is committed in Task 2 with the rest.

---

### Task 2: The nine cards and their front matter

**Files:**
- Create: `assets/posts/<slug>/title.png` and `title.webp` × 9
- Modify: the nine Weekly Tape posts in `_posts/`

**Interfaces:**
- Consumes: `docs/title_card.py` and `.preview/check-cards.py` from Task 1.
- Produces: every Tape post's `image:` is `/assets/posts/<slug>/title.png`. Task 3's CSS change assumes it.

- [ ] **Step 1: Render all nine**

Run exactly these, from the worktree root:

```bash
cd ~/charthorizon/website/.worktrees/title-cards
python3 docs/title_card.py 2026-08-15-paid-to-wait          --motif grains   --chart corn.png
python3 docs/title_card.py 2026-08-08-warning-filed-on-tuesday --motif equities --chart ym_dow.png
python3 docs/title_card.py 2026-08-04-where-the-metal-went  --motif metals   --chart gold.png
python3 docs/title_card.py 2026-08-01-yen-warning-shot      --motif fx       --chart usdjpy.png
python3 docs/title_card.py 2026-06-27-bond-market-vote      --motif rates    --chart bonds.png
python3 docs/title_card.py 2026-06-17-hollow-advance        --motif macro    --chart dow.png
python3 docs/title_card.py 2026-06-14-weekly-tape           --motif fx       --chart fx.png
python3 docs/title_card.py 2026-06-09-weekly-tape           --motif macro    --chart macro-shift.png
python3 docs/title_card.py 2026-06-11-spacex-ipo            --motif softs    --no-chart
```

The two Dow pieces take different motifs (`equities`, `macro`) on purpose: both would otherwise carry the same photograph, and adjacent strand rows on the cover showing one picture twice read as a duplication bug rather than as a series.

- [ ] **Step 2: Look at all nine as a contact sheet**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
python3 - <<'PY'
import glob, pathlib
from PIL import Image
fs = sorted(glob.glob("assets/posts/*/title.png"))
CW, CH, COLS = 440, 248, 3
rows = (len(fs) + COLS - 1) // COLS
sheet = Image.new("RGB", (CW*COLS, CH*rows), (20, 20, 20))
for i, f in enumerate(fs):
    sheet.paste(Image.open(f).resize((CW, CH), Image.LANCZOS), ((i % COLS)*CW, (i//COLS)*CH))
sheet.save("/tmp/cards-sheet.png")
print(len(fs), "cards ->", "/tmp/cards-sheet.png")
PY
```

Expected: nine cards. **Open the sheet and check three things:** every headline is fully inside its card and not clipped; no two adjacent cards carry the same photograph; the SpaceX card has motif and type but no candles. If a headline overflows, the wrap loop's floor (`size > 52 * SS`) is too high for that title — report it rather than hand-editing the image.

- [ ] **Step 3: Repoint the front matter**

In each of the nine posts, replace the `image:` line with the card and write a fresh `image_alt`. The alt describes *the card*, not the market — it is what a screen reader announces for the cover's lead figure.

```yaml
# _posts/2026-08-15-paid-to-wait.md
image: /assets/posts/2026-08-15-paid-to-wait/title.png
image_alt: "Title card: grain elevators at dawn, with corn's price action drawn across them"
```

Use this table for the other eight. Keep every other line of front matter untouched — in particular `cards:`, which the article body still uses for its in-body charts.

| Post | `image_alt` |
|---|---|
| `2026-08-08-warning-filed-on-tuesday` | `"Title card: the New York Stock Exchange floor in 1920, with the Dow's price action drawn across it"` |
| `2026-08-04-where-the-metal-went` | `"Title card: a foundry pour, with gold's price action drawn across it"` |
| `2026-08-01-yen-warning-shot` | `"Title card: a freighter at the dock, with the dollar-yen price action drawn across it"` |
| `2026-06-27-bond-market-vote` | `"Title card: exchange trading posts in 1922, with the bond price action drawn across them"` |
| `2026-06-17-hollow-advance` | `"Title card: an exchange facade in 1928, with the Dow's price action drawn across it"` |
| `2026-06-14-weekly-tape` | `"Title card: a freighter at the dock, with the dollar's price action drawn across it"` |
| `2026-06-09-weekly-tape` | `"Title card: an exchange facade in 1928, with the week's price action drawn across it"` |
| `2026-06-11-spacex-ipo` | `"Title card: cotton bales stacked in a dark warehouse"` |

- [ ] **Step 4: Run the check**

```bash
cd ~/charthorizon/website/.worktrees/title-cards && python3 .preview/check-cards.py
```

Expected: `weekly tape posts: 9`, then `cards: all present, 1280x720, dark in both twins` and `card checks passed`.

- [ ] **Step 5: Build**

```bash
cd ~/charthorizon/website/.worktrees/title-cards && REPO="$PWD" ~/charthorizon/ops/website-build.sh
```

Expected: `all checks passed`, and `broken local refs: 0` in particular — that is what proves every new `image:` path resolves.

- [ ] **Step 6: Commit**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
git add assets/posts/*/title.png assets/posts/*/title.webp _posts
git commit -m "cards: title cards for the nine Weekly Tape posts"
```

---

### Task 3: The cover shows the card whole

**Files:**
- Modify: `assets/css/blog.css` (the `.lead-figure img` rule)
- Modify: `_config.yml` (`css_version` 12 → 13)
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: the cards and front matter from Task 2.

- [ ] **Step 1: Write the failing check**

Append to `.preview/check-cards.py`, immediately before the `if fail:` block:

```python
# --- the cover must not crop the headline off the card ------------------------
# The card is 16:9 with the headline baked into its lower half. The lead figure was
# built for the old chart cards and crops 2:1 FROM THE TOP, which eats the headline
# exactly. This is the one CSS line the whole task exists for.
css = (REPO / "assets/css/blog.css").read_text(encoding="utf-8")
if "aspect-ratio:2/1" in css.replace(" ", ""):
    fail.append("blog.css still crops .lead-figure to 2/1 — that cuts the card's headline off")
if "aspect-ratio:16/9" not in css.replace(" ", ""):
    fail.append("blog.css does not set a 16/9 lead figure")
print("  lead figure:       16/9, headline not cropped")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website/.worktrees/title-cards && python3 .preview/check-cards.py
```

Expected: FAIL with `blog.css still crops .lead-figure to 2/1 …`.

- [ ] **Step 3: Change the crop**

In `assets/css/blog.css`, the `.lead-figure img` rule currently reads:

```css
.lead-figure img{display:block; width:100%; aspect-ratio:2/1; object-fit:cover; object-position:top;
  margin:0; border:1px solid var(--rule); border-radius:10px; box-shadow:0 1px 16px rgba(var(--shadow-tint),.10)}
```

Replace the whole rule, comment included, with:

```css
/* 16:9, because a Weekly Tape lead is now a title card with its headline set into the
   lower half of the image — the old 2:1 crop from the top ate exactly that. The Ledger's
   chart cards (1200x1036) crop acceptably at 16:9 too, in fact better than at 2:1, so one
   rule serves both editions and no per-edition branch is needed. */
.lead-figure img{display:block; width:100%; aspect-ratio:16/9; object-fit:cover; object-position:top;
  margin:0; border:1px solid var(--rule); border-radius:10px; box-shadow:0 1px 16px rgba(var(--shadow-tint),.10)}
```

Delete the old comment block directly above it (`assets/css/blog.css:473-476`, beginning "The card is 1200x1036 — nearly square") — it explains the 2:1 crop and now describes the opposite of what the code does.

Bump `css_version` in `_config.yml` from `12` to `13`.

- [ ] **Step 4: Document it**

In `CLAUDE.md`, the `index.html` bullet currently says the lead is "the newest Weekly Tape, its OG card cropped 2:1 from the top". Replace that clause with a description of the card, and add the generator where the publishing workflow is described:

- In the `index.html` bullet: "…the newest Weekly Tape, shown as its **title card** — a dark photographic motif with the market's own price action drawn across it and the headline set into the image, rendered 16:9…"
- In "Publishing a post", after the images step: a short paragraph saying that Weekly Tape posts get a title card from `docs/title_card.py` (`--motif` picks the photograph, `--chart` the price panel, `--no-chart` for a post without one), that the motifs live in the private content repo under `$CH_CONTENT` and only the finished card is committed here, that the card becomes the post's `image:` and therefore its share image, and that **the Hedgers' Ledger deliberately keeps its chart card** so the two editions look different.

- [ ] **Step 5: Build, check, screenshot**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
REPO="$PWD" ~/charthorizon/ops/website-build.sh && python3 .preview/check-cards.py && python3 .preview/check-front.py
cd _site && (python3 -m http.server 8899 >/dev/null 2>&1 &) ; sleep 1 ; cd ..
SP=/private/tmp/claude-501/-Users-notwoalike-charthorizon-website/1c6f54c5-3353-43f2-8c34-4b66c5b961f4/scratchpad
for w in 1280 900 375; do node .preview/shot.mjs http://localhost:8899/ "$SP/cards-$w.png" $w full; done
node "$SP/shot-dark.mjs" http://localhost:8899/ "$SP/cards-dark.png"
```

Expected: all three check runs green. Then **look at the screenshots**: the lead is the title card with its headline fully visible and not cropped; at 375 nothing overflows; in the dark edition the card sits on the navy without looking washed out or glaring. The dark shot is the important one — the whole reason for a picture card is that it needs no correction there.

- [ ] **Step 6: Commit**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
git add assets/css/blog.css _config.yml CLAUDE.md
git commit -m "cover: the lead figure is 16:9, so a title card keeps its headline"
```

---

### Task 4: Final verification

**Files:** none modified.

- [ ] **Step 1: Build the committed tree**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
REPO="$PWD" ~/charthorizon/ops/website-build.sh --from-head && python3 .preview/check-cards.py && python3 .preview/check-front.py
```

`--from-head` builds what the nightly job would publish. All three must pass. A failure here that did not appear on the working tree means something was left uncommitted.

- [ ] **Step 2: Confirm the share image changed**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
grep -o 'og:image" content="[^"]*"' _site/2026/08/15/paid-to-wait/index.html
```

Expected: the title card PNG, not the corn chart. That is the second half of what this change buys — the card shares as well as it leads.

- [ ] **Step 3: Confirm the Ledger is untouched**

```bash
cd ~/charthorizon/website/.worktrees/title-cards
grep -o 'og:image" content="[^"]*"' _site/2026/08/16/hedgers-ledger/index.html
git diff --stat video-rail...HEAD -- _posts | grep -c hedgers || echo "0 ledger posts touched"
```

Expected: the Ledger's own chart card, and zero Ledger posts in the diff. The two editions look different on purpose.

- [ ] **Step 4: Confirm nothing outside this repo changed**

```bash
cd ~/charthorizon && git status --porcelain
```

Expected: no changes under `content/`, `ops/` or `dashboard/`. `$CH_CONTENT` is read-only for this work.

- [ ] **Step 5: Report, do not deploy**

Summarise: the check output, the screenshot paths, `git diff --stat video-rail...HEAD`. Then **stop**. This branch sits on top of the unmerged `video-rail`; merging and deploying both is the operator's call.

---

## Self-Review

**Spec coverage.** Generator → Task 1; motif registry and the `scene-*` exclusion → Task 1's `MOTIFS` dict and its comment; the nine cards and the assignment table → Task 2; front matter and share image → Task 2 plus Task 4 Step 2; the 16:9 lead figure → Task 3; `css_version` → Task 3; CLAUDE.md → Task 3; the spec's five tests → Task 2 Step 5 (build), Task 1 Step 1 and Task 3 Step 1 (the check script), Task 3 Step 5 (screenshots, both editions), Task 4 Step 2 (share image). The spec's "no file outside this repo" → Task 4 Step 4.

**Naming consistency.** `MOTIFS` keys `grains|metals|fx|softs|equities|macro|rates` are used identically in Task 1's dict and Task 2's nine commands. `title.png` / `title.webp` are the only output names, asserted in `check-cards.py` and referenced in the front-matter table. `BAND = 0.72` is the agreed two thirds.

**Known sharp edges, handled in the steps.** Newsreader's weight axis stops at 700, so `instanced(..., 700)` is the maximum and no step asks for more. `--chart` is required rather than derived from `image:`, because Task 2 overwrites `image:` with the card and a derived path would break on any re-run. The darkness check has a demonstrated failure mode (Task 1 Step 5) rather than being asserted to work.
