#!/usr/bin/env python3
"""One scheduled run. Updates rates + forecast, commits changes to data/*.json."""
import json, os, subprocess, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def run(script):
    return subprocess.run([sys.executable, script], cwd=ROOT).returncode

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)

def commit():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    git("config", "user.name", "pj-rates-bot")
    git("config", "user.email", "actions@users.noreply.github.com")
    git("add", "data")
    if git("diff", "--staged", "--quiet").returncode == 0:
        print("No changes to commit in data/")
        return
    git("commit", "-m", "Update rates " + datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"))
    for attempt in range(5):
        git("pull", "--rebase", "origin", "main")
        push_res = git("push", "origin", "main")
        if push_res.returncode == 0:
            print("Successfully pushed update")
            return
        print(f"Push attempt {attempt + 1} failed: {push_res.stderr.strip()}")
        time.sleep(5)
    print("::error::git push failed. Check Settings > Actions > General > Workflow permissions = Read and write.")

def step():
    rc = run("scripts/update_rates.py")
    run("scripts/forecast.py")
    commit()
    return rc

def has_today_rate():
    try:
        path = os.path.join(ROOT, "data", "rates.json")
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        today = datetime.now(IST).strftime("%Y-%m-%d")
        return bool(d.get("g22") and d["g22"][-1][0] >= today)
    except Exception:
        return False

def main():
    t = datetime.now(IST)
    # If during morning market release (9:00 - 11:00 AM IST) and today's rate isn't in yet,
    # try up to 3 times with a short 2-minute delay between attempts.
    if 9 <= t.hour < 11 and not has_today_rate():
        rc = 1
        for i in range(3):
            rc = step()
            if has_today_rate():
                print(f"Today's rate acquired on attempt {i + 1}")
                return 0
            if i < 2:
                time.sleep(120)
        return 1 if rc != 0 else 0
    else:
        # Standard fast single run (takes < 15 seconds)
        rc = step()
        return 1 if rc != 0 else 0

if __name__ == "__main__":
    sys.exit(main())
