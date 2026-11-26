#!/usr/bin/env python3
"""build_poster.py — authoring tool for the news-image-20261126 entry.

Emits poster.svg (a build artifact, never committed) for "The World in
One Day — Thursday 26 November 2026": a one-page broadsheet poster,
1024x1024, designed to the push recipe:

  * 12 front-page leads in clean white boxes, solid red number chips;
    at most 2 of the leads are finance/economy stories.
  * Region blocks below the leads, one numbered list per region.
  * A "LEFT OUT & WHY — DATE CHECK" box and a sourced footer.

Every headline is taken verbatim or near-verbatim from SOURCES.md,
which lists the outlet and URL each story was verified against.
Text is measured with PIL against the real DejaVu Sans files so the
SVG layout never overflows its boxes; the script fails loudly if the
page does not fit instead of silently clipping a story.

Run:  python3 build_poster.py     (writes poster.svg beside itself)
No network. Deterministic: same data in, same SVG out.
"""

from pathlib import Path
from xml.sax.saxutils import escape

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REGULAR = str(FONT_DIR / "DejaVuSans.ttf")
BOLD = str(FONT_DIR / "DejaVuSans-Bold.ttf")
OBLIQUE = str(FONT_DIR / "DejaVuSans-Oblique.ttf")

PAGE = 1024
MARGIN = 26
CW = PAGE - 2 * MARGIN  # 972 px of content width

PAPER = "#F8F4EC"
INK = "#1B1B1B"
NAVY = "#16283F"
RED = "#D32F2F"
RED_DARK = "#B71C1C"
GREY = "#5A5A5A"
BOX_LINE = "#CFC8B8"

_fonts = {}


def font(size, bold=False, oblique=False):
    key = (size, bold, oblique)
    if key not in _fonts:
        path = BOLD if bold else (OBLIQUE if oblique else REGULAR)
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def width(text, size, bold=False, oblique=False):
    return font(size, bold, oblique).getlength(text)


def wrap(text, size, max_w, bold=False, oblique=False):
    """Greedy word wrap using real font metrics."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if width(trial, size, bold, oblique) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- data
# Leads: (headline, outlet). Finance/economy leads are marked with a
# trailing comment; the recipe caps them at 2 of the 12.
LEADS = [
    ("Hormuz tankers hit mines, ablaze", "Reuters"),
    ("490,334 Russian dead since 2022 — leak", "BBC"),
    ("Odesa strike kills 2; Kyiv flat ablaze", "Reuters"),
    ("RSF drones kill 19 civilians in Sudan", "Reuters"),
    ("26 miners trapped in W. Java gold mine", "Kilambi"),
    ("Supercell devastates Tupancireta, Brazil", "Al Jazeera"),
    ("Pope Leo XIV laments COP31 failure", "AP"),
    ("AI staff: models too powerful to release", "Axios"),
    ("Nollywood legend Pete Edochie dies", "AllAfrica"),
    ("Ethiopia polio drive for 11.3M children", "Addis Standard"),
    ("US tariffs: China, EU + 14 more", "AP"),          # economy 1 of 2
    ("Asian stocks tumble; KOSPI -5.8%", "Reuters"),    # finance 2 of 2
]

# Regions: (name, bar colour, [(headline, outlet), ...])
REGIONS_LEFT = [
    ("NORTH AMERICA", "#1F4E79", [
        ("Abrego Garcia leaves US voluntarily for Spain", "NYT"),
        ("Sullivan concedes Alaska Senate race to Peltola", "NYT"),
        ("Giuliani awarded Medal of Freedom", "Politico"),
        ("Justice Dept. apologises over Omar search claim", "NYT"),
    ]),
    ("LATIN AMERICA & CARIBBEAN", "#2E7D32", [
        ("Car bomb hits governor's office in Meta, Colombia", "Al Jazeera"),
        ("Chile convicts 7 over 2024 wildfire that killed 138", "PaiPee"),
        ("WHO chief in Cuba urges US to lift fuel blockade", "Reuters"),
    ]),
    ("EUROPE", "#5E35B1", [
        ("Von der Leyen: Europe to join Ukraine peace talks", "Archynewsy"),
        ("Merz: Russia is 'escalating' threats to Europe", "Reuters"),
        ("EU leaders to debate Costa budget cuts Thu-Fri", "Reuters"),
    ]),
    ("GLOBAL: MARKETS, CULTURE & SPORT", "#7B1F4D", [
        ("Nasdaq futures -2% on tariff fears; Nvidia -5%", "Reuters"),
        ("Palmeiras lose 3-0 at Chapecoense", "Rio Times"),
    ]),
]

REGIONS_RIGHT = [
    ("MIDDLE EAST & NORTH AFRICA", "#7A6200", [
        ("Houthi strike on Riyadh tower injures 11", "NYT"),
        ("Israel kills Hamas security chief Abuelouf + family", "Reuters"),
        ("Iran deploys new systems to control Hormuz", "Reuters"),
        ("Iran VP: US blockade does not worry Tehran", "Reuters"),
    ]),
    ("SUB-SAHARAN AFRICA", "#8C5A12", [
        ("DRC halts all cobalt exports from month-end", "Daily Plug"),
        ("Amnesty seeks UN action over 14 deaths in Ethiopia", "Radio Generation"),
        ("S. Africa court voids Phala Phala report", "Daily Maverick"),
        ("Abiy proposes inclusive dialogue for Sudan", "Daily Plug"),
    ]),
    ("ASIA-PACIFIC", "#1565C0", [
        ("Solomons + Australia sign treaty barring foreign base", "NYT"),
        ("Japan to fire missiles at Indian ranges", "Kilambi"),
        ("Australia passes digital duty of care law", "Kilambi"),
        ("Danantara posts first profit: Rp259.6 trillion", "Kilambi"),
    ]),
]

LEFT_OUT = (
    "Held back: anything filed before 25 Nov 2026 UTC — an item is only "
    "on this page if it belongs to the 26 Nov (Asia) cycle. Just Security's "
    "Early Edition for 26 Nov was not yet out at build time, so this page "
    "anchors on its 25 Nov edition plus the wires it aggregates (Reuters, "
    "AP, NYT, BBC, others). Also held: market briefs and follow-ups that "
    "add no new fact. Full list in SOURCES.md."
)

BY_THE_NUMBERS = "BY THE NUMBERS — 36 stories · 7 regions · 12 leads · 20+ outlets · 1 news day"
SOURCES_LINE = ("Sources: Just Security Early Edition (25 Nov 2026), Reuters, AP, NYT, BBC, "
                "Al Jazeera + more — full list in SOURCES.md")

# ------------------------------------------------------------- svg kit

els = []


def rect(x, y, w, h, fill, stroke=None, sw=1.0, rx=0):
    s = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
         f'fill="{fill}"')
    if rx:
        s += f' rx="{rx}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    els.append(s + "/>")


def text(x, y, s, size, fill=INK, bold=False, oblique=False, anchor="start",
         spacing=None):
    attrs = (f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
             f'text-anchor="{anchor}"')
    if bold:
        attrs += ' font-weight="bold"'
    if oblique:
        attrs += ' font-style="italic"'
    if spacing:
        attrs += f' letter-spacing="{spacing}"'
    els.append(f"<text {attrs}>{escape(s)}</text>")


# ------------------------------------------------------------- layout

def masthead():
    text(MARGIN, 60, "THE WORLD IN ONE DAY", 44, NAVY, bold=True)
    text(MARGIN, 90, "THURSDAY 26 NOVEMBER 2026", 23, RED_DARK, bold=True,
         spacing=1)
    text(PAGE - MARGIN, 90, "GLOBAL EDITION", 13, GREY, bold=True,
         anchor="end", spacing=2)
    text(MARGIN, 111,
         "36 stories · 7 regions · 12 front-page leads · every story sourced",
         12.5, GREY)
    rect(MARGIN, 119, CW, 3.5, RED)
    rect(MARGIN, 125.5, CW, 1, INK)
    return 127


def lead_box_height(headline, w):
    """Natural height of a lead box whose headline wraps inside w."""
    pad = 12
    chip = 27
    tw = w - pad - (pad + chip + 9)
    lines = wrap(headline, 15, tw, bold=True)
    content_h = max(chip, len(lines) * 18)
    return pad + content_h + 3 + 13 + pad - 3


def lead_box(x, y, w, num, headline, outlet, box_h):
    """Draw one white lead box at a caller-chosen (row-uniform) height."""
    pad = 12
    chip = 27
    tx = x + pad + chip + 9
    tw = x + w - pad - tx
    lines = wrap(headline, 15, tw, bold=True)
    lh = 18
    rect(x, y, w, box_h, "#FFFFFF", stroke=BOX_LINE, sw=1, rx=3)
    rect(x + pad, y + pad, chip, chip, RED, rx=4)
    text(x + pad + chip / 2, y + pad + 19.5, str(num), 15, "#FFFFFF",
         bold=True, anchor="middle")
    for i, ln in enumerate(lines):
        text(tx, y + pad + 13.5 + i * lh + 2, ln, 15, INK, bold=True)
    # Outlet sits on the box's bottom edge line so a row reads as a grid.
    text(tx, y + box_h - 11, outlet.upper(), 10.5, GREY, spacing=1)


def leads(y):
    text(MARGIN, y + 16, "FRONT PAGE — 12 LEADS", 16.5, RED, bold=True)
    text(PAGE - MARGIN, y + 16, "the day's biggest stories, promoted from "
         "every region", 12, GREY, oblique=True, anchor="end")
    y += 24
    num = 0
    per_row = 4
    gap = 8
    bw = (CW - (per_row - 1) * gap) / per_row
    for row_start in range(0, len(LEADS), per_row):
        row = LEADS[row_start:row_start + per_row]
        row_h = max(lead_box_height(headline, bw) for headline, _ in row)
        for col, (headline, outlet) in enumerate(row):
            num += 1
            lead_box(MARGIN + col * (bw + gap), y, bw, num, headline,
                     outlet, row_h)
        y += row_h + gap
    return y - gap


def region_block(x, y, w, name, colour, stories, first_num):
    bar_h = 24
    rect(x, y, w, bar_h, colour)
    label = f"{name} — {len(stories)} STORIES"
    text(x + 10, y + 16.5, label, 13.5, "#FFFFFF", bold=True, spacing=0.5)
    cy = y + bar_h + 6
    num = first_num
    for headline, outlet in stories:
        line = f"{headline} — {outlet}"
        lines = wrap(line, 14, w - 34)
        num_w = width(f"{num}. ", 14, bold=True)
        for i, ln in enumerate(lines):
            if i == 0:
                text(x + 2, cy + 13, f"{num}.", 14, RED, bold=True)
                text(x + 2 + num_w, cy + 13, ln, 14, INK)
            else:
                text(x + 2 + num_w, cy + 13, ln, 14, INK)
            cy += 18
        cy += 2
        num += 1
    return cy + 4, num


def regions(y):
    col_w = (CW - 16) / 2
    left_x, right_x = MARGIN, MARGIN + col_w + 16
    ly, ry = y, y
    num = len(LEADS) + 1
    for name, colour, stories in REGIONS_LEFT:
        ly, num = region_block(left_x, ly, col_w, name, colour, stories, num)
        ly += 10
    # Right column restarts its own numbering run after the left column
    # so the two columns read top-to-bottom in poster order.
    right_first = len(LEADS) + 1 + sum(len(s) for _, _, s in REGIONS_LEFT)
    num = right_first
    for name, colour, stories in REGIONS_RIGHT:
        ry, num = region_block(right_x, ry, col_w, name, colour, stories, num)
        ry += 10
    return max(ly, ry) - 10


def left_out(y):
    pad = 12
    title = "LEFT OUT & WHY — DATE CHECK"
    lines = wrap(LEFT_OUT, 12, CW - 2 * pad)
    box_h = pad + 15 + 4 + len(lines) * 15.5 + pad - 2
    rect(MARGIN, y, CW, box_h, "#FFFFFF", stroke=RED, sw=1.2, rx=3)
    text(MARGIN + pad, y + pad + 11, title, 12.5, RED_DARK, bold=True,
         spacing=0.5)
    cy = y + pad + 15 + 4
    for ln in lines:
        cy += 15.5
        text(MARGIN + pad, cy - 4, ln, 12, INK)
    return y + box_h


def footer(y):
    rect(MARGIN, y, CW, 1, INK)
    text(MARGIN, y + 18, BY_THE_NUMBERS, 12.5, INK, bold=True)
    text(MARGIN, y + 36, SOURCES_LINE, 11.5, GREY)
    return y + 40


def main():
    rect(0, 0, PAGE, PAGE, PAPER)
    y = masthead()
    y = leads(y + 6)
    y = regions(y + 12)
    y = left_out(y + 10)
    y = footer(y + 10)
    if y > PAGE - 8:
        raise SystemExit(f"layout overflow: content ends at {y:.0f}px "
                         f"of {PAGE}")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE}" '
        f'height="{PAGE}" viewBox="0 0 {PAGE} {PAGE}" '
        f'font-family="DejaVu Sans, sans-serif">\n'
        + "\n".join(els)
        + "\n</svg>\n"
    )
    out = HERE / "poster.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"poster.svg written; content ends at {y:.0f}px")


if __name__ == "__main__":
    main()
