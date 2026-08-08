# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **blog** for ChartHorizon — "The Weekly Tape" — served at **chart-horizon.com**.
A **Jekyll** site (the GitHub Pages default SSG), deployed from `main` via
`.github/workflows/deploy-pages.yml`, which runs a real `jekyll build` in CI and publishes
the result. The custom domain is pinned by `CNAME` (`chart-horizon.com`); DNS lives at
Cloudflare (DNS-only).

It was split out of the private ChartHorizon dashboard repo. **The hard constraint:** this
repo is **public**, so the site must **not** expose the dashboard's **source** — no links to
its private repo or code. The dashboard *product* is positioned as a downloadable
**local-first app** (installs on your machine, runs in your browser): the `/dashboard/` page
may describe it and, once ready, offer the installer/download here. Apart from that download,
outbound links stay support/social only.

> History: this repo started as a standalone dark marketing landing page. It was converted
> into the blog; the homepage is now the post list and the old landing page was retired.

## Publishing a post (the core workflow)

1. Add `_posts/YYYY-MM-DD-slug.md` with front matter: `layout: post`, `title`, `date`,
   optional `subtitle` (shown as the dek and as the index excerpt), and `cards` (the
   image base path). Optional `edition:` overrides the masthead section shown in the
   index/archive dateline; without it `_includes/edition.html` derives it from the title
   ("Hedgers' Ledger" if the title contains *Hedgers*, otherwise "Weekly Tape"). The post body is **only** the article — the `post` layout supplies
   the `<h1>`, the dek, and the trailing educational/risk disclaimer automatically.
   Optional **SEO-only** front matter (never shown on-page, just feeds `<head>` meta — see
   "SEO" below): `seo_title` (keyword-rich `<title>`/`og:title`), `description` (search meta
   description, overrides `subtitle`), `image` (social-share image, abs path under `/assets/...`),
   `image_alt`. Without `image`, the site default `og_image` (`_config.yml`) is used.
2. Put images under `assets/posts/<slug>/...` and reference them with the `cards` var,
   e.g. `![alt]({{ page.cards }}/wti_crude.webp)`. **In-body charts are WebP** (~67% smaller
   than the PNGs they replaced); only the card used as the OG `image:` keeps a PNG twin,
   because share-card crawlers are the one audience whose WebP support isn't worth betting
   on. The upstream bot does this automatically — `content/livermore/blog/publish.py`
   writes both and prunes the unused PNGs.
3. Commit + push to `main` → CI builds and deploys. The post appears at the top of the
   homepage list automatically. `permalink` is `/:year/:month/:day/:title/`.
   **The homepage shows the 10 most recent posts** and then links to `/archive/`; the
   Ledger publishes weekly, so an uncapped `site.posts` loop became a hundred-row ladder
   within a year. Everything older is on the archive page, grouped by year.

> **Bump `css_version` in `_config.yml` whenever you touch `assets/css/blog.css`.** It is
> the stylesheet's cache key. It used to be `site.time`, which made every daily FX push
> re-download the CSS for every returning reader.

## Architecture

- **`_layouts/default.html`** — the page shell for every page: `<head>` (self-hosted Newsreader
  `@font-face`/preload, favicon, cookieless Cloudflare Web Analytics beacon), the centred
  **broadsheet masthead** (inline horizon SVG mark + `CHARTHORIZON` wordmark + a
  `The Weekly Tape · Futures Desk` sub-line, closed by a 3px double rule, then a dateline row —
  nav **The Tape** (home) / **FX Map** (`/fx/`) / **Dashboard** (`/dashboard/`) /
  **About** (`/about/`) + edition date + Support pill), and the footer (risk disclaimer +
  Impressum/Datenschutz links).
- **`_layouts/post.html`** — wraps `default`, renders title/dek/content + the per-post
  disclaimer. **`index.html`** — `default` + the 10 most recent posts, each opened by an
  edition dateline (`_includes/edition.html`), then a "Back issues" link to `/archive/`.
- **`about.html`** (`/about/`) — the anonymous "About the Desk" page (`default` layout, normal
  indexed page): the four-signal method, the three editions, the not-advice stance, and the
  deliberate no-byline statement. Links only X (`@PlayLoneHand`) — support/social only, per the
  public-repo constraint. Gets an `AboutPage` JSON-LD branch in `default.html`.
- **`dashboard.html`** (`/dashboard/`, the **Dashboard** tab) — `default` layout, normal indexed
  page for the **local-first dashboard**: it installs on your machine and runs **in the browser**.
  Setting `dl_version` in the front matter is the single switch that flips the whole page from
  coming-soon copy to launched copy and derives the three platform download URLs from the GitHub
  release (see the comment block at the top of the file). **Currently launched at v1.1.3.**
  Two download affordances: a `.dl-top` release line set as dateline furniture directly under
  the masthead rule (above the fold — the page is ~5,300px and the foot is a fine place to *end*
  but a poor place to be the only one), and the full `.dl` platform block with first-run notes at
  `#download`. Editorial broadsheet treatment (centred `.kicker` + `.notice-head` + a `.dash-reads`
  chip strip of the four/five signals), reusing `.fx-chips`. Contact is X-only (`@PlayLoneHand`) —
  no email/waitlist, so **zero third-party requests** stays intact (no `privacy.html` change).
  Screenshots are the product imagery; still **no link to the dashboard source/repo**. Gets a
  `WebPage` JSON-LD branch in `default.html`.
- **`archive.html`** (`/archive/`) — every post grouped by year, with the same edition dateline as
  the index. Indexed, in the sitemap. **`404.html`** — broadsheet not-found page (`noindex`,
  `sitemap: false`); without it GitHub Pages serves its own GitHub-branded 404, on a site whose
  standing constraint is that it never points at its own repository.
- **`fx.html`** (`/fx/`, the **FX Map** tab) — `default` layout; renders ChartHorizon's daily
  FX currency-strength scoreboard (bias columns + neutral + pairs grid + interest-rate table)
  natively in the paper theme from **`_data/fx.json`**, interleaved with two **TradingView**
  widgets (ticker tape, economic calendar). See "The FX Map page" below.
- **`assets/css/blog.css`** is the single source of truth for the look — a cool-newsprint
  financial-broadsheet theme: tokens in `:root` (`--paper #f5f4f1`, `--ink #17150f`, gold
  `--gold #c8a24a`, `--rule-strong` for the masthead double rule, `--card`, `--bull`/`--bear`,
  hairlines, muted, quote bg, and `--measure` for the prose column). Three rules worth knowing
  before editing it: **both** muted tones clear 4.5:1 on every surface they sit on (gold is
  2.19:1 on paper — never body text, never a focus ring there); `:focus-visible` is one ink
  ring defined once, not per-component; and prose is capped at `--measure` (~72 chars/line)
  while figures, boards and tables break out to the full 760px sheet. Both layouts and the index pull from it, so the index and every
  page match. Type is **Newsreader**, self-hosted under `assets/fonts/` and declared via
  `@font-face` at the top of `blog.css` (preloaded in `default.html`), so the site still makes
  **zero third-party requests** on content pages — Georgia is the fallback.
- **`impressum.html` / `privacy.html`** are Jekyll pages on the shared `default` layout
  (front matter `lang: de`, `noindex: true`; `.legal` styles live in `blog.css`, so they
  match the light theme). The layout reads per-page `lang` and `noindex`. Their content is
  an unfilled German placeholder template (amber `[...]` `.ph` fields) — not real legal or
  contact info.
- **Third-party embeds fail loudly, not silently.** Privacy extensions and DNS filters block
  TradingView outright. `fx.html` probes for the widget frames after a grace period and toggles
  `.no-tv` on `<html>`; the CSS then hides the empty widget shells, reveals a first-party
  `.tv-fallback` note, and suppresses the "click a pair for its live chart" hint (the chart modal
  shows `.fx-modal-empty` instead of an empty frame). The probe keeps watching, so frames that
  arrive late undo the fallback. It runs off `DOMContentLoaded`, **not `load`** — a proxy that
  black-holes the request rather than refusing it never fires `load` at all.
- **Analytics ↔ privacy coupling:** two third-party scripts must stay disclosed in
  `privacy.html` — the cookieless Cloudflare beacon in `default.html` (loads on **every** page)
  in §3, and the **TradingView** widgets on `/fx/` (that **one** page only) in §6. Keep them in
  sync if you add/remove third-party scripts. (The Newsreader web font is **self-hosted** under
  `assets/fonts/`, not loaded from a CDN — so it adds no third-party request and needs no
  disclosure. Keep it that way.)

## The FX Map page (`/fx/`)

A second content surface besides the post list. It's a **hybrid**: ChartHorizon's own
"FX Strength & Pairs" scoreboard (bias columns, neutral row, top-6 bullish/bearish pairs,
filter-logic note, interest-rate table) rendered natively in the paper theme from a daily
snapshot, **interleaved** with two light-theme **TradingView** widgets (ticker tape, economic
calendar) that carry their own licensed live data — the strength read with a live FX price band
and the rate-decision calendar next to it.

- **Data**: `_data/fx.json` (`site.data.fx`) — `as_of`, `bullish`/`bearish`/`neutral` (currency +
  score + display `label`), `bullish_pairs`/`bearish_pairs` (top 6 each, with a `Bull/Bear ±x/12`
  label), `rate_table` (policy rate, central bank, instrument, rate-bias + tone, as-of), and the
  score scale. `fx.html` iterates it at build time; **the snapshot half is static daily, not
  live** (a public static site can't query the local dashboard) — the live half is the TradingView
  widgets.
- **Refresh (cross-repo — runs on the dashboard machine, NOT in this repo):** the private
  dashboard's daily job (`AUTO_UPDATE_CHARTHORIZON.command`, launchd ~23:30) calls
  `content_bot/fx_blog_push.command` → `content_bot/fx_blog_export.py`, which renders the real
  `forex.js` scoreboard headless, writes `_data/fx.json` here, and `git push`es it (only when the
  data actually moved) → CI rebuilds. So the FX numbers refresh once a day, hands-off. To edit the
  snapshot by hand, change `_data/fx.json`; the next dashboard run overwrites it.
- **TradingView = third-party scripts**, loaded only on this page → disclosed in `privacy.html`
  §6 (see the coupling note above). Constraint-safe: the page shows dashboard *output*, never
  links to dashboard source/installers/releases.
- It's a normal indexed page (no `noindex`/`sitemap:false`) → in `/sitemap.xml`, with its own
  `seo_title`/`description`. Not a post, so it's absent from `/feed.xml`.

## SEO

All hand-rolled in `default.html`'s `<head>` (no `jekyll-seo-tag` — its title logic fights the
`seo_title`/`subtitle` scheme), plus two `github-pages` plugins. Nothing here loads third-party
scripts, so the analytics↔privacy coupling is untouched.

- **Meta**: `<title>`, `description`, `canonical`, Open Graph + Twitter Card, and JSON-LD
  (`BlogPosting` on posts, `WebSite` on the home page) — all derived from one set of `meta_*`
  Liquid vars so they never drift. JSON-LD is inline metadata, not a script that runs.
- **Per-post knobs**: `seo_title`, `description`, `image`, `image_alt` (see "Publishing a post").
  Site-wide default share image: `og_image` in `_config.yml` → `assets/og-default.png`.
- **Plugins** (`_config.yml`, bundled with `github-pages`): `jekyll-sitemap` → `/sitemap.xml`,
  `jekyll-feed` → `/feed.xml`. `robots.txt` points crawlers at the sitemap. Pages with
  `sitemap: false` + `noindex: true` (impressum, privacy) stay out of both index and sitemap.
- **Search Console**: paste tokens into `google_site_verification` / `bing_site_verification`
  in `_config.yml`, then submit the sitemap in each provider's console. This is the step that
  actually gets the site crawled and indexed — the meta tags above only shape *how* it appears.

## Developing locally

A static server (`python3 -m http.server`) will **not** render Liquid/posts — you need
Jekyll. Requires Ruby ≥ 2.7 (macOS system Ruby 2.6 is too old for the `github-pages` gem):

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000, live reload
```

`Gemfile` pins the `github-pages` gem so local Jekyll matches what CI/GitHub Pages runs.
Keep `CNAME` intact on every change — removing it drops the custom domain.
