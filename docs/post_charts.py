#!/usr/bin/env python3
"""Draw a post's chart cards straight from the dashboard's SQLite archive.

    python3 docs/post_charts.py cot   --slug 2026-08-20-x --name zb_cot --market zb_tbond \
        --kicker BONDS --title "..." --sub "..." --price-label "30-Year T-Bond"
    python3 docs/post_charts.py line  --slug ... --name ... --market zb_tbond --since 2026-01-02
    python3 docs/post_charts.py multi --slug ... --name ... --market gold silver bitcoin usdx \
        --since 2026-08-03 --rebase

WHY THIS EXISTS
    The other route to a post figure is content/livermore/blog/screenshots.py, which
    needs the dashboard serving on :8000 and returns the app's own cool grey-blue card.
    Those cards are drawn for a dark trading UI and glare on the cream page; the front
    page had to dim them. Drawing from charthorizon.db in the blog's OWN :root palette
    gives figures that sit on the paper with no correction at all, and removes the
    "dashboard must be running" dependency from writing a post.

    The DB is opened READ-ONLY. This script never writes outside assets/posts/<slug>/.

WHAT COMES OUT
    Body figures are WebP only (the title card is the JPEG twin of a photograph; these
    are flat line art, and the card that a *crawler* has to read is the title card, not
    these). Sizes are fixed so the templates can hard-code width/height and reserve the
    space: one-panel cards 2400x1520 -> declared 1200x760, two-panel COT cards
    2400x2072 -> declared 1200x1036. --png additionally writes the PNG twin, which only
    the card chosen as a post's `image:` needs.

    --source writes the bare price trace with no furniture, positioned in exactly the
    band docs/title_card.py crops (x 5%-91.5%, y 10.5%-54%), for use as its --chart.
    It is a build artefact: pass it to title_card.py, then delete it.

DATA NOTES THAT WILL BITE
    · The column is `market_key`, not market_id. Tables: ohlcv_bars(market_key,date,
      open,high,low,close,volume) and cot(market_key,date,comm_net,oi,cot_label).
    · cot.cot_net is a DUPLICATE of comm_net, not the speculative side. There is no
      spec series in this archive. Say "commercial" or "producer/merchant" (cot_label
      tells you which) and never imply a spec/commercial divergence from this table.
    · FX is stored USD-based and inverted: USD/JPY = 1/jpy_fx.close. Use --invert.
    · The continuous price series ROLLS. A single-session gap of several per cent
      across an entire complex on one date is a roll, not a move. Check before
      annotating a daily change.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sqlite3
import sys
import tempfile
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from matplotlib.ticker import FuncFormatter
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DB = pathlib.Path.home() / "charthorizon/dashboard/app/ff_data/charthorizon.db"
DB = pathlib.Path(os.environ.get("CH_DB", DEFAULT_DB))

# --- palette: assets/css/blog.css :root ------------------------------------
PAPER = "#fbfbf9"      # --card, not --paper: a figure sits on the card, not the sheet
INK = "#17150f"        # --ink
GOLD = "#7d641e"       # --gold-ink. Foil gold #c8a24a is 2.19:1 on paper and cannot
                       # legally carry text there; the kicker and wordmark are text.
RULE = "#ddd9d0"       # --rule
MUTED = "#6b6356"      # --muted
BULL = "#39744b"       # --bull
BEAR = "#a8503f"       # --bear

SS = 2                              # supersample; every size below is in final pixels
W = 1200
H1, H2 = 760, 1036                  # one-panel / two-panel card heights
DPI = 100


# --------------------------------------------------------------------------- font
def _newsreader() -> str:
    """Newsreader ships as woff2 only, which matplotlib's FreeType cannot open.
    Instance the variable font to a static TTF and register that.

    Gotcha: instancing the opsz axis RENAMES the family (to 'Newsreader 16pt' or
    similar). Reading the name back out of the saved font is the only way to be sure
    matplotlib is not silently falling back to DejaVu Sans."""
    out = pathlib.Path(tempfile.gettempdir()) / "charthorizon-newsreader-400.ttf"
    if not out.exists():
        f = TTFont(str(REPO / "assets/fonts/newsreader.woff2"))
        instantiateVariableFont(f, {"wght": 400, "opsz": 16})
        f.flavor = None
        f.save(str(out))
    fm.fontManager.addfont(str(out))
    return fm.FontProperties(fname=str(out)).get_name()


FAMILY = _newsreader()
plt.rcParams.update({
    "font.family": FAMILY,
    "text.color": INK,
    "axes.edgecolor": RULE,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
})


# --------------------------------------------------------------------------- data
def db() -> sqlite3.Connection:
    if not DB.exists():
        sys.exit(f"!! archive not found: {DB}\n   set $CH_DB if the dashboard lives elsewhere")
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def prices(con, key, since=None, until=None, invert=False):
    q = "select date, close from ohlcv_bars where market_key=? and close is not null"
    a = [key]
    if since:
        q, a = q + " and date>=?", a + [since]
    if until:
        q, a = q + " and date<=?", a + [until]
    rows = con.execute(q + " order by date", a).fetchall()
    if not rows:
        sys.exit(f"!! no price rows for {key}")
    xs = [date.fromisoformat(d) for d, _ in rows]
    ys = [(1 / c if invert else c) for _, c in rows]
    return xs, ys


def cot_rows(con, key, since=None, until=None):
    q = "select date, comm_net, cot_label from cot where market_key=? and comm_net is not null"
    a = [key]
    if since:
        q, a = q + " and date>=?", a + [since]
    if until:
        q, a = q + " and date<=?", a + [until]
    rows = con.execute(q + " order by date", a).fetchall()
    if not rows:
        sys.exit(f"!! no COT rows for {key}")
    xs = [date.fromisoformat(d) for d, _, _ in rows]
    ys = [v for _, v, _ in rows]
    return xs, ys, rows[-1][2] or "Commercial Net"


# --------------------------------------------------------------------------- chrome
def thousands(v, _=None):
    if abs(v) >= 1000:
        return f"{v/1000:,.0f}K"
    return f"{v:,.0f}"


def frame(height: int, kicker: str, title: str, sub: str, note: str):
    fig = plt.figure(figsize=(W * SS / DPI, height * SS / DPI), dpi=DPI)
    s = SS
    fig.text(0.042, 0.962, " ".join(kicker.upper()), color=GOLD, fontsize=15 * s,
             va="center", ha="left")
    fig.text(0.958, 0.962, "CHARTHORIZON", color=GOLD, fontsize=15 * s,
             va="center", ha="right")
    y = 0.938
    fig.add_artist(plt.Line2D([0.042, 0.958], [y, y], color=INK, lw=1.6 * s,
                              transform=fig.transFigure))
    fig.text(0.042, 0.895, title, color=INK, fontsize=27 * s, va="center", ha="left")
    if sub:
        fig.text(0.042, 0.852, sub, color=MUTED, fontsize=14 * s, va="center", ha="left")
    fig.add_artist(plt.Line2D([0.042, 0.958], [0.052, 0.052], color=RULE, lw=1 * s,
                              transform=fig.transFigure))
    fig.text(0.042, 0.028, note, color=MUTED, fontsize=12.5 * s, va="center", ha="left")
    return fig


def style(ax, *, xdates=True):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.spines["bottom"].set_linewidth(1.0 * SS)
    ax.grid(axis="y", color=RULE, lw=0.9 * SS, ls=(0, (1, 3)))
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6 * SS, labelsize=13 * SS)
    if xdates:
        # Span-aware: "2026-08" on every tick of a three-week window is not a label.
        lo, hi = ax.get_xlim()
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=9))
        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%Y-%m" if hi - lo > 200 else "%d %b"))


def mark(ax, x, y, text, *, dx=28, dy=34, color=INK, ha="left"):
    """A value label on a leader line. Offsets are in points, so they scale with SS."""
    ax.annotate(text, xy=(x, y), xytext=(dx * SS, dy * SS), textcoords="offset points",
                color=color, fontsize=13.5 * SS, ha=ha, va="center", linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=color, lw=1.2 * SS,
                                shrinkA=0, shrinkB=4 * SS))


def save(fig, slug: str, name: str, height: int, png: bool):
    out = REPO / "assets/posts" / slug / "cards"
    out.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.gettempdir()) / f"{slug}-{name}.png"
    fig.savefig(tmp, dpi=DPI)
    plt.close(fig)
    im = Image.open(tmp).convert("RGB")
    want = (W * SS, height * SS)
    if im.size != want:
        im = im.resize(want, Image.LANCZOS)
    im.save(out / f"{name}.webp", "WEBP", quality=88, method=6)
    if png:
        im.resize((W, height), Image.LANCZOS).save(out / f"{name}.png", "PNG")
    tmp.unlink(missing_ok=True)
    print(f"   {out.relative_to(REPO)}/{name}.webp  {want[0]}x{want[1]}"
          f"  -> declare width=\"{W}\" height=\"{height}\"")


def parse_marks(specs):
    """--mark 2026-08-19=+1.27%|the year's largest day  (| is a line break, : offsets)"""
    out = []
    for s in specs or []:
        when, _, rest = s.partition("=")
        text, _, off = rest.partition("@")
        dx, dy = (off.split(",") + ["", ""])[:2] if off else ("", "")
        out.append((date.fromisoformat(when), text.replace("|", "\n"),
                    float(dx or 28), float(dy or 34)))
    return out


# --------------------------------------------------------------------------- charts
def draw_cot(a):
    con = db()
    px, py = prices(con, a.market, since=a.since, until=a.until, invert=a.invert)
    cx, cy, label = cot_rows(con, a.market, since=a.since, until=a.until)
    fig = frame(H2, a.kicker, a.title, a.sub, a.note)
    top = fig.add_axes([0.075, 0.475, 0.885, 0.345])
    bot = fig.add_axes([0.075, 0.105, 0.885, 0.305])

    top.plot(px, py, color=INK, lw=1.5 * SS, solid_joinstyle="round")
    if a.invert:
        top.invert_yaxis()
    top.set_ylabel(a.price_label, fontsize=13 * SS, labelpad=10 * SS)
    style(top)
    top.set_xticklabels([])
    top.tick_params(axis="x", labelbottom=False)

    width = max(1.0, (cx[-1] - cx[0]).days / max(len(cx), 1) * 0.78)
    bot.bar(cx, cy, width=width, color=[BULL if v >= 0 else BEAR for v in cy],
            linewidth=0)
    bot.axhline(0, color=INK, lw=1.1 * SS)
    bot.set_ylabel(f"{label}, contracts", fontsize=13 * SS, labelpad=10 * SS)
    bot.yaxis.set_major_formatter(FuncFormatter(thousands))
    style(bot)
    for x, y in zip(cx, cy):
        bot.set_xlim(min(cx), max(px[-1], cx[-1]))
    top.set_xlim(*bot.get_xlim())

    at = dict(zip(cx, cy))
    for when, text, dx, dy in parse_marks(a.mark):
        if when not in at:
            sys.exit(f"!! no COT report dated {when} for {a.market}")
        v = at[when]
        mark(bot, when, v, text, dx=dx, dy=dy, color=BULL if v >= 0 else BEAR,
             ha="right" if dx < 0 else "left")
    save(fig, a.slug, a.name, H2, a.png)


def draw_line(a):
    con = db()
    px, py = prices(con, a.market, since=a.since, until=a.until, invert=a.invert)
    fig = frame(H1, a.kicker, a.title, a.sub, a.note)
    ax = fig.add_axes([0.075, 0.115, 0.885, 0.66])
    ax.plot(px, py, color=INK, lw=1.6 * SS, solid_joinstyle="round")
    if a.invert:
        ax.invert_yaxis()
    if a.price_label:
        ax.set_ylabel(a.price_label, fontsize=13 * SS, labelpad=10 * SS)
    style(ax)
    at = dict(zip(px, py))
    for when, text, dx, dy in parse_marks(a.mark):
        if when not in at:
            sys.exit(f"!! no bar dated {when} for {a.market}")
        mark(ax, when, at[when], text, dx=dx, dy=dy,
             ha="right" if dx < 0 else "left")
    if a.source:
        # docs/title_card.py recovers direction from HUE: a pixel is keyed bear only
        # where red exceeds blue by more than 8. Ink (#17150f) misses that by exactly
        # one, so an ink trace always comes out green — including on a market that
        # fell all year. Colour the source by the direction of the run instead.
        tone = a.source_tone
        if tone == "auto":
            tone = "bull" if py[-1] >= py[0] else "bear"
        src_colour = {"bull": BULL, "bear": BEAR, "ink": INK}[tone]
        src = pathlib.Path(a.source)
        bare = plt.figure(figsize=(1280 * SS / DPI, 720 * SS / DPI), dpi=DPI)
        b = bare.add_axes([0.05, 1 - 0.54, 0.865, 0.54 - 0.105])
        b.plot(px, py, color=src_colour, lw=3.0 * SS, solid_joinstyle="round")
        if a.invert:
            b.invert_yaxis()
        b.set_axis_off()
        bare.savefig(src, dpi=DPI, facecolor=PAPER)
        plt.close(bare)
        print(f"   {src}  (title-card source; delete after use)")
    save(fig, a.slug, a.name, H1, a.png)


def draw_multi(a):
    con = db()
    fig = frame(H1, a.kicker, a.title, a.sub, a.note)
    ax = fig.add_axes([0.075, 0.115, 0.80, 0.66])
    # The house multi-line palette: ink, bear-red, then olive-gold DASHED. Bull green
    # is deliberately absent — in the COT panels green and red mean long and short, and
    # a categorical series in those hues reads as a position it isn't.
    colours = [INK, BEAR, GOLD, MUTED]
    dashes = ["-", "-", "--", "-"]
    labels = a.label or a.market
    if len(labels) != len(a.market):
        sys.exit("!! --label must give one label per --market")
    for i, key in enumerate(a.market):
        xs, ys = prices(con, key, since=a.since, until=a.until,
                        invert=key in (a.invert_key or []))
        if a.rebase:
            base = ys[0]
            ys = [100 * v / base for v in ys]
        c = colours[i % len(colours)]
        ax.plot(xs, ys, color=c, lw=1.7 * SS, ls=dashes[i % len(dashes)],
                solid_joinstyle="round")
        ax.annotate(f"{labels[i]}  {ys[-1]:,.1f}", xy=(xs[-1], ys[-1]),
                    xytext=(10 * SS, 0), textcoords="offset points",
                    color=c, fontsize=13.5 * SS, va="center", ha="left")
    if a.rebase:
        ax.axhline(100, color=RULE, lw=1.2 * SS)
        ax.set_ylabel(a.price_label or f"rebased, {a.since} = 100",
                      fontsize=13 * SS, labelpad=10 * SS)
    style(ax)
    save(fig, a.slug, a.name, H1, a.png)


# --------------------------------------------------------------------------- cli
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kind", required=True)
    for kind in ("cot", "line", "multi"):
        s = sub.add_parser(kind)
        s.add_argument("--slug", required=True)
        s.add_argument("--name", required=True)
        s.add_argument("--market", required=True, nargs="+" if kind == "multi" else None)
        s.add_argument("--kicker", default="MARKETS")
        s.add_argument("--title", required=True)
        s.add_argument("--sub", default="")
        s.add_argument("--note",
                       default="Data: ChartHorizon & CFTC · not financial advice")
        s.add_argument("--price-label", default="")
        s.add_argument("--since")
        s.add_argument("--until")
        s.add_argument("--invert", action="store_true")
        s.add_argument("--png", action="store_true")
        s.add_argument("--mark", action="append")
        if kind == "line":
            s.add_argument("--source")
            s.add_argument("--source-tone", default="auto",
                           choices=("auto", "bull", "bear", "ink"))
        if kind == "multi":
            s.add_argument("--label", nargs="+")
            s.add_argument("--rebase", action="store_true")
            s.add_argument("--invert-key", nargs="+")
    a = p.parse_args()
    {"cot": draw_cot, "line": draw_line, "multi": draw_multi}[a.kind](a)


if __name__ == "__main__":
    main()
