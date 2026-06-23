#!/usr/bin/env python3
"""Build 15 LLA favicon versions as TRUE VECTORS (real SVG paths — no embedded
raster). Styles: emblem-only, LLA-monogram-only, lockup (emblem + LLA).
Treatments A-E. Renders crisp PNG + ICO from the vector master for legacy use.
"""
import os, math, shutil, re
import cairosvg
from PIL import Image
from emblem_vector import build_emblem_group, CX, CY
from text_to_path import text_svg_group

ROOT = "/home/user/workspace/site"
ASSETS = os.path.join(ROOT, "docs", "assets")
SVG_DIR = os.path.join(ROOT, "lla_svgs")
PLAYFAIR = "/home/user/workspace/fonts/PlayfairDisplay.ttf"
GARAMOND = "/home/user/workspace/fonts/EBGaramond.ttf"

NAVY = "#010D25"
MINT = "#6CF3D2"
BLUE = "#5A96EB"
WHITE = "#FFFFFF"

PNG_SIZES = [16, 32, 48, 64, 128, 180, 192, 256, 512]

# Treatment table:
# bg, fg paint, font for monogram, font path, weight
TREATMENTS = {
    "A": dict(name="Navy / White",     bg=NAVY,  fg=WHITE,      grad=False, font=PLAYFAIR, wght=700),
    "B": dict(name="Navy / Gradient",  bg=NAVY,  fg="grad",     grad=True,  font=PLAYFAIR, wght=700),
    "C": dict(name="Transparent",      bg=None,  fg=WHITE,      grad=False, font=PLAYFAIR, wght=700),
    "D": dict(name="White / Navy",     bg=WHITE, fg=NAVY,       grad=False, font=PLAYFAIR, wght=700),
    "E": dict(name="Navy / Garamond",  bg=NAVY,  fg=WHITE,      grad=False, font=GARAMOND, wght=600),
}

def grad_def(x1=0.85, y1=0.0, x2=0.1, y2=1.0):
    return (f'<linearGradient id="embGrad" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{MINT}"/>'
            f'<stop offset="1" stop-color="{BLUE}"/></linearGradient>')

def fg_paint(t):
    return "url(#embGrad)" if t["fg"] == "grad" else t["fg"]

def bg_rect(t, W, H, r):
    if t["bg"] is None:
        return ""
    return f'<rect x="0" y="0" width="{W:.2f}" height="{H:.2f}" rx="{r:.2f}" fill="{t["bg"]}"/>'

def svg_open(W, H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}" height="{H:.2f}" '
            f'viewBox="0 0 {W:.2f} {H:.2f}">')

# ---------- EMBLEM ONLY ----------
def svg_emblem(t):
    S = 512; r = S * 0.18
    paint = fg_paint(t)
    g = build_emblem_group(stroke=paint, node_fill=paint, dot_fill=paint, sw=9)
    return (f'{svg_open(S,S)}<defs>{grad_def()}</defs>'
            f'{bg_rect(t,S,S,r)}{g}</svg>')

# ---------- LLA MONOGRAM ONLY ----------
def svg_lla(t):
    S = 512; r = S * 0.18
    paint = fg_paint(t)
    target_h = 168 if t["font"] == PLAYFAIR else 176
    track = 12 if t["font"] == PLAYFAIR else 30
    g, w, h = text_svg_group("LLA", t["font"], target_h, S/2, S/2, paint,
                             wght=t["wght"], tracking=track)
    return (f'{svg_open(S,S)}<defs>{grad_def()}</defs>'
            f'{bg_rect(t,S,S,r)}{g}</svg>')

# ---------- LOCKUP (emblem + divider + LLA) ----------
def svg_lockup(t):
    H = 512
    pad = H * 0.14
    em = H - 2 * pad           # emblem square fits in padded height
    # emblem is drawn in its own 512 coord space; scale + translate it
    es = em / 512.0
    ex = pad
    ey = (H - em) / 2
    paint = fg_paint(t)
    emblem_g = build_emblem_group(stroke=paint, node_fill=paint, dot_fill=paint, sw=9)
    emblem_block = (f'<g transform="translate({ex:.2f} {ey:.2f}) scale({es:.5f})">'
                    f'{emblem_g}</g>')
    # divider
    gap1 = H * 0.055
    divx = ex + em + gap1
    cap_h = em * 0.46
    divh = cap_h * 1.35
    divy = (H - divh) / 2
    divcol = paint if t["fg"] != "grad" else "url(#embGrad)"
    if t["bg"] == NAVY and t["fg"] == WHITE: divcol = WHITE
    divider = (f'<rect x="{divx:.2f}" y="{divy:.2f}" width="3.2" height="{divh:.2f}" '
               f'rx="1.6" fill="{divcol}" opacity="0.55"/>')
    # LLA text
    gap2 = H * 0.06
    track = 12 if t["font"] == PLAYFAIR else 30
    # measure first to know width, placing text center after divider+gap
    tmp_g, tw, th = text_svg_group("LLA", t["font"], cap_h, 0, 0, paint,
                                   wght=t["wght"], tracking=track)
    txc = divx + 3.2 + gap2 + tw / 2
    g, tw, th = text_svg_group("LLA", t["font"], cap_h, txc, H/2, paint,
                               wght=t["wght"], tracking=track)
    W = txc + tw / 2 + pad
    r = H * 0.16
    return (f'{svg_open(W,H)}<defs>{grad_def()}</defs>'
            f'{bg_rect(t,W,H,r)}{emblem_block}{divider}{g}</svg>')

BUILDERS = {"emblem": svg_emblem, "lla": svg_lla, "lockup": svg_lockup}

def svg_dims(svg_str):
    w = float(re.search(r'width="([\d.]+)"', svg_str).group(1))
    h = float(re.search(r'height="([\d.]+)"', svg_str).group(1))
    return w, h

def render_png(svg_str, out_path, w, h):
    cairosvg.svg2png(bytestring=svg_str.encode(), write_to=out_path,
                     output_width=int(round(w)), output_height=int(round(h)))

# Also write the 5 brand SVGs into lla_svgs/ (lockup style, brand-named)
LLA_SVGS_MAP = {
    "A": "A_navy_white", "B": "B_navy_gradient", "C": "C_transparent",
    "D": "D_white_navy", "E": "E_navy_garamond",
}

def main():
    for d in (ASSETS, SVG_DIR):
        os.makedirs(d, exist_ok=True)
    for group in ("emblem", "lla", "lockup"):
        for tk, t in TREATMENTS.items():
            name = f"{group}_{tk}"
            d = os.path.join(ASSETS, name)
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
            svg = BUILDERS[group](t)
            with open(os.path.join(d, f"{name}.svg"), "w") as f:
                f.write(svg)
            vw, vh = svg_dims(svg)
            ar = vw / vh
            for s in PNG_SIZES:
                render_png(svg, os.path.join(d, f"{name}-{s}.png"), s*ar, s)
            for mult, tag in [(1, "1x"), (2, "2x"), (4, "4x")]:
                base = 512*mult
                render_png(svg, os.path.join(d, f"{name}-full-{tag}.png"), base*ar, base)
            # ICO (square) from rendered sizes
            ico_imgs = []
            for s in [16, 32, 48, 64, 128, 256]:
                if abs(ar - 1.0) < 0.01:
                    ico_imgs.append(Image.open(os.path.join(d, f"{name}-{s}.png")).convert("RGBA"))
                else:
                    tmp = os.path.join(d, f"_tmp-{s}.png")
                    render_png(svg, tmp, s*ar, s)
                    wide = Image.open(tmp).convert("RGBA")
                    sq = Image.new("RGBA", (max(wide.size), max(wide.size)), (0, 0, 0, 0))
                    sq.alpha_composite(wide, (0, (sq.height-wide.height)//2))
                    sq = sq.resize((s, s), Image.LANCZOS)
                    ico_imgs.append(sq)
                    os.remove(tmp)
            ico_imgs[0].save(os.path.join(d, f"{name}.ico"),
                             sizes=[(im.width, im.height) for im in ico_imgs])
            print(f"built {name}  ({vw:.0f}x{vh:.0f}, ar={ar:.2f})")
    # brand-named lockup SVGs + emblem-only SVGs in lla_svgs/
    for tk, t in TREATMENTS.items():
        base = LLA_SVGS_MAP[tk]
        with open(os.path.join(SVG_DIR, f"{base}.svg"), "w") as f:
            f.write(svg_lockup(t))
        with open(os.path.join(SVG_DIR, f"{base}_emblem.svg"), "w") as f:
            f.write(svg_emblem(t))
    print("DONE")

if __name__ == "__main__":
    main()
