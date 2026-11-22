# Setup and "why isn't it updating?" checklist

## One-time setup (5 minutes)
1. Unzip `prashanth-jewellery-site.zip`. **The files are at the top level of the zip** (no extra folder). Upload *everything*, including the hidden `.github` folder, to the **root** of your repo (Add file → Upload files; on Windows enable "Hidden items", on Mac press Cmd+Shift+.).
2. Settings → Pages → Branch `main`, folder `/ (root)` → Save.
3. Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
4. Actions tab → "Update Kerala rates" → **Run workflow**. (Uploading the scripts also starts one run by itself.)
5. Open the finished run → **Summary**. It lists every data source with `ok` / `failed` and the row count, and the line "Saved: 22K …".

## Schedule
- 8:50 AM IST: a run starts, waits for 9:00, then **polls every 5 minutes until 11:05 AM**.
- Every 30 minutes the rest of the day (at :07 and :37 past the hour).
- The page re-reads the data every 5 minutes between 9 and 11 AM and every 30 minutes otherwise.
- A public repo has unlimited Actions minutes. A private repo has 2,000 free minutes a month, and the morning run alone uses about 3,600, so keep the repo public (or buy minutes).

## If the website still shows old rates
| Symptom | Cause | Fix |
|---|---|---|
| Actions tab has no "Update Kerala rates" | `.github/workflows/update-rates.yml` is not at the repo root (often uploaded inside a folder, or the hidden folder was skipped) | Re-upload so the path is exactly `.github/workflows/update-rates.yml` |
| Run is red: "git push failed" | Workflow permission is read-only | Step 3 above |
| Run is red: "No gold rate could be read" | Data sites blocked GitHub or changed layout | Open the Summary, see which source failed, send me the text |
| Run is green but "No change" all day | Sources have not published the new rate yet, or the board really did not move (e.g. Sundays) | Check the "Newest saved rate" warning line |
| Runs exist but the site is old | Pages not deployed from `main`, or browser cache | Settings → Pages shows the last deploy; hard-refresh the page |
| No scheduled runs at all | GitHub delays or pauses schedules on inactive repos; a push or "Run workflow" wakes it up | Click Run workflow once |

## Manual fix in 1 minute
Edit `data/rates.json`, add `["2026-11-23", 11500]` to `g22` (and `silver`), keep dates ascending, commit. The site updates immediately.
