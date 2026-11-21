# Product Requirements Document — Prashanth Jewellery · Kerala Gold & Silver Rate Intelligence

| | |
|---|---|
| **Product** | Kerala Gold Rate Intelligence and Prediction Platform for Prashanth Jewellery, Thalassery |
| **Document status** | Living document, reflects the project as of 21 Nov 2026 |
| **Owner** | Abhinav U (Instagram `abhinav.u_`, YouTube `@AbhinavU`) |
| **Built with** | Claude (AI-assisted); footer credit: "Created by AI · Powered by Abhinav.U" |
| **Repo** | `AbhinavU29/Prashanth-Jewellery-` (GitHub Pages + GitHub Actions) |
| **Preview** | https://claude.ai/artifact/1sHz9f4McxcEYAZ8J83kvA (private snapshot, no daily auto-update) |

Legend: ✅ completed · 🟡 partly done / needs verification · 🔲 planned · ⛔ pending (needs owner action)

---
## 1. Purpose and scope
**Problem.** Customers and staff want one trustworthy place to see today's Kerala 22K/24K gold and silver board rates, how they moved, and what may come next. Rates change several times a day, differ slightly between websites, and are usually shown without history or uncertainty.

**Goal.** A fast, premium, mobile-first website that shows (1) published Kerala rates, (2) six months of history as chart and table, (3) a clearly labelled, honestly calibrated prediction, (4) a price calculator, and (5) shop details. It updates itself without manual work.

**In scope:** price intelligence, calculator, shop information. **Out of scope (by owner's decision):** billing, ordering, e-commerce, user accounts.

**Audience:** Prashanth Jewellery customers (mostly on phones), shop staff, the owner.

## 2. Feature inventory

### 2.1 Rates (✅)
- 22K gold per gram and per pavan (8 g); 24K per gram and per 10 g; silver (999) per gram and per kg.
- 24K is **derived** from 22K at 24/22 (matches published 24K, e.g. ₹14,225 on 30 Oct 2026). Silver is a separate series.
- Change vs yesterday; when unchanged, the change is shown versus the **last day the rate actually moved** (e.g. "Unchanged · ▲ ₹10 vs 6 Nov") so weekends are still informative.
- Hero "phone" card with 30-day bar strip (low → high colour scale), Low/High legend, last-update time.
- **Colour semantics (owner decision): high / rising = red, low / falling = green** (buyer's view). Applied to rate cards, bars, chart markers, table rows, stat cards, forecast tags. The live "market open" dot stays green.

### 2.2 History: six months, chart and table (✅)
- Month tabs for the last 6 months (currently Jun–Nov 2026) × asset tabs (22K / 24K / Silver) × view toggle (Chart / Table). Data stored for May 2026 onward.
- Table: every calendar day of the month, **earliest date first**; days without a verified rate show "No verified rate"; highest and lowest rows highlighted and badged; today's row badged "Today" (or "Latest" if stale).
- Chart: smooth line + area, hover/touch tooltip, high/low markers, pulsing "Today ₹…" marker, line-draw animation.
- Summary cards: Lowest (with date), Highest (with date), **Today's price range** (today's rate positioned on a low→high bar; "Month-end price range" for past months).
- Mobile: table rows become cards (date + rate + change + per-pavan/kg), no sideways scrolling.

### 2.3 Prediction (✅ rebuilt, see §5)
Projected range for the next board rate, 80% confidence range (never a single "guaranteed" price), centre, tag (Neutral / Leaning up / Leaning down), basis chip, "unchanged on x% of Sundays", driver list, accuracy panel (back-test + live record), explicit disclaimer. Predictions are **visually separate from actual rates**: dashed line + translucent band + "Predicted" label on the chart, dashed "Predicted" row in the table, dashed "Predicted" chip.

### 2.4 Price calculator (✅)
22K / 24K / silver; weight in grams, pavan (gold) or kg (silver); making charge % (blank by default); GST % (3% default, editable). Shows rate, weight, metal value, making charge, GST, total. Large touch targets; 16 px inputs (no iOS zoom). Estimate only.

### 2.5 Status and freshness (✅)
Header badge "Kerala Market Live / Awaiting today's rate" by comparing latest rate date with today (IST). "Daily update status" card: rate date, last updated, source, last checked, days of history.

### 2.6 Shop and brand (✅ / ⛔)
- Prashanth Jewellery, Thalassery, Kannur, Kerala. Services: gold and silver jewellery for ladies, gents, kids; polishing and repair.
- Google Maps card + "Open in Google Maps" / "Get directions" (coordinates 11.7478537, 75.492669). Embedded map removed (blank in sandboxed preview).
- Owner's logo (gold ring "PJ JEWELLERS") used in nav, intro, shop panel, footer, favicon (embedded WebP). Original in `assets/logo.png`.
- Instagram and YouTube round icons in footer.
- ⛔ Street address, phone and opening hours are **not verified**; fill the `SHOP` object in `index.html` to show them.

### 2.7 Experience layer (✅)
Intro splash (logo reveal with shine, then today's 22K/24K/silver rates with trend colour, sparkline, "Updated …" stamp; tap to skip; ~4.5 s), dark/light mode (follows device, remembered), count-up prices, chart draw animation, skeleton/blur loading states on refresh and tab changes, View-Transition cross-fade on tab switches (fallback: blur loading), scroll reveals, floating price cards, pointer tilt on the hero card, hover lifts. Continuous motion is switched off for "reduce motion" users; one-time reveals stay.

## 3. Design system (✅ rebuilt 21 Nov 2026)
Apple-inspired: SF Pro (system) → Inter fallback; large, tightly tracked headings; graphite neutrals (`#F5F5F7` / `#1D1D1F`, dark `#000` / `#1C1C1E`); one accent (blue `#0A84FF` → indigo `#5E5CE6`); semantic red `#FF3B30` and green `#34C759`; frosted-glass cards (blur + saturate), hairline borders, soft layered shadows, segmented controls, pill buttons. No gold UI colours (the gold logo is the only gold). Breakpoints: ≤640 px phone (card tables, stacked), 641–1024 px tablet, >1024 px desktop. Theme history: peach/purple-orange (v1) → gold (v2, rejected by owner) → Apple graphite/blue (v3, current).

## 4. Data
### 4.1 Series and sources
| Series | Coverage | Source(s) |
|---|---|---|
| 22K ₹/g | daily 1 May → present (no gaps) | Oct–Nov: livegoldkerala.com, Goodreturns, keralagold.org, goldkerala.com; Jun–Sep: livegoldkerala.com; May: keralagoldrates.com (last update of each day). All mirror the Kerala association (AKGSMA) board rate |
| Silver ₹/g | 14 Oct → present | Goodreturns, Groww, Bankbazaar (earlier months not verifiable: sources contradicted each other) |
| IBJA 999 gold AM/PM ₹/10 g | 14 Oct → 20 Nov (backfilled) | bullionworld.in, 5paisa, IBJA daily report |
| Market note | 17 Nov | IBJA daily bullion report |
Known data caveats: sources differ by a few rupees on some days (e.g. 4 Nov 12,825 vs 13,090; 13 May spike to ₹15,390 confirmed by two sources); 4–6 Nov intraday revisions. The rule: keep the first verified value for old days; recent days (today/yesterday) may be revised.

### 4.2 Files (`data/`)
`rates.json` (`g22`, `silver` as `[date, value]`, `updated`, `source`) · `market.json` (`ibja`, `note`) · `forecast.json` (see §5) · `forecast_log.json` (every forecast + the actual rate once known) · `market_history.json` (daily COMEX gold, USD/INR, DXY, US 10Y, crude; created on first successful run). `index.html` embeds fallback copies of rates and forecast so it also works as a single file.

## 5. Prediction engine (`scripts/forecast.py`)
### 5.1 Findings that shaped the design (measured on 205 days of Kerala data)
- Daily move σ ≈ 1.3%; lag-1…5 autocorrelation ≈ 0 (−0.09 … 0.05). Walk-forward tests of AR(1), EWMA momentum, 3-day momentum and mean reversion **did not beat "unchanged"** (MAE 0.86% vs 0.87–0.96%; direction hit rate 46–53%). The previous page's "Bullish/Bearish" labels from momentum therefore had no edge and its ±0.6σ range was too narrow.
- Kerala board ≈ **1.012 × IBJA 999** of the same day (σ 0.3%), but relates to the *previous* day's IBJA only at σ 1.4%. So the next move is driven by overnight international gold/INR changes, not by Kerala's own history.
- The board is often unchanged on Sundays (23% of last 26 Sundays exactly unchanged; far smaller moves than weekdays).
### 5.2 Method
1. **Volatility:** EWMA (λ = 0.94) of daily log-returns × day-of-week factor (shrunk toward 1).
2. **Range:** centre ± z·σ, where z is the empirical 80% quantile of past standardised moves (calibrated, not assumed normal). Rounded to ₹5.
3. **Centre / direction:** priority (a) live signal = COMEX gold (Yahoo `GC=F`) × USD/INR (`INR=X`) move since ~10:30 IST on the last rate date, pass-through 0.9; (b) ridge regression (α = 30) on gold-in-INR, DXY, US 10Y, crude, last return, 5-day momentum, Sat/Sun flags — **activated only if** out-of-sample (walk-forward ≥ 40 days) MAE beats "unchanged" by ≥ 3% and direction accuracy ≥ 55%; (c) otherwise "unchanged".
4. **Accountability:** back-test (last 90 days: coverage, average width vs a flat ±1.3% band) and a **live track record** (`forecast_log.json`), both shown on the page.
### 5.3 Current output (21 Nov 2026)
For Sun 22 Nov: ₹11,235 – ₹11,700, centre ₹11,465, Neutral, basis "Kerala history only". Back-test: 90 days, coverage 78.9% (target 80%), average width ₹396 vs ₹457 for a flat band.
### 5.4 Status
✅ Range model, calibration, weekday effect, back-test, log, UI. ✅ Ridge pipeline tested on synthetic data (stays off for noise, switches on when gold truly drives the rate). 🟡 Live Yahoo / IBJA feeds **not yet run against the real sites** (sandbox had no internet). 🔲 Review model after ~30 live forecasts; add MCX gold, Kerala premium model, gradient boosting if justified.

## 6. Update pipeline and schedule
`.github/workflows/update-rates.yml` → `scripts/update_rates.py` (gold: livegoldkerala → keralagoldrates → Goodreturns; silver: Goodreturns → Groww; IBJA table; backfills missing days; sanity rule ±15% from previous; writes only on change) → `scripts/forecast.py` (continue-on-error) → commit `data/*.json`.
**Schedule (IST):** every 5 min 9:00–11:00; every 30 min the rest of the day (UTC crons in the workflow). The page re-reads `data/rates.json` and `forecast.json` on the same pattern (5 min 9–11, else 30 min) and when the tab becomes visible. GitHub may delay scheduled runs; private repos have a free-minutes quota (~70 runs/day).

## 7. Technical details
Single-file static site (`index.html`, vanilla JS, inline SVG charts, no frameworks), logo embedded as WebP in CSS variables. Hosting: GitHub Pages. Python 3 standard library only. Repo layout: `index.html`, `PRD.md`, `README.md`, `assets/logo.png`, `data/*.json`, `scripts/update_rates.py`, `scripts/forecast.py`, `.github/workflows/update-rates.yml`. No browser storage except theme preference (guarded). Accessibility: ARIA tablists, labelled icons, focus rings, reduced-motion handling. Typography uses curly apostrophes.

## 8. Quality and testing done
Syntax checks (`node --check`, `ast.parse`), DOM-stub tests of rendering (tables 21–31 rows, today badge, colour inversion, range card, intro card, forecast panel, chart overlay), parser tests with captured page text, synthetic ridge tests. **Not done:** visual QA on real devices, live-site scraper runs, cross-browser testing (Safari/Firefox), Lighthouse/accessibility audit.

## 9. Delivery log (what has been built, in order)
1. Dashboard concept → real Kerala rates replaced all mock data. 2. Peach/purple "AI SaaS" theme from owner's reference; hosted preview. 3. Month tabs, chart/table toggle with highest/lowest, six months of data, ascending table, mobile cards. 4. Calculator, dark/light mode, shop section, Google Maps card, footer credit and social icons. 5. Auto-update pipeline (GitHub Actions), multi-source scraper, backfill, 5-min morning cadence. 6. Colour rules (high red / low green, trend-based on unchanged days), today's row and today's range card, Today marker on chart. 7. Intro animation (ring → owner's logo), today's rates on loading screen. 8. Gold theme (rejected) → Apple-inspired redesign, animation system, count-up, skeletons. 9. Prediction rebuilt with evidence-based method, back-test and live accountability. 10. This PRD.

## 10. Backlog
| Item | Status |
|---|---|
| Upload repo, enable Pages, set Actions write permission, run workflow once | ⛔ owner |
| Verify Yahoo / IBJA / Goodreturns parsers on first live run; fix selectors if a site blocks GitHub IPs | ⛔ first run |
| Add shop phone, hours, street address | ⛔ owner |
| Silver history before 14 Oct | ⛔ needs trusted source |
| Evaluate ridge model once ≥ 80 aligned samples; tune α, features | 🔲 |
| Notifications (WhatsApp/Telegram) on large moves; shareable rate image | 🔲 |
| Malayalam language toggle | 🔲 |
| Real-device QA, Lighthouse ≥ 90, Safari/Firefox checks | 🔲 |
| Custom domain; analytics | 🔲 |

## 11. Risks and assumptions
Scraped sites can change layout or block bots (pipeline fails safe: data untouched, workflow shows red). Board rates are revised intraday; sources disagree by ₹5–25. Prediction is statistical, not advice; the page says so. GitHub cron is best-effort. Rates exclude GST, making charges and hallmarking fees. Assumed: AKGSMA board rate is the reference for "Kerala rate".

## 12. Acceptance criteria
Page shows today's rate within one scheduled cycle of publication; status badge Live on days with a rate; history for 6 months with correct highlight rows; prediction always shown as a range labelled Predicted; back-test coverage within ±8 points of 80%; usable at 360 px width with no horizontal scroll; dark/light and reduced-motion respected; owner can add a day's rate manually by editing `data/rates.json`.

## 13. Maintenance runbook
Add a missing day: edit `data/rates.json` (`g22`/`silver` rows `["YYYY-MM-DD", value]`, keep sorted), commit. Force an update: Actions → Update Kerala rates → Run workflow. Scraper red: open the run log, find "source failed" / "Could not read" lines, adjust regexes in `update_rates.py` (parsers are tested on sample text in this PRD's history: see function docstrings). Reset forecast history: delete `data/forecast_log.json`. Change schedule: edit the `cron` lines (UTC = IST − 5:30).
