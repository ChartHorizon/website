# CLAUDE.md

## What this is

The standalone **landing page** for ChartHorizon, served at **chart-horizon.com**.
Pure static HTML/CSS/JS — no build system, no framework, no package manifest.
Three pages (`index.html`, `impressum.html`, `privacy.html`) plus `assets/`.
Deployed to **GitHub Pages** from this repo's `main` via
`.github/workflows/deploy-pages.yml` (uploads the repo root). The custom domain is
pinned by the `CNAME` file (`chart-horizon.com`); DNS lives at Cloudflare (DNS-only).

This repo is **public** (it only holds the same static files the live site already
serves — nothing secret). It was split out of the ChartHorizon dashboard repo, which
is now private; this site must therefore **not** link to dashboard source, installers,
GitHub releases, or describe the dashboard as a public download.

## Editing

Edit the HTML/CSS/JS directly. Preview locally with a static server (the page uses
relative asset paths, so `file://` works for a quick look, but a server matches prod):

```bash
python3 -m http.server 8080   # then open http://localhost:8080
```

Pushing to `main` redeploys via GitHub Pages. Keep `CNAME` intact on every change —
removing it drops the custom domain.
