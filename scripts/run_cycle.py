#!/usr/bin/env python3
"""One scheduled run. Updates rates + forecast, commits changes.
Between 9:00 and 11:05 AM IST it keeps polling every 5 minutes inside the same run (GitHub's own 5-minute
cron is unreliable); at any other time it does a single update. Exit code 1 = nothing could be read."""
import os, subprocess, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata"); ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def run(script): return subprocess.run([sys.executable, script], cwd=ROOT).returncode
def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)

def commit():
    if os.environ.get("GITHUB_ACTIONS") != "true": return
    git("config", "user.name", "pj-rates-bot"); git("config", "user.email", "actions@users.noreply.github.com"); git("add", "data/*.json")
    if git("diff", "--staged", "--quiet").returncode == 0: return
    git("commit", "-m", "Update rates " + datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"))
    for _ in range(3):
        git("pull", "--rebase", "-q")
        if git("push").returncode == 0: print("pushed update"); return
        time.sleep(5)
    print("::error::git push failed. Check Settings > Actions > General > Workflow permissions = Read and write.")

def step():
    rc = run("scripts/update_rates.py"); run("scripts/forecast.py"); commit(); return rc

def in_window(t): return 9 <= t.hour < 11 or (t.hour == 11 and t.minute < 5)

def main():
    t = datetime.now(IST)
    if t.hour == 8 and t.minute >= 40: time.sleep((t.replace(hour=9, minute=0, second=0, microsecond=0) - t).total_seconds()); t = datetime.now(IST)
    if not in_window(t): return 1 if step() else 0
    end = t.replace(hour=11, minute=5, second=0, microsecond=0); fails = 0
    while True:
        fails = fails + 1 if step() else 0
        t = datetime.now(IST)
        if t >= end: break
        time.sleep(min(300, (end - t).total_seconds()))
    return 1 if fails >= 6 else 0

if __name__ == "__main__": sys.exit(main())
