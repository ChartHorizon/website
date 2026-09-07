# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The **blog** for ChartHorizon — "The Weekly Tape" — served at **chart-horizon.com**.
A **Jekyll** site (the GitHub Pages default SSG). The custom domain is pinned by `CNAME`
(`chart-horizon.com`); DNS lives at Cloudflare.

> **The site deploys to Cloudflare Pages, and only there.** Nothing about a `git push`
> publishes anything — not to GitHub, not anywhere. **Publishing is `ops/website-build.sh
> --from-head && ops/website-deploy.sh`** (project `charthorizon`), and if you did not run
> those two commands, the change is not live no matter how green the commit looks. See
> "Publishing a post" and "Developing locally".
>
> Deployment moved off GitHub on 2026-08-15, when the ChartHorizon account was flagged: every
> repo, release and the Pages site began returning 404 to logged-out visitors while still
> looking normal to the signed-in owner, so the site went dark. **As of 2026-08-21 the operator
> does not intend to go back**, so treat Cloudflare as the permanent home rather than a
> stopgap — do not offer the GitHub path as the "real" one being restored later.
> `git push` to GitHub still works and is still worth doing **as a backup**; it just is not a
> deployment. `.github/workflows/deploy-pages.yml` is dead weight kept only as a record.
> Apex and `www` are **proxied** CNAMEs to `charthorizon.pages.dev` (the zone used to be
> DNS-only); the old GitHub A records (185.199.108-111.153) are gone and stay gone.

It was split out of the private ChartHorizon dashboard repo. **The hard constraint:** this
repo is **public**, so the site must **not** expose the dashboard's **source** — no links to
its private repo or code. The dashboard *product* is positioned as a downloadable
**local-first app** (installs on your machine, runs in your browser): the `/dashboard/` page
may describe it and, once ready, offer the installer/download here. Apart from that download,
outbound links stay support/social only — with one further exception since 2026-09-06:
**`/resources/` links out to third-party educational material** (see the `resources.html`
bullet under "Architecture"). That is a reading list, not a change to the constraint: the rule
is about never exposing the dashboard's *source*, which nothing on that page does.

> History: this repo started as a standalone dark marketing landing page. It was converted
> into the blog and the old landing page was retired; the homepage became a plain post list,
> and on 2026-08-17 that list became the broadsheet cover described under "Architecture".

## Publishing a post (the core workflow)

1. Add `_posts/YYYY-MM-DD-slug.md` with front matter: `layout: post`, `title`, `date`,
   optional `subtitle` (shown as the dek and as the index excerpt), and `cards` (the
   image base path). Optional `edition:` overrides the masthead section shown in the
   index/archive dateline; without it `_includes/edition.html` derives it from the title
   ("Hedgers' Ledger" if the title contains *Hedgers*, otherwise "Weekly Tape"). Callers that
   need to compare editions rather than display them — the cover's lead/strand selection, the
   two hubs — call `edition.html` with `key=true`, which returns the machine key `tape`/`ledger`
   instead: the display name carries an HTML entity (`&rsquo;`) no caller should have to spell
   to match on. The post body is **only** the article — the `post` layout supplies
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

   Weekly Tape posts also get a **title card**: `docs/title_card.py` composites a dark
   photographic motif (`--motif`) with the week's price action drawn across it
   (`--chart`; `--no-chart` for a post without one) and the headline set into the image,
   1280×720. The motifs themselves live in the private content repo, resolved through
   `$CH_CONTENT` — only the finished card is committed here. That card becomes the post's
   `image:`, and therefore its share image and its cover lead figure. It's written as
   `title.jpg` (q86, the WebP-incompatible-crawler twin) + `title.webp` (what the page
   loads) — **JPEG, not PNG**, because a title card is a photograph and PNG's lossless
   encoding mostly buys size for grain it doesn't need to keep (the nine cards ran 8.5MB
   as PNG, 1.1MB as JPEG at q86). The **chart cards** under `assets/posts/*/cards/` stay
   **PNG**: they're flat line art (solid fills, hard edges, text), which is what PNG is
   actually for and where JPEG would add ringing around every line for no size win. The
   **Hedgers' Ledger deliberately keeps its chart card** instead of a title card, so the
   two editions read as visibly different at a glance.

   A Tape post **may point `image:` at one of its own chart cards instead** (2026-08-18
   "Funded in Euros" does, at `cards/jpy_cot.png`). The cover then renders that lead
   **uncropped** — see `.lead-figure-plate` under "Architecture" — and the post must carry
   `image_w`/`image_h`, because only a title card has a shape the template can assume.
   Doing it costs the edition contrast above, so it is a per-post decision, not a default.
   Note the share card is unchanged by any of this: X and Facebook crop a near-square plate
   to ~1.91:1 from the centre, which loses the card's own headline — the Ledger has always
   shared this way, so a chart-card Tape lead is consistent with it, not a new problem.
3. **Commit** the post, then publish with `ops/website-build.sh --from-head &&
   ops/website-deploy.sh`. Committing is what makes it live: `--from-head` builds the
   committed tree, not the working tree, precisely so the drafts `publish.py` stages into
   `_posts/` are not published the moment they are written. (The nightly `ops/daily-update.sh`
   runs the same two commands, so a committed post also goes out on its own that evening.)
   A `git push` is backup only — it deploys nothing, so it never substitutes for the two
   commands above. "Committed and pushed" is not "published".
   The post appears on the cover automatically, as a lead if it is the newest of its edition
   or a strand row otherwise.
   `permalink` is `/:year/:month/:day/:title/`.
   **The cover shows ten post links, not simply the ten most recent**: two derived leads (the
   newest Weekly Tape, the newest Hedgers' Ledger) plus four more of each edition in the
   strands below — capped so the Ledger's weekly cadence can't turn an uncapped `site.posts`
   loop into a hundred-row ladder within a year. Everything older is on the archive page,
   grouped by year.

> **Bump `css_version` in `_config.yml` whenever you touch `assets/css/blog.css`.** It is
> the stylesheet's cache key. It used to be `site.time`, which made every daily FX push
> re-download the CSS for every returning reader.

## Architecture

- **`_layouts/default.html`** — the page shell for every page: `<head>` (self-hosted Newsreader
  `@font-face`/preload, favicon, cookieless Cloudflare Web Analytics beacon), the centred
  **broadsheet masthead** (inline horizon SVG mark + `CHARTHORIZON` wordmark + a
  `The Weekly Tape · Futures Desk` sub-line, closed by a 3px double rule, then a dateline row —
  nav **The Tape** (home) / **FX Map** (`/fx/`) / **Dashboard** (`/dashboard/`) /
  **Resources** (`/resources/`) / **About** (`/about/`) + edition date + Support pill), and the footer (risk disclaimer +
  Impressum/Datenschutz links). A page widens to 1080px by setting `wide: true` in its front
  matter — today only `index.html` does. The layout puts `wide-page` on `<body>` and `wide` on
  `<main>`; the 760px cap lives on `body` (`assets/css/blog.css`), not on a wrapper, so a class
  on `main` alone would do nothing, and the CSS lifts the cap there and hands it back to
  `.site-head`/`.site-foot`, which stay at 760px so the masthead and footer read as the same
  narrow paper while the cover steps out from under them.
- **`_layouts/post.html`** — wraps `default`, renders title/dek/content + the per-post
  disclaimer, then the **"Elsewhere in the paper"** block: 4-6 links to other editions, all
  derived, so no post needs front matter. It exists for crawling — before it, a post was
  reachable only from the home page (10 most recent) and `/archive/`, and Google left 15 of
  22 URLs at "discovered, currently not indexed". Two rules there are load-bearing and
  commented in place: picks walk **down** the run from the current post (taking the section's
  three newest instead skews inbound links 8-9 on new posts against 1-2 on old ones — the
  opposite of the point), and they render in a final pass over `site.posts` so the list still
  reads newest-first. Rows come from `_includes/post-teaser.html`, which reuses the index and
  archive dateline markup. Verify changes by rendering, not by eye — see "Developing locally".
- **`index.html`** — the cover: `default` layout with `wide: true`. A lead story (the newest
  Weekly Tape, usually shown as its **title card** — a dark photographic motif with the
  market's own price action drawn across it and the headline set into the image, cropped to
  16:9) and a
  second lead (the newest Hedgers' Ledger, no picture), then the two editions as side-by-side
  strands of four headlines each, each strand ending in its own hub link, then a rail carrying
  the FX standing from
  `_data/fx.json`, a dashboard plate, and an **"On video"** card from `_data/videos.yml`
  (newest entry only). That card is a **link, never an embed**: its still is a copy committed
  under `assets/video/<id>.webp`, because an iframe — or even a thumbnail pulled from
  `i.ytimg.com` — would put Google on the most-visited page of a site whose standing promise
  is zero third-party requests, and would make `privacy.html` wrong. `videos.yml` is
  hand-maintained; the upload pipeline records no video ids anywhere to read from.
  The lead is the newest *Tape*, not simply the newest
  post: the Ledger publishes automatically every week, and as a permanent lead it would bury
  the written notes under a headline that is just a date. Ten post links total (2 leads + 4 +
  4); a "Back issues" link closes the page to `/archive/`.
  **The lead picture is a link to its own story** — readers click the picture before the
  headline, and a cover plate that goes nowhere is a dead target. It is a plain `<a>`, not
  the `aria-hidden`/`tabindex="-1"` decoration trick usually used for a link that repeats the
  headline beneath it, because `image_alt` describes a chart with real numbers in it and
  hiding the link would take that away from screen readers to save one tab stop.
  **`.lead-figure-plate`**: when the lead's `image:` is a chart card (path contains
  `/cards/`) the 16:9 crop is dropped and the card renders whole. A title card is *built* to
  be cropped — headline in the lower half, motif carrying the rest — but a chart is read, and
  cropping one cuts the data (on the COT card the cut severed the bar pane mid-annotation and
  left a leader line pointing at nothing). Such a post carries `image_w`/`image_h` so the
  browser can still reserve the space; a title card needs no front matter, being always
  1280×720.
- **`tape.html`** / **`ledger.html`** (`/tape/`, `/ledger/`) — one hub per edition: that
  edition's full run, grouped by year, reusing `/archive/`'s list markup. **An edition can have
  an empty run** — the Ledger did from 2026-08-30, when the eleven old releases were retired
  (they 301 to `/ledger/` from `_redirects`, spelled out date by date because the bot reuses the
  `hedgers-ledger` slug every week), until the first issue of the reworked edition. Both places
  that would otherwise render a heading over nothing carry a state for it: the hub shows
  `.hub-empty` saying why, and the cover puts `strands-single` on `.strands` so the Tape strand
  takes the full width instead of leaving a headed empty column. `lead_ledger == nil` is the
  has-any test — it is the newest post of the whole run.
  The hubs exist because Google left 15 of 22 URLs at "discovered, currently not indexed" and
  thin internal linking was the half of that problem fixable here — every post's foot
  (`_layouts/post.html`) now links its own hub, and so does the cover's matching strand.
  Since 2026-08-30 a Ledger post carries a second half, **"The hedging program"**, from the
  upstream generator (`content/livermore/blog/hedgeboard.py`). It reports the **change, not the
  state**: one `.program-board` table listing only the markets whose COT net crossed the midpoint
  of its own trailing six-month range with that week's report, then a card and a fact paragraph
  per turn. It shipped for one afternoon as nine per-category tables covering all 39 markets and
  was cut the same day — a reader cannot act on 37 unchanged rows, and the two with news in them
  were findable only by scanning a `Turned` column that is empty in every cell on a quiet week.
  The fixed column geometry stays (a week's longest market name would otherwise set the header
  width and make it jump between issues), but the widths are now 34/36/30, not 44/40/16: both
  right-hand columns carry a phrase now, and at 16% the last one wrapped its own heading.
  A week with **no** turn keeps the section and says so in a line — the whole-board counts are
  there anyway, and a half that vanishes without visible cause reads as a bug.
  The turn cards are **not** the extremes cards: they are shot at `range=6m` with the hedging
  overlay ON, because that overlay is range-relative and only at 6M is its midpoint the one the
  verdict comes from. Hence `prog_<key>.webp` alongside `<key>.webp` — a market can be an extreme
  and a turn in the same issue, and the two pictures are not the same picture.
- **`about.html`** (`/about/`) — the anonymous "About the Desk" page (`default` layout, normal
  indexed page): the three-signal method, the three editions, the not-advice stance, and the
  deliberate no-byline statement. Links only X (`@ChartHorizon`) — support/social only, per the
  public-repo constraint. Gets an `AboutPage` JSON-LD branch in `default.html`.
- **`dashboard.html`** (`/dashboard/`, the **Dashboard** tab) — `default` layout, normal indexed
  page for the **local-first dashboard**: it installs on your machine and runs **in the browser**.
  Setting `dl_version` in the front matter is the single switch that flips the whole page from
  coming-soon copy to launched copy and derives the three platform download URLs from `dl_repo`
  (see the comment block at the top of the file). **Live at v1.2.2 — macOS and Windows; Linux is still `"soon"`.**
  **The installers are hosted on Cloudflare R2, not in this repo and not on GitHub**, at
  `https://dl.chart-horizon.com/v<version>/`. They were on GitHub Releases until 2026-08-21,
  which the account flag turned into three 404s for every logged-out visitor — the page sat at
  coming-soon from 2026-08-15 for exactly that reason. Committing them here was never an option
  either: Cloudflare Pages refuses any file over 25 MiB and these are 34–71 MiB.
  Publish a new release with **`ops/website-installers.sh <version>`** in the monorepo (it pulls
  the assets, uploads them under an immutable versioned key, and verifies all three over HTTPS),
  **then** bump `dl_version`. That order is load-bearing — reversed, the page ships buttons
  pointing at objects that do not exist yet.
  Note `dashboard/tools/download-stats.py` counts *GitHub* release downloads and therefore stops
  seeing new ones; R2 has its own metrics in the Cloudflare dashboard.
  One download affordance, reachable from two places: the full `.dl` platform block at
  `#download`, and a `.dl-top` release line set as dateline furniture directly under the masthead
  rule that **jumps to it** (above the fold — the page is ~5,300px and the foot is a fine place to
  *end* but a poor place to be the only one). That line used to start the file itself and no
  longer does: the buttons carry the architecture each build is and the first-run notes for an
  unsigned one, and a reader who downloaded from up top arrived at neither. It is **one** link,
  not one per platform — three links with three names and one destination read as three different
  places to anyone tabbing or listening through them — with the platform names moved into the
  label beside it, derived from the same three URLs as the buttons.
  Each live button carries a `.dl-arch` line under its version (**macOS = Apple Silicon**, the dmg
  being arm64-only; **Windows = 64-bit (x64)**; Linux would be x86_64). The labels are hardcoded,
  not derived — a universal2 dmg or an arm64 exe would turn one into a lie — and coming-soon
  buttons deliberately carry none, so `.dl-btn` needs `justify-content:center` to keep the shorter
  card balanced. Note the Windows *setup* stub reports 32-bit (`file` says PE32/i386) as every
  Inno stub does; the payload is the x64 freeze, verified upstream by PE machine field `8664` on
  `dist\ChartHorizon\ChartHorizon.exe`, never on the `…-Windows-Setup.exe`.
  The `.dl-firstrun` disclosure is a card at `.dl-grid`'s own 440px so it lines up under the
  buttons as their fourth element rather than reading as a footnote; it stays collapsed by
  default. Editorial broadsheet treatment (centred `.kicker` + `.notice-head` + a `.dash-reads`
  chip strip of the four/five signals), reusing `.fx-chips`. Contact is X-only (`@ChartHorizon`) —
  no email/waitlist, so **zero third-party requests** stays intact (no `privacy.html` change).
  Screenshots are the product imagery; still **no link to the dashboard source/repo**. Gets a
  `WebPage` JSON-LD branch in `default.html`.
  **Every plate exists twice** — `board-<name>.webp` and `board-<name>-dark.webp` — because the
  app has a dark theme of its own and a dimmed light screenshot is not it. `_includes/board.html`
  emits both `<img>`s and `blog.css` shows one per edition; `loading="lazy"` on a `display:none`
  image never fires, so a reader still downloads exactly one set. Regenerate them with
  **`ops/website-plates.sh`** in the monorepo (the dashboard must be serving on :8000) — it
  shoots both editions from one session at one viewport and refuses to finish if the pair comes
  out at different pixel sizes, because the page swaps between them on a click and any drift in
  data or framing reads as a jump. Never hand-replace one edition on its own.
- **`resources.html`** (`/resources/`, the **Resources** tab) — "The Reading Room": outside
  material that explains the mechanics behind the desk's signals, added 2026-09-06. `default`
  layout, normal indexed page, `CollectionPage` JSON-LD branch in `default.html` — which
  since 2026-09-07 carries a `mainEntity` `ItemList` of the entries, flattened across sections
  first so `position` runs continuously (a nested loop restarts it at every heading), plus a
  `dateModified` from the page's `last_modified_at`. That front-matter date is also the only
  thing that puts a `<lastmod>` on a standing page in `/sitemap.xml`: `jekyll-sitemap` derives
  one from a post's date but takes it from `last_modified_at` for a page, and this page says in
  print that it grows. **Bump it whenever `resources.yml` changes.**
  **All content comes from `_data/resources.yml`** — sections in file order, items in file
  order — so adding a resource is a YAML entry and no template change; that file's header
  comment documents every field. Two are optional and the template is written for their
  absence: `signal` (which of the desk's own lights the piece speaks to — Positioning,
  Hedging program, Term structure, Rate bias — rendered in the gold slot of the same
  `.post-dateline` furniture the index and `/archive/` use, so an off-site link still reads
  as an entry in this paper) and `topics` (**omit it when the only topic would restate the
  title**; a bullet repeating the headline above it reads as a bug — `Importance of
  Multi-Asset Analysis` is the live example, and `take` carries that entry on its own).
  **`take` is optional to the template and mandatory in practice** (added 2026-09-07): the
  desk's own sentence or two on a piece, set in full `--ink` while every borrowed line around
  it — title, byline, source, topics — stays muted, which is the same distinction said
  visually. Without it the page is other people's titles wrapped around paid links, which is
  Google's own definition of a thin affiliate page and a named category in its spam policy,
  not a matter of taste; it also took `<main>` from 455 words to 848. Write one for every entry.
  A contextual inbound link lives in `about.html` under "The three lights" — the nav counts
  for crawling but is discounted, and this page had no other way in.
  **One link per item, the headline**, carrying a decorative `aria-hidden` `↗` — the same
  rule as `/dashboard/`'s download line: a second "watch it here" under the same headline is
  two names for one destination. That the links go to YouTube is said in *words*, in the
  section note, because an arrow is a hint and not a sentence.
  **Nothing here is embedded**, so the page still makes zero third-party requests (verified:
  origin + the two Cloudflare beacon hosts, nothing else) and `privacy.html` needs no change.
  Keep it that way — an embedded player would make §3/§6 wrong, the same trap `videos.yml`
  documents for the cover's "On video" card.
  **Paid links, since 2026-09-06.** The paid section ("The desk's shelf", three Amazon books)
  sits **first in the file and renders as a plate** — a commercial decision by the operator,
  not an editorial ranking, which is why the page says so in as many words (see the standing
  paragraphs below). `affiliate: true` and `featured: true` are **separate flags on purpose**:
  a section can be paid without being promoted, and the legal disclosure must never depend on
  the decoration. `affiliate: true` on a *section* marks every item in it —
  section-level so it cannot be forgotten on one entry. Two things follow and neither is
  styling: an "Affiliate link" chip prints **at the link**, because § 5a Abs. 4 UWG wants the
  commercial purpose recognisable there and not only in a note further up; and the link gains
  `rel="sponsored nofollow"`, which is Google's requirement for a paid link (without it the
  site is running undisclosed paid links and risks a manual action). Such a section's `note`
  must carry the Amazon Associates sentence **verbatim** — "As an Amazon Associate I earn from
  qualifying purchases." — which the Operating Agreement prescribes; do not paraphrase it. The
  chip is deliberately **not** gold: gold is the slot the desk's own signal sits in, and a
  disclosure wearing the accent colour reads as a recommendation. Its tone is `--muted`, not
  `--muted-2`, which measured exactly 4.50 on the chip ground — a legal notice does not sit on
  the AA floor.
  **Store redirection is Amazon's job, not this site's.** The links point at amazon.com and
  Amazon's own OneLink forwards visitors to their local marketplace, configured account-side
  (confirmed by the operator 2026-09-06). **Never embed the OneLink JavaScript widget** as the
  alternative — it is a third-party script on every page carrying it, and it would break the
  zero-third-party-request promise and make `privacy.html` §3 wrong for a redirect Amazon
  already performs for free.
  **Check the Associates tag before adding an Amazon link**: resolve the short link and read
  the tag out of the destination — **anchored**, because an Amazon search URL also carries
  `dib_tag=se` and an unanchored `grep -io 'tag=[^&]*'` reports *that* first and looks exactly
  like a wrong tag:
  `curl -sSI https://amzn.to/<id> | grep -io '[?&]tag=[^&]*'`. It has to be `charthorizon-20`.
  One of the three links supplied on 2026-09-06 carried `elevati09-20` — copied from someone
  else's page, so it would have paid a stranger; it was held back until a fresh link was cut.
  All three were re-verified on 2026-09-07 and are correct.
  The two standing paragraphs at the top are load-bearing and were rewritten twice the same
  day: the first says none of it is the desk's work; the second says which links are paid and
  states outright that **the shelf leads the page because it pays**. The original single
  paragraph said flatly that nothing here was an endorsement, which a commission makes untrue;
  the first rewrite then claimed "nothing is on this page because it pays", which the promotion
  to first position made untrue in turn. Both are the same failure — copy that outlived the
  arrangement it described. If the commercial arrangement changes again, this paragraph is the
  first thing to check.
  Adding this fifth nav tab is also what forced `white-space:nowrap` on `.dateline .site-nav a`
  plus `flex-wrap` on the nav under 560px: a flex row shrinks its items before it wraps, so
  without the pair the narrow masthead broke the labels themselves ("THE / TAPE") instead of
  moving a whole tab to a second line.
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
  match the light theme). The layout reads per-page `lang` and `noindex`. **Both carry real
  legal and contact data as of 2026-08-24** — operator name and postal address, the
  `kontakt@chart-horizon.com` address (Cloudflare Email Routing, not a mailbox of its own),
  USt-IdNr., and BayLDA as the competent authority. They were an unfilled placeholder template
  until then; the amber `.ph` field styling is gone with it, so a returning `[...]` would now
  render as plain body text rather than announcing itself.
  Note this is the one place the site names its operator: `about.html` still says the desk
  publishes under the masthead and not a byline, which stays true, but the Impressum is a legal
  obligation and the anonymity is therefore editorial, not actual.
  **Privacy §3 and §6 track what the site actually loads** — see the coupling note below.
  **Cloudflare's Email Address Obfuscation must stay OFF for this zone** (Security → Settings,
  formerly Scrape Shield). It rewrites `mailto:kontakt@chart-horizon.com` to a
  `/cdn-cgi/l/email-protection#…` link reading `[email protected]`, restored by an injected
  script — so with JavaScript off the Impressum shows no address at all, and § 5 DDG wants the
  contact leicht erkennbar und unmittelbar erreichbar, not conditional on a script running. It
  was on by default and was turned off on 2026-08-24; verify with a JS-disabled render, not by
  reading the source you deployed. The trade is that the address gets harvested — that is the
  correct trade for a statutory contact.
- **TradingView is click-to-load, and nothing fetches it before the reader asks.** The embeds
  set third-party cookies, so `/fx/` renders a first-party `.tv-consent` ask in place of each
  widget (a bar over the ticker, a card over the calendar) and the pair overlay asks too. A
  bootstrap script at the **top of `fx.html`**, not in `<head>`, stamps `tv-ask`/`tv-ok` on
  `<html>` before the widget markup is parsed — same pre-paint reason as the theme script, since
  the ask and the frames are mutually exclusive. Consent lives in `localStorage` under
  `ch_tv_consent` and is withdrawable from the `.tv-revoke` line under the calendar; withdrawing
  **unmounts the live frames**, because leaving them up would keep TradingView served by a reader
  who just said no. `mountAllTv()` and `probe()` both return early while unconsented — without
  that second guard the blocked-embed copy would blame a filter for the reader's own choice.
  This is what keeps §6 of `privacy.html` (consent under § 25 Abs. 1 TDDDG) true; the two move
  together.
- **Third-party embeds fail loudly, not silently.** Privacy extensions and DNS filters block
  TradingView outright. `fx.html` probes for the widget frames after a grace period and toggles
  `.no-tv` on `<html>`; the CSS then hides the empty widget shells, reveals a first-party
  `.tv-fallback` note, and suppresses the "click a pair for its live chart" hint (the chart modal
  shows `.fx-modal-empty` instead of an empty frame). The probe keeps watching, so frames that
  arrive late undo the fallback. It runs off `DOMContentLoaded`, **not `load`** — a proxy that
  black-holes the request rather than refusing it never fires `load` at all.
  `.fx-modal-empty` sizes its overlay with `height:fit-content`, **never `auto`**: a `<dialog>`
  is fixed with both block insets at 0, so an auto height makes the box stretch to the viewport
  instead of centring — it framed 856px around two lines of text, taller than the panel with a
  chart in it.
- **Analytics ↔ privacy coupling:** two third-party scripts must stay disclosed in
  `privacy.html` — the cookieless Cloudflare beacon in `default.html` (loads on **every** page)
  in §3, and the **TradingView** widgets on `/fx/` (that **one** page only) in §6. Keep them in
  sync if you add/remove third-party scripts — and note §4 enumerates **both** `localStorage`
  keys by name (`ch_theme_mode`, `ch_tv_consent`), so a third one is a documentation change too.
  (The Newsreader web font is **self-hosted** under `assets/fonts/`, not loaded from a CDN — so
  it adds no third-party request and needs no disclosure. Keep it that way.)

## The FX Map page (`/fx/`)

A second content surface besides the cover and the editions. It's a **hybrid**: ChartHorizon's own
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
  data actually moved) — the same nightly job then deploys to Pages (there is no CI; the push
  alone rebuilds nothing). So the FX numbers refresh once a day, hands-off. To edit the
  snapshot by hand, change `_data/fx.json`; the next dashboard run overwrites it.
- **TradingView = third-party scripts**, loaded only on this page, and **only after the reader
  clicks** (`ch_tv_consent`; see the click-to-load note under "Architecture") → disclosed in
  `privacy.html` §6 (see the coupling note above). So the page's default state is the strength
  board plus two first-party asks, not two live widgets — screenshot it accordingly. Constraint-safe: the page shows dashboard *output*, never
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
- **Search Console**: both providers are verified and crawling as of 2026-08-15. Google uses the
  `google_site_verification` token in `_config.yml`; **Bing needs no token** — its property was
  imported from Google Search Console, which carries the ownership proof across, so
  `bing_site_verification` stays empty on purpose. Verification and the sitemap only decide
  *whether* pages are crawled; the meta tags above shape *how* they appear.
- **The bottleneck is not technical.** Bing reported 14 URLs indexed, 0 errors, 0 excluded — and
  4 impressions with 0 clicks over six months, against **1 backlink**. Crawling works; nothing is
  blocked. What the site lacks is authority, which no amount of front-matter tuning buys. Treat
  new SEO ideas against that fact before spending effort on them.

## Developing locally

A static server (`python3 -m http.server`) will **not** render Liquid/posts — you need Jekyll.

**`bundle install` does not work on this Mac and never will**: it wants the `github-pages`
metagem, which needs Ruby ≥ 3.0 (via `ffi`/`i18n`), and only system Ruby 2.6.10 is installed —
no Homebrew, no rbenv. Use the monorepo scripts instead, which run **Jekyll 3.10.0, the exact
version `github-pages` pins**, on 2.6 by holding every dependency at its last 2.6-compatible
release:

```bash
ops/website-toolchain.sh              # once: gems -> ~/.local/share/charthorizon/jekyll-gems
ops/website-build.sh                  # build the WORKING TREE  -> _site/ + verify
ops/website-build.sh --from-head      # build the COMMITTED tree (what the nightly job does)
ops/website-deploy.sh                 # upload _site/ to Cloudflare Pages
```

`website-build.sh` verifies what it produced — post count, local-only file leaks, CNAME,
sitemap, feed, broken internal refs, the `/fx/` snapshot date — and fails loudly, because a
green build has never meant a correct one here. To preview without deploying, serve `_site/`
(`python3 -m http.server`) and screenshot with `.preview/shot.mjs`.

Three traps the scripts already handle, worth knowing before touching them: RubyGems on 2.6
reports a *misleading* "last version to support your Ruby" (it names one that still needs 3.0);
`JEKYLL_NO_BUNDLER_REQUIRE=true` is mandatory or Jekyll loads the Gemfile and demands
github-pages; and Psych 3.1 cannot parse `_config.yml`'s unquoted `permalink: /:year/…` inside
a flow mapping, so the build patches a *copy* of the config rather than the file. On macOS the
`--from-head` export must also be resolved with `pwd -P`, or Jekyll's `/var` vs `/private/var`
prefix check silently fails to load the layouts.

Keep `CNAME` intact on every change — it is what the Pages custom domain is matched against.
The `Gemfile` is unused — there is no CI and none is coming back. Leave it anyway: it is the
written record of the versions `github-pages` pinned, which is what the toolchain script
reproduces by hand.
