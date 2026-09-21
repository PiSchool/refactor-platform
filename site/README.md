# site/

The project landing page (paper info, demo screenshots, results) served at
[pischool.github.io/refactor-platform](https://pischool.github.io/refactor-platform/).

Static HTML/CSS/JS: no build step, no dependencies.

## Structure

```
index.html   page content
styles.css   all styling
assets/      images and favicons
```

## Preview locally

```
cd site
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

Pushing to `main` with changes under `site/` triggers
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml), which
publishes this directory as-is to GitHub Pages.

## CI

PRs and pushes that only touch `site/**` are excluded (via `paths-ignore`)
from [`.github/workflows/ci.yml`](../.github/workflows/ci.yml); the
backend/frontend/docs/browser/container checks don't apply to a static
page and won't run.
