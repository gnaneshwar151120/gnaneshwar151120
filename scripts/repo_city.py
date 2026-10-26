"""Generate assets/repo-city.svg: every public repo as a building in an isometric, animated city.

python3 scripts/repo_city.py

- Districts are the kinds of work; building height follows repo size (log scale).
- Certifications float above the city as blimps.
- Technologies ride a train around the island.
Plain SVG with CSS and SMIL animation, so GitHub shows it as an image. Edit REPOS / TECH / CERTS and rerun.
"""
import math
from pathlib import Path

W, H = 1000, 900
OX, OY = 438, 330          # screen position of grid (0, 0)
A, B, Z = 27, 13.5, 36       # iso step x, iso step y, pixels per unit of height
GX, GY = 17, 12            # island size in grid units

DISTRICTS = {
    "infra": ("AUTOMATION &amp; INFRA", "#34d399", (9.8, 0.4, 6.8, 4.6)),
    "data":  ("DATA ENGINEERING",   "#4c8dff", (0.4, 0.4, 7.6, 4.6)),
    "ml":    ("MACHINE LEARNING",   "#a78bfa", (9.8, 6.2, 6.8, 5.4)),
    "ana":   ("ANALYTICS",          "#f59e0b", (0.4, 6.2, 7.6, 5.4)),
}

# (label on the roof, repo name, size in KB, district, grid x, grid y)
# Only repos with a real README and real work in them. Add a line here when a new repo qualifies.
REPOS = [
    ("post-pipeline",     "linkedin-post-pipeline",                  1488, "infra", 10.6, 1.0),
    ("almalinux-monitor", "wsl-almalinux-monitoring",                 707, "infra", 13.8, 1.0),
    ("nyc-taxi-etl",      "pyspark-nyc-taxi-etl",                   48045, "data", 1.4, 1.0),
    ("sql-solutions",     "StrataScratch-SQL-solutions",               73, "data", 4.8, 1.0),
    ("ad-hoc-sql",        "AD_HOC",                                  1541, "data", 3.1, 3.2),
    ("pca-images",        "Linear_Algebra_Meets_Images_PCA",         1368, "ml", 10.6, 7.0),
    ("card-churn",        "credit-card-cancellation-prediction",      835, "ml", 13.8, 7.0),
    ("card-default",      "defaultcreditcard",                       6356, "ml", 14.2, 9.6),
    ("insurance-claims",  "insurance-auto-claims-analysis",          1605, "ana", 1.4, 7.0),
    ("mental-health",     "Mental-Health-Care-in-the-Last-4-WEEKS",  2408, "ana", 4.8, 7.0),
    ("ipl-best-xi",       "BEST-XI-OF-IPL-2024",                     1592, "ana", 1.4, 9.4),
    ("aqi-index",         "AQI_INDEX",                                282, "ana", 4.8, 9.4),
]

TECH = ["Python", "SQL", "PySpark", "Claude Code", "MCP", "Prometheus", "Grafana", "Loki",
        "Puppet", "Linux", "NGINX", "PostgreSQL", "Azure", "Playwright", "Databricks", "GitHub Actions"]

# (text, colour, x, y, drift seconds)
CERTS = [
    ("4× Claude Certified", "#d97757", 800, 64, 7),
    ("3× Microsoft Certified", "#0078d4", 752, 128, 9),
    ("6× Grafana Labs", "#f46800", 170, 236, 8),
    ("Databricks Fundamentals", "#ff3621", 850, 240, 10),
]

LOOP = 8


def P(x, y, z=0.0):
    return OX + (x - y) * A, OY + (x + y) * B - z * Z


def pts(*ps):
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in ps)


def path(points, z=0.0, close=False):
    s = [P(x, y, z) for x, y in points]
    return "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in s) + (" Z" if close else "")


def shade(hex_color, f):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c * f))) for c in (r, g, b))


def height(kb):
    return max(.8, min(3.4, .8 + .62 * (math.log10(kb + 1) - .8)))


def box(x, y, w, d, h, color, seed=0, body="#18233f"):
    g = [P(x, y), P(x + w, y), P(x + w, y + d), P(x, y + d)]
    t = [P(x, y, h), P(x + w, y, h), P(x + w, y + d, h), P(x, y + d, h)]
    o = ["<g>",
         f'<polygon points="{pts(g[3], g[2], t[2], t[3])}" fill="{shade(body, 1.25)}"/>',
         f'<polygon points="{pts(g[1], g[2], t[2], t[1])}" fill="{body}"/>',
         f'<polygon points="{pts(*t)}" fill="{shade(color, .85)}" stroke="{color}" stroke-width="1.4"/>',
         f'<polyline points="{pts(t[3], t[2], t[1])}" fill="none" stroke="{shade(color, 1.25)}" stroke-width="2"/>']
    rows = int((h - .35) / .42)
    for i in range(rows):
        zz = .3 + i * .42
        for j, (u0, u1) in enumerate(((.16, .42), (.58, .84))):
            for face in (0, 1):
                if face == 0:   # right face, x = x + w
                    q = [P(x + w, y + d * u0, zz), P(x + w, y + d * u1, zz), P(x + w, y + d * u1, zz + .2), P(x + w, y + d * u0, zz + .2)]
                else:           # left face, y = y + d
                    q = [P(x + w * u0, y + d, zz), P(x + w * u1, y + d, zz), P(x + w * u1, y + d, zz + .2), P(x + w * u0, y + d, zz + .2)]
                delay = ((seed * 7 + i * 3 + j * 5 + face * 4) % 13) * .29
                o.append(f'<polygon class="win" style="animation-delay:{delay:.2f}s" points="{pts(*q)}" fill="{color}"/>')
    o.append("</g>")
    return "\n".join(o)


def pill(cx, cy, text, color, size=12.5, pad=12, mono=True, bg="#0b1226"):
    w = len(text) * size * (.62 if mono else .58) + pad * 2
    h = size + 12
    cls = "mono" if mono else "sans"
    return (f'<g transform="translate({cx:.1f} {cy:.1f})"><rect x="{-w / 2:.1f}" y="{-h / 2:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2:.1f}" '
            f'fill="{bg}" fill-opacity=".93" stroke="{color}" stroke-opacity=".8"/>'
            f'<text class="{cls}" x="0" y="{size * .36:.1f}" text-anchor="middle" font-size="{size}" font-weight="700" fill="{shade(color, 1.3)}">{text}</text></g>')


def build():
    o = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img"
  aria-label="Gnaneshwar Reddy's repo city: each public repository is a building, grouped into automation and infrastructure, data engineering, machine learning and analytics districts. Certifications float above as blimps and technologies ride a train around the island.">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a0f1e"/><stop offset="1" stop-color="#121a36"/></linearGradient>
  <radialGradient id="glow" cx=".5" cy=".62" r=".55"><stop offset="0" stop-color="#4c8dff" stop-opacity=".2"/><stop offset="1" stop-color="#4c8dff" stop-opacity="0"/></radialGradient>
  <style>
    .sans {{ font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .win {{ animation: win 3.4s ease-in-out infinite; opacity: .3; }}
    @keyframes win {{ 0%, 100% {{ opacity: .22; }} 50% {{ opacity: .95; }} }}
    .star {{ animation: tw 2.6s ease-in-out infinite; }}
    @keyframes tw {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
    .caret {{ animation: caret 1s steps(1) infinite; }}
    @keyframes caret {{ 50% {{ opacity: 0; }} }}
  </style>
</defs>
<rect width="{W}" height="{H}" rx="22" fill="url(#bg)"/>
<rect width="{W}" height="{H}" rx="22" fill="url(#glow)"/>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="21.5" fill="none" stroke="#2a3a66"/>''']

    # stars
    for i in range(46):
        sx, sy = (i * 211) % (W - 40) + 20, (i * 97) % 300 + 14
        if sx < 580 and sy < 190:   # keep the header text clear
            continue
        o.append(f'<circle class="star" style="animation-delay:{(i % 9) * .31:.2f}s" cx="{sx}" cy="{sy}" r="{1 + (i % 3) * .5}" fill="#c9d5f2"/>')

    # header
    o.append('''<g class="sans">
  <text x="44" y="66" class="mono" font-size="15" fill="#7aa7ff" letter-spacing="3">@gnaneshwar151120</text>
  <text x="44" y="116" font-size="46" font-weight="800" fill="#eef3ff" letter-spacing="-1">Gnaneshwar Reddy</text>
  <text x="44" y="148" font-size="18" fill="#9fb0d4">AI agents · infra monitoring · data. <tspan fill="#7aa7ff" font-weight="700">Welcome to my repo city.</tspan></text>
  <text x="44" y="174" class="mono" font-size="13" fill="#6f7fa6">every building is one of my repos · height = repo size<tspan class="caret" fill="#34d399"> ▍</tspan></text>
</g>''')

    # certification blimps
    for text, col, x, y, dur in CERTS:
        w = len(text) * 8.2 + 44
        o.append(f'''<g><animateTransform attributeName="transform" type="translate" values="0 0; 14 -6; 0 0" dur="{dur}s" repeatCount="indefinite"/>
  <g transform="translate({x} {y})">
    <path d="M{-w / 2 + 6} 18 L{-w / 2 - 14} 6 L{-w / 2 - 14} 30 Z" fill="{shade(col, .7)}"/>
    <rect x="{-w / 2:.1f}" y="0" width="{w:.1f}" height="36" rx="18" fill="{shade(col, .35)}" stroke="{col}" stroke-width="2"/>
    <rect x="-16" y="36" width="32" height="10" rx="3" fill="{shade(col, .55)}"/>
    <text class="sans" x="4" y="24" text-anchor="middle" font-size="14.5" font-weight="800" fill="#fff4ee">{text}</text>
  </g></g>''')

    # tech train: carriages on a track around the island
    m = 1.1
    loop = [(-m, -m), (GX + m, -m), (GX + m, GY + m), (-m, GY + m)]
    d = path(loop, z=-.6, close=True)
    o.append(f'<path d="{d}" stroke="#33498a" stroke-width="6" fill="none" stroke-linejoin="round"/>')
    o.append(f'<path d="{d}" stroke="#0a0f1e" stroke-width="2" fill="none" stroke-dasharray="3 7"/>')
    dur = 72
    for i, t in enumerate(["🚂"] + TECH):
        begin = -i * dur / (len(TECH) + 1) * .78
        if t == "🚂":
            car = ('<g><rect x="-34" y="-17" width="68" height="30" rx="8" fill="#ff3621" stroke="#fde68a" stroke-width="2"/>'
                   '<rect x="8" y="-27" width="12" height="12" rx="2" fill="#ff3621"/>'
                   '<text class="sans" x="0" y="5" text-anchor="middle" font-size="12" font-weight="800" fill="#fff">TECH ▸</text>'
                   '<circle cx="-18" cy="15" r="5" fill="#0a0f1e" stroke="#fde68a" stroke-width="2"/><circle cx="18" cy="15" r="5" fill="#0a0f1e" stroke="#fde68a" stroke-width="2"/></g>')
        else:
            col = ("#34d399", "#7aa7ff", "#a78bfa", "#f59e0b")[i % 4]
            wpx = len(t) * 7.6 + 24
            car = (f'<g><rect x="{-wpx / 2:.1f}" y="-15" width="{wpx:.1f}" height="28" rx="6" fill="#141d38" stroke="{col}" stroke-width="2"/>'
                   f'<rect x="{-wpx / 2:.1f}" y="-15" width="{wpx:.1f}" height="6" rx="3" fill="{col}"/>'
                   f'<text class="sans" x="0" y="7" text-anchor="middle" font-size="12.5" font-weight="700" fill="#e6edf8">{t}</text>'
                   f'<circle cx="{-wpx / 2 + 12:.1f}" cy="15" r="4.5" fill="#0a0f1e" stroke="{col}" stroke-width="2"/>'
                   f'<circle cx="{wpx / 2 - 12:.1f}" cy="15" r="4.5" fill="#0a0f1e" stroke="{col}" stroke-width="2"/></g>')
        o.append(f'<g>{car}<animateMotion dur="{dur}s" begin="{begin:.2f}s" repeatCount="indefinite" path="{d}"/></g>')

    # island slab and districts
    c = [P(0, 0), P(GX, 0), P(GX, GY), P(0, GY)]
    cb = [P(0, 0, -.6), P(GX, 0, -.6), P(GX, GY, -.6), P(0, GY, -.6)]
    o.append(f'<polygon points="{pts(c[3], c[2], cb[2], cb[3])}" fill="#1a2650"/>')
    o.append(f'<polygon points="{pts(c[1], c[2], cb[2], cb[1])}" fill="#121c3e"/>')
    o.append(f'<polygon points="{pts(*c)}" fill="#0f1834" stroke="#2a3a66" stroke-width="1.5"/>')
    grid = [path([(i, 0), (i, GY)]) for i in range(1, GX)] + [path([(0, j), (GX, j)]) for j in range(1, int(GY) + 1)]
    o.append(f'<path d="{" ".join(grid)}" stroke="#ffffff" stroke-opacity=".045" fill="none"/>')
    o.append(f'<polyline points="{pts(c[3], c[2], c[1])}" fill="none" stroke="#4c8dff" stroke-opacity=".5" stroke-width="2"/>')
    for key, (name, col, (x, y, w, d)) in DISTRICTS.items():
        q = [P(x, y), P(x + w, y), P(x + w, y + d), P(x, y + d)]
        o.append(f'<polygon points="{pts(*q)}" fill="{col}" fill-opacity=".07" stroke="{col}" stroke-opacity=".35" stroke-dasharray="5 5"/>')
    # avenues, with traffic
    for r in ([(8.4, 0.2), (8.4, GY - .2)], [(.2, 4.5), (GX - .2, 4.5)]):
        o.append(f'<path d="{path(r)}" stroke="#33498a" stroke-width="5" fill="none" stroke-linecap="round"/>')
        o.append(f'<path d="{path(r)}" stroke="#7aa7ff" stroke-width="2.5" fill="none" stroke-dasharray="4 16" opacity=".8">'
                 f'<animate attributeName="stroke-dashoffset" from="0" to="-40" dur="1.4s" repeatCount="indefinite"/></path>')

    # buildings, back to front
    cols = {k: v[1] for k, v in DISTRICTS.items()}
    blds = sorted(REPOS, key=lambda r: r[4] + r[5])
    for i, (lbl, _, kb, dist, x, y) in enumerate(blds):
        o.append(box(x, y, 1.7, 1.7, height(kb), cols[dist], seed=i))

    # district names painted flat on the ground along each district's front edge (iso text)
    ux, uy = A / math.hypot(A, B), B / math.hypot(A, B)
    for key, (name, col, (x, y, w, d)) in DISTRICTS.items():
        if key == "data":   # runs along the avenue instead, where nothing stands in front of it
            sx, sy = P(x + w - .3, y + d - .4)
            o.append(f'<text class="mono" transform="matrix({ux:.4f} {-uy:.4f} {ux:.4f} {uy:.4f} {sx:.1f} {sy:.1f})" '
                     f'font-size="15" font-weight="800" fill="{col}" letter-spacing="2" opacity=".85">{name}</text>')
            continue
        sx, sy = P(x + .3, y + d - .25)
        o.append(f'<text class="mono" transform="matrix({ux:.4f} {uy:.4f} {-ux:.4f} {uy:.4f} {sx:.1f} {sy:.1f})" '
                 f'font-size="15" font-weight="800" fill="{col}" letter-spacing="2" opacity=".85">{name}</text>')

    # roof labels: front buildings keep their spot, ones behind move up until nothing overlaps
    placed = []
    for lbl, _, kb, dist, x, y in sorted(blds, key=lambda r: -(r[4] + r[5])):
        px, py = P(x + .85, y + .85, height(kb))
        w, h = len(lbl) * 12.5 * .62 + 20, 25
        ly = py - 16
        while any(abs(px - qx) < (w + qw) / 2 + 4 and abs(ly - qy) < h + 3 for qx, qy, qw in placed):
            ly -= 8
        placed.append((px, ly, w))
        if py - ly > 20:
            o.append(f'<line x1="{px:.1f}" y1="{py - 4:.1f}" x2="{px:.1f}" y2="{ly + 12:.1f}" stroke="{cols[dist]}" stroke-opacity=".6" stroke-width="1.5"/>')
        o.append(pill(px, ly, lbl, cols[dist], size=12.5, pad=10))

    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "assets" / "repo-city.svg"
    out.write_text(build())
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
