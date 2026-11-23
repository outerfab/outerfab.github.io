"""Subset the brand fonts to woff2 for the site. Run with the fonttools venv:
    ~/.local/share/work-tools/venv/bin/python website/tools/subset_fonts.py

IBM Plex carries the Reserved Font Name "Plex" (OFL 1.1). A subset is a modified version, so the
family is renamed here; copyright and licence records are kept, and OFL texts ship in assets/fonts/.
"""
import pathlib, shutil
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "brand" / "fonts"
OUT = ROOT / "src" / "assets" / "fonts"; OUT.mkdir(parents=True, exist_ok=True)

# Basic Latin, Latin-1, plus the typographic and technical glyphs the copy uses:
# µ × ° · – — ‘ ’ “ ” … • → ← ↑ ↓ ≤ ≥ ≈ − ± ✓
UNICODES = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [
    0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2190, 0x2191, 0x2192, 0x2193,
    0x2212, 0x2248, 0x2264, 0x2265, 0x00B5, 0x03BC, 0x2116, 0x2713,
]
FONTS = [  # source file, new family, style, output name
    ("IBMPlexMono-SemiBold.ttf", "Outerfab Mono", "SemiBold", "outerfab-mono-600.woff2"),
    ("IBMPlexSans-Regular.ttf", "Outerfab Sans", "Regular", "outerfab-sans-400.woff2"),
    ("IBMPlexSans-Medium.ttf", "Outerfab Sans", "Medium", "outerfab-sans-500.woff2"),
]

def rename(font, family, style):
    full = f"{family} {style}"; ps = full.replace(" ", "-")
    for rec in font["name"].names:
        if rec.nameID in (1, 16): rec.string = family
        elif rec.nameID in (2, 17): rec.string = style
        elif rec.nameID == 4: rec.string = full
        elif rec.nameID == 6: rec.string = ps
        elif rec.nameID == 3: rec.string = f"{ps};subset"
    font["name"].names = [r for r in font["name"].names if r.nameID not in (7, 8, 9, 10, 11, 12)] # trademark, vendor URLs, designer

for src, family, style, out in FONTS:
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga", "calt", "tnum", "lnum", "case", "ccmp", "locl", "mark", "mkmk"]
    opts.name_IDs = ["*"]; opts.notdef_outline = True; opts.hinting = False; opts.desubroutinize = True
    font = TTFont(SRC / src)
    sub = subset.Subsetter(opts); sub.populate(unicodes=UNICODES); sub.subset(font)
    rename(font, family, style)
    font.flavor = "woff2"; font.save(OUT / out)
    print(f"{out}: {(OUT / out).stat().st_size / 1024:.1f} KB")

for lic in ("OFL-IBMPlexMono.txt",):
    shutil.copy(SRC / lic, OUT / "OFL-IBM-Plex.txt")
print("total:", round(sum(p.stat().st_size for p in OUT.glob("*.woff2")) / 1024, 1), "KB")
