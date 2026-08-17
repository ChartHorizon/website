# Front Page — "Real Broadsheet Cover"

**Date:** 2026-08-17
**Status:** Approved (pending spec review)
**Surface:** chart-horizon.com — the home page, plus two new section hubs

## Goal

Turn the home page from a single ruled ladder of ten posts into an actual front page: a lead
story with a picture, the two editions as separate strands, and a right-hand rail carrying the
FX standing and the dashboard. Today the site has four content surfaces and the home page shows
exactly one of them.

A second, non-cosmetic goal rides along. Search Console shows 15 of 22 URLs at "discovered,
currently not indexed" against **1 backlink**. Authority is the real bottleneck and no markup
buys it — but thin internal linking is the half that *is* controllable, and today an older post
hangs off `/archive/` and "Elsewhere in the paper" alone. Two topical hubs plus a front page
carrying more than ten links is the missing structure.

## Resolved design decisions (from brainstorming)

| Decision | Choice |
|---|---|
| What "more" means | **Real front page** (vs denser list / data-first / product-first) |
| Grid | **Home only widens to ~1080px**; masthead, footer and every other page stay 760px |
| Blocks | Lead + two strands + **FX rail** + **dashboard block**. No method box. |
| Editions | **Split into two strands**, not one mixed list |
| Structure | **Two new hubs** `/tape/` and `/ledger/`; nav unchanged at four items |
| Lead story | **Newest Weekly Tape**, with the newest Ledger beside it as second lead |
| Lead picture | Post card **cropped 2:1 from the top** (see "The picture" below) |
| Edition split | **Derived** from the existing `edition.html` rule (vs Jekyll categories) |

## Hard constraints (unchanged, must stay true)

- **Public repo:** no link to dashboard source, installers or releases. The dashboard block on
  the front page links to `/dashboard/` and nothing else. No download button while
  `dl_version` is empty — every `releases/download/…` URL currently 404s.
- **Zero third-party requests on content pages.** The front page adds none: the FX rail renders
  from `_data/fx.json` at build time, the plate is a local WebP. `privacy.html` needs no edit,
  and the analytics↔privacy coupling is untouched.
- **Single source of truth for the look:** `assets/css/blog.css`. New front-page components go
  there, reusing existing tokens and existing dateline styles.
- **Data pipeline:** `_data/fx.json` is written by the cross-repo dashboard job. We read it; we
  never change its shape. No change to any file outside this repo — in particular
  `content/livermore/blog/publish.py` and the nightly Ledger bot stay untouched.
- **No post front matter changes.** Every existing post and every future generated post must
  land in the right strand with no edit.
- Keep `CNAME` intact. Bump `css_version`.

## Architecture

All work is Liquid + CSS. No new build step, no plugin, no JavaScript.

### 1. The edition key (`_includes/edition.html`)

`edition.html` already resolves a post's masthead section — explicit `edition:` front matter
wins, otherwise a title containing *Hedgers* means Ledger, everything else is Weekly Tape.
`_layouts/post.html` already compares those captured strings to keep "Elsewhere in the paper"
inside one section, so the pattern is proven here.

The include gains one optional parameter so the same rule can produce a machine key instead of
a display name:

```liquid
{% include edition.html post=p %}          → "Hedgers&rsquo; Ledger" | "Weekly Tape"  (unchanged)
{% include edition.html post=p key=true %} → "ledger" | "tape"
```

One file, one rule, two renderings. Comparing display strings across files would couple callers
to an HTML entity (`&rsquo;`) — the key exists to avoid exactly that.

Membership is then tested with the pattern `post.html` already uses:

```liquid
{%- capture k %}{% include edition.html post=p key=true %}{% endcapture -%}
{%- if k == 'ledger' -%}…{%- endif -%}
```

Rejected alternative: real Jekyll categories. Cleaner data model, but it needs front matter in
all 18 posts *and* a change to the generator in the outer monorepo — a cross-repo edit for no
visible gain. Revisit only if a third edition ever appears.

### 2. Widening the shell (`_layouts/default.html`, `blog.css`)

The shell takes its class from page front matter, not from a URL test:

```liquid
<body{% if page.wide %} class="wide-page"{% endif %}>
<main id="main"{% if page.wide %} class="wide"{% endif %}>
```

`index.html` sets `wide: true`. The **body** class is load-bearing: the 760px cap lives on
`body` (`blog.css:68`), not on a wrapper, so `main.wide` alone would do nothing. The CSS lifts
the cap on `body.wide-page`, hands 760px back to `.site-head` and `.site-foot`, and gives
`main.wide` 1080px. Every other page renders a byte-identical `<body>` tag. The masthead and
footer keep their narrow measure, so the cover deliberately steps out from under a narrow head —
that is the broadsheet gesture, not an oversight.

### 3. The front page (`index.html`)

Markup order is also the mobile order, so no `order:` juggling is needed:

1. `.index-standfirst` — full width, unchanged copy.
2. `.front-grid` — CSS grid, `minmax(0,1fr) 300px`, `gap: 48px`.
   - **Main column:** lead, second lead, then `.strands`.
   - **Rail:** FX block, dashboard block.

Selection runs as two passes over `site.posts` (newest-first), one per edition, each with its
own counter: item 1 becomes that edition's lead, items 2–5 become that strand's rows, and the
loop breaks at 6. Nothing can appear twice because a post has exactly one key.

- **Lead** — newest `tape` post: figure (see below), edition dateline, `<h2>` headline,
  `subtitle` as dek.
- **Second lead** — newest `ledger` post: same dateline, smaller headline, dek, no picture,
  separated by a hairline.
- **Strands** — two columns below, headed `The Weekly Tape` and `Hedgers' Ledger` with the
  existing `.section-rule` treatment. Each row is dateline + headline, **no dek**: that is what
  makes eight entries fit the height four take today. Each column ends in its hub link.
- Below the grid, the existing `Back issues →` link to `/archive/` stays.

Post count on the cover stays 10 — the same as today, reorganised and roughly half the height.

### 4. The picture

Cards are 1200×1036, nearly square. At the main column's ~700px that is a ~600px-tall lead that
pushes the strands and the whole rail below the fold — the opposite of the point. So the lead
figure is a fixed **2:1 box**, `object-fit: cover; object-position: top`: the price panel with
its title and header row shows, the COT and calendar-spread panels below are cropped away. The
full four-panel chart is one click into the article, where it belongs.

Source is the WebP twin of the lead post's OG card, derived inside the loop as
`lead.image | replace: '.png', '.webp'` (~48 KB against 153 KB for the PNG). `publish.py`
writes both by design; spot-checked on two post directories, and test 3 below checks the
current lead's twin on every build.

**Fallback:** if the lead's `image` is missing or equals the site default `og_image`
(`/assets/og-default.png` — one post, 2026-06-11, is in that state), the lead renders **without
a figure** rather than showing a placeholder logo. The strands and rail move up accordingly.

`width`/`height` on the `<img>` plus the fixed `aspect-ratio` on the box means no layout shift.
The lead image loads eagerly — it is above the fold.

### 5. The FX rail (`_data/fx.json`)

Static, build-time, first-party:

- `as_of` as a small dateline ("FX standing · Aug 16, 2026").
- Top three from `bullish` and top three from `bearish` as chips, reusing the existing
  `.fx-chips` component and the `--bull` / `--bear` tokens.
- The leading pair: first entry of `bullish_pairs` with its `label` ("AUD/JPY · Bull +7.1/12").
- Link: `The full FX map →` to `/fx/`.

The snapshot is refreshed nightly by the cross-repo job, so the rail ages exactly as `/fx/`
does. If `site.data.fx` is absent or empty the whole block is skipped rather than rendering an
empty shell.

### 6. The dashboard block

`{% include board.html plate="board-screener" … %}` — the include already emits both editions of
the plate and the CSS already shows one per theme, so a dark-edition reader gets the dark board
rather than a dimmed photograph of the light one, and `loading="lazy"` on the hidden one means
only one is ever fetched. Two sentences of copy, then `More about the dashboard →` to
`/dashboard/`. No download button, no release URL.

### 7. The hubs (`tape.html`, `ledger.html`)

Two new pages, `permalink: /tape/` and `/ledger/`, on the `default` layout at the normal 760px
measure — they are lists, not covers.

- Each renders its full edition run, newest first, in the same dateline markup the index and
  `/archive/` share.
- Each has its own `seo_title` / `description`, is indexed and lands in `sitemap.xml`
  automatically via `jekyll-sitemap`.
- Each ends with a link to `/archive/`.
- `/archive/` gains a line in its dek pointing at both hubs.
- `_layouts/post.html`'s foot gains a link to the post's **own** hub next to the existing
  "All back issues" link — derived from the edition key it already computes, so it costs no
  front matter. This is the change that gives every single post a link into a topical hub.

The nav bar stays at four items. Six wrap badly on a phone, and "The Tape" is the brand for the
whole paper, not for one strand.

### 8. Styling (`blog.css`)

New `/* Front page */` block. New classes: `.front-grid`, `.lead`, `.lead-figure`,
`.lead-second`, `.strands`, `.strand`, `.rail`, `.rail-fx`, `.rail-board`. Reused as-is:
`.post-dateline`, `.post-edition`, `.post-date`, `.post-link`, `.section-rule`, `.fx-chips`,
`.more-issues`.

Three house rules the new block must respect, all already documented in `CLAUDE.md`:

- Both muted tones clear 4.5:1 on every surface they sit on. Gold is 2.19:1 on paper — never
  body text, never a focus ring there.
- `:focus-visible` is one ink ring defined once, not per component. Add none.
- Prose stays capped at `--measure`; only figures, boards and tables break out.

**Dark edition:** the existing dimming rule at `blog.css:434` is scoped to `.post-body` and
`.board`. The lead card is neither, so the selector gains `.lead-figure` — otherwise a
white-backed chart card glares on the night press run.

**Breakpoints:** below 940px the rail moves under the strands (grid collapses to one column).
Below 640px the strands stack too, and `main.wide` is moot because the viewport is narrower
than 760px anyway.

## Files

| File | Change |
|---|---|
| `index.html` | rewritten — `wide: true`, front grid, leads, strands, rail |
| `tape.html` | **new** — `/tape/` hub |
| `ledger.html` | **new** — `/ledger/` hub |
| `_includes/edition.html` | `key=true` parameter |
| `_layouts/default.html` | `wide-page` on `body` and `wide` on `main`, both from `page.wide` |
| `_layouts/post.html` | hub link in the "Elsewhere in the paper" foot |
| `archive.html` | dek gains links to both hubs |
| `assets/css/blog.css` | front-page block, `main.wide`, dark-edition selector |
| `_config.yml` | `css_version` 5 → 6 |

Untouched: `CNAME`, `_redirects`, `robots.txt`, `privacy.html`, `impressum.html`, `fx.html`,
`dashboard.html`, `about.html`, `404.html`, `_data/fx.json`, every file in `_posts/`, and
everything outside this repo.

## Testing

`ops/website-build.sh` is the gate; a green build has never meant a correct one here, so the
checks below run on top of what it already verifies (post count, local-only leaks, CNAME,
sitemap, feed, broken internal refs, FX snapshot date).

1. **Build** with `ops/website-build.sh`, clean.
2. **No post is lost and none is duplicated:** the entries on `/tape/` plus those on `/ledger/`
   equal `site.posts` exactly, and no URL appears twice on the front page.
3. **The lead picture resolves:** the derived `.webp` path for the current lead exists in
   `_site/`; the fallback path renders figureless for a post whose `image` is the site default.
4. **The hubs are indexable:** `/tape/` and `/ledger/` present in `_site/sitemap.xml`, neither
   carrying `noindex`.
5. **Screenshots** at 1280 / 900 / 375 in **both** editions (`.preview/shot.mjs` against a
   static server on `_site/`) — checking that the rail collapses under the strands at 900, that
   nothing overflows horizontally at 375, and that the lead card is not glaring in dark.
6. **No new third-party requests:** the front page's network log contains the Cloudflare beacon
   and nothing else third-party.

## Non-goals

- No navigation change, no sixth nav item.
- No download button, no release URL, while the GitHub account stays flagged.
- No email capture, no waitlist, no third-party script, no JS on the front page.
- No change to `_data/fx.json`'s shape or to any file in the outer monorepo.
- No restyle of post pages, `/fx/`, `/dashboard/` or `/about/`. This is the cover and the two
  hubs, nothing else.
