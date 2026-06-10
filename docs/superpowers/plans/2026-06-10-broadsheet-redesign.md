# Financial-Broadsheet Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-skin the ChartHorizon Jekyll site into a cool-newsprint financial broadsheet (self-hosted Newsreader serif, gold accent, ruled-index homepage, drop-cap posts) with zero changes to behaviour, content, data, SEO, analytics, or the public-repo constraint.

**Architecture:** Pure re-skin. All visual change lives in `assets/css/blog.css` (single source of truth) plus small markup edits to `_layouts/default.html`, `_layouts/post.html`, and `index.html`. The Newsreader font is **self-hosted** under `assets/fonts/` so the site keeps zero third-party requests on content pages (no Google Fonts CDN) — meaning `privacy.html` needs no edit. CSS token *names* are preserved across the rewrite, so each task leaves the site in a valid, buildable state.

**Tech Stack:** Jekyll (github-pages gem), kramdown, plain CSS, self-hosted variable WOFF2 font. No JS, no new plugins. Verification is `bundle exec jekyll build` (must exit 0) + visual inspection at three breakpoints — there is no JS/test harness in this repo, so "tests" here are build-success + explicit visual assertions.

**Branch:** Work happens on `redesign/financial-broadsheet` (already created; the design spec is already committed there). Reference spec: `docs/superpowers/specs/2026-06-10-broadsheet-redesign-design.md`.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `assets/fonts/newsreader.woff2` | Create | Self-hosted Newsreader variable font, roman |
| `assets/fonts/newsreader-italic.woff2` | Create | Self-hosted Newsreader variable font, italic |
| `assets/css/blog.css` | Modify | The whole look: tokens, `@font-face`, base type, masthead, index, post, FX, footer |
| `_layouts/default.html` | Modify | Font preload + `theme-color` in `<head>`; centred broadsheet masthead markup |
| `index.html` | Modify | One class on the `<h1>` for the index title (logic unchanged) |
| `_layouts/post.html` | Modify | Wrap `{{ content }}` in `.post-body` so the drop cap targets the first body paragraph |
| `CLAUDE.md` | Modify | Update the theme description (palette, self-hosted font) to match reality |

**Pre-flight (run once before Task 1):** confirm the toolchain builds the *current* site, so later build checks are meaningful.

```bash
cd /Users/notwoalike/Desktop/Chart-Horizon.com
git branch --show-current      # expect: redesign/financial-broadsheet
bundle install                 # installs github-pages gem if needed
bundle exec jekyll build       # expect: exit 0, "done in N s"
```
If `bundle` is missing or Ruby is < 2.7, stop and resolve the toolchain before continuing (see CLAUDE.md "Developing locally").

---

### Task 1: Vendor the Newsreader font (self-hosted WOFF2)

**Files:**
- Create: `assets/fonts/newsreader.woff2`
- Create: `assets/fonts/newsreader-italic.woff2`

- [ ] **Step 1: Download the variable WOFF2 files from Google's CSS API**

Google Fonts serves the variable `.woff2` when requested with a modern browser User-Agent. This script pulls the **latin** subset for both the roman and italic faces and saves them locally. Run from the repo root:

```bash
mkdir -p assets/fonts
python3 - <<'PY'
import urllib.request, re
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
url = ('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@'
       '0,6..72,200..800;1,6..72,200..800&display=swap')
css = urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read().decode()
# CSS is a series of `/* subset */` comments each followed by an @font-face block
parts = re.split(r'/\*\s*([\w-]+)\s*\*/', css)
want = {}
for i in range(1, len(parts) - 1, 2):
    subset, body = parts[i], parts[i + 1]
    if subset != 'latin':
        continue
    style = 'italic' if 'font-style: italic' in body else 'normal'
    m = re.search(r'url\((https://[^)]+\.woff2)\)', body)
    if m:
        want[style] = m.group(1)
assert 'normal' in want and 'italic' in want, ('missing face', want)
for style, path in (('normal', 'assets/fonts/newsreader.woff2'),
                    ('italic', 'assets/fonts/newsreader-italic.woff2')):
    data = urllib.request.urlopen(urllib.request.Request(want[style], headers=UA)).read()
    with open(path, 'wb') as f:
        f.write(data)
    print(path, len(data), 'bytes')
PY
```
Expected: prints two lines, each a path with a byte count in the tens of KB.

- [ ] **Step 2: Verify the files are valid WOFF2**

Run:
```bash
ls -la assets/fonts/
printf 'newsreader.woff2: ' && head -c4 assets/fonts/newsreader.woff2 && echo
printf 'newsreader-italic.woff2: ' && head -c4 assets/fonts/newsreader-italic.woff2 && echo
```
Expected: both files exist, non-zero size, and the first 4 bytes are `wOF2` (the WOFF2 magic number). If you see HTML or `wOFF` (old WOFF1) instead, the download failed — re-check the User-Agent.

- [ ] **Step 3: Commit**

```bash
git add assets/fonts/newsreader.woff2 assets/fonts/newsreader-italic.woff2
git commit -m "feat(fonts): self-host Newsreader variable woff2 (roman + italic)"
```

---

### Task 2: Rewrite tokens, `@font-face`, and base typography in `blog.css`

This swaps the palette to cool-newsprint, declares the self-hosted font, and restyles global typography. **Token names are preserved** (`--rule`, `--tline`, `--thead`, `--quote-bg`, `--quote-ink`, `--muted`, `--gold`, `--gold-ink`), so the not-yet-rewritten component rules below still resolve and the site stays buildable.

**Files:**
- Modify: `assets/css/blog.css` (lines 1–68 — the header comment, `:root`, base elements through `.post-disclaimer`)

- [ ] **Step 1: Replace the top of the file (the comment block + `:root` + base element rules)**

Replace everything from the opening `/* ChartHorizon … */` comment through the `.post-disclaimer{…}` rule (the original lines 1–68) with:

```css
/* ChartHorizon — The Weekly Tape
   Cool-newsprint financial-broadsheet theme. Single source of truth for the index and every page.
   Type: Newsreader, self-hosted under /assets/fonts (zero third-party requests). */

@font-face{
  font-family:'Newsreader'; font-style:normal; font-weight:200 800; font-display:swap;
  src:url('/assets/fonts/newsreader.woff2') format('woff2');
}
@font-face{
  font-family:'Newsreader'; font-style:italic; font-weight:200 800; font-display:swap;
  src:url('/assets/fonts/newsreader-italic.woff2') format('woff2');
}

:root{
  --paper:#f5f4f1; --ink:#17150f; --gold:#c8a24a; --gold-ink:#9a7b27;
  --rule:#ddd9d0; --rule-strong:#17150f; --tline:#ddd9d0; --thead:#ecebe6;
  --muted:#6b6356; --muted-2:#857f74;
  --quote-bg:#efede7; --quote-ink:#4a443a; --card:#fbfbf9;
  --bull:#3f7d52; --bear:#a8503f;
  --serif:'Newsreader',Georgia,'Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  max-width:760px; margin:0 auto; padding:0 22px;
  background:var(--paper); color:var(--ink);
  font:18px/1.62 var(--serif);
  font-optical-sizing:auto;
  -webkit-font-smoothing:antialiased;
}

/* ---- article typography ---- */
h1{font:600 38px/1.12 var(--serif); letter-spacing:-.4px; margin:.55em 0 .12em}
h2{font:600 25px/1.25 var(--serif); letter-spacing:-.2px; margin:1.5em 0 .35em; border-top:1px solid var(--rule); padding-top:1.1em}
p{margin:.75em 0}
em{color:var(--muted)}
strong{color:var(--ink)}
.dek{color:var(--muted); font-style:italic; font-size:18px; line-height:1.5; margin:.2em 0 1.35em}
a{color:var(--gold-ink); text-decoration:none; border-bottom:1px solid rgba(200,162,74,.4)}
a:hover{color:var(--gold)}
img{max-width:100%; border-radius:6px; margin:18px 0; box-shadow:0 1px 14px rgba(0,0,0,.10)}
table{border-collapse:collapse; width:100%; font:14px/1.45 var(--sans); margin:14px 0}
td,th{border:1px solid var(--rule); padding:8px 12px; text-align:left}
th{background:var(--thead); font-weight:600}
hr{border:none; border-top:1px solid var(--rule); margin:34px 0}
blockquote{border-left:3px solid var(--gold); background:var(--quote-bg); padding:12px 18px; margin:20px 0; border-radius:0 4px 4px 0; color:var(--quote-ink)}
blockquote p{margin:.3em 0}
.post-disclaimer{font:italic 13px/1.55 var(--sans); color:var(--muted)}
```

- [ ] **Step 2: Build and verify it compiles**

Run:
```bash
bundle exec jekyll build
```
Expected: exit 0, no Sass/CSS errors (Jekyll copies `.css` verbatim, so failure here would be a Liquid/site error, not CSS). Then confirm the token landed:
```bash
grep -c "f5f4f1" _site/assets/css/blog.css   # expect: 1 (or more)
grep -c "Newsreader" _site/assets/css/blog.css # expect: >= 3 (two @font-face + --serif)
```

- [ ] **Step 3: Commit**

```bash
git add assets/css/blog.css
git commit -m "feat(theme): newsprint palette, self-hosted Newsreader, base typography"
```

---

### Task 3: Wire the font + theme-color into `<head>` (`default.html`)

**Files:**
- Modify: `_layouts/default.html` (the `theme-color` meta near line 34; add a preload near line 60, before the stylesheet link)

- [ ] **Step 1: Update `theme-color` to the newsprint stock**

Find:
```html
<meta name="theme-color" content="#fbfaf7">
```
Replace with:
```html
<meta name="theme-color" content="#f5f4f1">
```

- [ ] **Step 2: Preload the roman font before the stylesheet**

Find:
```html
<link rel="stylesheet" href="{{ '/assets/css/blog.css' | relative_url }}">
```
Replace with:
```html
<link rel="preload" href="{{ '/assets/fonts/newsreader.woff2' | relative_url }}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{{ '/assets/css/blog.css' | relative_url }}">
```
(`crossorigin` is required on font preloads even same-origin, or the browser fetches the font twice.)

- [ ] **Step 3: Build and verify**

Run:
```bash
bundle exec jekyll build
grep -c 'rel="preload".*newsreader.woff2' _site/index.html   # expect: 1
grep -c 'content="#f5f4f1"' _site/index.html                  # expect: 1
```
Expected: both greps return 1.

- [ ] **Step 4: Commit**

```bash
git add _layouts/default.html
git commit -m "feat(theme): preload self-hosted font, update theme-color"
```

---

### Task 4: Broadsheet masthead — markup + CSS (`default.html`, `blog.css`)

**Files:**
- Modify: `_layouts/default.html` (the `<header class="site-head">…</header>` block, original lines 78–101)
- Modify: `assets/css/blog.css` (replace the `.site-head … .site-foot a:hover` block — original lines 20–50 — i.e. the header + footer shell rules)

- [ ] **Step 1: Replace the header markup**

Find the entire `<header class="site-head"> … </header>` block and replace with:

```html
<header class="site-head">
  <a class="brand" href="{{ '/' | relative_url }}">
    <svg class="mark" width="30" height="30" viewBox="0 0 100 100" aria-hidden="true">
      <g transform="translate(0,3)" fill="none" stroke-linecap="round">
        <line x1="14" y1="64" x2="86" y2="64" stroke="#17150f" stroke-width="2.6"/>
        <g stroke="#c8a24a" stroke-width="5.2">
          <path d="M33 64 a17 17 0 0 1 34 0"/>
          <line x1="50" y1="19" x2="50" y2="28"/>
          <line x1="26.4" y1="35.6" x2="32" y2="41.3"/>
          <line x1="73.6" y1="35.6" x2="68" y2="41.3"/>
        </g>
      </g>
    </svg>
    <span class="word">ChartHorizon</span>
  </a>
  <div class="masthead-sub">{{ site.tagline }} · Futures Desk</div>
  <div class="masthead-rule"></div>
  <div class="dateline">
    <nav class="site-nav">
      <a href="{{ '/' | relative_url }}"{% if page.url == '/' or page.layout == 'post' %} class="active"{% endif %}>The Tape</a>
      <a href="{{ '/fx/' | relative_url }}"{% if page.url == '/fx/' %} class="active"{% endif %}>FX Map</a>
    </nav>
    <span class="edition">{{ 'now' | date: "%B %-d, %Y" }}</span>
    <a class="support" href="https://buymeacoffee.com/charthorizon" target="_blank" rel="noopener" aria-label="Support ChartHorizon on Buy Me a Coffee">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>Support
    </a>
  </div>
</header>
```

- [ ] **Step 2: Replace the header + footer CSS shell**

In `blog.css`, replace the block that begins `/* ---- header / footer shell ---- */` and runs through `.site-foot a:hover{color:var(--ink)}` with:

```css
/* ---- broadsheet masthead ---- */
.site-head{padding:34px 0 0; text-align:center}
.site-head .brand{display:inline-flex; align-items:center; gap:11px; text-decoration:none; color:inherit; border:none}
.site-head .mark{flex:none}
.site-head .word{font:600 28px/1 var(--serif); letter-spacing:.08em; text-transform:uppercase}
.masthead-sub{font:11px/1 var(--sans); letter-spacing:.24em; text-transform:uppercase; color:var(--muted-2); margin-top:10px}
.masthead-rule{border-top:3px double var(--rule-strong); margin-top:14px}
.dateline{display:flex; align-items:center; flex-wrap:wrap; gap:8px 16px; padding:9px 0; border-bottom:1px solid var(--rule);
  font:11px/1 var(--sans); letter-spacing:.1em; text-transform:uppercase}
.dateline .site-nav{display:flex; gap:16px}
.dateline .site-nav a{color:var(--muted); text-decoration:none; border:none}
.dateline .site-nav a:hover{color:var(--ink)}
.dateline .site-nav a.active{color:var(--ink); font-weight:600}
.dateline .edition{margin-left:auto; color:var(--muted-2)}
.dateline .support{display:inline-flex; align-items:center; gap:6px; color:var(--gold-ink); text-decoration:none; border:none; letter-spacing:.06em}
.dateline .support svg{width:13px; height:13px; fill:currentColor; flex:none}
.dateline .support:hover{color:var(--gold)}
@media (max-width:560px){
  .site-head .word{font-size:24px}
  .masthead-sub{letter-spacing:.18em}
  .dateline{justify-content:center; gap:8px 14px}
  .dateline .edition{margin-left:0}
}

.site-foot{margin-top:54px; padding:22px 0 46px; border-top:1px solid var(--rule); font:13px/1.62 var(--sans); color:var(--muted)}
.site-foot strong{color:var(--ink)}
.site-foot .legal-links{margin-top:8px}
.site-foot a{color:var(--muted); text-decoration:none; border-bottom:1px solid var(--rule)}
.site-foot a:hover{color:var(--ink)}
```

- [ ] **Step 3: Build and visually verify the masthead**

Run:
```bash
bundle exec jekyll serve --port 4000 --detach
```
Then open `http://localhost:4000/` and confirm:
- The wordmark **CHARTHORIZON** is centred, with the gold horizon mark to its left.
- Under it: `THE WEEKLY TAPE · FUTURES DESK` in small uppercase letterspaced sans.
- A **3px double rule** spans the column beneath that.
- Below the rule, a single row: nav (**The Tape** active) on the left, the current date and the **Support** pill on the right.
- Resize to ~400px wide: the row stays legible (wraps/centres), nothing overflows.

(If using the Playwright MCP: `browser_navigate` to the URL, `browser_resize` to 1000×900 then 400×900, `browser_take_screenshot` each.)

Stop the server when done: `kill $(cat .jekyll-cache/.../pid 2>/dev/null) 2>/dev/null || pkill -f "jekyll serve"`.

- [ ] **Step 4: Commit**

```bash
git add _layouts/default.html assets/css/blog.css
git commit -m "feat(masthead): centred broadsheet masthead with double rule + dateline row"
```

---

### Task 5: Ruled-index homepage (`index.html`, `blog.css`)

**Files:**
- Modify: `index.html` (add a class to the `<h1>`)
- Modify: `assets/css/blog.css` (replace the `/* ---- index post list ---- */` block — original lines 70–77)

- [ ] **Step 1: Tag the index title**

In `index.html`, find:
```html
<h1>The Weekly Tape</h1>
```
Replace with:
```html
<h1 class="index-title">The Weekly Tape</h1>
```
(Leave the `<p class="dek">…</p>` and the `<ul class="post-list">…</ul>` loop exactly as they are.)

- [ ] **Step 2: Replace the index post-list CSS**

Replace the block beginning `/* ---- index post list ---- */` through `.post-list .post-excerpt{…}` with:

```css
/* ---- index post list ---- */
.index-title{margin-top:.7em}
.post-list{list-style:none; padding:0; margin:26px 0 0}
.post-list li{padding:20px 0; border-top:1px solid var(--rule)}
.post-list li:first-child{border-top:2px solid var(--rule-strong)}
.post-list .post-date{display:block; font:11px/1.3 var(--sans); letter-spacing:.12em; text-transform:uppercase; color:var(--gold-ink)}
.post-list .post-link{display:inline-block; margin:.16em 0 0; font:600 25px/1.18 var(--serif); letter-spacing:-.2px; color:var(--ink); border:none}
.post-list .post-link:hover{color:var(--gold-ink)}
.post-list .post-excerpt{margin:.3em 0 0; color:var(--muted)}
```

- [ ] **Step 3: Build and visually verify**

Run `bundle exec jekyll serve --port 4000 --detach`, open `http://localhost:4000/`, confirm:
- A heavier (2px ink) rule opens the list under the dek; hairline rules separate entries.
- Each entry: gold uppercase date, Newsreader headline (hover → gold), muted excerpt.

- [ ] **Step 4: Commit**

```bash
git add index.html assets/css/blog.css
git commit -m "feat(home): ruled broadsheet index list"
```

---

### Task 6: Post layout + drop cap (`post.html`, `blog.css`)

**Files:**
- Modify: `_layouts/post.html` (wrap `{{ content }}` in `.post-body`)
- Modify: `assets/css/blog.css` (append a post block after the index block)

- [ ] **Step 1: Wrap the post content**

In `_layouts/post.html`, find:
```html
  {{ content }}

  <hr>
```
Replace with:
```html
  <div class="post-body">
    {{ content }}
  </div>

  <hr>
```

- [ ] **Step 2: Add the drop-cap rule**

In `blog.css`, immediately after the `.post-list .post-excerpt{…}` rule (end of the index block), add:

```css
/* ---- post body: broadsheet drop cap on the first paragraph ---- */
.post-body>p:first-of-type::first-letter{
  float:left; font:600 64px/48px var(--serif); color:var(--gold-ink);
  padding:4px 9px 0 0;
}
```

- [ ] **Step 3: Build and visually verify the drop cap**

Run `bundle exec jekyll serve --port 4000 --detach`, open the post at `http://localhost:4000/2026/06/09/the-weekly-tape-june-9-2026/` and confirm:
- The **"T"** of "The grain complex went over…" renders as a large gold drop cap, floated left, ~3 lines tall.
- The dek ("Prices through June 8 · COT report June 2 · Data: ChartHorizon") is **not** drop-capped and stays italic/muted.
- Exactly **one** drop cap on the page (the `h2`/subsequent paragraphs are normal).
- Section `h2`s carry a hairline top rule; blockquotes show the gold left rule; the card images and tables read correctly on newsprint.

- [ ] **Step 4: Commit**

```bash
git add _layouts/post.html assets/css/blog.css
git commit -m "feat(post): .post-body wrapper + first-paragraph drop cap"
```

---

### Task 7: Re-tune the FX Map surfaces (`blog.css`)

The `.fx-*` rules already use the preserved tokens (`--tline`, `--thead`, `--quote-bg`) and the bull/bear greens/reds that match `--bull`/`--bear`, so they mostly update for free. The only hardcoded value that needs cooling is the card background `#fffdf8`.

**Files:**
- Modify: `assets/css/blog.css` (the `.fx-col,.fx-pairshelf{…}` rule in the FX block)

- [ ] **Step 1: Cool the FX card surface**

Find:
```css
.fx-col,.fx-pairshelf{border:1px solid var(--tline); border-radius:10px; padding:14px 16px; background:#fffdf8}
```
Replace with:
```css
.fx-col,.fx-pairshelf{border:1px solid var(--tline); border-radius:10px; padding:14px 16px; background:var(--card)}
```

- [ ] **Step 2: Build and visually verify `/fx/`**

Run `bundle exec jekyll serve --port 4000 --detach`, open `http://localhost:4000/fx/`, confirm:
- The strength board (bullish/bearish columns), neutral row, pairs grid, method note, and the interest-rate table all read cleanly on the newsprint stock; bull = green, bear = red, headers/cards have hairline borders on the cool card surface.
- The `<h2>`s ("Interest rates", "Economic calendar") show the broadsheet hairline top rule (from the global `h2` style).
- Both **TradingView** widgets (ticker tape at top, economic calendar at bottom) load and sit correctly — they remain `colorTheme:"light"` with transparent backgrounds, so the newsprint shows through.

- [ ] **Step 3: Commit**

```bash
git add assets/css/blog.css
git commit -m "feat(fx): cool the FX card surface to match newsprint"
```

---

### Task 8: Update `CLAUDE.md` to match the new theme

The architecture notes still describe the old paper theme and "No web fonts." Bring them current.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the `blog.css` architecture bullet**

Find:
```
- **`assets/css/blog.css`** is the single source of truth for the look — a light "paper"
  editorial theme (palette + serif type lifted from the original post preview): tokens in
  `:root` (`--paper #fbfaf7`, `--ink #1a1814`, gold `--gold #c8a24a`, hairlines, table tans,
  muted, quote bg). Both layouts and the index pull from it, so the index and every post
  match. No web fonts (system `Iowan Old Style` → `Georgia` fallback).
```
Replace with:
```
- **`assets/css/blog.css`** is the single source of truth for the look — a cool-newsprint
  financial-broadsheet theme: tokens in `:root` (`--paper #f5f4f1`, `--ink #17150f`, gold
  `--gold #c8a24a`, `--rule-strong` for the masthead double rule, `--card`, `--bull`/`--bear`,
  hairlines, muted, quote bg). Both layouts and the index pull from it, so the index and every
  page match. Type is **Newsreader**, self-hosted under `assets/fonts/` and declared via
  `@font-face` at the top of `blog.css` (preloaded in `default.html`), so the site still makes
  **zero third-party requests** on content pages — Georgia is the fallback.
```

- [ ] **Step 2: Update the `default.html` architecture bullet**

Find:
```
- **`_layouts/default.html`** — the page shell for every page: `<head>` (system-serif type,
  favicon, cookieless Cloudflare Web Analytics beacon), the brand header (inline horizon SVG
  mark + wordmark + a two-item nav — **The Tape** (home) / **FX Map** (`/fx/`) — + tagline),
  and the footer (risk disclaimer + Impressum/Datenschutz links).
```
Replace with:
```
- **`_layouts/default.html`** — the page shell for every page: `<head>` (self-hosted Newsreader
  `@font-face`/preload, favicon, cookieless Cloudflare Web Analytics beacon), the centred
  **broadsheet masthead** (inline horizon SVG mark + `CHARTHORIZON` wordmark + a
  `The Weekly Tape · Futures Desk` sub-line, closed by a 3px double rule, then a dateline row —
  nav **The Tape** (home) / **FX Map** (`/fx/`) + edition date + Support pill), and the footer
  (risk disclaimer + Impressum/Datenschutz links).
```

- [ ] **Step 3: Add a self-hosted-font note to the analytics↔privacy coupling bullet**

Find:
```
- **Analytics ↔ privacy coupling:** two third-party scripts must stay disclosed in
  `privacy.html` — the cookieless Cloudflare beacon in `default.html` (loads on **every** page)
  in §3, and the **TradingView** widgets on `/fx/` (that **one** page only) in §6. Keep them in
  sync if you add/remove third-party scripts.
```
Replace with:
```
- **Analytics ↔ privacy coupling:** two third-party scripts must stay disclosed in
  `privacy.html` — the cookieless Cloudflare beacon in `default.html` (loads on **every** page)
  in §3, and the **TradingView** widgets on `/fx/` (that **one** page only) in §6. Keep them in
  sync if you add/remove third-party scripts. (The Newsreader web font is **self-hosted** under
  `assets/fonts/`, not loaded from a CDN — so it adds no third-party request and needs no
  disclosure. Keep it that way.)
```

- [ ] **Step 4: Verify and commit**

Run:
```bash
grep -c "financial-broadsheet theme" CLAUDE.md   # expect: 1
grep -c "Iowan Old Style" CLAUDE.md              # expect: 0
```
```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE): describe the newsprint broadsheet theme + self-hosted font"
```

---

### Task 9: Final verification sweep

**Files:** none (verification + optional fixes only)

- [ ] **Step 1: Clean build**

```bash
bundle exec jekyll build
```
Expected: exit 0, no warnings about missing files. Confirm the fonts shipped:
```bash
ls _site/assets/fonts/   # expect: newsreader.woff2, newsreader-italic.woff2
```

- [ ] **Step 2: Visual sweep at three breakpoints**

Serve (`bundle exec jekyll serve --port 4000 --detach`) and inspect at ~1000px, ~560px, ~400px wide (Playwright MCP `browser_resize` + `browser_take_screenshot`, or a real browser):
- `/` — masthead, double rule, dateline, ruled index.
- `/2026/06/09/the-weekly-tape-june-9-2026/` — drop cap once, on the first body paragraph only.
- `/fx/` — board, rate table, both TradingView widgets present.
- `/impressum.html` — `.legal` content reads correctly on the new palette (it inherits tokens automatically).

- [ ] **Step 3: Confirm zero new third-party requests**

In the browser devtools Network tab (or Playwright `browser_network_requests`) on `/` and a post, confirm:
- The font loads from `…/assets/fonts/newsreader.woff2` (same origin) — **no** request to `fonts.googleapis.com` or `fonts.gstatic.com`.
- The only third-party request site-wide is the Cloudflare beacon (`static.cloudflareinsights.com`).
- On `/fx/` only, TradingView requests appear (`s3.tradingview.com`) — expected and already disclosed in `privacy.html` §6.

If any check fails, fix inline and commit with a `fix:` message. If all pass, the implementation is complete.

- [ ] **Step 4: Stop the dev server**

```bash
pkill -f "jekyll serve" 2>/dev/null || true
```

---

## Post-implementation

- **Do not merge to `main` automatically.** When all tasks pass, use the
  `superpowers:finishing-a-development-branch` skill to choose how to integrate (PR vs merge).
  Merging to `main` triggers the Pages deploy — that is the moment the redesign goes live.
- Out of scope (optional follow-ups): regenerating `assets/og-default.png` to match the new look;
  adding `docs/` to Jekyll `exclude` so spec/plan markdown never publishes.

## Self-Review notes (already applied)

- **Spec coverage:** palette (Task 2), self-hosted font + zero-third-party (Tasks 1–3, 9§3),
  masthead (Task 4), ruled index (Task 5), post + drop cap (Task 6), FX re-skin (Task 7),
  footer/legal (Task 4 CSS + inherited), CLAUDE.md currency (Task 8), unchanged behaviour
  (verified, no logic edits). All spec sections map to a task.
- **Drop-cap correctness:** targets `.post-body>p:first-of-type`, not `.post>p`, so it cannot
  hit the dek (spec self-review fix carried through).
- **Token consistency:** `--rule`, `--tline`, `--thead`, `--quote-bg`, `--quote-ink`, `--muted`,
  `--gold(-ink)` names are preserved so untouched component rules keep resolving; new names
  (`--rule-strong`, `--muted-2`, `--card`, `--bull`, `--bear`) are defined in Task 2 before any
  task uses them.
