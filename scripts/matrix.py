"""Generate the Matrix-style profile visuals in assets/matrix/.

python3 scripts/matrix.py

Original artwork: procedural digital rain, terminal typing and progress bars in SVG with CSS/SMIL animation.
No film stills, logos or fonts are used.
"""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets" / "matrix"
G, G2, G3, BG = "#00ff41", "#00c837", "#008f11", "#050a05"
GLYPHS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789Z:.=*+<>|"
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New", monospace'

BASE_CSS = f"""
    .m {{ font-family: {MONO}; }}
    .caret {{ animation: caret 1s steps(1) infinite; }}
    @keyframes caret {{ 50% {{ opacity: 0; }} }}
    .scan {{ animation: scan 6s linear infinite; }}
    @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY(100%); }} }}
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rain(w, h, cols, seed=7, opacity=1.0, size=16):
    """Columns of glyphs falling forever; each column carries its own gradient (bright head, fading tail)."""
    rnd = random.Random(seed)
    out = []
    step = w / cols
    for c in range(cols):
        n = rnd.randint(10, 22)
        x = c * step + step / 2
        length = n * size
        dur = rnd.uniform(4.5, 11)
        begin = -rnd.uniform(0, dur)
        gid = f"rg{seed}_{c}"
        out.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{length}">'
                   f'<stop offset="0" stop-color="{G}" stop-opacity="0"/><stop offset=".75" stop-color="{G3}" stop-opacity=".7"/>'
                   f'<stop offset=".97" stop-color="{G}"/><stop offset="1" stop-color="#d7ffe0"/></linearGradient>')
        glyphs = "".join(f'<tspan x="{x:.1f}" y="{(i + 1) * size}">{esc(rnd.choice(GLYPHS))}</tspan>' for i in range(n))
        out.append(f'<g opacity="{opacity * rnd.uniform(.45, 1):.2f}"><animateTransform attributeName="transform" type="translate" '
                   f'from="0 {-length:.0f}" to="0 {h:.0f}" dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
                   f'<text class="m" font-size="{size - 2}" text-anchor="middle" fill="url(#{gid})">{glyphs}</text></g>')
    return "\n".join(out)


def frame(w, h, body, label, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">
<defs>
  <radialGradient id="vig" cx=".5" cy=".5" r=".7"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".75"/></radialGradient>
  <clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath>
  <style>{BASE_CSS}{extra_css}</style>
</defs>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="{BG}"/>
{body}
<rect width="{w}" height="{h}" fill="url(#vig)"/>
<rect class="scan" x="0" y="0" width="{w}" height="40" fill="{G}" opacity=".04"/>
</g>
<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="17.5" fill="none" stroke="{G3}" stroke-opacity=".8"/>
</svg>'''


def typed(lines, start, per, loop, x, y0, dy, size, cls=""):
    """Terminal lines that type in one after another and clear at the end of the loop."""
    css, out = [], []
    for i, line in enumerate(lines):
        a, b = (start + i * per) / loop * 100, (start + i * per + per * .7) / loop * 100
        css.append(f".t{i}{cls} {{ animation: t{i}{cls} {loop}s steps({max(len(line), 1)}) infinite; clip-path: inset(0 100% 0 0); }}"
                   f"@keyframes t{i}{cls} {{ 0%, {a:.1f}% {{ clip-path: inset(0 100% 0 0); }} {b:.1f}%, 96% {{ clip-path: inset(0 0 0 0); }} 100% {{ clip-path: inset(0 100% 0 0); }} }}")
        out.append(f'<text class="m t{i}{cls}" x="{x}" y="{y0 + i * dy}" font-size="{size}" fill="{G}">{esc(line)}</text>')
    return "\n".join(out), "\n".join(css)


def hero():
    w, h = 1000, 440
    lines, css = typed(["> Wake up, Gnaneshwar...", "> The repos have you...", "> Follow the green packets."], .4, 2.2, 13, 70, 120, 40, 24)
    body = f'''{rain(w, h, 58, seed=3, opacity=.55)}
<rect x="40" y="60" width="{w - 80}" height="{h - 120}" rx="14" fill="#000" fill-opacity=".72" stroke="{G3}" stroke-opacity=".6"/>
<text class="m" x="70" y="92" font-size="12" fill="{G3}" letter-spacing="3">OPERATOR TERMINAL · gnaneshwar151120</text>
{lines}
<text class="m" x="70" y="300" font-size="50" font-weight="700" fill="{G}" letter-spacing="2">GNANESHWAR REDDY<tspan class="caret">█</tspan></text>
<text class="m" x="72" y="336" font-size="17" fill="{G2}">AI agents · infra monitoring · data   //  Engineer @ Genzeon</text>
<text class="m" x="72" y="358" font-size="13" fill="{G3}">4x Claude Certified · 3x Microsoft Certified · 6x Grafana Labs · Databricks</text>'''
    return frame(w, h, body, "Gnaneshwar Reddy. Wake up. The repos have you. Follow the green packets. AI agents, infra monitoring and data.", css)


def pill(color, title, sub, file_label):
    w, h = 480, 150
    c1, c2 = ("#ff3b3b", "#8b0000") if color == "red" else ("#3b8bff", "#0b2d8b")
    body = f'''{rain(w, h, 26, seed=11 if color == "red" else 13, opacity=.35, size=14)}
<g transform="translate(60 75) rotate(-28)">
  <ellipse cx="0" cy="30" rx="34" ry="8" fill="#000" opacity=".55"/>
  <rect x="-46" y="-19" width="92" height="38" rx="19" fill="{c2}"/>
  <path d="M-27 -19 h27 v38 h-27 a19 19 0 0 1 0 -38 z" fill="{c1}"/>
  <rect x="-36" y="-13" width="60" height="7" rx="3.5" fill="#fff" opacity=".45"/>
  <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0; 0 -5; 0 0" dur="3s" repeatCount="indefinite"/>
</g>
<text class="m" x="130" y="68" font-size="24" font-weight="700" fill="{c1}">{esc(title)}</text>
<text class="m" x="130" y="98" font-size="15" fill="{G2}">{esc(sub)}</text>
<text class="m" x="130" y="124" font-size="12" fill="{G3}">{esc(file_label)}<tspan class="caret"> ▍</tspan></text>'''
    return frame(w, h, body, f"{title}: {sub}")


def construct():
    """Every tool from the resume master, grouped; chips load one by one. Tools still being learned stay "loading"."""
    w, h = 1000, 470
    groups = [("AI", ["Claude Code", "AI agents", "MCP", "prompt engineering"]),
              ("TESTING", ["pytest", "Playwright", "httpx"]),
              ("INFRA", ["Linux", "NGINX", "Redis", "Puppet"]),
              ("OBSERVE", ["Prometheus", "Grafana", "Loki", "Alloy"]),
              ("DATA", ["Python", "SQL", "PySpark", "PostgreSQL", "MySQL", "Databricks*"]),
              ("CLOUD+OPS", ["Azure", "Azure DevOps", "Git", "GitHub", "Power BI", "Data Factory*"])]
    loop, start, per = 14, .5, .22
    css, rows, k = [], [], 0
    for gi, (name, tools) in enumerate(groups):
        y = 118 + gi * 44
        rows.append(f'<text class="m" x="70" y="{y}" font-size="13" fill="{G3}" letter-spacing="2">{name}</text>')
        x = 200
        for t in tools:
            learning = t.endswith("*")
            t = t.rstrip("*")
            cw = len(t) * 8.7 + 24
            a = (start + k * per) / loop * 100
            b = a + .6
            css.append(f".c{k} {{ animation: c{k} {loop}s infinite; opacity: 0; }}"
                       f"@keyframes c{k} {{ 0%, {a:.1f}% {{ opacity: 0; }} {b:.1f}%, 96% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}")
            if learning:
                rows.append(f'<g class="c{k}"><rect x="{x}" y="{y - 18}" width="{cw + 74:.0f}" height="26" rx="6" fill="none" stroke="{G3}" stroke-dasharray="4 3"/>'
                            f'<text class="m" x="{x + 12}" y="{y}" font-size="14.5" fill="{G2}">{esc(t)}</text>'
                            f'<text class="m caret" x="{x + cw - 4:.0f}" y="{y}" font-size="12" fill="{G3}">loading</text></g>')
                cw += 74
            else:
                rows.append(f'<g class="c{k}"><rect x="{x}" y="{y - 18}" width="{cw:.0f}" height="26" rx="6" fill="{G}" fill-opacity=".1" stroke="{G}" stroke-opacity=".8"/>'
                            f'<text class="m" x="{x + 12}" y="{y}" font-size="14.5" fill="{G}">{esc(t)}</text></g>')
            x += cw + 10
            k += 1
    done = start + k * per + .4
    fin, fcss = typed(["> I know MCP."], done, 1.6, loop, 70, 412, 0, 26, cls="f")
    body = f'''{rain(w, h, 58, seed=21, opacity=.22)}
<rect x="40" y="40" width="{w - 80}" height="{h - 80}" rx="14" fill="#000" fill-opacity=".8" stroke="{G3}" stroke-opacity=".6"/>
<text class="m" x="70" y="76" font-size="13" fill="{G3}" letter-spacing="3">THE CONSTRUCT · LOADING TRAINING PROGRAMS</text>
<text class="m" x="{w - 70}" y="76" font-size="12" fill="{G3}" text-anchor="end">dashed = still loading</text>
{"".join(rows)}
{fin}'''
    flat = ", ".join(t.rstrip("*") for _, ts in groups for t in ts)
    return frame(w, h, body, f"The Construct: tools I know: {flat}. Databricks and Azure Data Factory still loading. I know MCP.", "\n".join(css) + fcss)


def agents():
    w, h = 1000, 330
    procs = [("agent.manager", "plans · routes · checks", "READ", G2),
             ("agent.tester[*]", "one per feature · every user role", "READ", G2),
             ("agent.flow", "follows each case downstream", "READ", G2),
             ("agent.recorder", "the only one allowed to write", "WRITE after PUBLISH", "#ffd166")]
    rows = []
    for i, (name, what, mode, col) in enumerate(procs):
        y = 128 + i * 34
        rows.append(f'<text class="m" x="70" y="{y}" font-size="16" fill="{G}">{esc(name)}</text>'
                    f'<text class="m" x="290" y="{y}" font-size="15" fill="{G2}">{esc(what)}</text>'
                    f'<rect x="700" y="{y - 17}" width="{len(mode) * 9.6 + 20:.0f}" height="24" rx="5" fill="none" stroke="{col}"/>'
                    f'<text class="m" x="710" y="{y}" font-size="14" fill="{col}">{esc(mode)}</text>'
                    f'<circle cx="54" cy="{y - 5}" r="4" fill="{col}"><animate attributeName="opacity" values="1;.2;1" dur="{1.2 + i * .3:.1f}s" repeatCount="indefinite"/></circle>')
    body = f'''{rain(w, h, 58, seed=31, opacity=.2)}
<rect x="40" y="40" width="{w - 80}" height="{h - 80}" rx="14" fill="#000" fill-opacity=".8" stroke="{G3}" stroke-opacity=".6"/>
<text class="m" x="70" y="80" font-size="13" fill="{G3}" letter-spacing="3">$ ps -agents   ·   CLAUDE CODE + MCP</text>
{"".join(rows)}
<text class="m" x="70" y="{h - 62}" font-size="18" font-weight="700" fill="{G}">Unlike the other agents, mine ask before they write.<tspan class="caret"> █</tspan></text>'''
    return frame(w, h, body, "My agents: a manager, testers per feature, a flow checker, all read-only, and one recorder that writes only after PUBLISH. Unlike the other agents, mine ask before they write.")


def programs():
    w, h = 1000, 262
    groups = [("4", "Anthropic", "Claude Architect (Professional, Foundations), Developer, Associate"),
              ("3", "Microsoft", "AZ-900 · DP-900 · GitHub Foundations"),
              ("6", "Grafana Labs", "PromQL · LogQL · Observability · Dashboards · Explorer · Trailblazer"),
              ("1", "Databricks", "Databricks Fundamentals")]
    rows = []
    for i, (n, who, what) in enumerate(groups):
        y = 104 + i * 30
        rows.append(f'<text class="m" x="70" y="{y}" font-size="16" fill="{G}">[✓] {n}× {esc(who)}</text>'
                    f'<text class="m" x="320" y="{y}" font-size="14" fill="{G2}">{esc(what)}</text>')
    body = f'''{rain(w, h, 58, seed=41, opacity=.2)}
<rect x="40" y="36" width="{w - 80}" height="{h - 72}" rx="14" fill="#000" fill-opacity=".8" stroke="{G3}" stroke-opacity=".6"/>
<text class="m" x="70" y="70" font-size="13" fill="{G3}" letter-spacing="3">TRAINING PROGRAMS COMPLETED · 14</text>
{"".join(rows)}'''
    return frame(w, h, body, "Training programs completed: 4 Anthropic Claude certifications, 3 Microsoft, 6 Grafana Labs, 1 Databricks.")


def operator():
    w, h = 1000, 200
    body = f'''{rain(w, h, 58, seed=51, opacity=.3)}
<rect x="40" y="34" width="{w - 80}" height="{h - 68}" rx="14" fill="#000" fill-opacity=".78" stroke="{G3}" stroke-opacity=".6"/>
<g transform="translate(110 100)">
  <circle r="30" fill="none" stroke="{G}" stroke-width="2"><animate attributeName="r" values="26;46" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values=".9;0" dur="1.6s" repeatCount="indefinite"/></circle>
  <circle r="26" fill="#002b0c" stroke="{G}" stroke-width="2"/>
  <path d="M-11 -12 c3 -3 6 -1 7 2 l2 5 c1 2 0 4 -2 5 l-2 1 c2 5 5 8 10 10 l1 -2 c1 -2 3 -3 5 -2 l5 2 c3 1 5 4 2 7 c-4 4 -10 4 -16 0 c-6 -4 -11 -9 -14 -15 c-3 -6 -1 -10 2 -13 z" fill="{G}">
    <animateTransform attributeName="transform" type="rotate" values="0;-12;12;-12;12;0;0" dur="1.6s" repeatCount="indefinite"/></path>
</g>
<text class="m" x="170" y="88" font-size="13" fill="{G3}" letter-spacing="3">INCOMING CALL · OPERATOR</text>
<text class="m" x="170" y="122" font-size="26" font-weight="700" fill="{G}">Pick up. Let's talk.</text>
<text class="m" x="170" y="148" font-size="14" fill="{G2}">exit through LinkedIn → Gnaneshwar Reddy</text>'''
    return frame(w, h, body, "Incoming call from the operator. Pick up. Let's talk on LinkedIn.")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "hero.svg": hero(),
        "red-pill.svg": pill("red", "Take the red pill", "see how deep the repos go", "→ github.com/gnaneshwar151120"),
        "blue-pill.svg": pill("blue", "Take the blue pill", "go back to the feed", "→ linkedin.com/in/gnaneshwar-reddy"),
        "construct.svg": construct(),
        "agents.svg": agents(),
        "programs.svg": programs(),
        "operator.svg": operator(),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg)
        print(f"wrote assets/matrix/{name} ({len(svg) // 1024} KB)")
