#!/usr/bin/env python3
"""Convert a text string into a single SVG path 'd' string using real glyph
outlines from a TTF (variable fonts instanced to a weight). Returns the path
data plus the advance width and font units-per-em so the caller can scale.
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import copy

_cache = {}

def _load(font_path, wght):
    key = (font_path, wght)
    if key in _cache:
        return _cache[key]
    f = TTFont(font_path)
    if "fvar" in f:
        f = instantiateVariableFont(f, {"wght": wght}, inplace=False)
    _cache[key] = f
    return f

def text_path(text, font_path, wght=700, tracking=0):
    """Return (path_d, total_width, units_per_em, ascent) in font units.
    tracking is extra spacing in font units between glyphs.
    """
    f = _load(font_path, wght)
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    glyf = f["glyf"]
    hmtx = f["hmtx"]
    gset = f.getGlyphSet()
    x = 0
    pen_paths = []
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        pen = SVGPathPen(gset)
        gset[gname].draw(pen)
        d = pen.getCommands()
        if d:
            # translate this glyph by current x; SVG path is in font Y-up coords.
            pen_paths.append((d, x))
        adv = hmtx[gname][0]
        x += adv + tracking
    total_w = x - (tracking if text else 0)
    return pen_paths, total_w, upem

def _combined_bounds(text, font_path, wght, tracking):
    """True geometric bounds (xMin,yMin,xMax,yMax) of the laid-out glyphs in
    font units, accounting for each glyph's x offset."""
    f = _load(font_path, wght)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    gset = f.getGlyphSet()
    x = 0
    xmin = ymin = 1e9; xmax = ymax = -1e9
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        bp = BoundsPen(gset)
        gset[gname].draw(bp)
        if bp.bounds:
            gx0, gy0, gx1, gy1 = bp.bounds
            xmin = min(xmin, gx0 + x); xmax = max(xmax, gx1 + x)
            ymin = min(ymin, gy0); ymax = max(ymax, gy1)
        x += hmtx[gname][0] + tracking
    return xmin, ymin, xmax, ymax

def text_svg_group(text, font_path, target_h, cx, cy, fill, wght=700,
                   tracking=0, baseline_factor=0.5):
    """Build an SVG <g> string that renders `text` as vector paths, scaled so
    the glyphs' cap height == target_h, and the true ink bounding box is
    centered at (cx, cy). Font glyphs are Y-up; we flip Y and scale.
    """
    pen_paths, total_w, upem = text_path(text, font_path, wght, tracking)
    xmin, ymin, xmax, ymax = _combined_bounds(text, font_path, wght, tracking)
    ink_h = ymax - ymin
    ink_w = xmax - xmin
    # Scale so the actual ink height == target_h
    scale = target_h / ink_h
    w_scaled = ink_w * scale
    h_scaled = ink_h * scale
    # In the group we apply: translate(tx,ty) scale(s,-s). A glyph point (gx,gy)
    # maps to (tx + gx*s, ty - gy*s). We want the ink box centered at (cx,cy):
    #   x: tx + xmin*s .. tx + xmax*s  centered -> tx = cx - s*(xmin+xmax)/2
    #   y: ty - ymax*s .. ty - ymin*s  centered -> ty = cy + s*(ymin+ymax)/2
    tx = cx - scale * (xmin + xmax) / 2
    ty = cy + scale * (ymin + ymax) / 2
    inner = []
    for d, gx in pen_paths:
        inner.append(f'<path d="{d}" transform="translate({gx:.3f} 0)"/>')
    g = (f'<g fill="{fill}" transform="translate({tx:.3f} {ty:.3f}) '
         f'scale({scale:.5f} {-scale:.5f})">' + "".join(inner) + "</g>")
    return g, w_scaled, h_scaled

if __name__ == "__main__":
    g, w = text_svg_group("LLA", "/home/user/workspace/fonts/PlayfairDisplay.ttf",
                          230, 256, 256, "#FFFFFF", wght=700, tracking=8)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
           f'viewBox="0 0 512 512"><rect width="512" height="512" rx="92" '
           f'fill="#010D25"/>{g}</svg>')
    open("/home/user/workspace/site/_lla_test.svg","w").write(svg)
    print("width", w)
