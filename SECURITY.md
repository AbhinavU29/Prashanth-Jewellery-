# Security notes — Prashanth Jewellery rates site

## What this site is
A **static, public, read-only** website: no login, no accounts, no database, no payments, no user data collected. Because there is nothing to sign in to, there is no authentication or server session to protect. Adding a login screen would only be decoration. If admin features are ever added (editing rates in a browser, customer accounts), they need a real backend or an identity provider (Cloudflare Access, Auth0, Firebase Auth) — see "Future" below.

## What is implemented
| Area | Measure |
|---|---|
| Browser policy | Content-Security-Policy meta tag: only own files, inline script/style, Google Fonts; no frames, no objects, no form posts, no `<base>`; `connect-src 'self'` so the page can only read its own `data/*.json`. |
| Privacy | `Referrer-Policy: strict-origin-when-cross-origin`; external links use `rel="noopener noreferrer"`; no cookies; no analytics; no third-party scripts. |
| Clickjacking | Frame-busting script on `*.github.io`. For real `X-Frame-Options` / `frame-ancestors` put the site behind Cloudflare or Netlify and use `_headers`. |
| Input validation | Calculator values are clamped (weight ≤ 1,000,000 g, making charge 0–100%, GST 0–50%) and parsed as numbers. |
| Data validation | `rates.json` and `forecast.json` are checked before use (shape, ISO dates, ascending order, numeric bounds, allowed tags). Anything malformed is ignored and the last good data stays on screen. Data is rendered with `textContent` or as numbers, never as raw HTML from files. |
| Page state ("session") | Selected month, asset, view, calculator inputs and scroll position are kept in `sessionStorage` for the tab. State expires after 12 hours and is discarded if it is tampered with or invalid. The intro animation plays once per tab session. Theme choice is the only thing in `localStorage`. |
| Updater | https only; host allow-list (also checked after redirects); 4 MB response cap; timeouts; value bounds; 15% jump guard; median across sources for the newest days; writes only on change. |
| CI | Workflow permission is `contents: write` only (to commit `data/*.json`); uses the built-in `GITHUB_TOKEN`; no personal tokens or API keys exist anywhere in the repo. |

## Secrets
There are none today. If a paid data API is added later: store the key in **GitHub → Settings → Secrets and variables → Actions**, read it from the environment in the script, never commit it, never put it in `index.html` (anything in the page is public).

## Recommended GitHub settings (owner)
1. Turn on two-factor authentication for your GitHub account.
2. Repo → Settings → Pages → tick **Enforce HTTPS**.
3. Settings → Code security → enable Dependabot alerts and Secret scanning.
4. Settings → Branches → protect `main` (the Actions bot needs "allow GitHub Actions to push").
5. Pin third-party actions to commit SHAs (currently `actions/checkout@v4`, `actions/setup-python@v5`).

## Known limits
- `'unsafe-inline'` is needed in the CSP because the script and styles are inline. Moving them into separate files would allow a stricter policy.
- GitHub Pages cannot send custom HTTP headers; `_headers` only applies on Netlify/Cloudflare Pages.
- Scraped prices come from public websites and are validated for range, not cryptographically verified.

## Reporting a problem
Contact the owner via the Instagram (@abhinav.u_) or X (@abhinav_u_) links on the site.
