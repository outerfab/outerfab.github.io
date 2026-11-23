#!/usr/bin/env python3
"""Regenerate the home page photograph in web sizes: python3 tools/make_home_photo.py

Needs Pillow with AVIF and WebP support. The build itself stays standard-library only,
so the generated files in src/assets/img/ are committed.
Source: media-src/wafer-space-run1.jpg (Photo: Tim Ansell, wafer.space Run 1, CC BY 4.0).
"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "media-src" / "wafer-space-run1.jpg"
OUT = ROOT / "src" / "assets" / "img"
WIDTHS = (480, 720, 960, 1280)
QUALITY = {"avif": 50, "webp": 68, "jpg": 72}

im = Image.open(SRC).convert("RGB")
for w in WIDTHS:
    h = round(im.height * w / im.width)
    small = im.resize((w, h), Image.LANCZOS)
    for ext, q in QUALITY.items():
        if ext == "jpg" and w != 960:
            continue  # one JPEG fallback is enough
        path = OUT / ("home-wafer-%d.%s" % (w, ext))
        kw = {"quality": q}
        if ext == "jpg":
            kw.update(optimize=True, progressive=True)
        if ext == "webp":
            kw.update(method=6)
        small.save(path, **kw)
        print("%-24s %4dx%-4d %6.1f KB" % (path.name, w, h, path.stat().st_size / 1024))
