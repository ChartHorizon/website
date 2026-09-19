# Chart-Horizon.com

The **ChartHorizon blog** ("The Weekly Tape"), served at **chart-horizon.com** — a
[Jekyll](https://jekyllrb.com/) site deployed to **Cloudflare Pages**.

> **A `git push` to this repo publishes nothing.** It is a backup. The site is built from the
> committed tree and uploaded by a build step that runs outside this repo, nightly and on
> demand. Deployment moved off GitHub Pages on 2026-08-15 and stays there.

- `_posts/` — blog posts (Markdown). Add `YYYY-MM-DD-slug.md` and commit; the nightly build
  publishes the committed tree.
- `_layouts/`, `index.html` — the page shell and the broadsheet cover (home page).
- `assets/css/blog.css` — the light "paper" theme; `assets/posts/<slug>/` — post images.
- `_data/fx.json` — the daily FX strength snapshot rendered by `/fx/`.
- `impressum.html`, `privacy.html` — legal pages.
- `CNAME` — pins the custom domain (do not delete).
- `.github/workflows/deploy-pages.yml` — **dead**, kept only as a record of the old path.

## Local preview

The site is **Jekyll 3.10** (the version `github-pages` pinned; see the `Gemfile`, which is
kept as that record and is not used to build). Render it with any matching Jekyll into
`_site/` and serve that directory to preview.
