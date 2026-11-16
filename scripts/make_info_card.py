"""
Build the neofetch-style info card SVG that sits to the RIGHT of the ASCII
portrait, and keep the cert count in README.md in sync with it.

All content comes from profile.json at the repo root -- edit that file, not
this script. The card height grows/shrinks with the number of rows. Rows fade
and slide in on a short stagger; STATIC=1 emits the frozen state for previews.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PROFILE = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "info-card.svg")
README = os.path.join(ROOT, "README.md")
STATIC = bool(os.environ.get("STATIC"))

W = 480
PAD = 20
TITLEBAR_H = 30
KEY_X = PAD
VAL_X = PAD + 92
BUL_X = KEY_X + 14
LINE_H = 20.5
FONT = 12.5
CHAR_W = 7.7  # widest common monospace fallback at 12.5px; used for fit checks

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
KEY = "#ffa657"
SECTION = "#58a6ff"
GREEN = "#3fb950"
ACCENT = "#22d3ee"

with open(PROFILE, encoding="utf-8") as f:
    P = json.load(f)

HOST = P["host"]
CERT_COUNT = sum(len(line) for line in P["certs"])

# row kinds: host | kv key value | sec title | bul text | sub text | gap
ROWS = [("host",)]
ROWS += [("kv", k, v) for k, v in P["about"]]
ROWS += [("gap",), ("sec", "Stack")]
ROWS += [("kv", k, v) for k, v in P["stack"]]
ROWS += [("gap",), ("sec", "Highlights"), ("bul", f"{CERT_COUNT} active certs")]
ROWS += [("sub", " · ".join(line)) for line in P["certs"]]
ROWS += [("bul", text) for text in P["projects"]]


def esc(s):
    return html.escape(s, quote=False)


def check_fit(text, x):
    if x + len(text) * CHAR_W > W - PAD:
        print(f"WARNING: may overflow the card, shorten it: {text!r}", file=sys.stderr)


def rise(inner, i):
    if STATIC:
        return f"<g>{inner}</g>"
    return f'<g class="ri" style="animation-delay:{0.15 + i * 0.06:.2f}s">{inner}</g>'


body = []
y = TITLEBAR_H + 30
for i, row in enumerate(ROWS):
    kind = row[0]
    if kind == "gap":
        y += LINE_H * 0.5
        continue
    if kind == "host":
        rule_x = KEY_X + (len(HOST) + len("@github")) * 8.6 + 10
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                 f'<tspan fill="{GREEN}">{esc(HOST)}</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{ACCENT}">github</tspan></text>'
                 f'<line x1="{rule_x:.0f}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "sec":
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="{FONT}" font-weight="700">'
                 f'&#8212; {esc(row[1])}</text>'
                 f'<line x1="{KEY_X + 12 + len(row[1])*8}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "kv":
        check_fit(row[2], VAL_X)
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="{FONT}" font-weight="700">{esc(row[1])}</text>'
                 f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="{FONT}">{esc(row[2])}</text>')
    elif kind == "bul":
        check_fit(row[1], BUL_X)
        inner = (f'<circle cx="{KEY_X+3}" cy="{y-4:.1f}" r="2.5" fill="{GREEN}"/>'
                 f'<text x="{BUL_X}" y="{y:.1f}" fill="{INK}" font-size="{FONT}">{esc(row[1])}</text>')
    elif kind == "sub":
        check_fit(row[1], BUL_X)
        inner = f'<text x="{BUL_X}" y="{y:.1f}" fill="{MUTED}" font-size="{FONT}">{esc(row[1])}</text>'
    else:
        continue
    body.append(rise(inner, i))
    y += LINE_H

H = round(y - LINE_H + 24)

style = "" if STATIC else (
    "<style>"
    ".ri{opacity:0;animation:ri .4s cubic-bezier(.2,.8,.2,1) forwards}"
    "@keyframes ri{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}"
    "@media (prefers-reduced-motion:reduce){.ri{opacity:1;animation:none}}"
    "</style>"
)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    style,
    '<defs>'
    f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2:.0f}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">{esc(HOST)}@github: ~$ neofetch</text>')
parts += body
parts.append("</svg>")

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(parts))
print("wrote", os.path.normpath(OUT), f"{W}x{H}")

# --- keep README's tagline and Credly badge in step with the cert list ---
with open(README, encoding="utf-8") as f:
    readme = f.read()
updated = re.sub(r"<p><b>.*?</b></p>",
                 lambda m: f"<p><b>{html.escape(P['tagline'], quote=False)} · {CERT_COUNT}× Certified</b></p>",
                 readme, count=1)
updated = re.sub(r"badge/Credly-\d+_active_[a-z]+-", f"badge/Credly-{CERT_COUNT}_active_certs-", updated)
if updated != readme:
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)
    print("updated README.md cert count ->", CERT_COUNT)
