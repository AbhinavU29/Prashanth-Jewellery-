# Prashanth Jewellery – Kerala rates
Static site (`index.html`) plus `data/rates.json` (six months of Kerala rates), which a GitHub Action refreshes every morning from livegoldkerala.com (fallback keralagoldrates.com) and Goodreturns.

1. Push this folder to the repo's `main` branch.
2. Settings → Pages → deploy from `main`, root folder.
3. Settings → Actions → General → Workflow permissions → Read and write.
4. Actions → "Update Kerala rates" → Run workflow once to confirm the scraper reads both pages.

Schedule (UTC cron in `.github/workflows/update-rates.yml`): every 5 minutes from 9:00 to 11:00 AM IST, every 30 minutes the rest of the day. The page re-reads `data/rates.json` on the same pattern. GitHub may delay scheduled runs by a few minutes.
