# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **blog** for ChartHorizon — "The Weekly Tape" — served at **chart-horizon.com**.
A **Jekyll** site (the GitHub Pages default SSG), deployed from `main` via
`.github/workflows/deploy-pages.yml`, which runs a real `jekyll build` in CI and publishes
the result. The custom domain is pinned by `CNAME` (`chart-horizon.com`); DNS lives at
Cloudflare (DNS-only).

It was split out of the private ChartHorizon dashboard repo. **The one hard constraint:**
this repo is **public**, so the site must **not** link to dashboard source, installers,
GitHub releases, or describe the dashboard as a public download. Outbound links stay
support/social only.

> History: this repo started as a standalone dark marketing landing page. It was converted
> into the blog; the homepage is now the post list and the old landing page was retired.

## Publishing a post (the core workflow)

1. Add `_posts/YYYY-MM-DD-slug.md` with front matter: `layout: post`, `title`, `date`,
   optional `subtitle` (shown as the dek and as the index excerpt), and `cards` (the
   image base path). The post body is **only** the article — the `post` layout supplies
   the `<h1>`, the dek, and the trailing educational/risk disclaimer automatically.
   Optional **SEO-only** front matter (never shown on-page, just feeds `<head>` meta — see
   "SEO" below): `seo_title` (keyword-rich `<title>`/`og:title`), `description` (search meta
   description, overrides `subtitle`), `image` (social-share image, abs path under `/assets/...`),
   `image_alt`. Without `image`, the site default `og_image` (`_config.yml`) is used.
2. Put images under `assets/posts/<slug>/...` and reference them with the `cards` var,
   e.g. `![alt]({{ page.cards }}/wti_crude.png)`.
3. Commit + push to `main` → CI builds and deploys. The post appears on the homepage list
   automatically (it iterates `site.posts`). `permalink` is `/:year/:month/:day/:title/`.

## Architecture

- **`_layouts/default.html`** — the page shell for every page: `<head>` (system-serif type,
  favicon, cookieless Cloudflare Web Analytics beacon), the brand header (inline horizon SVG
  mark + wordmark + a two-item nav — **The Tape** (home) / **FX Map** (`/fx/`) — + tagline),
  and the footer (risk disclaimer + Impressum/Datenschutz links).
- **`_layouts/post.html`** — wraps `default`, renders title/dek/content + the per-post
  disclaimer. **`index.html`** — `default` + the `site.posts` list.
- **`fx.html`** (`/fx/`, the **FX Map** tab) — `default` layout; renders ChartHorizon's daily
  FX currency-strength scoreboard natively in the paper theme from **`_data/fx.json`**, then
  embeds two **TradingView** widgets (ticker tape + forex cross-rate matrix). See "The FX Map
  page" below.
- **`assets/css/blog.css`** is the single source of truth for the look — a light "paper"
  editorial theme (palette + serif type lifted from the original post preview): tokens in
  `:root` (`--paper #fbfaf7`, `--ink #1a1814`, gold `--gold #c8a24a`, hairlines, table tans,
  muted, quote bg). Both layouts and the index pull from it, so the index and every post
  match. No web fonts (system `Iowan Old Style` → `Georgia` fallback).
- **`impressum.html` / `privacy.html`** are Jekyll pages on the shared `default` layout
  (front matter `lang: de`, `noindex: true`; `.legal` styles live in `blog.css`, so they
  match the light theme). The layout reads per-page `lang` and `noindex`. Their content is
  an unfilled German placeholder template (amber `[...]` `.ph` fields) — not real legal or
  contact info.
- **Analytics ↔ privacy coupling:** two third-party scripts must stay disclosed in
  `privacy.html` — the cookieless Cloudflare beacon in `default.html` (loads on **every** page)
  in §3, and the **TradingView** widgets on `/fx/` (that **one** page only) in §6. Keep them in
  sync if you add/remove third-party scripts.

## The FX Map page (`/fx/`)

A second content surface besides the post list: ChartHorizon's **FX Strength Map** — the
dashboard's "FX Strength & Pairs" scoreboard (which of the eight majors lean bullish/bearish,
the high-conviction pairs) rendered natively in the paper theme, plus live **TradingView**
widgets (ticker tape + forex cross-rate matrix, light theme).

- **Data**: `_data/fx.json` (`site.data.fx`) — `as_of`, `bullish`/`bearish` (currency + score),
  `bullish_pairs`/`bearish_pairs`, and the score/threshold scale. `fx.html` iterates it at build
  time; **the page is a static daily snapshot, not live** (a public static site can't query the
  local dashboard).
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
