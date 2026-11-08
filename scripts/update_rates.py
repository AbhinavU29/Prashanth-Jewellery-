#!/usr/bin/env python3
"""Daily Kerala rate updater (runs in GitHub Actions). Reads published Kerala rates from several
sites, backfills any missed days, and writes data/rates.json only when something changed.
Exits non-zero (data untouched) if no gold rate can be read."""
import json, re, sys, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UA = {"User-Agent": "Mozilla/5.0 (compatible; PJRatesBot/1.0)"}
MONTHS = ["january","february","march","april","may","june","july","august","september","october","november","december"]
MON = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
mnum = lambda m: [x[:3] for x in MONTHS].index(m.lower()[:3]) + 1
num = lambda x: float(x.replace(",", ""))
ymd = lambda y, m, d: f"{int(y):04d}-{m:02d}-{int(d):02d}"

def text(url):
    html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))

def try_parse(url, fn, *a):
    try: return fn(text(url), *a)
    except Exception as e:
        print("source failed:", url, e, file=sys.stderr); return {}

# ---- gold parsers -> {date: 22K ₹/gram}
def g_livegold(body, year):   # 'Thu, 1 Oct ₹13,680 ₹1,09,440 ₹14,924'
    return {ymd(year, mnum(m), d): num(g) for _, d, m, g in re.findall(r"(\w{3}),\s*(\d{1,2})\s+([A-Za-z]{3,9})\s+₹\s*([\d,]+)\s+₹\s*[\d,]+\s+₹\s*[\d,]+", body)}
def g_kgr(body, year):        # 'May 1 ₹13,715 ₹14,962 ...' several per day, last wins
    return {ymd(year, mnum(m), d): num(g) for m, d, g in re.findall(r"\b" + MON + r"\s+(\d{1,2})\s+₹\s*([\d,]+)\s+₹", body)}
def g_goodreturns(body, _):   # 'Nov 08, 2026 ₹14,357 (0) ₹13,160 (0)'  (24K then 22K)
    return {ymd(y, mnum(m), d): num(g) for m, d, y, g in re.findall(r"\b" + MON + r"\s+(\d{1,2}),\s*(\d{4})\s*₹\s*[\d,]+\s*\([^)]*\)\s*₹\s*([\d,]+)", body)}
# ---- silver parsers -> {date: ₹/gram}
def s_goodreturns(body, _):   # 'Nov 08, 2026 ₹2,050 ₹20,500 ₹2,05,000 (0)'  (per 10 g first)
    return {ymd(y, mnum(m), d): num(g) / 10 for m, d, y, g in re.findall(r"\b" + MON + r"\s+(\d{1,2}),\s*(\d{4})\s*₹\s*([\d,]+)\s*₹\s*[\d,]+\s*₹\s*[\d,]+", body)}
def s_groww(body, _):         # "08 Nov '26 ₹205.00 0.00"
    return {ymd(2000 + int(y), mnum(m), d): num(g) for d, m, y, g in re.findall(r"\b(\d{1,2})\s+" + MON + r"\s+'(\d{2})\s*₹\s*([\d,.]+)", body)}

def collect_gold(now):
    found, months = {}, [(now.year, now.month)]
    if now.day <= 3: months.insert(0, (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12))
    for y, m in months:
        n = MONTHS[m - 1]
        for url, fn in ((f"https://www.livegoldkerala.com/gold-rate-history/{y}/{n}", g_livegold),
                        (f"https://keralagoldrates.com/daily-gold-prices-{n}-{y}/", g_kgr)):
            rows = try_parse(url, fn, y)
            if rows: found.update(rows); break
    if now.strftime("%Y-%m-%d") not in found:   # monthly pages can lag; Goodreturns has the last 10 days
        for k, v in try_parse("https://www.goodreturns.in/gold-rates/kerala.html", g_goodreturns, now.year).items():
            found.setdefault(k, v)
    return found

def collect_silver(now):
    for url, fn in (("https://www.goodreturns.in/silver-rates/kerala.html", s_goodreturns), ("https://groww.in/silver-rates", s_groww)):
        rows = try_parse(url, fn, now.year)
        if rows: return rows
    return {}

def merge(rows, found, today, yesterday):
    have = {d: i for i, (d, _) in enumerate(rows)}
    for d, v in sorted(found.items()):
        if d > today: continue
        prev = [r[1] for r in rows if r[0] < d]
        if prev and abs(v - prev[-1]) / prev[-1] > 0.15:
            print(f"skip {d}: {v} is >15% from {prev[-1]}", file=sys.stderr); continue
        if d not in have: rows.append([d, round(v)])
        elif d >= yesterday and rows[have[d]][1] != round(v): rows[have[d]][1] = round(v)   # recent days may be revised
    rows.sort()

path = "data/rates.json"
data = json.load(open(path)); before = json.dumps([data["g22"], data["silver"]])
now = datetime.now(IST); today = now.strftime("%Y-%m-%d"); yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
gold = collect_gold(now)
if not gold: sys.exit("Could not read any Kerala gold rates; data left unchanged.")
merge(data["g22"], gold, today, yesterday)
silver = collect_silver(now)
if silver: merge(data["silver"], silver, today, yesterday)
else: print("Warning: no silver rate found; gold was still updated.", file=sys.stderr)
if json.dumps([data["g22"], data["silver"]]) != before:
    data["updated"] = now.isoformat(timespec="seconds")
    json.dump(data, open(path, "w"), indent=0)
    print("updated:", data["g22"][-1], data["silver"][-1])
else:
    print("no change:", data["g22"][-1], data["silver"][-1])
