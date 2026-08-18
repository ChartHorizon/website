# Post Title Cards — a photographic lead image with the headline set into it

**Date:** 2026-08-18
**Status:** Approved (pending spec review)
**Surface:** chart-horizon.com — the nine Weekly Tape posts, the cover's lead figure
**Branches from:** `video-rail` (unmerged), because both change `index.html` and `blog.css`

## Goal

Give every **Weekly Tape** post a title card: a dark photographic motif with the market's own
price action drawn across it and the headline set into the image. The card becomes the post's
lead image on the cover and its share image everywhere else.

The Hedgers' Ledger keeps its chart card. That is not a compromise — it makes the two editions
visibly different, which is what the strand split on the cover already asserts.

## Why a picture card rather than the chart card

The operator's reason, and it is the load-bearing one: **a photographic card works in both
editions.** The chart cards are drawn on near-white and glare on the night press run — the
front-page redesign had to dim them with `brightness(.92)` precisely because of this. A card
built dark from the start needs no such correction and reads the same on paper and on navy.

The chart is not lost. It is drawn *into* the card, which also solves the reuse problem: two
posts on the same market share a motif, but never share a card, because the price action differs
every week.

## Resolved design decisions (from visual brainstorming)

Settled by looking at rendered candidates, not descriptions.

| Decision | Choice |
|---|---|
| Chart treatment | **Kursband** — candles keyed out of the card and laid over the photo (vs a translucent inset plate, vs a full-frame watermark) |
| Band height | **Two thirds of the frame** (vs the lower third, vs full-frame) |
| Chart colour | **Bull/bear**, split by hue from the source card (vs one amber wash) |
| Title type | **Newsreader, all caps** (vs Newsreader large mixed-case, vs DIN Condensed poster caps) |
| Kicker colour | **The dark edition's lifted gold** `#d6b264` (vs cream) |
| Motifs | **The existing pool only** — no paid image generation |

Two findings from the same session, recorded because they will come up again:

- **Newsreader cannot go bolder.** Its weight axis is clipped at 400–700, so "more striking"
  is a question of size, case or a different face — never more weight.
- **Legibility on a photograph is a *ground* problem before it is a colour problem.** The first
  kicker was unreadable not because gold is weak but because it sat on the bright sky. The fix
  was darkening the whole frame, after which the lifted gold holds.

## The card

1280×720. Built in this order:

1. **Motif** — cover-cropped to 16:9, converted to a luminance duotone (navy → cream), dimmed.
   Colour in the source is discarded, so a warm and a cold photo of the same subject come out
   alike. This mirrors what the video pipeline's `Thumbnail.tsx` does, for the same reason.
2. **Kursband** — the price panel of the post's own chart card, cropped to the plot area only
   (no header, no axis labels — those duplicate the card's own kicker and wordmark), keyed so
   the near-white ground drops out. Rising and falling candles are separated by comparing the
   red and blue channels of the source and coloured with the dark edition's `--bull` / `--bear`,
   each lifted slightly because the token values vanish against a near-black ground. Drawn
   across the lower **two thirds**.
3. **Scrim** — a bottom-up gradient over the whole frame, so type never lands on a bright patch
   whatever the motif does.
4. **Type** — kicker (`WEEKLY TAPE · <date>`, tracked, `#d6b264`), the title in Newsreader 700
   all caps wrapped to at most three lines and shrunk to fit, a gold rule, and the
   `CHARTHORIZON` wordmark top right.

## Architecture

### The generator — `docs/title_card.py`

Lives in this repo next to `docs/og_card.py`, its ancestor. `docs/` is in the build's `exclude`
list, so it never ships.

```
python3 docs/title_card.py --slug 2026-08-15-paid-to-wait \
    --title "Paid to Wait" --date 2026-08-15 --motif grains
```

Writes `assets/posts/<slug>/title.png` and `title.webp` — the same twin convention the chart
cards use: PNG because share-card crawlers are the one audience whose WebP support is not worth
betting on, WebP for the page.

The chart is taken from the post's existing `image:` card. `--no-chart` omits the band for a
post that has none.

**Motifs stay in the private repo.** The script resolves them under `$CH_CONTENT`
(default `~/charthorizon/content`), so no absolute local path is committed — the front-page
review flagged exactly that leak in a committed plan the day before. Only the finished card
lands here; the site never depends on a sibling repo at build time.

### Motif registry

A table in the script, keyed by market group:

| Key | File under `$CH_CONTENT/assets/brand/thumb-scenes/` |
|---|---|
| `grains` | `thumb-scene-1.png` — grain elevators |
| `metals` | `thumb-scene-3.png` — foundry |
| `fx` | `thumb-scene-5.png` — freighter at the dock |
| `softs` | `thumb-scene-7.png` — cotton bales |
| `equities` | `thumb-arch-nyse-floor-1920.jpg` |
| `macro` | `thumb-arch-exchange-facade-1928.jpg` |
| `rates` | `thumb-arch-trading-posts-1922.jpg` |

The eleven `scene-*.jpg` images are deliberately **not** in the registry. They are the video
narrative pool: a recurring character in colour. A recurring face over every post reads as a
byline, and `/about/` makes a point of the desk having none.

`fx` is an acknowledged stretch — a freighter is trade, not currency. Accepted rather than
generating a new motif, which the operator ruled out for now.

### How the site uses it

- Tape posts get `image: /assets/posts/<slug>/title.png` and a fresh `image_alt`. The card
  therefore becomes the Open Graph and Twitter share image too.
- **`.lead-figure` changes from `aspect-ratio: 2/1` to `16/9`.** Load-bearing: the title is
  baked into the card's lower half and a 2:1 crop from the top would cut it off. The Ledger's
  chart cards crop acceptably at 16:9 as well — better than at 2:1 — so one rule serves both
  editions and no per-edition branch is needed.
- `css_version` bumped.
- Ledger posts, `_data/`, the hubs, the rail and every other page are untouched.

## Assignment

| Post | Market | Motif |
|---|---|---|
| 2026-08-15 Paid to Wait | corn | `grains` |
| 2026-08-04 Where the Metal Went | gold | `metals` |
| 2026-08-08 The Warning Was Filed on Tuesday | Dow | `equities` |
| 2026-06-17 The Tape Answers Back | Dow | `macro` |
| 2026-06-27 the bond market's vote | bonds | `rates` |
| 2026-08-01 the yen did not turn | USD/JPY | `fx` |
| 2026-06-14 The Dollar at the 100 Line | dollar | `fx` |
| 2026-06-09 The Weekly Tape, June 9 | macro | `macro` |
| 2026-06-11 No Tape to Read | — | `softs`, **`--no-chart`** |

"No Tape to Read" has no chart card, so it gets the motif and the type without a band. That is
also what the piece is about.

Two posts share `fx` and two share `macro`. Their cards still differ, because the price action
does — except "No Tape to Read", which has none, and is the one card in the run that is motif
and type alone.

The two Dow pieces are split across `equities` and `macro` on purpose: both would otherwise
take the trading floor, and adjacent strand rows carrying the same photograph read as a
duplication bug rather than as a series. Where the pool allows a defensible second choice, the
assignment takes it.

## Hard constraints (unchanged)

- **Public repo:** no dashboard source, installers or releases. Cards carry no such reference.
- **Zero third-party requests on content pages.** Cards are committed local files; nothing is
  fetched at render time.
- **No file outside this repo is written.** `$CH_CONTENT` is read-only here.
- **No paid image generation.** The pool is what exists.
- **`_data/fx.json` and the Ledger posts are untouched.**
- `CNAME` intact; `css_version` bumped.

## Testing

1. `ops/website-build.sh` clean — post count, leaks, CNAME, sitemap, feed, broken refs.
2. `.preview/check-front.py` — its existing seven groups, plus: every Weekly Tape post's
   `image:` resolves to a `title.png` that exists, and its `.webp` twin exists too.
3. **The cover's lead shows a title, not a cropped-off one.** Assert the rendered lead figure
   uses `aspect-ratio: 16/9`, and check by eye at 1280 that the headline inside the card is
   fully visible — the failure this change exists to prevent is a crop that eats it.
4. Screenshots at 1280 / 900 / 375 in both editions. The card must need no dimming in dark —
   if it looks wrong there, the recipe is too bright, not the CSS.
5. Share preview: `og:image` of one Tape post points at the title card PNG.

## Non-goals

- No change to the Ledger's cards or to the nightly bot. A future Tape post gets its card by
  running the script; nothing generates one automatically.
- No new motifs, no paid generation.
- No change to `/fx/`, `/dashboard/`, `/about/`, the hubs, the legal pages or the rail.
- No retrofit of Ledger posts, ever — the two editions look different on purpose.
