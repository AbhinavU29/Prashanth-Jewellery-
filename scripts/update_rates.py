#!/usr/bin/env python3
"""Fetch Kerala 22K gold, silver and the IBJA benchmark and merge them into data/*.json.

Hardening: https only, host allow-list (also after redirects), size cap, timeouts, value bounds,
15% jump guard, majority/median across sources for the newest two days, writes only on change.
Exit code 1 (red run, e-mail from GitHub) when no gold rate could be read at all."""
import json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
ALLOWED = {"www.livegoldkerala.com", "livegoldkerala.com", "keralagoldrates.com", "www.goodreturns.in", "goodreturns.in", "groww.in", "bullionworld.in"}
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-IN,en;q=0.9"}
MAX_BYTES = 4_000_000
GOLD_OK, SILVER_OK = (3000, 60000), (30, 1500)
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
MON = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
mnum = lambda m: [x[:3] for x in MONTHS].index(m.lower()[:3]) + 1
num = lambda x: float(x.replace(",", ""))
ymd = lambda y, m, d: f"{int(y):04d}-{m:02d}-{int(d):02d}"
REPORT = []

def raw(url):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED: raise ValueError("blocked url " + url)
    last = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                if urllib.parse.urlparse(r.geturl()).hostname not in ALLOWED: raise ValueError("redirected off the allow-list")
                return r.read(MAX_BYTES).decode("utf-8", "ignore")
        except Exception as e: last = e
    raise last

def text(url):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw(url)))

def attempt(name, url, fn, *a):
    try: rows = fn(text(url), *a)
    except Exception as e: REPORT.append((name, f"failed: {str(e)[:70]}", 0)); return {}
    REPORT.append((name, "ok" if rows else "no rows found (layout changed?)", len(rows))); return rows

def parse_kgr_revisions(raw_html):
    matches = re.findall(r'data-22k="?(\d+)"?\s+data-24k="?(\d+)"?\s+data-date="?([\d-]+)"?\s+data-datetime="?([\d\-T:+]+)"?', raw_html)
    by_date = {}
    for g22, g24, d, dt in matches:
        v22, v24 = int(g22), int(g24)
        if not (GOLD_OK[0] <= v22 <= GOLD_OK[1]): continue
        tm = dt.split("T")[1][:5] if "T" in dt else "09:30"
        hr, mn = [int(x) for x in tm.split(":")[:2]]
        period = "AM" if hr < 12 else "PM"
        hr12 = hr % 12 or 12
        time_str = f"{hr12}:{mn:02d} {period}"
        by_date.setdefault(d, []).append({
            "dt": dt, "time": time_str, "session": "Morning", "g22": v22, "g24": v24
        })
    revs = {}
    for d, items in by_date.items():
        items.sort(key=lambda x: x["dt"])
        clean = []
        for it in items:
            if not clean or clean[-1]["g22"] != it["g22"]: clean.append(it)
        if len(clean) > 1:
            for idx, it in enumerate(clean):
                if idx == 0: it["session"] = "Morning"
                elif idx == 1:
                    tm = int(it["dt"].split("T")[1][:2]) if "T" in it["dt"] else 13
                    it["session"] = "Afternoon" if tm < 16 else "Evening"
                else: it["session"] = "Evening"
                it.pop("dt", None)
            revs[d] = clean
    return revs

# ---- parsers -> {date: value}
def g_livegold(b, y):  return {ymd(y, mnum(m), d): num(g) for _, d, m, g in re.findall(r"(\w{3}),\s*(\d{1,2})\s+([A-Za-z]{3,9})\s+₹\s*([\d,]+)\s+₹\s*[\d,]+\s+₹\s*[\d,]+", b)}
def g_kgr(b, y):       return {ymd(y, mnum(m), d): num(g) for m, d, g in re.findall(r"\b" + MON + r"\s+(\d{1,2})\s+₹\s*([\d,]+)\s+₹", b)}
def g_goodreturns(b, _): return {ymd(y, mnum(m), d): num(g) for m, d, y, g in re.findall(r"\b" + MON + r"\s+(\d{1,2}),\s*(\d{4})\s*₹\s*[\d,]+\s*\([^)]*\)\s*₹\s*([\d,]+)", b)}
def s_goodreturns(b, _): return {ymd(y, mnum(m), d): num(g) / 10 for m, d, y, g in re.findall(r"\b" + MON + r"\s+(\d{1,2}),\s*(\d{4})\s*₹\s*([\d,]+)\s*₹\s*[\d,]+\s*₹\s*[\d,]+", b)}
def s_groww(b, _):     return {ymd(2000 + int(y), mnum(m), d): num(g) for d, m, y, g in re.findall(r"\b(\d{1,2})\s+" + MON + r"\s+'(\d{2})\s*₹\s*([\d,.]+)", b)}
def ibja(b, _):        return {f"{y}-{m}-{d}": [int(a), int(p)] for d, m, y, a, p in re.findall(r"(\d{2})/(\d{2})/(\d{4})\s+Gold\s+999\s+(\d{5,6})\s+(\d{5,6})\s+10 Gms", b)}

def consensus(sources, lo_hi, recent_from):
    """sources: ordered list of {date: value}. Newest days: median across sources; older days: first source wins."""
    dates = sorted({d for s in sources for d in s}); out = {}
    for d in dates:
        vals = [s[d] for s in sources if d in s and lo_hi[0] <= s[d] <= lo_hi[1]]
        if not vals: continue
        vals.sort(); out[d] = vals[len(vals) // 2] if d >= recent_from else vals[0] if len(vals) == 1 else next(s[d] for s in sources if d in s and lo_hi[0] <= s[d] <= lo_hi[1])
    return out

def merge(rows, found, today, yday):
    have = {d: i for i, (d, _) in enumerate(rows)}
    for d, v in sorted(found.items()):
        if d > today: continue
        prev = [r[1] for r in rows if r[0] < d]
        if prev and abs(v - prev[-1]) / prev[-1] > 0.15: print(f"skip {d}: {v} is >15% from {prev[-1]}", file=sys.stderr); continue
        if d not in have: rows.append([d, round(v)])
        elif d >= yday and rows[have[d]][1] != round(v): rows[have[d]][1] = round(v)
    rows.sort()

def main():
    now = datetime.now(IST); today = now.strftime("%Y-%m-%d"); yday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    path = "data/rates.json"; data = json.load(open(path))
    revisions = data.get("revisions", {})
    before = json.dumps([data.get("g22", []), data.get("silver", []), data.get("revisions", {})], sort_keys=True)
    months = [(now.year, now.month)] + ([(now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)] if now.day <= 3 else [])
    lg, kg = {}, {}
    for y, m in months:
        n = MONTHS[m - 1]
        kgr_url = f"https://keralagoldrates.com/daily-gold-prices-{n}-{y}/"
        try:
            kgr_raw = raw(kgr_url)
            m_revs = parse_kgr_revisions(kgr_raw)
            revisions.update(m_revs)
            kgr_txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", kgr_raw))
            kg_rows = g_kgr(kgr_txt, y)
            for rd, ritems in m_revs.items():
                if ritems: kg_rows[rd] = ritems[-1]["g22"]
            kg.update(kg_rows)
            REPORT.append((f"keralagoldrates {n}", "ok", len(kg_rows)))
        except Exception as e:
            REPORT.append((f"keralagoldrates {n}", f"failed: {str(e)[:70]}", 0))
        lg.update(attempt(f"livegoldkerala {n}", f"https://www.livegoldkerala.com/gold-rate-history/{y}/{n}", g_livegold, y))
    gr = attempt("goodreturns gold", "https://www.goodreturns.in/gold-rates/kerala.html", g_goodreturns, now.year)
    gold = consensus([lg, kg, gr], GOLD_OK, yday)
    sg = attempt("goodreturns silver", "https://www.goodreturns.in/silver-rates/kerala.html", s_goodreturns, now.year)
    sw = attempt("groww silver", "https://groww.in/silver-rates", s_groww, now.year)
    silver = consensus([sg, sw], SILVER_OK, yday)
    ib = attempt("IBJA benchmark", "https://bullionworld.in/ibja-gold-price.php", ibja, now.year)
    lines = ["### Kerala rate update " + now.strftime("%d %b %Y %H:%M IST"), "| Source | Result | Rows |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in REPORT]
    if not gold:
        lines.append("**No gold rate could be read from any source. Data left unchanged.**")
    else:
        merge(data["g22"], gold, today, yday)
        if silver: merge(data["silver"], silver, today, yday)
        data["revisions"] = revisions
        if json.dumps([data["g22"], data["silver"], data["revisions"]], sort_keys=True) != before:
            data["updated"] = now.isoformat(timespec="seconds")
            json.dump(data, open(path, "w"), indent=0)
            lines.append(f"**Saved:** 22K {data['g22'][-1]}, silver {data['silver'][-1]}, revisions: {len(data['revisions'])}")
        else:
            lines.append(f"No change: 22K {data['g22'][-1]}, silver {data['silver'][-1]}")
        if data["g22"][-1][0] < yday: lines.append(f"::warning::Newest saved rate is {data['g22'][-1][0]} - sources have nothing newer yet")
    try:
        mp = "data/market.json"; mk = json.load(open(mp)); old = json.dumps(mk.get("ibja"), sort_keys=True); mk.setdefault("ibja", {}).update(ib)
        if json.dumps(mk["ibja"], sort_keys=True) != old: json.dump(mk, open(mp, "w"), indent=0, ensure_ascii=False)
    except Exception as e: print("IBJA merge skipped:", e, file=sys.stderr)
    out = "\n".join(lines); print(out)
    if os.environ.get("GITHUB_STEP_SUMMARY"): open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(out + "\n")
    return 0 if gold else 1

if __name__ == "__main__": sys.exit(main())
