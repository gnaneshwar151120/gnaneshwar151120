"""Escape the Matrix: a community game played through GitHub Issues.

python3 scripts/escape.py render                              # draw the board + buttons from game/escape.json
python3 scripts/escape.py move --title "matrix: up" --player octocat   # play one move, redraw, print the reply
python3 scripts/escape.py reset                               # start over (keeps nothing)

A visitor opens an issue titled "matrix: up|down|left|right". The workflow in .github/workflows/escape.yml runs
`move`, commits the new board and answers the issue with the printed reply. Neo moves one cell per issue; then the
agents take a breadth-first step towards him. Reach the ringing phone to escape. Standard library only.
"""
import argparse
import json
import random
import re
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matrix import BG, G, G2, G3, MONO, esc, frame, rain  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "game" / "escape.json"
OUT = ROOT / "assets" / "matrix"
REPO = "gnaneshwar151120/gnaneshwar151120"

# N = Neo, S = agent, E = the exit phone, # = wall
LAYOUTS = [
    ["N...#......#.",
     ".##.#.####.#.",
     ".#.......#...",
     ".#.###.#.#.##",
     "...#.S.#...S.",
     ".#.#.###.#.#.",
     ".#.......#..E"],
    ["N.#.....#....",
     "..#.###.#.##.",
     ".##...#...#..",
     "....#.#S#.#.#",
     ".####.#.#....",
     "......#...#S.",
     ".####...#.#.E"],
    ["N.....#......",
     ".###.##.###..",
     ".#.......#.#.",
     "...#S##.....#",
     ".#.#...#.#S#.",
     ".#...#.#.#...",
     "...#.#...#..E"],
]
COLS, ROWS = 13, 7
MAX_MOVES = 60          # the system reboots after this many moves: point to the agents
REST_EVERY = 3          # the agents rest on every third move
FRENZY_AFTER = 30       # after this many moves, every agent moves every turn
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
ALIASES = {"u": "up", "w": "up", "↑": "up", "▲": "up", "d": "down", "s": "down", "↓": "down", "▼": "down",
           "l": "left", "a": "left", "←": "left", "◀": "left", "r": "right", "→": "right", "▶": "right"}
ARROW = {"up": "▲", "down": "▼", "left": "◀", "right": "▶"}

TAUNTS = [
    "Every path is a graph, {u}. I have already searched it.",
    "Breadth-first, {u}. I never miss a node.",
    "Your move was logged. Mine was computed.",
    "Humans guess. Agents plan.",
    "The exit is a phone. Phones can be traced.",
    "Interesting choice, {u}. Statistically, a poor one.",
    "I do not get tired, {u}. I only get closer.",
]
CAUGHT = "Caught. The simulation thanks you for your data, {u}."
ESCAPED = "Signal lost. Neo is out. Well played, {u}."
WALL = "That is a wall, {u}. Even the Matrix has rules."
REBOOT = "Too slow. The system rebooted. Agents take the point."


def parse(layout):
    neo, agents, walls, exit_ = None, [], set(), None
    for y, row in enumerate(LAYOUTS[layout]):
        for x, ch in enumerate(row):
            if ch == "#":
                walls.add((x, y))
            elif ch == "N":
                neo = (x, y)
            elif ch == "S":
                agents.append((x, y))
            elif ch == "E":
                exit_ = (x, y)
    return neo, agents, walls, exit_


def new_run(state):
    layout = (state.get("run", 0)) % len(LAYOUTS)
    neo, agents, _, _ = parse(layout)
    state.update(run=state.get("run", 0) + 1, layout=layout, neo=list(neo), agents=[list(a) for a in agents],
                 moves=0, trail=[], players=[])
    return state


def load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return new_run({"humans": 0, "agents_score": 0, "log": [], "hall": [], "taunt": "Welcome, human. Pick a direction."})


def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1) + "\n")


def open_cell(c, walls):
    x, y = c
    return 0 <= x < COLS and 0 <= y < ROWS and c not in walls


def step_towards(start, goal, walls, blocked):
    """First cell on a shortest path from start to goal (breadth-first search), or start if there is none."""
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for dx, dy in DIRS.values():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in prev and open_cell(nxt, walls) and (nxt not in blocked or nxt == goal):
                prev[nxt] = cur
                q.append(nxt)
    if goal not in prev:
        return start
    cur = goal
    while prev[cur] != start and prev[cur] is not None:
        cur = prev[cur]
    return cur


def parse_title(title):
    m = re.match(r"\s*matrix\s*:\s*(\S+)", title or "", re.I)
    if not m:
        return None
    word = m.group(1).lower()
    return word if word in DIRS else ALIASES.get(word)


def clean_player(p):
    return re.sub(r"[^A-Za-z0-9-]", "", p or "")[:39] or "anonymous"


def move(state, direction, player):
    """Apply one move. Returns (outcome, message). outcome: wall | moved | escaped | caught | reboot."""
    _, _, walls, exit_ = parse(state["layout"])
    neo = tuple(state["neo"])
    agents = [tuple(a) for a in state["agents"]]
    dx, dy = DIRS[direction]
    nxt = (neo[0] + dx, neo[1] + dy)
    if not open_cell(nxt, walls):
        state["taunt"] = WALL.format(u="@" + player)
        return "wall", state["taunt"]

    state["trail"] = (state["trail"] + [list(neo)])[-6:]
    state["moves"] += 1
    if player not in state["players"]:
        state["players"].append(player)
    neo = nxt
    state["neo"] = list(neo)
    entry = {"run": state["run"], "user": player, "dir": direction}

    if neo in agents:
        outcome = "caught"
    elif neo == exit_:
        outcome = "escaped"
    else:
        # agents take turns and rest every third move; once the run drags on, they all move every turn
        if state["moves"] > FRENZY_AFTER:
            movers = range(len(agents))
        elif state["moves"] % REST_EVERY == 0:
            movers = []
        else:
            movers = [state["moves"] % len(agents)]
        for i in movers:
            others = {a for j, a in enumerate(agents) if j != i}
            agents[i] = step_towards(agents[i], neo, walls, others)
        state["agents"] = [list(a) for a in agents]
        outcome = "caught" if neo in agents else ("reboot" if state["moves"] >= MAX_MOVES else "moved")

    u = "@" + player
    if outcome == "escaped":
        state["humans"] += 1
        state["hall"] = (state["hall"] + [{"run": state["run"], "user": player, "moves": state["moves"],
                                           "crew": len(state["players"])}])[-5:]
        msg = ESCAPED.format(u=u)
    elif outcome == "caught":
        state["agents_score"] += 1
        msg = CAUGHT.format(u=u)
    elif outcome == "reboot":
        state["agents_score"] += 1
        msg = REBOOT
    else:
        msg = random.Random(state["moves"] * 31 + state["run"]).choice(TAUNTS).format(u=u)
    entry["result"] = outcome
    state["log"] = (state["log"] + [entry])[-8:]
    state["taunt"] = msg
    if outcome in ("escaped", "caught", "reboot"):
        state["last_end"] = {"run": state["run"], "result": outcome, "user": player, "moves": state["moves"]}
        new_run(state)
    return outcome, msg


# ---------------------------------------------------------------- drawing

CELL, MX, MY = 54, 28, 96
W, H = 1000, 560


def neo_svg(cx, cy):
    return (f'<g filter="url(#glow)"><circle cx="{cx}" cy="{cy - 11}" r="6.5" fill="#d7ffe0"/>'
            f'<path d="M{cx - 5} {cy - 4} L{cx + 5} {cy - 4} L{cx + 12} {cy + 17} L{cx - 12} {cy + 17} Z" fill="#d7ffe0"/>'
            f'<rect x="{cx - 5}" y="{cy - 13}" width="10" height="2.6" rx="1" fill="{BG}"/></g>')


def agent_svg(cx, cy):
    return (f'<g><circle cx="{cx}" cy="{cy - 11}" r="6.5" fill="#0d1f10" stroke="{G}" stroke-width="1.4"/>'
            f'<path d="M{cx - 6} {cy - 4} L{cx + 6} {cy - 4} L{cx + 10} {cy + 17} L{cx - 10} {cy + 17} Z" fill="#0d1f10" stroke="{G}" stroke-width="1.4"/>'
            f'<path d="M{cx} {cy - 4} L{cx - 2} {cy + 8} L{cx} {cy + 11} L{cx + 2} {cy + 8} Z" fill="{G}"/>'
            f'<rect x="{cx - 6}" y="{cy - 13.5}" width="12" height="3.2" rx="1.2" fill="{G}" class="shades"/></g>')


def phone_svg(cx, cy):
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="10" fill="none" stroke="{G}" stroke-width="1.5">'
                    f'<animate attributeName="r" values="10;24" dur="1.6s" begin="{i * .53:.2f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".9;0" dur="1.6s" begin="{i * .53:.2f}s" repeatCount="indefinite"/></circle>'
                    for i in range(3))
    return (rings + f'<rect x="{cx - 11}" y="{cy - 15}" width="22" height="30" rx="4" fill="{BG}" stroke="{G}" stroke-width="1.6"/>'
            f'<text class="m" x="{cx}" y="{cy + 6}" font-size="17" text-anchor="middle" fill="{G}">☎</text>')


def board_svg(state):
    _, _, walls, exit_ = parse(state["layout"])
    rnd = random.Random(state["layout"] * 101 + 5)
    cells = []
    for y in range(ROWS):
        for x in range(COLS):
            px, py = MX + x * CELL, MY + y * CELL
            if (x, y) in walls:
                glyph = esc(rnd.choice("ｱｲｳｴｵｶｷｸｹｺｻｼｽ0123456789"))
                cells.append(f'<rect x="{px + 2}" y="{py + 2}" width="{CELL - 4}" height="{CELL - 4}" rx="5" fill="#082a10" stroke="{G3}" stroke-opacity=".7"/>'
                             f'<text class="m" x="{px + CELL / 2}" y="{py + CELL / 2 + 6}" font-size="18" text-anchor="middle" fill="{G3}" opacity=".85">{glyph}</text>')
            else:
                cells.append(f'<circle cx="{px + CELL / 2}" cy="{py + CELL / 2}" r="1.6" fill="{G3}" opacity=".6"/>')
    trail = "".join(f'<circle cx="{MX + tx * CELL + CELL / 2}" cy="{MY + ty * CELL + CELL / 2}" r="{3 + i}" fill="{G}" opacity="{.08 + i * .05:.2f}"/>'
                    for i, (tx, ty) in enumerate(state["trail"]))
    c = lambda p: (MX + p[0] * CELL + CELL / 2, MY + p[1] * CELL + CELL / 2)  # noqa: E731
    pieces = [phone_svg(*c(exit_)), trail]
    big = lambda f, p: f'<g transform="translate({c(p)[0]} {c(p)[1] + 2}) scale(1.25)">{f(0, 0)}</g>'  # noqa: E731
    pieces += [big(agent_svg, a) for a in state["agents"]]
    pieces.append(big(neo_svg, state["neo"]))
    bw, bh = COLS * CELL, ROWS * CELL
    return (f'<rect x="{MX - 10}" y="{MY - 10}" width="{bw + 20}" height="{bh + 20}" rx="12" fill="#020602" fill-opacity=".88" stroke="{G3}"/>'
            + "".join(cells) + "".join(pieces))


def panel_svg(state):
    x0 = MX + COLS * CELL + 34
    out = [f'<text class="m" x="{x0}" y="{MY + 8}" font-size="12" fill="{G3}" letter-spacing="2">SCORE</text>',
           f'<text class="m" x="{x0}" y="{MY + 44}" font-size="30" fill="#d7ffe0" font-weight="700">{state["humans"]}'
           f'<tspan fill="{G3}" font-size="22"> : </tspan><tspan fill="{G}">{state["agents_score"]}</tspan></text>',
           f'<text class="m" x="{x0}" y="{MY + 64}" font-size="11" fill="{G2}">humans · agents</text>',
           f'<text class="m" x="{x0}" y="{MY + 104}" font-size="12" fill="{G3}" letter-spacing="2">LAST MOVES</text>']
    log = list(reversed(state["log"]))[:6]
    if not log:
        out.append(f'<text class="m" x="{x0}" y="{MY + 128}" font-size="13" fill="{G2}">no moves yet. be first.</text>')
    for i, e in enumerate(log):
        mark = {"escaped": " ★", "caught": " ✕", "reboot": " ⟲"}.get(e.get("result"), "")
        out.append(f'<text class="m" x="{x0}" y="{MY + 128 + i * 21}" font-size="13" fill="{G if i == 0 else G2}">'
                   f'{ARROW[e["dir"]]} @{esc(e["user"][:16])}{mark}</text>')
    yh = MY + 268
    out.append(f'<text class="m" x="{x0}" y="{yh}" font-size="12" fill="{G3}" letter-spacing="2">ESCAPED</text>')
    hall = list(reversed(state["hall"]))[:3]
    if not hall:
        out.append(f'<text class="m" x="{x0}" y="{yh + 24}" font-size="13" fill="{G2}">nobody. yet.</text>')
    for i, h in enumerate(hall):
        out.append(f'<text class="m" x="{x0}" y="{yh + 24 + i * 21}" font-size="13" fill="#d7ffe0">'
                   f'#{h["run"]} @{esc(h["user"][:14])} <tspan fill="{G3}">{h["moves"]}m</tspan></text>')
    return "\n".join(out)


def render(state):
    end = state.get("last_end")
    status = f'RUN #{state["run"]} · MOVE {state["moves"]}/{MAX_MOVES}'
    if end and state["moves"] == 0:
        word = {"escaped": "ESCAPED", "caught": "CAUGHT", "reboot": "REBOOTED"}[end["result"]]
        status = f'RUN #{end["run"]} {word} · RUN #{state["run"]} LOADING'
    body = [rain(W, H, 46, seed=17, opacity=.16, size=15),
            f'<text class="m" x="{MX - 10}" y="48" font-size="26" fill="{G}" font-weight="700" letter-spacing="3">ESCAPE THE MATRIX<tspan class="caret">_</tspan></text>',
            f'<text class="m" x="{W - 28}" y="48" font-size="13" fill="{G2}" text-anchor="end" letter-spacing="1">{esc(status)}</text>',
            f'<text class="m" x="{MX - 10}" y="70" font-size="12.5" fill="{G3}">guide Neo to the ringing phone. one move per issue. the agents run a breadth-first search.</text>',
            board_svg(state), panel_svg(state),
            f'<text class="m" x="{MX - 10}" y="{H - 34}" font-size="14" fill="{G}">agent&gt; <tspan fill="#d7ffe0">{esc(state["taunt"])}</tspan></text>',
            f'<text class="m" x="{MX - 10}" y="{H - 14}" font-size="11.5" fill="{G3}">your move: pick a direction below · the board updates in about a minute</text>']
    css = (".shades { animation: shades 3s ease-in-out infinite; } @keyframes shades { 50% { opacity: .35; } }"
           f" text.m {{ font-family: {MONO}; }}")
    glow = ('<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    svg = frame(W, H, "\n".join(body), f'Escape the Matrix, run {state["run"]}: {state["taunt"]}', css)
    return svg.replace("<defs>", "<defs>\n  " + glow, 1)


def button_svg(direction):
    label = {"up": "▲  UP", "down": "▼  DOWN", "left": "◀  LEFT", "right": "RIGHT  ▶"}[direction]
    w, h = 240, 64
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Move Neo {direction}">
<style>.m {{ font-family: {MONO}; }} .p {{ animation: p 2.4s ease-in-out infinite; }} @keyframes p {{ 50% {{ stroke-opacity: .35; }} }}</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{BG}"/>
<rect class="p" x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="none" stroke="{G}" stroke-width="1.6"/>
<text class="m" x="{w / 2}" y="{h / 2 + 7}" font-size="20" font-weight="700" text-anchor="middle" fill="{G}" letter-spacing="2">{label}</text>
</svg>'''


def write_all(state):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "escape.svg").write_text(render(state))
    for d in DIRS:
        (OUT / f"move-{d}.svg").write_text(button_svg(d))


def reply(outcome, msg, player, state):
    head = {"wall": "🧱 **Blocked.**", "moved": f"✅ **Neo moved.** Run #{state['run']}, move {state['moves']}.",
            "escaped": "★ **Neo escaped!** You made the winning move.", "caught": "✕ **Neo was caught.**",
            "reboot": "⟲ **System reboot.**"}[outcome]
    tail = "A new run has started." if outcome in ("escaped", "caught", "reboot") else "Make the next move from the profile."
    return (f"{head}\n\n> agent> {msg}\n\n{tail} The board updates in about a minute: "
            f"[github.com/gnaneshwar151120](https://github.com/gnaneshwar151120)\n\n"
            f"<sub>Escape the Matrix · moves are issues, the agents are a breadth-first search in a GitHub Action.</sub>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "move", "reset"])
    ap.add_argument("--title", default="")
    ap.add_argument("--player", default="")
    a = ap.parse_args()
    if a.cmd == "reset":
        state = new_run({"humans": 0, "agents_score": 0, "log": [], "hall": [], "taunt": "Welcome, human. Pick a direction."})
    else:
        state = load()
    if a.cmd == "move":
        direction, player = parse_title(a.title), clean_player(a.player)
        if not direction:
            print("🤔 **Unknown move.** Use one of the buttons on the profile; titles look like `matrix: up`.")
            return
        outcome, msg = move(state, direction, player)
        print(reply(outcome, msg, player, state))
    save(state)
    write_all(state)


if __name__ == "__main__":
    main()
