# Outerfab website

Source of the Outerfab website as a GitHub Page: https://outerfab.github.io/

Static HTML and CSS, built by a standard-library Python script. No framework.

## Build

    python3 build.py            # writes dist/
    python3 build.py --strict   # exit non-zero on warnings and dead internal links
    cd dist && python3 -m http.server 8000

Asset paths start with `/`, so open the site through a local server, not as files.

## Layout

`src/pages/*.html` are pages with front matter (`title`, `description`, `path`, optional `theme`, `schema`, `noindex`).
`src/partials/` holds header, footer and figures, `src/assets/` the stylesheet, fonts and images, `brand/logo/` the logo.
`site.json` holds public values only (form IDs and redirects). Never put a key or token in it.

## Deployment

`.github/workflows/pages.yml` builds on every push to `main` and deploys `dist/` to GitHub Pages.
The build runs with `SITE_URL=https://outerfab.com`: this repository is the live site. `outerfab.com` and `www.outerfab.com` point
to GitHub Pages through Cloudflare DNS (proxied), and the custom domain is set in the repository's Pages settings.

The files `_headers` and `_redirects` in `dist/` are for Cloudflare Pages and have no effect on GitHub Pages.
The redirects in `site.json` therefore also become small forwarding pages; the security headers are not sent.
