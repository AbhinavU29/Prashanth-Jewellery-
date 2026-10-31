# Prashanth Jewellery – Kerala rates
Static site (`index.html`) plus `data/rates.json` (six months of Kerala rates), which a GitHub Action refreshes every morning from livegoldkerala.com (fallback keralagoldrates.com) and Goodreturns.

1. Push this folder to the repo's `main` branch.
2. Settings → Pages → deploy from `main`, root folder.
3. Settings → Actions → General → Workflow permissions → Read and write.
4. Actions → "Update Kerala rates" → Run workflow once to confirm the scraper reads both pages.
