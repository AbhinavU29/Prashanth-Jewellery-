#!/usr/bin/env python3
"""Daily Kerala rate updater. Reads the month tables published by livegoldkerala.com
(fallback: keralagoldrates.com), saves every day it finds into data/rates.json, and
adds today's silver rate. Exits non-zero, leaving the data untouched, if gold cannot be read."""
import json, re, sys, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UA = {"User-Agent": "Mozilla/5.0 (compatible; PJRatesBot/1.0)"}
MONTHS = ["january","february","march","april","may","june","july","august","september","october","november","december"]
SILVER_URLS = ["https://www.goodreturns.in/silver-rates/kerala.html", "https://keralagoldrates.com/today-silver-rate-kerala/"]

def text(url):
    html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))

def num(x): return float(x.replace(",", ""))

def parse_livegold(body, year):
    """'Thu, 1 Oct ₹13,680 ₹1,09,440 ₹14,924' -> {date: 22K per gram}"""
    out = {}
    for _, d, mon, g in re.findall(r"(\w{3}),\s*(\d{1,2})\s+([A-Za-z]{3,9})\s+₹\s*([\d,]+)\s+₹\s*[\d,]+\s+₹\s*[\d,]+", body):
        m = next(i for i, n in enumerate(MONTHS, 1) if n.startswith(mon.lower()[:3]))
        out[f"{year}-{m:02d}-{int(d):02d}"] = num(g)
    return out

def parse_kgr(body, year):
    """'May 1 ₹13,715 ₹14,962 ...' (several updates per day) -> last one of each day wins"""
    out = {}
    for mon, d, g in re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+₹\s*([\d,]+)\s+₹", body):
        m = next(i for i, n in enumerate(MONTHS, 1) if n.startswith(mon.lower()))
        out[f"{year}-{m:02d}-{int(d):02d}"] = num(g)
    return out

def gold_for_month(year, month):
    name = MONTHS[month - 1]
    tries = [(f"https://www.livegoldkerala.com/gold-rate-history/{year}/{name}", parse_livegold),
             (f"https://keralagoldrates.com/daily-gold-prices-{name}-{year}/", parse_kgr)]
    for url, fn in tries:
        try:
            rows = fn(text(url), year)
            if rows: return rows
        except Exception as e:
            print("source failed:", url, e, file=sys.stderr)
    return {}

def silver_today():
    for url in SILVER_URLS:
        try:
            m = re.search(r"silver[^₹]{0,160}?₹\s*([\d,]+(?:\.\d+)?)\s*(?:/\s*g|per\s*gram)", text(url), re.I)
            if m: return num(m.group(1))
        except Exception as e:
            print("silver source failed:", url, e, file=sys.stderr)
    return None

path = "data/rates.json"
data = json.load(open(path))
now = datetime.now(IST); today = now.strftime("%Y-%m-%d")

found = {}
prev_month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
for y, m in ([prev_month] if now.day <= 3 else []) + [(now.year, now.month)]:
    found.update(gold_for_month(y, m))
if not found:
    sys.exit("Could not read any Kerala gold rates; data left unchanged.")

def upsert(rows, d, v):
    last = rows[-1][1]
    if abs(v - last) / last > 0.15: sys.exit(f"{d}: {v} is more than 15% from the last saved rate {last}; not saving.")
    for r in rows:
        if r[0] == d: r[1] = round(v); return
    rows.append([d, round(v)]); rows.sort()

for d, v in sorted(found.items()):
    if d <= today: upsert(data["g22"], d, v)

s = silver_today()
if s: upsert(data["silver"], today, s)
else: print("Warning: silver rate not found today; gold was still updated.", file=sys.stderr)

data["updated"] = now.isoformat(timespec="seconds")
json.dump(data, open(path, "w"), indent=0)
print(f"{today}: gold days saved {len(found)}, latest {data['g22'][-1]}, silver {s}")
