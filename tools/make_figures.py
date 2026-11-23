"""Generate the hero figure (a bonded die, top view) as a one-colour datasheet drawing."""
import pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "src" / "partials" / "fig-hero.svg"
W, H = 600, 400; cx, cy, D = 300, 200, 120
x0, y0 = cx - D / 2, cy - D / 2
N = 8
def spread(a, b, i): return a + (b - a) * i / (N - 1)
body = [f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="8" fill="#0c0c0c"/>',
        '<rect x="40" y="34" width="520" height="332" rx="6" fill="none" stroke="#ffffff" stroke-opacity=".28"/>']
wires, fingers, pads = [], [], []
for i in range(N):
    px = spread(x0 + 14, x0 + D - 14, i); fx = spread(cx - 108, cx + 108, i)      # top and bottom
    wires += [f'M{px:.1f} {y0+8:.1f}L{fx:.1f} 88', f'M{px:.1f} {y0+D-8:.1f}L{fx:.1f} 312']
    fingers += [f'<rect x="{fx-7:.1f}" y="76" width="14" height="12" fill="#8A94A0"/>', f'<rect x="{fx-7:.1f}" y="312" width="14" height="12" fill="#8A94A0"/>']
    pads += [f'<rect x="{px-3:.1f}" y="{y0+5:.1f}" width="6" height="6" fill="#111"/>', f'<rect x="{px-3:.1f}" y="{y0+D-11:.1f}" width="6" height="6" fill="#111"/>']
    py = spread(y0 + 14, y0 + D - 14, i); fy = spread(cy - 84, cy + 84, i)          # left and right
    wires += [f'M{x0+8:.1f} {py:.1f}L118 {fy:.1f}', f'M{x0+D-8:.1f} {py:.1f}L482 {fy:.1f}']
    fingers += [f'<rect x="106" y="{fy-7:.1f}" width="12" height="14" fill="#8A94A0"/>', f'<rect x="482" y="{fy-7:.1f}" width="12" height="14" fill="#8A94A0"/>']
    pads += [f'<rect x="{x0+5:.1f}" y="{py-3:.1f}" width="6" height="6" fill="#111"/>', f'<rect x="{x0+D-11:.1f}" y="{py-3:.1f}" width="6" height="6" fill="#111"/>']
body += fingers
body.append(f'<path d="{"".join(wires)}" fill="none" stroke="#ffffff" stroke-opacity=".85" stroke-width="1.25"/>')
body.append(f'<rect x="{x0}" y="{y0}" width="{D}" height="{D}" fill="#F26A1B"/>')
body += pads
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
       f'aria-label="Top view of a bare die on a board, wire-bonded from each die pad to a board finger">' + "".join(body) + "</svg>\n")
OUT.write_text(svg); print(OUT.name, len(svg), "bytes")


# ---------------------------------------------------------------------------------------------
# Article and service figures. Dark ones sit on the dark pages; light ones sit in white panels on
# the light article pages. One colour plus the orange die, mono labels, "Fig. n" captions in HTML.
PART = pathlib.Path(__file__).resolve().parent.parent / "src" / "partials"
FONT = 'font-family="Outerfab Mono, ui-monospace, Menlo, monospace" font-weight="600"'


def T(x, y, s, fill, size=11, anchor="start", extra=""):
    size = size + 2 if size <= 12 else size
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'


def svg(w, h, body, label, bg=None, vb=None):
    bgr = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="8" fill="{bg}"/>' if bg else ""
    (PART / f"fig-{label[0]}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb or f"0 0 {w} {h}"}" role="img" aria-label="{label[1]}">{bgr}{body}</svg>\n')
    print(f"fig-{label[0]}.svg")


# 1. Cross-section of a chip-on-board (dark)
INK, STEEL, ORG, WHT = "#111111", "#8A94A0", "#F26A1B", "#ffffff"
b = []
b.append(f'<rect x="40" y="206" width="520" height="30" fill="#1c1c1c" stroke="{WHT}" stroke-opacity=".3"/>')
b.append(f'<rect x="104" y="200" width="28" height="6" fill="{STEEL}"/><rect x="468" y="200" width="28" height="6" fill="{STEEL}"/>')
b.append(f'<rect x="236" y="200" width="128" height="6" fill="{STEEL}"/>')
b.append(f'<rect x="240" y="168" width="120" height="32" fill="{ORG}"/>')
b.append(f'<rect x="246" y="164" width="10" height="4" fill="{WHT}"/><rect x="344" y="164" width="10" height="4" fill="{WHT}"/>')
b.append(f'<path d="M251 164C236 118 150 116 118 200M349 164C364 118 450 116 482 200" fill="none" stroke="{WHT}" stroke-width="1.6"/>')
b.append(f'<path d="M84 200C84 44 516 44 516 200" fill="{WHT}" fill-opacity=".06" stroke="{WHT}" stroke-opacity=".5" stroke-dasharray="5 4"/>')
for x1, y1, x2, y2, txt, anc in ((300, 150, 300, 118, "die", "middle"), (300, 218, 300, 268, "die attach", "middle")):
    pass
b.append(T(300, 189, "die", INK, 12, "middle"))
b.append(T(300, 262, "die attach", STEEL, 11, "middle") + f'<path d="M300 244V208" stroke="{STEEL}" stroke-width="1"/>')
b.append(T(118, 262, "bond pad", STEEL, 11, "middle") + f'<path d="M118 244V208" stroke="{STEEL}" stroke-width="1"/>')
b.append(T(482, 262, "bond pad", STEEL, 11, "middle") + f'<path d="M482 244V208" stroke="{STEEL}" stroke-width="1"/>')
b.append(T(200, 78, "bond wire", WHT, 11, "middle") + f'<path d="M200 84V112" stroke="{WHT}" stroke-opacity=".6"/>')
b.append(T(430, 78, "hard epoxy glob-top", WHT, 11, "middle") + f'<path d="M470 84L494 104" stroke="{WHT}" stroke-opacity=".6"/>')
b.append(T(52, 225, "board", STEEL, 11))
svg(600, 290, "".join(b), ("section", "Side section of a chip-on-board: die on a die attach pad, wires to bond pads, epoxy glob-top over both"), "#0c0c0c")

# 2. Wire rules, top view (light)
K = "#111111"; SD = "#5c6570"
b = []
b.append(f'<rect x="40" y="60" width="150" height="240" fill="{ORG}"/>')
for y in (110, 170, 250, 280):
    b.append(f'<rect x="182" y="{y-4}" width="8" height="8" fill="{K}"/>')
b.append(f'<rect x="400" y="44" width="16" height="12" fill="{SD}"/><rect x="400" y="164" width="16" height="12" fill="{SD}"/>')
b.append(f'<path d="M190 110L400 50" fill="none" stroke="{K}" stroke-width="1.6"/>')
b.append(f'<path d="M190 110H360" stroke="{SD}" stroke-dasharray="4 4"/>')
b.append(f'<path d="M190 110L250 50M190 110L250 170" stroke="{SD}" stroke-dasharray="2 4"/>')
b.append(f'<path d="M232 110A42 42 0 0 0 220 80" fill="none" stroke="{K}"/>')
b.append(T(240, 104, "&#8804; 45&#176;", K, 11))
b.append(T(366, 114, "straight out", SD, 10))
b.append(f'<path d="M190 170H400" stroke="{K}" stroke-width="1.6"/>')
b.append(T(330, 200, "length: 1 mm minimum, under 3 mm", K, 11, "middle"))
b.append(f'<rect x="400" y="244" width="16" height="12" fill="{SD}"/><rect x="400" y="274" width="16" height="12" fill="{SD}"/>')
b.append(f'<path d="M190 250L400 280M190 280L400 250" fill="none" stroke="{SD}" stroke-width="1.6" stroke-dasharray="6 4"/>')
b.append(T(330, 316, "no crossing wires", SD, 11, "middle"))
b.append(T(115, 48, "die", K, 12, "middle"))
b.append(T(430, 34, "PCB bond pads", SD, 11, "start"))
svg(640, 330, "".join(b), ("wire-rules", "Top view of the wire rules: angle up to 45 degrees from straight out, length from 1 to under 3 millimetres, no crossing wires"))

# 3. Clearance zones, side view (light)
b = []
S = 40  # px per mm
x0 = 130
b.append(f'<rect x="{x0}" y="60" width="{2*S}" height="140" fill="{ORG}" fill-opacity=".14" stroke="{ORG}" stroke-dasharray="4 4"/>')
b.append(f'<rect x="{x0+2*S}" y="60" width="{3*S}" height="140" fill="{SD}" fill-opacity=".1" stroke="{SD}" stroke-dasharray="4 4"/>')
b.append(f'<rect x="20" y="200" width="610" height="8" fill="{K}"/>')
b.append(f'<rect x="20" y="168" width="92" height="32" fill="{ORG}"/>')
b.append(f'<rect x="{x0-10}" y="196" width="20" height="4" fill="{SD}"/>')
b.append(f'<path d="M112 168C112 130 {x0} 130 {x0} 196" fill="none" stroke="{K}" stroke-width="1.4"/>')
b.append(f'<rect x="{x0+2*S+30}" y="{200-S}" width="36" height="{S}" fill="{K}"/>')
b.append(f'<rect x="{x0+5*S+60}" y="{200-70}" width="80" height="70" fill="{K}"/>')
b.append(f'<path d="M{x0} 196L{x0+150} 46" stroke="{SD}" stroke-dasharray="2 4"/>')
b.append(T(x0+160, 40, "distance from the pads &#8805; height", SD, 10, "start"))
b.append(T(x0+S, 84, "zone 1", ORG, 11, "middle") + T(x0+S, 102, "nothing", K, 10, "middle"))
b.append(T(x0+3.5*S, 84, "zone 2", SD, 11, "middle") + T(x0+3.5*S, 102, "&#8804; 1 mm tall", K, 10, "middle"))
b.append(T(x0+5*S+100, 84, "beyond 5 mm", K, 11, "middle") + T(x0+5*S+100, 102, "tall parts, kept back", K, 10, "middle"))
for x, t in ((x0, "0"), (x0+2*S, "2 mm"), (x0+5*S, "5 mm")):
    b.append(f'<path d="M{x} 210V220" stroke="{K}"/>' + T(x, 240, t, K, 11, "middle"))
b.append(T(x0+2.5*S, 268, "measured outward from the outermost bond pad", SD, 10, "middle"))
b.append(T(66, 160, "die", K, 11, "middle"))
svg(640, 280, "".join(b), ("zones", "Side view of the clearance zones around the bond pads: nothing within 2 millimetres, parts up to 1 millimetre tall from 2 to 5 millimetres, taller parts beyond"), vb="0 20 640 260")

# 4. Gold panel (light): working edges on the long sides
b = []
sc = 2.4; pw, ph = 200 * sc, 80 * sc; ox, oy = 40, 34
b.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" fill="#fff" stroke="{K}" stroke-width="1.4"/>')
we = 12
b.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{we}" fill="{SD}" fill-opacity=".25"/><rect x="{ox}" y="{oy+ph-we}" width="{pw}" height="{we}" fill="{SD}" fill-opacity=".25"/>')
cols = 8
inner_x0 = ox + 14; inner_w = pw - 28; cw = inner_w / cols
for c in range(cols):
    x = inner_x0 + c * cw + 4
    for r in range(8):
        y = oy + we + 5 + r * ((ph - 2 * we - 10) / 8)
        b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw-8:.1f}" height="{(ph-2*we-10)/8-3:.1f}" fill="none" stroke="{K}" stroke-opacity=".55"/>')
        b.append(f'<rect x="{x+(cw-8)/2-3:.1f}" y="{y+ (((ph-2*we-10)/8-3)/2)-3:.1f}" width="6" height="6" fill="{ORG}"/>')
for i in range(1, 20):
    x = ox + i * pw / 20
    b.append(f'<circle cx="{x:.1f}" cy="{oy+we/2}" r="2" fill="#fff" stroke="{K}"/>' if i % 3 else f'<path d="M{x-3:.1f} {oy+we/2}h6M{x:.1f} {oy+we/2-3}v6" stroke="{K}"/>')
    b.append(f'<circle cx="{x:.1f}" cy="{oy+ph-we/2}" r="2" fill="#fff" stroke="{K}"/>' if i % 3 else f'<path d="M{x-3:.1f} {oy+ph-we/2}h6M{x:.1f} {oy+ph-we/2-3}v6" stroke="{K}"/>')
b.append(T(ox, oy+ph+22, "working edges and board positions are schematic", SD, 10))
svg(640, 250, "".join(b), ("panel-gold", "Schematic gold-wire panel layout with working edges and columns of boards; dimensions depend on the selected process"))

# 5. Aluminium panel (light): working edges on the two short ends
b = []
sc = 5.0; pw, ph = 100 * sc, 45 * sc; ox, oy = 70, 40
b.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" fill="#fff" stroke="{K}" stroke-width="1.4"/>')
we = 18
b.append(f'<rect x="{ox}" y="{oy}" width="{we}" height="{ph}" fill="{SD}" fill-opacity=".25"/><rect x="{ox+pw-we}" y="{oy}" width="{we}" height="{ph}" fill="{SD}" fill-opacity=".25"/>')
cw = (pw - 2 * we - 16) / 6; rh = (ph - 16) / 2
for c in range(6):
    for r in range(2):
        x = ox + we + 8 + c * cw; y = oy + 8 + r * rh
        b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw-4:.1f}" height="{rh-4:.1f}" fill="none" stroke="{K}" stroke-opacity=".55"/>')
        b.append(f'<rect x="{x+(cw-4)/2-4:.1f}" y="{y+(rh-4)/2-4:.1f}" width="8" height="8" fill="{ORG}"/>')
for yy in (oy + 30, oy + ph - 30):
    b.append(f'<circle cx="{ox+we/2}" cy="{yy}" r="3" fill="#fff" stroke="{K}"/><circle cx="{ox+pw-we/2}" cy="{yy}" r="3" fill="#fff" stroke="{K}"/>')
b.append(T(ox, oy+ph+22, "working edges and board positions are schematic", SD, 10))
svg(640, 200, "".join(b), ("panel-alu", "Schematic aluminium-wire panel layout with working edges and board positions; dimensions depend on the selected process"))

# 6. Three faults (light)
b = []
def pair(x, title, kind):
    out = [T(x + 90, 24, title, K, 12, "middle")]
    out.append(f'<rect x="{x}" y="60" width="26" height="26" fill="{ORG}"/><rect x="{x+150}" y="66" width="16" height="14" fill="{SD}"/>')
    if kind == "open":
        out.append(f'<path d="M{x+26} 73L{x+70} 73M{x+108} 73L{x+150} 73" stroke="{K}" stroke-width="1.6"/>' + T(x+89, 58, "&#215;", K, 16, "middle"))
    elif kind == "gnd":
        out.append(f'<path d="M{x+26} 73H{x+150}" stroke="{K}" stroke-width="1.6"/><path d="M{x+88} 73V118" stroke="{K}" stroke-width="1.6" stroke-dasharray="4 3"/>')
        out.append(f'<path d="M{x+20} 118H{x+166}" stroke="{K}" stroke-width="3"/>' + T(x+90, 138, "ground", SD, 10, "middle"))
    else:
        out.append(f'<rect x="{x}" y="100" width="26" height="26" fill="{ORG}"/><rect x="{x+150}" y="106" width="16" height="14" fill="{SD}"/>')
        out.append(f'<path d="M{x+26} 73H{x+150}M{x+26} 113H{x+150}" stroke="{K}" stroke-width="1.6"/><path d="M{x+88} 73V113" stroke="{K}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    return "".join(out)
b.append(pair(20, "open", "open") + pair(230, "short to ground", "gnd") + pair(440, "short to neighbour", "nb"))
b.append(T(110, 172, "the wire does not connect", SD, 10, "middle") + T(320, 172, "the wire touches ground", SD, 10, "middle") + T(530, 172, "two wires touch", SD, 10, "middle"))
svg(640, 190, "".join(b), ("faults", "The three faults we test for on every bond: open, short to ground, short to neighbour"))
