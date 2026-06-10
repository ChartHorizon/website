# ChartHorizon Redesign — "Financial Broadsheet"

**Date:** 2026-06-10
**Status:** Approved (pending spec review)
**Surface:** chart-horizon.com — the "Weekly Tape" Jekyll blog + the `/fx/` FX Map page

## Goal

Re-skin the entire public site into a **cool-newsprint financial broadsheet** at an
"impeccable" quality bar, while changing **nothing** about behaviour, content, data flow,
SEO, analytics, or the public-repo constraint. The look should read like a real weekly
market letter from a futures desk: a centred masthead with double rules, the Newsreader
serif, a warm-grey newsprint stock, and the existing gold horizon mark as the single accent.

## Resolved design decisions (from visual brainstorming)

| Decision | Choice |
|---|---|
| Direction | **Financial Broadsheet** (vs refined paper / dark terminal / modern editorial) |
| Paper stock | **Cool Newsprint** `#f5f4f1` (vs FT salmon / warm cream) |
| Headline voice | **Newsreader** web font (vs system Georgia / Playfair Display) |
| Homepage | **Index** — clean ruled list (vs featured-lead front page) |
| Flourish | **Drop cap** on the first paragraph of each post — included |

## Hard constraints (unchanged, must stay true)

- **Public repo:** no links to dashboard source, installers, GitHub releases, or any
  description of the dashboard as a downloadable. Outbound links stay support/social only.
- **Single source of truth:** the look lives in `assets/css/blog.css`. Both layouts and
  every page pull from it.
- **Analytics ↔ privacy coupling:** third-party scripts must stay disclosed in `privacy.html`
  (Cloudflare beacon §3 on every page; TradingView §6 on `/fx/` only). **This redesign adds
  no new third-party requests** (see Font strategy), so `privacy.html` needs no edit.
- **Data pipeline:** `_data/fx.json` is written by the cross-repo dashboard job. We restyle
  how it renders; we never change the JSON shape or the Liquid that reads it.
- Keep `CNAME` intact.

## Architecture / approach

All work is **CSS + targeted template markup**, no new build steps, no JS, no plugins.

1. **`assets/css/blog.css`** — rewrite the `:root` tokens and the component rules to the
   broadsheet palette and Newsreader type. This is the bulk of the work and the single
   source of truth.
2. **`assets/fonts/`** (new) — self-hosted Newsreader variable `.woff2` (roman + italic),
   declared via `@font-face`.
3. **`_layouts/default.html`** — add the font `@font-face`/preload wiring in `<head>`;
   restructure the header into the centred broadsheet masthead + nav/dateline row; update
   `theme-color`. Footer markup lightly adjusted for the new styling.
4. **`index.html`** — minor markup so the post list renders as the ruled broadsheet index
   (dateline kicker + headline + excerpt). Logic (`for post in site.posts`) unchanged.
5. **`_layouts/post.html`** — one small markup change: wrap `{{ content }}` in
   `<div class="post-body">…</div>` so the drop cap can target the first *body* paragraph.
   (The dek is also a `<p>` inside `.post`, so a bare `.post > p:first-of-type` would wrongly
   hit the dek.) Title/dek/disclaimer otherwise restyle via `blog.css`.
6. **`fx.html`** — unchanged markup; its existing `.fx-*` classes get restyled in `blog.css`.
   Section headings (`<h2>`) gain the broadsheet section-rule treatment via CSS.

### Font strategy (important)

- **Self-host Newsreader**, do **not** call the Google Fonts CDN. Variable `.woff2` files go
  in `assets/fonts/`, declared with `@font-face` (`font-display: swap`) and a
  `<link rel="preload">` for the roman text weight.
- Rationale: a Google Fonts request is a third-party request that would need a `privacy.html`
  disclosure and erodes the cookieless posture. Self-hosting keeps **zero third-party
  requests on content pages** — coupling untouched, and fast.
- `--serif: 'Newsreader', Georgia, 'Times New Roman', serif`. Georgia remains the fallback so
  text is readable before the font swaps. Optical sizing: large `opsz` for headlines/masthead,
  text `opsz` for body. `--sans` (system) is retained for uppercase meta only.

## Design tokens (`:root`)

```
--paper      #f5f4f1   /* cool newsprint stock */
--ink        #17150f   /* warm near-black */
--gold       #c8a24a   /* accent — unchanged */
--gold-ink   #9a7b27   /* accent text/links — unchanged */
--rule       #ddd9d0   /* hairlines */
--rule-strong #17150f  /* masthead double rule = ink */
--thead      #ecebe6   /* table headers */
--muted      #6b6356   /* secondary text */
--muted-2    #857f74   /* uppercase meta */
--quote-bg   #efede7   /* blockquote / chip tint on newsprint */
--card       #fbfbf9   /* FX card surface */
--bull       #3f7d52   /* re-tuned for newsprint contrast */
--bear       #a8503f
--serif      'Newsreader', Georgia, 'Times New Roman', serif
--sans       -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
```

## Components

### Masthead & header (`default.html` + `.site-head`)
- Centred: gold horizon mark + `CHARTHORIZON` wordmark; beneath it the tagline line
  `THE WEEKLY TAPE · FUTURES DESK` in uppercase letterspaced `--sans`; closed by a **3px
  double rule** in `--rule-strong`.
- A thin nav/dateline row under the rule: nav (**The Tape** → `/`, **FX Map** → `/fx/`,
  with `.active` state) on the left; the site build date (`'now' | date`) on the right; the
  **Support** (Buy Me a Coffee) pill preserved on this row.
- Responsive: tagline hides < 560px; wordmark hides < 430px (as today). The masthead stays
  centred and legible at every width.

### Homepage index (`index.html` + `.post-list`)
- Masthead → `The Weekly Tape` heading + dek → hairline-ruled list. Each row: gold uppercase
  **dateline**, Newsreader headline (hover → gold-ink), muted excerpt from `subtitle`.
- Even rule weight between items (the "clean index" option, not a featured lead).

### Post layout (`post.html` + article CSS)
- Single column, ~720px measure for comfortable Newsreader reading. Bold Newsreader title,
  italic muted dek, `h2` section heads separated by hairline rules.
- **Drop cap:** `.post-body > p:first-of-type::first-letter` — a Newsreader gold/ink drop cap
  (~3 lines tall, `float:left`). Targeting `.post-body` (the wrapper around `{{ content }}`)
  rather than `.post` keeps it off the dek; if the first body block is an image rather than a
  paragraph the rule simply doesn't match, which is the desired fallback.
- Images, blockquotes (gold left-rule on `--quote-bg`), tables, `hr` restyled to the palette.
- Trailing disclaimer stays in small `--sans`.

### FX Map (`fx.html` — CSS only)
- `.fx-*` board/columns/chips/neutral/pairs/method/rate-table restyled to newsprint tokens;
  bull/bear use `--bull`/`--bear`. Cards use `--card` + hairline borders.
- `<h2>` section heads ("Interest rates", "Economic calendar") get the broadsheet
  section-rule treatment (uppercase label + hairline) consistent with the rest of the page.
- TradingView ticker + calendar keep `colorTheme:"light"`; verify they sit correctly on the
  cooler stock (transparent backgrounds already let `--paper` show through).

### Footer & legal
- `.site-foot` restyled to the palette (risk disclaimer + © + Impressum/Datenschutz links).
- `impressum.html` / `privacy.html` inherit all tokens automatically via `.legal`; placeholder
  content and `noindex`/`sitemap:false` behaviour untouched.

## Explicitly unchanged

Post publishing workflow and front-matter knobs; `_data/fx.json` shape and cross-repo refresh;
all Liquid logic; SEO meta / JSON-LD / canonical scheme; sitemap, feed, robots; Cloudflare
analytics; TradingView embeds and their privacy disclosure; `CNAME`; all on-page copy; the FX
number snapshot.

## Testing / verification

- `bundle exec jekyll build` succeeds with no errors.
- Visual check via the running site (Playwright/local serve): homepage index, a post (drop cap
  renders once, only on the first text paragraph), and `/fx/` (board + rate table + both
  TradingView widgets) at desktop (~1000px), tablet (~560px), and mobile (~400px) widths.
- Confirm **no new third-party network requests** appear on content pages (only the existing
  Cloudflare beacon site-wide and TradingView on `/fx/`); the font loads from `assets/fonts/`.
- Confirm masthead, nav active-states, and the Support pill behave at all breakpoints.

## Out of scope (not in this change)

- Regenerating `assets/og-default.png` to match the new look (optional follow-up).
- Any change to the dashboard repo or the FX export script.
- New pages, new nav items, or content rewrites.
