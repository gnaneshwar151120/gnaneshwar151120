"""Draw the last year of GitHub contributions as a Matrix signal: assets/matrix/signal.svg.

GITHUB_TOKEN=... python3 scripts/signal.py     # falls back to `gh auth token`

One glyph per day, brighter the more you contributed; a scan line sweeps the year. The daily workflow
.github/workflows/signal.yml reruns this so the chart stays current. Standard library only.
"""
import datetime as dt
import json
import os
import random
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matrix import BG, G, G2, G3, GLYPHS, esc, frame, rain  # noqa: E402,F401

USER = "gnaneshwar151120"
OUT = Path(__file__).resolve().parents[1] / "assets" / "matrix" / "signal.svg"
QUERY = """query($u: String!) { user(login: $u) { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { date contributionCount } } } } } }"""
LEVEL = [("#0c2412", .9), (G3, 1), (G2, 1), (G, 1), ("#d7ffe0", 1)]


def token():
    t = os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def fetch():
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


def level(n, top):
    if n == 0:
        return 0
    return min(4, 1 + int(3 * n / max(top, 1)))


def stats(weeks):
    days = [d for w in weeks for d in w]
    active = sum(1 for _, n in days if n)
    best = max(days, key=lambda d: d[1])
    run = longest = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    return active, longest, best


def render(total, weeks):
    w, h = 1000, 330
    cell, x0, y0 = 16, 92, 104
    top = max(n for wk in weeks for _, n in wk)
    rnd = random.Random(11)
    out, months = [], []
    for wi, wk in enumerate(weeks):
        x = x0 + wi * cell
        first = dt.date.fromisoformat(wk[0][0])
        if first.day <= 7:
            months.append(f'<text class="m" x="{x}" y="{y0 - 14}" font-size="11" fill="{G3}">{first.strftime("%b").lower()}</text>')
        for date, n in wk:
            row = dt.date.fromisoformat(date).isoweekday() % 7  # Sunday on top, like GitHub
            y = y0 + row * cell
            lv = level(n, top)
            col, op = LEVEL[lv]
            g = esc(rnd.choice(GLYPHS[:46]))
            title = f"<title>{date}: {n} contribution{'s' if n != 1 else ''}</title>"
            if lv == 0:
                out.append(f'<text class="m" x="{x + 7}" y="{y + 12}" font-size="12" text-anchor="middle" fill="{col}" opacity="{op}">{g}{title}</text>')
            else:
                dur = rnd.uniform(1.6, 3.4)
                out.append(f'<rect x="{x}" y="{y}" width="{cell - 2}" height="{cell - 2}" rx="3" fill="{col}" opacity=".16"/>'
                           f'<text class="m" x="{x + 7}" y="{y + 12}" font-size="12" text-anchor="middle" fill="{col}" '
                           f'filter="url(#glow)">{g}{title}<animate attributeName="opacity" values="1;.55;1" dur="{dur:.1f}s" repeatCount="indefinite"/></text>')
    labels = "".join(f'<text class="m" x="{x0 - 12}" y="{y0 + r * cell + 12}" font-size="10.5" text-anchor="end" fill="{G3}">{d}</text>'
                     for r, d in ((1, "mon"), (3, "wed"), (5, "fri")))
    gw = len(weeks) * cell
    active, longest, best = stats(weeks)
    best_txt = f'{best[1]} on {dt.date.fromisoformat(best[0]).strftime("%b %-d")}' if best[1] else "-"
    figures = [("CONTRIBUTIONS", str(total)), ("ACTIVE DAYS", str(active)), ("LONGEST STREAK", f"{longest}d"), ("PEAK DAY", best_txt)]
    figs = "".join(f'<text class="m" x="{x0 + i * 215}" y="{h - 66}" font-size="11" fill="{G3}" letter-spacing="2">{k}</text>'
                   f'<text class="m" x="{x0 + i * 215}" y="{h - 40}" font-size="22" font-weight="700" fill="{G if i else "#d7ffe0"}">{esc(v)}</text>'
                   for i, (k, v) in enumerate(figures))
    legend = "".join(f'<rect x="{w - 150 + i * 18}" y="44" width="14" height="14" rx="3" fill="{LEVEL[i][0]}" opacity="{.5 if i == 0 else .9}"/>' for i in range(5))
    body = f'''{rain(w, h, 50, seed=43, opacity=.14, size=14)}
<rect x="40" y="30" width="{w - 80}" height="{h - 60}" rx="14" fill="#000" fill-opacity=".8" stroke="{G3}" stroke-opacity=".6"/>
<text class="m" x="{x0 - 30}" y="58" font-size="13" fill="{G3}" letter-spacing="3">SIGNAL · ONE GLYPH PER DAY · LAST 12 MONTHS</text>
<text class="m" x="{w - 160}" y="56" font-size="10.5" fill="{G3}" text-anchor="end">less</text>{legend}<text class="m" x="{w - 58}" y="56" font-size="10.5" fill="{G3}">more</text>
{"".join(months)}{labels}
{"".join(out)}
<rect class="sweep" x="{x0}" y="{y0 - 4}" width="{cell * 2}" height="{7 * cell + 6}" fill="url(#sweep)"/>
{figs}'''
    css = (f".sweep {{ animation: sweep 7s linear infinite; }} "
           f"@keyframes sweep {{ from {{ transform: translateX(-{cell * 2}px); }} to {{ transform: translateX({gw}px); }} }}")
    defs = ('<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<linearGradient id="sweep" x1="0" x2="1"><stop offset="0" stop-color="{G}" stop-opacity="0"/>'
            f'<stop offset=".85" stop-color="{G}" stop-opacity=".22"/><stop offset="1" stop-color="{G}" stop-opacity="0"/></linearGradient>')
    svg = frame(w, h, body, f"Signal: {total} contributions in the last year, {active} active days, longest streak {longest} days.", css)
    return svg.replace("<defs>", "<defs>\n  " + defs, 1)


if __name__ == "__main__":
    total, weeks = fetch()
    OUT.write_text(render(total, weeks))
    print(f"wrote assets/matrix/signal.svg ({total} contributions)")
