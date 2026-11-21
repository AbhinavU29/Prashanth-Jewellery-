#!/usr/bin/env python3
"""Builds data/forecast.json: the likely range for the next Kerala 22K board rate.

Method (details in docs/PRD.md):
  * volatility: EWMA of daily log-returns of the Kerala board rate, scaled by a day-of-week factor
    (the board is usually unchanged on Sundays, so Sunday ranges are much tighter);
  * range width: calibrated from past standardised moves so the 80% range really held ~80% of the time;
  * direction: history alone has no reliable edge (autocorrelation ~0 in 6 months of data), so the
    centre is "unchanged" unless a live market signal exists (COMEX gold x USD/INR move since the
    Kerala board was last set), which is passed through at 90%;
  * every forecast is logged and later scored against the real rate (live track record)."""
import json, math, os, statistics as st, sys, urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata"); DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
BETA, LEVEL, FLOOR = 0.9, 0.8, 0.004
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
load = lambda n, d: json.load(open(os.path.join(DATA, n))) if os.path.exists(os.path.join(DATA, n)) else d
def save(n, o): json.dump(o, open(os.path.join(DATA, n), "w"), indent=0, ensure_ascii=False)
D = date.fromisoformat

def quantile(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1); return xs[f] + (xs[c] - xs[f]) * (k - f)

def prep(rows):
    dates = [D(d) for d, _ in rows]; vals = [v for _, v in rows]
    return dates, vals, [math.log(vals[i] / vals[i - 1]) for i in range(1, len(vals))]

def ewma(rets, lam=0.94, seed=20):
    var = sum(r * r for r in rets[:seed]) / max(1, min(seed, len(rets))) or 1e-4; before = []
    for r in rets: before.append(max(math.sqrt(var), FLOOR)); var = lam * var + (1 - lam) * r * r
    return before, max(math.sqrt(var), FLOOR)

def wd_ratio(dates, rets, j, wd, window=182):
    """Day-of-week volatility factor from returns with index < j (daily gaps only), shrunk towards 1."""
    grp, allr = [], []
    for i in range(max(0, j - window), j):
        if (dates[i + 1] - dates[i]).days != 1: continue
        allr.append(rets[i] ** 2)
        if dates[i + 1].weekday() == wd: grp.append(rets[i] ** 2)
    if len(grp) < 4 or not allr: return 1.0
    w = len(grp) / (len(grp) + 8); return w * math.sqrt(st.mean(grp) / st.mean(allr)) + (1 - w)

def standardised(dates, rets):
    before, nxt = ewma(rets); out = []
    for j in range(len(rets)): out.append((before[j], abs(rets[j]) / (before[j] * wd_ratio(dates, rets, j, dates[j + 1].weekday()))))
    return before, nxt, out

def backtest(dates, vals, rets, window=90):
    before, _, e = standardised(dates, rets); hits = tot = 0; widths = []; flat = []
    allsd = st.pstdev(rets)
    for j in range(max(40, len(rets) - window), len(rets)):
        z = min(max(quantile([x[1] for x in e[max(0, j - 150):j]], LEVEL), 0.5), 2.5)
        s = before[j] * wd_ratio(dates, rets, j, dates[j + 1].weekday())
        tot += 1; hits += abs(rets[j]) <= z * s; widths.append(2 * z * s * vals[j]); flat.append(2 * 1.2816 * allsd * vals[j])
    return {"days": tot, "coverage": round(hits / tot, 3), "avg_width": round(st.mean(widths)), "flat_width": round(st.mean(flat)),
            "typical_move": round(st.mean(abs(vals[i] - vals[i - 1]) for i in range(len(vals) - window, len(vals))))}

def yahoo(sym):
    req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=15m", headers={"User-Agent": "Mozilla/5.0 (compatible; PJRatesBot/1.0)"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]
    return [(t, c) for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c]

def intl_signal(last_date):
    """Move in COMEX gold priced in rupees since ~10:30 IST on the last Kerala rate date (None if unavailable)."""
    try:
        gold, fx = yahoo("GC%3DF"), yahoo("INR%3DX")
        ref = datetime.fromisoformat(str(last_date) + "T05:00:00+00:00").timestamp()
        at = lambda s: next((c for t, c in reversed(s) if t <= ref), None)
        g0, f0 = at(gold), at(fx)
        if not g0 or not f0: return None
        return {"move": math.log(gold[-1][1] * fx[-1][1] / (g0 * f0)), "xau": round(gold[-1][1], 1), "usd_inr": round(fx[-1][1], 2)}
    except Exception as e:
        print("market signal unavailable:", e, file=sys.stderr); return None


# ---------------- market factors + ridge model (walk-forward validated) ----------------
SYMS = {"gold": "GC%3DF", "usdinr": "INR%3DX", "dxy": "DX-Y.NYB", "us10y": "%5ETNX", "oil": "CL%3DF"}
def yahoo_daily(sym):
    req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1y&interval=1d", headers={"User-Agent": "Mozilla/5.0 (compatible; PJRatesBot/1.0)"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]; off = r["meta"].get("gmtoffset", 0)
    return {datetime.utcfromtimestamp(t + off).date().isoformat(): c for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c}
def update_market_history():
    h = load("market_history.json", {})
    for k, sym in SYMS.items():
        try: h.setdefault(k, {}).update(yahoo_daily(sym))
        except Exception as e: print("market history failed:", k, e, file=sys.stderr)
    save("market_history.json", h); return h

def solve(A, b):
    n = len(b); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[c][c]: f = M[r][c] / M[c][c]; M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if M[i][i] else 0.0 for i in range(n)]
def ridge_fit(X, y, alpha):
    n, p = len(X), len(X[0]); mu = [st.mean(c) for c in zip(*X)]; sd = [st.pstdev(c) or 1.0 for c in zip(*X)]; ym = st.mean(y)
    Z = [[(x - m) / s for x, m, s in zip(row, mu, sd)] for row in X]
    A = [[sum(Z[i][a] * Z[i][b] for i in range(n)) + (alpha if a == b else 0) for b in range(p)] for a in range(p)]
    return solve(A, [sum(Z[i][a] * (y[i] - ym) for i in range(n)) for a in range(p)]), mu, sd, ym
def ridge_pred(m, x): w, mu, sd, ym = m; return ym + sum(wi * (xi - mi) / si for wi, xi, mi, si in zip(w, x, mu, sd))

def ml_model(dates, vals, rets, mh):
    """Ridge regression of the next Kerala return on market factors. Used only if it beats 'unchanged' out of sample."""
    out = {"name": "Ridge regression on market factors", "status": "collecting", "oos_days": 0, "n_samples": 0}
    try:
        def v(k, d):
            s = mh.get(k, {}); ks = [x for x in s if x <= d]; return (s[max(ks)], max(ks)) if ks else (None, None)
        def prev(k, d):
            a, da = v(k, d)
            if a is None: return None, None
            b, _ = v(k, str(date.fromisoformat(da) - timedelta(days=1))); return a, b
        def mf(d):
            r = []
            for k in ("gold", "usdinr", "dxy", "oil"):
                a, b = prev(k, d)
                if not a or not b: return None
                r.append(math.log(a / b))
            a, b = prev("us10y", d)
            return None if a is None or b is None else [r[0] + r[1], r[2], a - b, r[3]]
        X, y = [], []
        for i in range(5, len(dates) - 1):
            m = mf(str(dates[i]))
            if m is None or (dates[i + 1] - dates[i]).days != 1: continue
            wd = dates[i + 1].weekday(); X.append(m + [rets[i - 1], sum(rets[i - 5:i]), float(wd == 6), float(wd == 5)]); y.append(rets[i])
        out["n_samples"] = len(X)
        if len(X) < 80: return out
        pr = [(ridge_pred(ridge_fit(X[:i], y[:i], 30.0), X[i]), y[i]) for i in range(60, len(y))]
        mae_m, mae_n = st.mean(abs(a - b) for a, b in pr), st.mean(abs(b) for _, b in pr)
        mv = [(a, b) for a, b in pr if abs(a) > 0.001 and b != 0]; da = st.mean((a > 0) == (b > 0) for a, b in mv) if mv else 0.0
        gain = 1 - mae_m / mae_n; out.update(oos_days=len(pr), gain_pct=round(gain * 100, 1), dir_acc=round(da, 2))
        out["status"] = "active" if len(pr) >= 40 and gain >= 0.03 and da >= 0.55 else "inactive"
        m0 = mf(str(dates[-1])); tw = (dates[-1] + timedelta(days=1)).weekday()
        if out["status"] == "active" and m0 is not None: out["pred"] = ridge_pred(ridge_fit(X, y, 30.0), m0 + [rets[-1], sum(rets[-5:]), float(tw == 6), float(tw == 5)])
        else: out["status"] = "inactive" if out["status"] == "active" else out["status"]
    except Exception as e: print("model failed:", e, file=sys.stderr)
    return out

def season(month):
    return ("Akshaya Tritiya and wedding season lift physical demand." if month in (4, 5) else "Onam shopping season supports demand." if month in (8, 9)
            else "Diwali/Dhanteras and the start of the wedding season support demand." if month in (10, 11) else "Peak wedding season in Kerala." if month in (12, 1, 2) else "Quieter demand months.") \
           + " Festive demand shows up mainly in premiums and making charges; the daily board rate follows international gold."

def drivers(rates, vals, rets, market, sig, bt):
    out = []; ib = market.get("ibja", {}); n = len(vals)
    ratios = [vals[i] * 24 / 22 * 10 / ib[str(dates_[i])][1] for i in range(n) if str(dates_[i]) in ib] if False else []
    ds = {str(d): v for d, v in zip(DATES, vals)}
    pairs = [(d, ds[d] * 24 / 22 * 10 / ib[d][1]) for d in sorted(ib) if d in ds]
    if pairs:
        mean, sd = st.mean(p[1] for p in pairs), st.pstdev(p[1] for p in pairs); d0, cur = pairs[-1]; z = (cur - mean) / sd if sd else 0
        tone = "up" if z > 2 else "down" if z < -2 else "flat"
        out.append({"t": "Kerala vs national benchmark", "v": f"{(cur - 1) * 100:+.2f}%", "tone": tone,
                    "d": f"Kerala 24K-equivalent vs IBJA 999 PM on {d0}. Usual gap {(mean - 1) * 100:+.2f}% ± {sd * 100:.2f}%." + (" Kerala is unusually high, so a drop is more likely." if tone == "up" else " Kerala is unusually low, so a rise is more likely." if tone == "down" else "")})
    ks = sorted(ib)
    if len(ks) >= 2:
        a, b = ib[ks[-1]][1], ib[ks[-2]][1]; ch = (a / b - 1) * 100; five = (a / ib[ks[max(0, len(ks) - 6)]][1] - 1) * 100
        out.append({"t": "IBJA 999 gold (national)", "v": f"₹{a:,}/10 g", "tone": "up" if ch > 0.3 else "down" if ch < -0.3 else "flat",
                    "d": f"{ch:+.1f}% vs previous PM fixing ({ks[-1]}); {five:+.1f}% over 5 fixings. Kerala's board rate follows this benchmark closely."})
    wk = (vals[-1] / vals[-8] - 1) * 100; streak = 0
    for i in range(n - 1, 0, -1):
        if vals[i] < vals[i - 1]: streak += 1
        else: break
    out.append({"t": "Kerala momentum (7 days)", "v": f"{wk:+.1f}%", "tone": "up" if wk > 1 else "down" if wk < -1 else "flat",
                "d": (f"{streak} straight daily falls. " if streak >= 3 else "") + f"Recent daily moves average {st.mean(abs(r) for r in rets[-7:]) * 100:.1f}% against {st.mean(abs(r) for r in rets) * 100:.1f}% over six months."})
    if sig: out.append({"t": "International gold since Kerala board", "v": f"{sig['move'] * 100:+.1f}%", "tone": "up" if sig["move"] > 0.002 else "down" if sig["move"] < -0.002 else "flat",
                        "d": f"COMEX gold ${sig['xau']:,} at ₹{sig['usd_inr']} per USD, converted to rupees. This is the main live input for the next board rate."})
    else: out.append({"t": "International gold since Kerala board", "v": "Not connected", "tone": "info", "d": "The live COMEX gold and USD/INR feed was unavailable on the last run, so the range uses Kerala history only."})
    if market.get("note"): out.append({"t": "Market note", "v": market["note"]["date"], "tone": "info", "d": market["note"]["text"]})
    return out

def run(now=None, signal="auto"):
    global DATES
    rates = load("rates.json", {}); market = load("market.json", {}); log = load("forecast_log.json", [])
    dates, vals, rets = prep(rates["g22"]); DATES = dates
    now = now or datetime.now(IST); target = dates[-1] + timedelta(days=1)
    before, nxt, e = standardised(dates, rets); ratio = wd_ratio(dates, rets, len(rets), target.weekday())
    s = nxt * ratio; z = min(max(quantile([x[1] for x in e[-150:]], LEVEL), 0.5), 2.5)
    sig = intl_signal(dates[-1]) if signal == "auto" else signal
    mh = update_market_history() if signal == "auto" else load("market_history.json", {})
    ml = ml_model(dates, vals, rets, mh)
    mu = BETA * sig["move"] if sig else (ml["pred"] if ml["status"] == "active" else 0.0); L = vals[-1]
    basis = "live market signal" if sig else "market-factor model" if ml["status"] == "active" else "history only"
    r5 = lambda x: int(round(x / 5.0)) * 5
    lo, mid, hi = r5(L * math.exp(mu - z * s)), r5(L * math.exp(mu)), r5(L * math.exp(mu + z * s))
    if hi - lo < 10: lo, hi = mid - 5, mid + 5
    ratio_mu = mu / s if s else 0; tag = "Leaning up" if ratio_mu > 0.35 else "Leaning down" if ratio_mu < -0.35 else "Neutral"
    same = [rets[i] for i in range(max(0, len(rets) - 182), len(rets)) if dates[i + 1].weekday() == target.weekday() and (dates[i + 1] - dates[i]).days == 1]
    bt = backtest(dates, vals, rets)
    # live track record: score earlier forecasts whose date now has a published rate, then add today's
    actual = {str(d): v for d, v in zip(dates, vals)}
    for it in log:
        if "actual" not in it and it["for"] in actual: it["actual"] = actual[it["for"]]; it["inside"] = it["lo"] <= it["actual"] <= it["hi"]
    if str(target) not in actual:
        log = [i for i in log if i["for"] != str(target)] + [{"for": str(target), "made": now.isoformat(timespec="minutes"), "lo": lo, "mid": mid, "hi": hi}]
    log = sorted(log, key=lambda i: i["for"])[-90:]; scored = [i for i in log if "actual" in i]
    fc = {"for_date": str(target), "weekday": DAYS[target.weekday()], "last_date": str(dates[-1]), "last_rate": L, "lo": lo, "mid": mid, "hi": hi,
          "level": int(LEVEL * 100), "tag": tag, "sigma_pct": round(s * 100, 2), "z": round(z, 2),
          "unchanged_share": {"n": len(same), "share": round(sum(1 for r in same if r == 0) / len(same), 2) if same else None},
          "signal": {"used": True, "move_pct": round(sig["move"] * 100, 1), "source": "COMEX gold x USD/INR"} if sig else {"used": False},
          "basis": basis, "model": {k: v for k, v in ml.items() if k != "pred"}, "backtest": bt, "drivers": drivers(rates, vals, rets, market, sig, bt) + [{"t": "Season", "v": now.strftime("%B"), "tone": "info", "d": season(now.month)}],
          "track": {"n": len(scored), "inside": sum(1 for i in scored if i["inside"]), "mae": round(st.mean(abs(i["actual"] - i["mid"]) for i in scored)) if scored else None,
                    "recent": [{k: i[k] for k in ("for", "lo", "hi", "actual", "inside")} for i in scored[-8:]]}}
    for k in ("drivers", "track"): fc.pop(k, None)   # UI no longer shows driver list / prediction history
    old = load("forecast.json", {}); strip = lambda f: {k: v for k, v in f.items() if k != "generated"}
    if strip(old) != strip(fc): fc["generated"] = now.isoformat(timespec="seconds"); save("forecast.json", fc)
    else: fc = old
    save("forecast_log.json", log); return fc

if __name__ == "__main__":
    f = run(); print(f"{f['for_date']} ({f['weekday']}): Rs {f['lo']}-{f['hi']} (centre {f['mid']}), tag {f['tag']}, signal {f['signal']}")
