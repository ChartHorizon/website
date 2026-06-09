# Chart-Horizon.com

The **ChartHorizon blog** ("The Weekly Tape"), served at **chart-horizon.com** — a
[Jekyll](https://jekyllrb.com/) site deployed to GitHub Pages.

- `_posts/` — blog posts (Markdown). Add `YYYY-MM-DD-slug.md` and push to publish.
- `_layouts/`, `index.html` — the page shell and the post-list homepage.
- `assets/css/blog.css` — the light "paper" theme; `assets/posts/<slug>/` — post images.
- `impressum.html`, `privacy.html` — legal pages (static HTML, copied as-is).
- `CNAME` — pins the custom domain (do not delete).
- `.github/workflows/deploy-pages.yml` — builds Jekyll and deploys on push to `main`.

## Local preview

Requires Ruby ≥ 2.7:

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000
```
