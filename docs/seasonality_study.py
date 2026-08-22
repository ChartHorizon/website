#!/usr/bin/env python3
"""Test the trader's maxim that a market punishes a broken seasonal.

    python3 docs/seasonality_study.py stats
    python3 docs/seasonality_study.py figures --slug 2026-08-22-the-calendar-had-no-vote
    python3 docs/seasonality_study.py calendar --month 9 10

THE CLAIM UNDER TEST
    "When a market does not do what it is supposed to do, it does the opposite
    twice as hard."  Operationally: a seasonal window whose realized sign differs
    from its expectation should be followed by a LARGER move in the direction the
    market actually went.

HOW IT IS MEASURED
    · Windows are calendar months. Month return = last close of the month over the
      last close of the month before, requiring >= 12 bars so a gap-filled stub does
      not enter as a month.
    · The expectation for (market, month, year) is the mean of that month's returns
      over years STRICTLY BEFORE it, needing MIN_PRIOR of them. This is the whole
      point: defining the seasonal from all 20 years and then grading those same
      years is look-ahead — a "failed" year is one that pulled the mean it is being
      graded against, which manufactures the effect the maxim predicts.
    · The score is the forward return SIGNED BY THE DIRECTION THE MARKET ACTUALLY
      WENT. Positive = the move continued; negative = it came back. So the maxim
      predicts a LARGER POSITIVE score after failures than after successes.
    · Significance by bootstrap over whole YEARS, not observations. Forward windows
      overlap and markets move together, so resampling observations would treat
      5,000 correlated numbers as 5,000 independent ones and turn noise into stars.

WHAT WILL BITE
    · The continuous series ROLL. Front-month yfinance data, unadjusted, so a
      contract change lands on a calendar date every year and looks exactly like a
      seasonal. ROLL_FREE is reported separately for that reason; RBOB gasoline in
      September is the textbook case (summer-to-winter blend spec, not a trade).
    · Natural gas means are hurricane outliers. Always read median beside mean.
"""
from __future__ import annotations

import argparse
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import date

from matplotlib.ticker import MaxNLocator

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from post_charts import (BEAR, GOLD, H1, INK, MUTED, RULE, SS, db, frame,  # noqa: E402
                         save, style)

MIN_PRIOR = 8
HORIZONS = (20, 40)                 # ~4 and ~8 trading weeks
ROLL_FREE = {"aud_fx", "cad_fx", "chf_fx", "eur_fx", "gbp_fx", "jpy_fx", "nzd_fx",
             "usdx", "es_sp500", "nq_nasdaq", "ym_dow", "rty_russell", "bitcoin",
             "ethereum"}
NAME = {"wti_crude": "WTI crude", "brent_crude": "Brent crude", "natural_gas": "Natural gas",
        "gasoline": "RBOB gasoline", "gold": "Gold", "silver": "Silver", "copper": "Copper",
        "corn": "Corn", "wheat": "Wheat", "soybeans": "Soybeans", "soybean_oil": "Soybean oil",
        "sugar": "Sugar", "coffee": "Coffee", "cocoa": "Cocoa", "cotton": "Cotton",
        "orange_juice": "Orange juice", "live_cattle": "Live cattle",
        "feeder_cattle": "Feeder cattle", "lean_hogs": "Lean hogs",
        "class_iii_milk": "Class III milk", "es_sp500": "S&P 500", "nq_nasdaq": "Nasdaq 100",
        "ym_dow": "Dow", "rty_russell": "Russell 2000", "zb_tbond": "30-year T-bond",
        "zn_10y": "10-year note", "zf_5y": "5-year note", "zt_2y": "2-year note",
        "usdx": "Dollar index", "eur_fx": "Euro", "jpy_fx": "Yen", "gbp_fx": "Sterling",
        "chf_fx": "Swiss franc", "aud_fx": "Aussie", "cad_fx": "Canadian dollar",
        "nzd_fx": "Kiwi", "bitcoin": "Bitcoin"}


# --------------------------------------------------------------------------- data
def load():
    con = db()
    rows = con.execute("select market_key,date,close from ohlcv_bars "
                       "where close is not null and close>0 "
                       "order by market_key,date").fetchall()
    series = defaultdict(list)
    for k, d, c in rows:
        series[k].append((d, c))
    return series


def month_returns(s):
    """{(year, month): return} for one market's [(date, close)] run."""
    me = {}
    for i, (d, c) in enumerate(s):
        me[(int(d[:4]), int(d[5:7]))] = (i, c)
    out = {}
    for (y, m), (i, c) in me.items():
        p = me.get((y, m - 1) if m > 1 else (y - 1, 12))
        if p and i - p[0] >= 12:        # a stub month is not a month
            out[(y, m)] = (c / p[1] - 1.0, i)
    return out


def observations(series):
    obs = []
    for k, s in series.items():
        if k not in NAME or s[0][0] > "2010-01-01":
            continue
        mr = month_returns(s)
        for (y, m), (r, i0) in sorted(mr.items()):
            prior = [mr[(yy, m)][0] for yy in range(2000, y) if (yy, m) in mr]
            if len(prior) < MIN_PRIOR:
                continue
            exp = statistics.mean(prior)
            if exp == 0:
                continue
            exp_sign = 1 if exp > 0 else -1
            act_sign = 1 if r > 0 else -1
            hit_prior = sum(1 for p in prior
                            if (1 if p > 0 else -1) == exp_sign) / len(prior)
            fwd = {h: s[i0 + h][1] / s[i0][1] - 1.0
                   for h in HORIZONS if i0 + h < len(s)}
            if not fwd:
                continue
            obs.append(dict(k=k, y=y, m=m, r=r, exp=exp, hit_prior=hit_prior,
                            failed=act_sign != exp_sign, act_sign=act_sign,
                            fwd=fwd, rollfree=k in ROLL_FREE))
    return obs


# --------------------------------------------------------------------------- test
def cont(o, h):
    """Forward return signed by the direction the market actually went."""
    return o["fwd"][h] * o["act_sign"]


def mean_cont(pool, h):
    v = [cont(o, h) for o in pool if h in o["fwd"]]
    if not v:
        return None
    return dict(n=len(v), mean=statistics.mean(v) * 100,
                median=statistics.median(v) * 100,
                pos=sum(1 for x in v if x > 0) / len(v) * 100)


def block_bootstrap(a, b, h, iters=4000, seed=7):
    """p for mean(a)-mean(b), resampling whole years to keep overlap + cross-market
    correlation intact."""
    years = sorted({o["y"] for o in a + b})
    by = defaultdict(lambda: ([], []))
    for o in a:
        if h in o["fwd"]:
            by[o["y"]][0].append(cont(o, h))
    for o in b:
        if h in o["fwd"]:
            by[o["y"]][1].append(cont(o, h))
    flat = lambda ys, i: [x for y in ys for x in by[y][i]]        # noqa: E731
    d0 = statistics.mean(flat(years, 0)) - statistics.mean(flat(years, 1))
    rnd, hits, n = random.Random(seed), 0, 0
    for _ in range(iters):
        pick = [rnd.choice(years) for _ in years]
        x, y = flat(pick, 0), flat(pick, 1)
        if not x or not y:
            continue
        n += 1
        if abs((statistics.mean(x) - statistics.mean(y)) - d0) >= abs(d0):
            hits += 1
    return d0 * 100, hits / max(n, 1)


CUTS = (
    ("all markets, every seasonal", lambda o: True),
    ("reliable seasonals (>=65% hit)", lambda o: o["hit_prior"] >= 0.65),
    ("very reliable (>=75% hit)", lambda o: o["hit_prior"] >= 0.75),
    ("roll-free markets", lambda o: o["rollfree"]),
    ("roll-free and reliable", lambda o: o["rollfree"] and o["hit_prior"] >= 0.65),
)


def cmd_stats(a):
    obs = observations(load())
    print("observations %d · markets %d · %d-%d · seasonal defined on >=%d prior years"
          % (len(obs), len({o['k'] for o in obs}), min(o['y'] for o in obs),
             max(o['y'] for o in obs), MIN_PRIOR))
    for label, f in CUTS:
        pool = [o for o in obs if f(o)]
        print("\n" + "=" * 76)
        print("%s  (n=%d)" % (label.upper(), len(pool)))
        for h in HORIZONS:
            fail = [o for o in pool if o["failed"]]
            ok = [o for o in pool if not o["failed"]]
            print("  -- %d trading days (~%d weeks)" % (h, h // 5))
            for nm, p in (("after FAILURE", fail), ("after success", ok),
                          ("all months", pool)):
                r = mean_cont(p, h)
                if r:
                    print("     %-15s n=%5d  mean %+6.2f%%  median %+6.2f%%  continued %4.1f%%"
                          % (nm, r["n"], r["mean"], r["median"], r["pos"]))
            if len(fail) > 30 and len(ok) > 30:
                d, p = block_bootstrap(fail, ok, h)
                print("     failure - success %+.2f pp   bootstrap p=%.3f" % (d, p))

    # the control that matters: is "failure" more than "the market moved a lot"?
    print("\n" + "=" * 76)
    print("CONTROL — failure minus success WITHIN buckets of |month move| (4 weeks)")
    pool = sorted([o for o in obs if 20 in o["fwd"]], key=lambda o: abs(o["r"]))
    n = len(pool)
    for q in range(5):
        b = pool[n * q // 5:n * (q + 1) // 5]
        f = [cont(o, 20) for o in b if o["failed"]]
        s = [cont(o, 20) for o in b if not o["failed"]]
        if len(f) < 20 or len(s) < 20:
            continue
        print("  |move| %5.1f-%5.1f%%  n=%4d/%4d   failure %+6.2f%%  success %+6.2f%%  diff %+6.2f pp"
              % (abs(b[0]["r"]) * 100, abs(b[-1]["r"]) * 100, len(f), len(s),
                 statistics.mean(f) * 100, statistics.mean(s) * 100,
                 (statistics.mean(f) - statistics.mean(s)) * 100))


def cmd_calendar(a):
    series = load()
    for month in a.month:
        print("\n" + "=" * 74)
        print("  MONTH %02d — 2006-2025" % month)
        print("=" * 74)
        res = []
        for k, s in series.items():
            if k not in NAME or s[0][0] > "2010-01-01":
                continue
            mr = month_returns(s)
            v = [r for (y, m), (r, _) in mr.items() if m == month and y <= 2025]
            if len(v) < 15:
                continue
            mu = statistics.mean(v)
            sign = 1 if mu > 0 else -1
            hit = sum(1 for r in v if (1 if r > 0 else -1) == sign) / len(v)
            res.append((hit, abs(mu), k, mu, statistics.median(v), hit, len(v)))
        res.sort(reverse=True)
        print("  %-18s %4s %9s %9s %6s  %s" % ("market", "yrs", "mean", "median", "hit", "way"))
        for _, _, k, mu, md, hit, n in res[:a.top]:
            print("  %-18s %4d %8.2f%% %8.2f%% %5.0f%%  %-7s %s"
                  % (NAME[k], n, mu * 100, md * 100, hit * 100,
                     "up" if mu > 0 else "down", "" if k in ROLL_FREE else "(rolled)"))


# --------------------------------------------------------------------------- figures
def fig_august(a, series):
    """Every August crude has had, and the one it is having."""
    s = series["wti_crude"]
    by_year = defaultdict(list)
    dates = defaultdict(list)
    base = {}
    for d, c in s:
        y, m = int(d[:4]), int(d[5:7])
        if m == 7:
            base[y] = c                     # rolling last July close
        elif m == 8 and y in base:
            by_year[y].append(c / base[y] * 100.0)
            dates[y].append(d)

    fig = frame(H1, "ENERGY", "Crude's August, twenty times over",
                "WTI front month, each August rebased to 31 July = 100",
                "Data: ChartHorizon · continuous front-month series · not financial advice")
    ax = fig.add_axes([0.075, 0.165, 0.885, 0.61])

    hist = [y for y in sorted(by_year) if y < 2026]
    for y in hist:
        v = by_year[y]
        ax.plot(range(1, len(v) + 1), v, color=RULE, lw=1.1 * SS, zorder=1)
    n = max(len(by_year[y]) for y in hist)
    avg = [statistics.mean([by_year[y][i] for y in hist if len(by_year[y]) > i])
           for i in range(n)]
    ax.plot(range(1, n + 1), avg, color=GOLD, lw=2.6 * SS, ls=(0, (6, 3)), zorder=3)
    cur = by_year[2026]
    ax.plot(range(1, len(cur) + 1), cur, color=INK, lw=3.0 * SS, zorder=4,
            solid_joinstyle="round")

    ax.axhline(100, color=INK, lw=1.1 * SS, zorder=2)
    ax.set_ylabel("31 July = 100", fontsize=13 * SS, labelpad=10 * SS)
    ax.set_xlabel("trading day of August", fontsize=13 * SS, labelpad=8 * SS)
    ax.set_xlim(1, n)
    style(ax, xdates=False)
    # "trading day 2.5" does not exist; AutoLocator offers halves on a 1-23 span
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))

    ax.annotate("2026", xy=(len(cur), cur[-1]), xytext=(10 * SS, 0),
                textcoords="offset points", color=INK, fontsize=15 * SS, va="center")
    ai = min(n, 14)
    ax.annotate("20-year\naverage", xy=(ai, avg[ai - 1]), xytext=(6 * SS, -34 * SS),
                textcoords="offset points", color=GOLD, fontsize=13.5 * SS,
                va="center", linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=GOLD, lw=1.2 * SS,
                                shrinkA=0, shrinkB=4 * SS))
    lo = min(range(len(cur)), key=lambda i: cur[i])
    # label the low from the data: trading day 3 is 5 August, not 3 August
    lo_day = date.fromisoformat(dates[2026][lo]).strftime("%-d %B")
    ax.annotate("%s: a Hormuz deal\nlooks close" % lo_day, xy=(lo + 1, cur[lo]),
                xytext=(14 * SS, -30 * SS), textcoords="offset points", color=INK,
                fontsize=13.5 * SS, va="center", linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=INK, lw=1.2 * SS,
                                shrinkA=0, shrinkB=4 * SS))
    save(fig, a.slug, "crude_august", H1, False)

    if a.source:
        import matplotlib.pyplot as plt
        f2 = plt.figure(figsize=(1200 * SS / 100, 760 * SS / 100), dpi=100)
        ax2 = f2.add_axes([0.05, 1 - 0.54, 0.865, 0.54 - 0.105])
        ax2.plot(range(1, len(cur) + 1), cur, color="#1f4f8f", lw=5.0 * SS)
        ax2.set_xlim(1, n)
        ax2.set_axis_off()
        f2.savefig(a.source, dpi=100)
        plt.close(f2)
        print("   source trace -> %s  (feed to title_card.py --chart, then delete)" % a.source)


def fig_test(a, obs):
    """The maxim, five ways, and it never shows up."""
    fig = frame(H1, "THE TEST", "What follows a broken season",
                "Mean return over the next four weeks, signed in the direction the market "
                "actually went",
                "35 markets · 2014-2026 · seasonal defined out-of-sample on prior years "
                "only · Data: ChartHorizon")
    ax = fig.add_axes([0.30, 0.145, 0.645, 0.63])

    labels, fails, oks = [], [], []
    for label, f in CUTS:
        pool = [o for o in obs if f(o)]
        rf = mean_cont([o for o in pool if o["failed"]], 20)
        ro = mean_cont([o for o in pool if not o["failed"]], 20)
        if not rf or not ro:
            continue
        labels.append(label)
        fails.append(rf["mean"])
        oks.append(ro["mean"])

    ypos = list(range(len(labels)))[::-1]
    hgt = 0.34
    ax.barh([y + hgt / 2 for y in ypos], fails, height=hgt, color=BEAR, linewidth=0,
            label="after the season FAILED")
    ax.barh([y - hgt / 2 for y in ypos], oks, height=hgt, color=INK, linewidth=0,
            label="after it worked")
    ax.axvline(0, color=INK, lw=1.4 * SS)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=13.5 * SS, color=INK)
    ax.set_xlim(-0.95, 0.95)   # no xlabel: the dek already says what the axis is
    style(ax, xdates=False)
    ax.grid(axis="x", color=RULE, lw=0.9 * SS, ls=(0, (1, 3)))
    ax.grid(axis="y", visible=False)
    leg = ax.legend(loc="upper right", frameon=False, fontsize=13.5 * SS,
                    handlelength=1.4, borderaxespad=0.6)
    for t in leg.get_texts():
        t.set_color(MUTED)
    fig.text(0.30, 0.088, "The maxim predicts the red bars far to the RIGHT of the black. "
             "They are not.", color=MUTED, fontsize=13.5 * SS, ha="left")
    save(fig, a.slug, "failure_test", H1, False)


def cmd_figures(a):
    series = load()
    fig_august(a, series)
    fig_test(a, observations(series))


# --------------------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    c = sub.add_parser("calendar")
    c.add_argument("--month", nargs="+", type=int, default=[9, 10])
    c.add_argument("--top", type=int, default=12)
    f = sub.add_parser("figures")
    f.add_argument("--slug", required=True)
    f.add_argument("--source")
    a = p.parse_args()
    {"stats": cmd_stats, "calendar": cmd_calendar, "figures": cmd_figures}[a.cmd](a)


if __name__ == "__main__":
    main()
