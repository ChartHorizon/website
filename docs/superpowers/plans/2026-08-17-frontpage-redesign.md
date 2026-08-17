# Front Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn chart-horizon.com's home page into a real broadsheet cover — lead story with a
picture, the two editions as separate strands, an FX rail and a dashboard block — and add
`/tape/` and `/ledger/` as section hubs.

**Architecture:** Liquid + CSS only. No JavaScript, no plugin, no new build step, no third-party
request. The two editions are derived from the existing `_includes/edition.html` rule, which
gains a `key=true` parameter so callers can compare on a machine key (`tape` / `ledger`) instead
of a display string carrying an HTML entity. The home page alone widens to 1080px via a body
class set from `wide: true` front matter.

**Tech Stack:** Jekyll 3.10.0 (Ruby 2.6, via `ops/website-toolchain.sh`), Liquid, kramdown,
hand-written CSS in one file. Verification: `ops/website-build.sh` plus a local check script and
Playwright screenshots via `.preview/shot.mjs`.

**Spec:** `docs/superpowers/specs/2026-08-17-frontpage-redesign-design.md`

## Global Constraints

Copied verbatim from the spec. Every task's requirements implicitly include these.

- **Public repo:** no link to dashboard source, installers or GitHub releases. The dashboard
  block links to `/dashboard/` and nothing else. No download button while `dl_version` is empty.
- **Zero third-party requests on content pages.** The front page adds none — the FX rail renders
  from `_data/fx.json` at build time, the plate is a local WebP. `privacy.html` is not edited.
- **No file outside this repo is touched.** In particular not `ops/website-build.sh` and not
  `content/livermore/blog/publish.py`.
- **No `_posts/*.md` is edited.** Every existing and every future generated post must land in
  the right strand with no front matter.
- **`_data/fx.json` is read-only here.** Its shape is owned by the cross-repo dashboard job.
- **Single source of truth for the look:** `assets/css/blog.css`.
- Three house rules the new CSS must respect: both muted tones clear 4.5:1 on every surface they
  sit on and gold (2.19:1 on paper) is never body text and never a focus ring there;
  `:focus-visible` is one ink ring defined once, add none; prose stays capped at `--measure`
  while figures, boards and tables break out.
- **Keep `CNAME` intact.** Bump `css_version` in `_config.yml` when `blog.css` changes.
- Every commit lands on a branch, not on `main` — see Task 0.

## Two deltas from the spec, discovered while reading the code

1. The 760px cap lives on `body` (`assets/css/blog.css:68`), not on a wrapper. `main.wide` alone
   would do nothing. So `_layouts/default.html` also puts a `wide-page` class on `<body>`, and
   the CSS lifts the cap there and re-applies 760px to `.site-head` and `.site-foot`. The
   rendered `<body>` tag is byte-identical on every other page.
2. `ops/website-build.sh` already verifies broken local `href`/`src` references, which covers the
   lead's derived `.webp` path — spec test 3 needs no new code. The remaining checks go in
   `.preview/check-front.py`, which is in `.gitignore` **and** in the build's `exclude` list, so
   it is neither published nor committed.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `.preview/check-front.py` | **new, gitignored** — asserts the invariants the build script does not: strand partition, no duplicate on the cover, hubs indexed, FX date on the cover | 1–4 |
| `_includes/edition.html` | the one edition rule, now rendering either the display name or a machine key | 1 |
| `tape.html` | **new** — `/tape/` hub, the Weekly Tape run grouped by year | 1 |
| `ledger.html` | **new** — `/ledger/` hub, the Hedgers' Ledger run grouped by year | 1 |
| `_layouts/default.html` | page shell; gains the `wide-page` body class and `wide` main class | 2 |
| `assets/css/blog.css` | the whole look; gains one `/* front page */` block | 2, 3, 4 |
| `_config.yml` | `css_version` bump | 2 |
| `index.html` | the cover: leads, strands, rail | 3, 4 |
| `_layouts/post.html` | "Elsewhere in the paper" foot gains a link to the post's own hub | 5 |
| `archive.html` | dek gains links to both hubs | 5 |

---

### Task 0: Branch and baseline

**Files:**
- Create: `/tmp/frontpage-baseline/` (throwaway, outside the repo)

- [ ] **Step 1: Confirm the toolchain is installed**

```bash
cd ~/charthorizon/website
ls ~/.local/share/charthorizon/jekyll-gems/bin/jekyll
```

Expected: the path exists. If it does not, run `ops/website-toolchain.sh` once — it installs
Jekyll 3.10.0 with every dependency pinned to its last Ruby-2.6-compatible release. Do not run
`bundle install`; it wants the `github-pages` metagem, which needs Ruby ≥ 3.0, and this Mac only
has system Ruby 2.6.10.

- [ ] **Step 2: Branch**

```bash
cd ~/charthorizon/website
git checkout -b frontpage-redesign
git status --porcelain
```

Expected: on `frontpage-redesign`, working tree clean apart from the untracked plan and spec
under `docs/superpowers/`.

- [ ] **Step 3: Build the current site and keep it as the regression baseline**

```bash
cd ~/charthorizon/website
ops/website-build.sh
rm -rf /tmp/frontpage-baseline
cp -R _site /tmp/frontpage-baseline
```

Expected: `all checks passed`. The copy is what Task 2 diffs against to prove that widening the
cover changed nothing on any other page.

- [ ] **Step 4: Note the current post count**

```bash
ls ~/charthorizon/website/_posts/*.md | wc -l
```

Expected: 18 at the time of writing. Later checks compare against this number computed live, not
against a hardcoded 18 — record it only to sanity-check the checker.

---

### Task 1: The edition key and the two hubs

**Files:**
- Modify: `_includes/edition.html` (whole file)
- Create: `tape.html`, `ledger.html`
- Create: `.preview/check-front.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `{% include edition.html post=P key=true %}` → the exact string `tape` or `ledger`,
  with no surrounding whitespace. Tasks 3 and 5 depend on those two literals. The parameterless
  form `{% include edition.html post=P %}` keeps rendering `Hedgers&rsquo; Ledger` or
  `Weekly Tape` exactly as before, and `_layouts/post.html` keeps working untouched.
- Produces: the pages `/tape/` and `/ledger/`, linked from Tasks 3 and 5.

- [ ] **Step 1: Write the failing check**

Create `.preview/check-front.py` with exactly this content:

```python
#!/usr/bin/env python3
"""Invariants for the front-page redesign that ops/website-build.sh does not cover.

Lives under .preview/ on purpose: that directory is in .gitignore AND in the exclude
list website-build.sh passes to Jekyll, so this file is neither committed nor published.
Run it after every build:  python3 .preview/check-front.py
"""
from __future__ import annotations

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / "_site"
SM = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

fail: list[str] = []


def read(rel: str) -> str:
    p = SITE / rel
    if not p.exists():
        fail.append(f"missing page: {rel}")
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def post_links(html: str) -> list[str]:
    """Every dated post URL an HTML page links to, in document order, with duplicates."""
    return re.findall(r'href="(/20\d\d/\d\d/\d\d/[^"]+/)"', html)


# --- 1. the hubs partition the run exactly -----------------------------------
tape = set(post_links(read("tape/index.html")))
ledger = set(post_links(read("ledger/index.html")))

both = tape & ledger
if both:
    fail.append(f"post(s) on BOTH hubs: {sorted(both)}")

total = len(tape) + len(ledger)
n_posts = len(list((REPO / "_posts").glob("*.md")))
print(f"  hubs:          {len(tape)} tape + {len(ledger)} ledger = {total}/{n_posts}")
if total != n_posts:
    fail.append(f"hubs list {total} posts, _posts holds {n_posts} — the split is not total")

# Each hub holds only its own edition. Matched on the post SLUG rather than on page
# text, so the prose (each hub's dek links the other one by name) cannot false-positive.
# Slug and edition key agree because both come from the title — the one thing that would
# part them is an explicit `edition:` override, which no post uses today. If one ever
# does, this check is what will say so, and it should then match on the key, not the slug.
stray_tape = sorted(u for u in tape if "hedgers" in u)
stray_ledger = sorted(u for u in ledger if "hedgers" not in u)
if stray_tape:
    fail.append(f"Ledger release(s) listed on /tape/: {stray_tape}")
if stray_ledger:
    fail.append(f"non-Ledger post(s) listed on /ledger/: {stray_ledger}")

# --- 2. both hubs are indexable and in the sitemap ---------------------------
for hub in ("tape", "ledger"):
    if 'name="robots" content="noindex"' in read(f"{hub}/index.html"):
        fail.append(f"/{hub}/ carries noindex")
urls = [e.text for e in ET.parse(SITE / "sitemap.xml").getroot().findall(f".//{SM}loc")]
for hub in ("/tape/", "/ledger/"):
    if not any(u.endswith(hub) for u in urls):
        fail.append(f"{hub} missing from sitemap.xml")
print(f"  sitemap hubs:  ok ({len(urls)} urls total)")

if fail:
    print("\nFRONT-PAGE CHECKS FAILED:")
    for f in fail:
        print("  !!", f)
    sys.exit(1)
print("\n  front-page checks passed")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website && python3 .preview/check-front.py
```

Expected: FAIL, reporting `missing page: tape/index.html` and `missing page: ledger/index.html`
plus the partition mismatch. That is the point — the hubs do not exist yet.

- [ ] **Step 3: Add the key parameter to `_includes/edition.html`**

Replace the whole file with:

```liquid
{%- comment -%}
  The masthead section a post ran under, for the index, the hubs and the archive datelines.

  `edition:` front matter wins; otherwise it is derived from the title, so the daily
  Hedgers' Ledger bot needs no change to be labelled correctly. Everything that is not
  a Ledger release is a Weekly Tape note — the two named editions in about.html.

  With `key=true` the SAME rule renders a machine key instead of the display name.
  Callers that COMPARE editions must use the key: the display name carries an HTML
  entity (&rsquo;), and no caller should have to spell that to match on it.

  The key is total by construction — anything that is not a Ledger is `tape` — so the
  two hubs always partition the run and no post can fall out of both.

  Usage: {% include edition.html post=post %}           -> "Hedgers&rsquo; Ledger" | "Weekly Tape"
         {% include edition.html post=post key=true %}  -> "ledger" | "tape"
{%- endcomment -%}
{%- assign is_ledger = false -%}
{%- if include.post.edition -%}
  {%- if include.post.edition contains "Hedgers" -%}{%- assign is_ledger = true -%}{%- endif -%}
{%- elsif include.post.title contains "Hedgers" -%}
  {%- assign is_ledger = true -%}
{%- endif -%}
{%- if include.key -%}
{%- if is_ledger -%}ledger{%- else -%}tape{%- endif -%}
{%- elsif include.post.edition -%}
{{- include.post.edition -}}
{%- elsif is_ledger -%}
Hedgers&rsquo; Ledger
{%- else -%}
Weekly Tape
{%- endif -%}
```

- [ ] **Step 4: Create `tape.html`**

```liquid
---
layout: default
permalink: /tape/
title: The Weekly Tape
seo_title: "The Weekly Tape — Futures Positioning Notes by Market, Every Week"
description: "Every Weekly Tape note: what the CFTC Commitments of Traders report, seasonality, hedging programs and term structure said about a market that week, read across grains, metals, energy, rates and FX."
---
<h1>The Weekly Tape</h1>
<p class="dek">The written notes — one market, one week, read across season, producer
   positioning, hedging program and term structure. The automated COT releases run in the
   <a href="{{ '/ledger/' | relative_url }}">Hedgers&rsquo; Ledger</a>.</p>

{%- assign run = "" | split: "" -%}
{%- for post in site.posts -%}
  {%- capture k %}{% include edition.html post=post key=true %}{% endcapture -%}
  {%- if k == "tape" -%}{%- assign run = run | push: post -%}{%- endif -%}
{%- endfor -%}
{%- assign by_year = run | group_by_exp: "post", "post.date | date: '%Y'" -%}
{% for year in by_year %}
<h2 class="section-rule archive-year"><span>{{ year.name }}</span></h2>
<ul class="archive-list hub-list">
  {% for post in year.items %}
  <li>
    <div class="post-dateline">
      <time class="post-date" datetime="{{ post.date | date: '%Y-%m-%d' }}">{{ post.date | date: "%b %-d" }}</time>
    </div>
    <a class="archive-link" href="{{ post.url | relative_url }}">{{ post.title }}</a>
  </li>
  {% endfor %}
</ul>
{% endfor %}

<p class="more-issues"><a href="{{ '/archive/' | relative_url }}">All back issues &rarr;</a></p>
```

Note on `push`: Jekyll 3.10 ships Liquid 4, where `push` returns a new array — it does **not**
mutate in place, which is why the result is re-assigned to `run`. Do not replace this with a
`where_exp` filter on the title: that would bypass `edition.html` and silently ignore an explicit
`edition:` front matter override.

- [ ] **Step 5: Create `ledger.html`**

```liquid
---
layout: default
permalink: /ledger/
title: The Hedgers' Ledger
seo_title: "Hedgers' Ledger — Weekly COT Extremes From the Commercial Book"
description: "Every Hedgers' Ledger release: where commercial hedgers sit against their own three-year range in each market, read from the CFTC Commitments of Traders report the week it published."
---
<h1>The Hedgers&rsquo; Ledger</h1>
<p class="dek">The weekly release: where the commercial book sits against its own three-year
   range, market by market, straight from the CFTC report. The written notes run in
   <a href="{{ '/tape/' | relative_url }}">The Weekly Tape</a>.</p>

{%- assign run = "" | split: "" -%}
{%- for post in site.posts -%}
  {%- capture k %}{% include edition.html post=post key=true %}{% endcapture -%}
  {%- if k == "ledger" -%}{%- assign run = run | push: post -%}{%- endif -%}
{%- endfor -%}
{%- assign by_year = run | group_by_exp: "post", "post.date | date: '%Y'" -%}
{% for year in by_year %}
<h2 class="section-rule archive-year"><span>{{ year.name }}</span></h2>
<ul class="archive-list hub-list">
  {% for post in year.items %}
  <li>
    <div class="post-dateline">
      <time class="post-date" datetime="{{ post.date | date: '%Y-%m-%d' }}">{{ post.date | date: "%b %-d" }}</time>
    </div>
    <a class="archive-link" href="{{ post.url | relative_url }}">{{ post.title }}</a>
  </li>
  {% endfor %}
</ul>
{% endfor %}

<p class="more-issues"><a href="{{ '/archive/' | relative_url }}">All back issues &rarr;</a></p>
```

- [ ] **Step 6: Add the one CSS rule the hubs need**

`.archive-list .post-dateline` reserves `13rem` because on `/archive/` the dateline holds the
edition label as well ("HEDGERS' LEDGER · JUL 25"). On a single-edition hub the label is
redundant and dropped, so the column would be a 13rem gap. Append to `assets/css/blog.css`,
directly after the `@media (max-width:560px)` line that closes the archive block (currently
line 202):

```css
/* section hubs (/tape/, /ledger/) reuse the archive list, minus the edition label —
   the page IS the edition — so the dateline column only has to clear "Aug 16". */
.hub-list .post-dateline{width:6.5rem}
@media (max-width:560px){ .hub-list .post-dateline{width:auto} }
```

Bump `css_version` in `_config.yml` from `5` to `6` in the same edit.

- [ ] **Step 7: Build and run the check**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
```

Expected: `all checks passed`, then `hubs: 9 tape + 9 ledger = 18/18` and `front-page checks
passed`. The 9/9 split is today's; the total is what must always equal the post count.

- [ ] **Step 8: Confirm the display form did not change**

```bash
cd ~/charthorizon/website
diff <(sed -n 's/.*<span class="post-edition">\(.*\)<\/span>.*/\1/p' /tmp/frontpage-baseline/archive/index.html) \
     <(sed -n 's/.*<span class="post-edition">\(.*\)<\/span>.*/\1/p' _site/archive/index.html)
```

Expected: no output. The archive's edition labels are byte-identical, proving the `key`
parameter did not disturb the default rendering.

- [ ] **Step 9: Commit**

```bash
cd ~/charthorizon/website
git add _includes/edition.html tape.html ledger.html assets/css/blog.css _config.yml
git commit -m "hubs: /tape/ and /ledger/, split on one derived edition key"
```

---

### Task 2: Widen the cover, and only the cover

**Files:**
- Modify: `_layouts/default.html:116` (the `<body>` tag), `:160` (the `<main>` tag)
- Modify: `index.html` (front matter only — add `wide: true`)
- Modify: `assets/css/blog.css` (new front-page block)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `body.wide-page main.wide` as the 1080px container on the home page only. Tasks 3
  and 4 render inside `main.wide`.

- [ ] **Step 1: Write the failing check**

Append to `.preview/check-front.py`, immediately before the `if fail:` block at the end:

```python
# --- 3. only the cover is wide ----------------------------------------------
home = read("index.html")
if 'class="wide-page"' not in home:
    fail.append("home page <body> is missing the wide-page class")
if 'id="main" class="wide"' not in home:
    fail.append("home page <main> is missing the wide class")
for other in ("about/index.html", "fx/index.html", "dashboard/index.html",
              "archive/index.html", "tape/index.html", "ledger/index.html"):
    if "wide-page" in read(other):
        fail.append(f"{other} widened by accident — only the cover may")
print("  wide shell:    cover only")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website && python3 .preview/check-front.py
```

Expected: FAIL with `home page <body> is missing the wide-page class`.

- [ ] **Step 3: Carry the flag from front matter into the shell**

In `_layouts/default.html`, change the `<body>` tag (line 116) from:

```liquid
<body>
```

to:

```liquid
<body{% if page.wide %} class="wide-page"{% endif %}>
```

and the `<main>` tag (line 160) from:

```liquid
<main id="main">
```

to:

```liquid
<main id="main"{% if page.wide %} class="wide"{% endif %}>
```

The flag is a page property, deliberately not a `page.url == "/"` test: a URL test hides the
decision from the page that owns it, and the next wide page would have to edit the layout.

- [ ] **Step 4: Set the flag on the cover**

In `index.html`, add `wide: true` to the front matter, after `layout: default`.

- [ ] **Step 5: Open the shell in CSS**

Append to `assets/css/blog.css`, at the end of the file:

```css
/* ---- the cover -----------------------------------------------------------
   Only the home page widens. The 760px measure is set on `body` (see the body rule
   at the top of this file), not on a wrapper, so the cap is lifted here and handed
   back to the masthead and the footer: the cover steps out from under a narrow head,
   which is the broadsheet gesture, not an oversight. Every other page renders a
   byte-identical <body> tag and is untouched. */
body.wide-page{max-width:none}
body.wide-page .site-head,
body.wide-page .site-foot{max-width:760px; margin-inline:auto}
body.wide-page main.wide{max-width:1080px; margin-inline:auto}
```

- [ ] **Step 6: Build and check**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
```

Expected: both pass, `wide shell: cover only`.

- [ ] **Step 7: Prove no other page moved**

```bash
cd ~/charthorizon/website
for p in about fx dashboard archive impressum privacy; do
  diff -q /tmp/frontpage-baseline/$p/index.html _site/$p/index.html
done
diff -q /tmp/frontpage-baseline/404.html _site/404.html
diff -rq /tmp/frontpage-baseline/2026 _site/2026
```

Expected: no output at all. Every page except the cover — including all 18 posts — is
byte-identical to the baseline built in Task 0.

- [ ] **Step 8: Screenshot the widened shell**

```bash
cd ~/charthorizon/website/_site && (python3 -m http.server 8899 >/dev/null 2>&1 &) ; sleep 1
cd ~/charthorizon/website
node .preview/shot.mjs http://localhost:8899/ /tmp/frontpage-wide-1280.png 1280 full
```

Expected: the post list now runs to 1080px while the masthead and footer stay narrow. It will
look wrong — a 1080px-wide single-column list is not a design — and that is fine: Task 3
replaces the list with the grid. Leave the server running for the next tasks.

- [ ] **Step 9: Commit**

```bash
cd ~/charthorizon/website
git add _layouts/default.html index.html assets/css/blog.css
git commit -m "shell: the cover widens to 1080px, every other page stays at 760"
```

---

### Task 3: Leads and strands

**Files:**
- Modify: `index.html` (body, below the standfirst)
- Modify: `assets/css/blog.css` (extend the cover block)

**Interfaces:**
- Consumes: `{% include edition.html post=P key=true %}` → `tape` | `ledger` (Task 1);
  `body.wide-page main.wide` (Task 2).
- Produces: the DOM hooks `.front-grid`, `.front-main` and `.rail`. Task 4 fills `.rail`; it must
  not change the grid declaration.

- [ ] **Step 1: Write the failing check**

Append to `.preview/check-front.py`, immediately before the `if fail:` block:

```python
# --- 4. the cover: leads, strands, no duplicates -----------------------------
links = post_links(home)
if len(links) != len(set(links)):
    dupes = sorted({u for u in links if links.count(u) > 1})
    fail.append(f"post(s) linked twice on the cover: {dupes}")
print(f"  cover posts:   {len(links)} links, {len(set(links))} distinct")
if len(links) != 10:
    fail.append(f"cover links {len(links)} posts, expected 10 (2 leads + 4 + 4)")

# The lead is the newest Weekly Tape, never the newest Ledger.
newest_tape = sorted(
    p.name for p in (REPO / "_posts").glob("*.md") if "hedgers" not in p.name.lower()
)[-1]
lead_url = "/" + newest_tape[:10].replace("-", "/", 2) + "/"
if not links or not links[0].startswith(lead_url):
    fail.append(f"first cover link is {links[0] if links else 'none'}, expected the newest "
                f"Weekly Tape at {lead_url}")

for hub in ('href="/tape/"', 'href="/ledger/"'):
    if hub not in home:
        fail.append(f"cover does not link {hub} — the strands must end in their hubs")
print("  cover leads:   newest Weekly Tape leads, both hubs linked")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website && python3 .preview/check-front.py
```

Expected: FAIL — the cover still links 10 posts in plain date order, so the lead assertion and
the hub-link assertion both fail.

- [ ] **Step 3: Rewrite the body of `index.html`**

Keep the existing front matter (now with `wide: true`), the `visually-hidden` `<h1>` and the
`.index-standfirst` paragraph exactly as they are. Replace everything from `<h2 class="section-rule">`
to the end of the file with:

```liquid
{%- comment -%}
  Selection, in one pass over site.posts (which is newest-first):
    · lead_tape   — the newest Weekly Tape. It leads even when a Ledger is newer: the
                    Ledger publishes automatically every week, and as a permanent lead it
                    would bury the written notes under a headline that is a date.
    · lead_ledger — the newest Ledger, second lead, no picture.
  A post has exactly one edition key, so nothing can appear in both strands, and the
  strand loop below skips whichever two posts became leads.
{%- endcomment -%}
{%- for p in site.posts -%}
  {%- capture k %}{% include edition.html post=p key=true %}{% endcapture -%}
  {%- if k == "tape" and lead_tape == nil -%}{%- assign lead_tape = p -%}{%- endif -%}
  {%- if k == "ledger" and lead_ledger == nil -%}{%- assign lead_ledger = p -%}{%- endif -%}
{%- endfor -%}

{%- comment -%}
  The lead picture is the post's own OG card as WebP (~48 KB against 153 KB for the PNG
  twin publish.py writes alongside it). A post whose `image` is the site default carries
  no card of its own, so the lead renders without a figure rather than showing the logo.
{%- endcomment -%}
{%- assign lead_img = "" -%}
{%- if lead_tape.image and lead_tape.image != site.og_image -%}
  {%- assign lead_img = lead_tape.image | replace: ".png", ".webp" -%}
{%- endif -%}

<div class="front-grid">
<div class="front-main">

  {%- if lead_tape %}
  <article class="lead">
    {%- if lead_img != "" %}
    <figure class="lead-figure">
      <img src="{{ lead_img | relative_url }}" width="1200" height="1036" decoding="async"
           alt="{{ lead_tape.image_alt | default: lead_tape.title }}">
    </figure>
    {%- endif %}
    <div class="post-dateline">
      <span class="post-edition">{% include edition.html post=lead_tape %}</span>
      <span class="sep" aria-hidden="true">&middot;</span>
      <time class="post-date" datetime="{{ lead_tape.date | date: '%Y-%m-%d' }}">{{ lead_tape.date | date: "%B %-d, %Y" }}</time>
    </div>
    <h2 class="lead-head"><a class="post-link" href="{{ lead_tape.url | relative_url }}">{{ lead_tape.title }}</a></h2>
    {%- if lead_tape.subtitle %}<p class="lead-dek">{{ lead_tape.subtitle }}</p>{% endif %}
  </article>
  {%- endif %}

  {%- if lead_ledger %}
  <article class="lead lead-second">
    <div class="post-dateline">
      <span class="post-edition">{% include edition.html post=lead_ledger %}</span>
      <span class="sep" aria-hidden="true">&middot;</span>
      <time class="post-date" datetime="{{ lead_ledger.date | date: '%Y-%m-%d' }}">{{ lead_ledger.date | date: "%B %-d, %Y" }}</time>
    </div>
    <h2 class="lead-head"><a class="post-link" href="{{ lead_ledger.url | relative_url }}">{{ lead_ledger.title }}</a></h2>
    {%- if lead_ledger.subtitle %}<p class="lead-dek">{{ lead_ledger.subtitle }}</p>{% endif %}
  </article>
  {%- endif %}

  <div class="strands">
    <section class="strand">
      <h2 class="section-rule"><span>The Weekly Tape</span></h2>
      <ul class="strand-list">
        {%- assign n = 0 -%}
        {%- for p in site.posts -%}
          {%- capture k %}{% include edition.html post=p key=true %}{% endcapture -%}
          {%- if k != "tape" or p.url == lead_tape.url -%}{%- continue -%}{%- endif -%}
          {%- assign n = n | plus: 1 -%}
          {%- if n > 4 -%}{%- break -%}{%- endif %}
        <li>
          <div class="post-dateline">
            <time class="post-date" datetime="{{ p.date | date: '%Y-%m-%d' }}">{{ p.date | date: "%b %-d, %Y" }}</time>
          </div>
          <a class="post-link" href="{{ p.url | relative_url }}">{{ p.title }}</a>
        </li>
        {%- endfor %}
      </ul>
      <p class="more-issues"><a href="{{ '/tape/' | relative_url }}">All Tape notes &rarr;</a></p>
    </section>

    <section class="strand">
      <h2 class="section-rule"><span>Hedgers&rsquo; Ledger</span></h2>
      <ul class="strand-list">
        {%- assign n = 0 -%}
        {%- for p in site.posts -%}
          {%- capture k %}{% include edition.html post=p key=true %}{% endcapture -%}
          {%- if k != "ledger" or p.url == lead_ledger.url -%}{%- continue -%}{%- endif -%}
          {%- assign n = n | plus: 1 -%}
          {%- if n > 4 -%}{%- break -%}{%- endif %}
        <li>
          <div class="post-dateline">
            <time class="post-date" datetime="{{ p.date | date: '%Y-%m-%d' }}">{{ p.date | date: "%b %-d, %Y" }}</time>
          </div>
          <a class="post-link" href="{{ p.url | relative_url }}">{{ p.title }}</a>
        </li>
        {%- endfor %}
      </ul>
      <p class="more-issues"><a href="{{ '/ledger/' | relative_url }}">All Ledger releases &rarr;</a></p>
    </section>
  </div>

</div>

<aside class="rail">
  {%- comment -%} Filled in Task 4: the FX standing and the dashboard block. {%- endcomment -%}
</aside>
</div>

<p class="more-issues front-foot"><a href="{{ '/archive/' | relative_url }}">Back issues &rarr;</a></p>
```

- [ ] **Step 4: Style the grid, the leads and the strands**

Append to the `/* ---- the cover ---- */` block in `assets/css/blog.css`:

```css
.front-grid{display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:0 48px; align-items:start; margin-top:8px}
.front-main{min-width:0}

/* lead story */
.lead{padding-bottom:20px; border-bottom:1px solid var(--rule); margin-bottom:20px}
.lead-figure{margin:0 0 13px}
/* The card is 1200x1036 — nearly square, and ~600px tall at this column width, which would
   push the strands and the whole rail under the fold. Cropped 2:1 from the top it shows the
   price panel and its header; the COT and calendar-spread panels are one click away in the
   article, where they are readable at full size. */
.lead-figure img{display:block; width:100%; aspect-ratio:2/1; object-fit:cover; object-position:top;
  margin:0; border:1px solid var(--rule); border-radius:10px; box-shadow:0 1px 16px rgba(var(--shadow-tint),.10)}
/* an h2 set as a headline — resets the section-opener chrome the global h2 carries */
.lead-head{margin:.1em 0 0; padding-top:0; border-top:none; font-weight:400; letter-spacing:normal}
.lead-head::before{content:none}
.lead-head .post-link{display:inline-block; font:600 clamp(29px,3.2vw,39px)/1.08 var(--serif);
  letter-spacing:-.5px; color:var(--ink); border:none; text-wrap:balance}
.lead-head .post-link:hover{color:var(--gold-ink)}
.lead-dek{margin:.4em 0 0; color:var(--muted); font-style:italic; line-height:1.5; max-width:58ch}
.lead-second{border-bottom:2px solid var(--rule-strong); padding-bottom:22px; margin-bottom:26px}
.lead-second .lead-head .post-link{font-size:clamp(21px,1.9vw,25px); line-height:1.18; letter-spacing:-.2px}
.lead-second .lead-dek{font-size:16px}

/* the two strands */
.strands{display:grid; grid-template-columns:1fr 1fr; gap:34px}
.strand{min-width:0}
.strand-list{list-style:none; padding:0; margin:4px 0 0}
.strand-list li{padding:13px 0; border-top:1px solid var(--rule)}
.strand-list li:first-child{border-top:none}
/* no dek here on purpose: dropping it is what lets eight entries occupy the height four
   took on the old single ladder */
.strand-list .post-link{display:inline-block; margin:.14em 0 0; font:600 19px/1.24 var(--serif);
  color:var(--ink); border:none; text-wrap:balance}
.strand-list .post-link:hover{color:var(--gold-ink)}
.strand .more-issues{margin-top:18px; padding-top:12px; border-top-width:1px}
.front-foot{margin-top:34px}

/* the cover folds down before the sheet does: rail under the strands, then one column */
@media (max-width:939px){
  .front-grid{grid-template-columns:minmax(0,1fr); gap:34px}
}
@media (max-width:600px){
  .strands{grid-template-columns:1fr; gap:26px}
}
```

Bump `css_version` in `_config.yml` from `6` to `7`.

- [ ] **Step 5: Build and check**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
```

Expected: `all checks passed`, `cover posts: 10 links, 10 distinct`, `cover leads: newest Weekly
Tape leads, both hubs linked`, `front-page checks passed`.

- [ ] **Step 6: Screenshot the cover at three widths, both editions**

```bash
cd ~/charthorizon/website/_site && (python3 -m http.server 8899 >/dev/null 2>&1 &) ; sleep 1
cd ~/charthorizon/website
for w in 1280 900 375; do
  node .preview/shot.mjs http://localhost:8899/ /tmp/frontpage-$w.png $w full
done
```

Then open the three files and confirm, by looking:

- 1280: lead card is a wide 2:1 crop showing the price panel, not a squashed square; the two
  strands sit side by side; the rail column is empty but reserved.
- 900: the rail area has moved below the strands, nothing is clipped.
- 375: one column throughout, no horizontal scrollbar, headline does not overflow.

For the dark edition, load the page and set the theme before shooting:

```bash
cd ~/charthorizon/website
cat > /tmp/shot-dark.mjs <<'EOF'
import pkg from '/Users/notwoalike/.npm/_npx/705bc6b22212b352/node_modules/playwright-core/index.js';
const { chromium } = pkg;
const EXE = '/Users/notwoalike/Library/Caches/ms-playwright/chromium-1226/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const browser = await chromium.launch({ executablePath: EXE });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 });
await page.addInitScript(() => localStorage.setItem('ch_theme_mode', 'dark'));
await page.goto(process.argv[2], { waitUntil: 'networkidle' });
await page.waitForTimeout(400);
await page.screenshot({ path: process.argv[3], fullPage: true });
await browser.close();
EOF
node /tmp/shot-dark.mjs http://localhost:8899/ /tmp/frontpage-dark.png
```

Expected in dark: the paper is navy and the lead chart card is **glaring white** — the existing
dimming rule is scoped to `.post-body` and `.board`, and the lead figure is neither. Fix it in
the next step; the screenshot is the evidence that the fix is needed.

- [ ] **Step 7: Extend the dark-edition dimming to the lead card**

In `assets/css/blog.css`, the three rules currently at lines 434, 438 and 440 read
`[data-theme="dark"] :is(.post-body,.board) img:not(.plate)`. Add `.lead-figure` to each
`:is(...)` list, so they become `:is(.post-body,.board,.lead-figure)`. Change nothing else about
them — the `:not(.plate)` guard and the hover behaviour stay as they are.

- [ ] **Step 8: Rebuild and re-shoot dark**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
node /tmp/shot-dark.mjs http://localhost:8899/ /tmp/frontpage-dark2.png
```

Expected: checks pass; the lead card in `/tmp/frontpage-dark2.png` is dimmed to match the night
press run rather than glaring.

- [ ] **Step 9: Commit**

```bash
cd ~/charthorizon/website
git add index.html assets/css/blog.css _config.yml
git commit -m "cover: lead story, second lead and the two strands"
```

---

### Task 4: The rail — FX standing and the dashboard

**Files:**
- Modify: `index.html` (the `<aside class="rail">` left empty in Task 3)
- Modify: `assets/css/blog.css` (extend the cover block)

**Interfaces:**
- Consumes: `.rail` from Task 3; `_data/fx.json` (`site.data.fx`) with keys `as_of`, `bullish`,
  `bearish`, `bullish_pairs` — each currency entry `{cur, score, label}`, each pair entry
  `{pair, spread, label}`; `_includes/board.html` with params `plate`, `w`, `h`, `alt`, `caption`.
- Produces: nothing later tasks consume.

- [ ] **Step 1: Write the failing check**

Append to `.preview/check-front.py`, immediately before the `if fail:` block:

```python
# --- 5. the rail: FX standing and the dashboard block ------------------------
import json

fx = json.loads((REPO / "_data/fx.json").read_text())
if str(fx["as_of"]) not in home:
    fail.append(f"cover does not show the FX as_of date ({fx['as_of']}) from _data/fx.json")
top_bull = fx["bullish"][0]["cur"] if fx["bullish"] else None
if top_bull and top_bull not in home:
    fail.append(f"cover does not show the strongest currency ({top_bull})")
if 'href="/fx/"' not in home:
    fail.append("cover does not link /fx/")
if 'href="/dashboard/"' not in home:
    fail.append("cover does not link /dashboard/")
if "/assets/dashboard/board-screener.webp" not in home:
    fail.append("cover does not carry the dashboard plate")
print(f"  rail:          fx {fx['as_of']}, plate + both links present")

# Constraint: the cover stays first-party apart from the site-wide analytics beacon.
# buymeacoffee is the masthead Support pill — a link the reader clicks, not a request
# the page makes, so it is allowed here and changes nothing about privacy.html.
external = re.findall(r'(?:src|href)="(https?://[^"]+)"', home)
allowed = ("https://static.cloudflareinsights.com/", "https://buymeacoffee.com/")
bad = [u for u in external if not u.startswith(allowed)]
if bad:
    fail.append(f"cover gained third-party requests: {bad}")
print(f"  third-party:   none beyond the beacon")

# The download buttons must stay off while the GitHub account is flagged.
if "releases/download" in home:
    fail.append("cover carries a release download URL — dead while the account is flagged")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website && python3 .preview/check-front.py
```

Expected: FAIL with `cover does not show the FX as_of date`, the missing links and the missing
plate. The rail is still an empty `<aside>`.

- [ ] **Step 3: Fill the rail in `index.html`**

Replace the empty `<aside class="rail">…</aside>` from Task 3 with:

```liquid
<aside class="rail">
  {%- assign fx = site.data.fx -%}
  {%- if fx and fx.bullish %}
  <section class="rail-block rail-fx">
    <h2 class="section-rule"><span>FX standing</span></h2>
    <p class="rail-meta">Currency strength &middot; {{ fx.as_of }}</p>
    <div class="fx-chips fx-col--bull">
      {%- for c in fx.bullish limit: 3 %}<span class="fx-chip">{{ c.cur }} <b>{{ c.label }}</b></span>{% endfor %}
    </div>
    <div class="fx-chips fx-col--bear">
      {%- for c in fx.bearish limit: 3 %}<span class="fx-chip">{{ c.cur }} <b>{{ c.label }}</b></span>{% endfor %}
    </div>
    {%- if fx.bullish_pairs and fx.bullish_pairs.size > 0 -%}
      {%- assign top = fx.bullish_pairs | first %}
    <p class="rail-lede">Widest spread: <strong>{{ top.pair }}</strong> &middot; {{ top.label }}</p>
    {%- endif %}
    <p class="more-issues"><a href="{{ '/fx/' | relative_url }}">The full FX map &rarr;</a></p>
  </section>
  {%- endif %}

  <section class="rail-block rail-board">
    <h2 class="section-rule"><span>The dashboard</span></h2>
    {% include board.html plate="board-screener" w=1320 h=1012
       alt="The ChartHorizon screener: forty futures markets ranked by season, positioning, hedging program and term structure"
       caption="The screener, reading forty markets at once." %}
    <p class="rail-lede">Every chart in these notes comes off the same local-first dashboard —
       it installs on your machine and runs in your browser, with your data staying there.</p>
    <p class="more-issues"><a href="{{ '/dashboard/' | relative_url }}">More about the dashboard &rarr;</a></p>
  </section>
</aside>
```

The chip wrappers carry `fx-col--bull` / `fx-col--bear` because `blog.css` colours
`.fx-col--bull .fx-chip b` through that ancestor. On a bare `.fx-chips` div those classes only
set a `border-color` that never paints, so nothing else comes along for the ride.

`board.html` emits both editions of the plate and the existing `.plate-light` / `.plate-dark`
rules show one per theme; the hidden one is `display:none`, so its `loading="lazy"` never fires
and the reader downloads exactly one.

- [ ] **Step 4: Style the rail**

Append to the `/* ---- the cover ---- */` block in `assets/css/blog.css`:

```css
.rail{min-width:0}
.rail-block + .rail-block{margin-top:30px}
.rail-meta{font:11.5px/1.4 var(--sans); letter-spacing:.05em; text-transform:uppercase;
  color:var(--muted); margin:9px 0 11px}
.rail .fx-chips + .fx-chips{margin-top:7px}
.rail .fx-chip{font-size:12.5px; padding:7px 10px}
.rail-lede{font:15px/1.5 var(--serif); color:var(--muted); margin:12px 0 0; max-width:none}
.rail-lede strong{color:var(--ink)}
/* the plate is furniture here, not a plate on a product page: no bleed, tighter caption */
.rail .board{margin:12px 0 0}
.rail .board figcaption{font-size:13px; margin-top:8px; text-align:left}
.rail .more-issues{margin-top:14px; padding-top:11px; border-top-width:1px}

/* below the fold-down the rail is a full-width footer band, so its two blocks sit
   side by side instead of stacking into a second long ladder */
@media (max-width:939px) and (min-width:601px){
  .rail{display:grid; grid-template-columns:1fr 1fr; gap:34px; align-items:start}
  .rail-block + .rail-block{margin-top:0}
}
```

Bump `css_version` in `_config.yml` from `7` to `8`.

- [ ] **Step 5: Build and check**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
```

Expected: all checks pass, including `third-party: none beyond the beacon`.

- [ ] **Step 6: Screenshot all four states**

```bash
cd ~/charthorizon/website/_site && (python3 -m http.server 8899 >/dev/null 2>&1 &) ; sleep 1
cd ~/charthorizon/website
for w in 1280 900 375; do node .preview/shot.mjs http://localhost:8899/ /tmp/rail-$w.png $w full; done
node /tmp/shot-dark.mjs http://localhost:8899/ /tmp/rail-dark.png
```

Confirm by looking: at 1280 the rail sits beside the leads and the chips wrap at most onto two
lines; at 900 the rail is a two-up band under the strands; at 375 everything is one column with
no horizontal overflow; in dark the plate is the app's own dark board, not a dimmed light one.

- [ ] **Step 7: Verify the network log carries nothing new**

```bash
cd ~/charthorizon/website
cat > /tmp/net-check.mjs <<'EOF'
import pkg from '/Users/notwoalike/.npm/_npx/705bc6b22212b352/node_modules/playwright-core/index.js';
const { chromium } = pkg;
const EXE = '/Users/notwoalike/Library/Caches/ms-playwright/chromium-1226/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const browser = await chromium.launch({ executablePath: EXE });
const page = await browser.newPage();
const hosts = new Set();
page.on('request', r => hosts.add(new URL(r.url()).host));
await page.goto(process.argv[2], { waitUntil: 'networkidle' });
await browser.close();
console.log([...hosts].sort().join('\n'));
EOF
node /tmp/net-check.mjs http://localhost:8899/
```

Expected: exactly `localhost:8899` and `static.cloudflareinsights.com`. Anything else is a
regression against the zero-third-party guarantee and means `privacy.html` would need editing —
stop and report instead.

- [ ] **Step 8: Commit**

```bash
cd ~/charthorizon/website
git add index.html assets/css/blog.css _config.yml
git commit -m "cover: FX standing and dashboard rail"
```

---

### Task 5: Wire the hubs into the rest of the paper

**Files:**
- Modify: `_layouts/post.html` (the `.more-issues` line at the foot of the "Elsewhere in the
  paper" block)
- Modify: `archive.html` (the `.dek` paragraph)

**Interfaces:**
- Consumes: `{% include edition.html post=P key=true %}` (Task 1), `/tape/` and `/ledger/`
  (Task 1).
- Produces: nothing.

- [ ] **Step 1: Write the failing check**

Append to `.preview/check-front.py`, immediately before the `if fail:` block:

```python
# --- 6. every post links into its own hub ------------------------------------
import glob as _glob

missing_hub = []
for f in sorted(_glob.glob(str(SITE / "20*/*/*/*/index.html"))):
    html = pathlib.Path(f).read_text(encoding="utf-8", errors="ignore")
    is_ledger = "Hedgers" in re.search(r"<h1>(.*?)</h1>", html, re.S).group(1)
    want_hub = 'href="/ledger/"' if is_ledger else 'href="/tape/"'
    if want_hub not in html:
        missing_hub.append(pathlib.Path(f).parent.name)
print(f"  post hub links: {len(_glob.glob(str(SITE / '20*/*/*/*/index.html'))) - len(missing_hub)} ok")
if missing_hub:
    fail.append(f"post(s) with no link to their own hub: {missing_hub[:5]}")

arch = read("archive/index.html")
if 'href="/tape/"' not in arch or 'href="/ledger/"' not in arch:
    fail.append("/archive/ does not link both hubs")
```

- [ ] **Step 2: Run it to make sure it fails**

```bash
cd ~/charthorizon/website && python3 .preview/check-front.py
```

Expected: FAIL — every post is listed under `post(s) with no link to their own hub`, and
`/archive/` does not link the hubs.

- [ ] **Step 3: Add the hub link to the post foot**

In `_layouts/post.html`, the block already computes `this_edition` for its section matching.
Add the key right after that capture:

```liquid
{%- capture this_key %}{% include edition.html post=page key=true %}{% endcapture -%}
```

Then replace the closing paragraph of the `post-more` nav:

```liquid
  <p class="more-issues"><a href="{{ '/archive/' | relative_url }}">All back issues &rarr;</a></p>
```

with:

```liquid
  {%- comment -%}
    The section hub first, the whole run second. This is the link that gives every post a
    path into a topical hub — the thing that was missing when Google left 15 of 22 URLs at
    "discovered, currently not indexed".
  {%- endcomment -%}
  <p class="more-issues">
    {%- if this_key == "ledger" -%}
    <a href="{{ '/ledger/' | relative_url }}">All Ledger releases &rarr;</a>
    {%- else -%}
    <a href="{{ '/tape/' | relative_url }}">All Tape notes &rarr;</a>
    {%- endif -%}
    <span class="sep" aria-hidden="true">&middot;</span>
    <a href="{{ '/archive/' | relative_url }}">Back issues &rarr;</a>
  </p>
```

- [ ] **Step 4: Space the two links**

Append to the cover block in `assets/css/blog.css`:

```css
/* two links share the foot rule under a post now — the hub, then the whole run */
.post-more .more-issues .sep{margin:0 10px; color:var(--muted-2)}
```

Bump `css_version` in `_config.yml` from `8` to `9`.

- [ ] **Step 5: Point the archive at both hubs**

In `archive.html`, replace the `.dek` paragraph with:

```liquid
<p class="dek">The full run, newest first — every Weekly Tape note and every Hedgers&rsquo;
   Ledger release since the desk started publishing. By edition:
   <a href="{{ '/tape/' | relative_url }}">The Weekly Tape</a> &middot;
   <a href="{{ '/ledger/' | relative_url }}">Hedgers&rsquo; Ledger</a>.</p>
```

- [ ] **Step 6: Build and run every check**

```bash
cd ~/charthorizon/website && ops/website-build.sh && python3 .preview/check-front.py
```

Expected: `all checks passed` and every one of the six check groups reporting ok, ending in
`front-page checks passed`.

- [ ] **Step 7: Screenshot a post from each edition**

```bash
cd ~/charthorizon/website/_site && (python3 -m http.server 8899 >/dev/null 2>&1 &) ; sleep 1
cd ~/charthorizon/website
node .preview/shot.mjs http://localhost:8899/2026/08/15/paid-to-wait/ /tmp/post-tape.png 1280 full
node .preview/shot.mjs http://localhost:8899/2026/08/16/hedgers-ledger/ /tmp/post-ledger.png 1280 full
```

Confirm by looking at the foot of each: the Tape note offers "All Tape notes → · Back issues →",
the Ledger release offers "All Ledger releases → · Back issues →", and the post body above is
otherwise unchanged.

- [ ] **Step 8: Commit**

```bash
cd ~/charthorizon/website
git add _layouts/post.html archive.html assets/css/blog.css _config.yml
git commit -m "links: every post and the archive lead into the section hubs"
```

---

### Task 6: Final verification and handover

**Files:** none modified.

- [ ] **Step 1: Full build from the committed tree**

```bash
cd ~/charthorizon/website
ops/website-build.sh --from-head && python3 .preview/check-front.py
```

`--from-head` builds the committed state, which is what the nightly job publishes. Expected: both
pass. If `check-front.py` fails here but passed on the working tree, something was left
uncommitted — that is exactly the failure this step exists to catch.

- [ ] **Step 2: Confirm nothing outside the intended set changed**

```bash
cd ~/charthorizon/website
git diff --stat main...HEAD
```

Expected exactly these files: `_config.yml`, `_includes/edition.html`, `_layouts/default.html`,
`_layouts/post.html`, `archive.html`, `assets/css/blog.css`, `index.html`, `ledger.html`,
`tape.html`, plus the spec and plan under `docs/superpowers/`. Nothing else — in particular no
file in `_posts/`, no `_data/fx.json`, no `privacy.html`, no `CNAME`.

- [ ] **Step 3: Confirm no file outside this repo was touched**

```bash
cd ~/charthorizon && git status --porcelain
```

Expected: no changes under `ops/`, `content/` or `dashboard/`. The `website/` directory is its
own inner repo and is ignored by the outer one, so it should not appear here at all.

- [ ] **Step 4: Report, do not deploy**

Summarise for the operator: the six check groups and their output, the screenshot paths, and the
`git diff --stat`. Then **stop**. Deployment is
`ops/website-build.sh --from-head && ops/website-deploy.sh` and it is the operator's call, not
this plan's — as is merging `frontpage-redesign` into `main`.

---

## Self-Review

**Spec coverage.** Every section of the spec maps to a task: edition key → Task 1; hubs → Task 1;
wide shell → Task 2; front page grid, leads, the 2:1 picture and its fallback → Task 3; FX rail
and dashboard block → Task 4; internal links from posts and the archive → Task 5; the spec's six
tests → the six check groups in `.preview/check-front.py` plus the screenshot steps, with spec
test 3 (the lead's WebP resolves) covered by `ops/website-build.sh`'s existing broken-reference
scan, as noted in the deltas.

**Naming consistency.** `key=true` returns `tape` | `ledger` and is compared against those exact
literals in Tasks 1, 3 and 5. The DOM hooks `.front-grid`, `.front-main`, `.rail` are declared in
Task 3 and only filled in Task 4. `css_version` runs 5 → 6 → 7 → 8 → 9, one bump per task that
touches `blog.css`; a single bump at the end would also be correct, but a bump per task keeps
each commit independently deployable.

**Known sharp edges, all handled in the steps.** `push` in Liquid 4 returns a new array rather
than mutating, hence the re-assign in Task 1. `.fx-chip b` takes its colour from a
`.fx-col--bull` / `.fx-col--bear` ancestor, hence the wrapper classes in Task 4. The dark
dimming rule is scoped by class list, hence the explicit edit in Task 3 Step 7 — with a
screenshot first, so the need is demonstrated rather than asserted.
