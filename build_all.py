#!/usr/bin/env python3
"""Build 15 LLA favicon versions: emblem-only, LLA-only, lockup.
Real emblem (extracted from logo) + Playfair Display / EB Garamond embedded.
Renders hi-res PNGs from a large master so downloads are crisp."""
import os, json, base64, io, shutil
import cairosvg
from PIL import Image

ROOT = "/home/user/workspace/site"
ASSETS = os.path.join(ROOT, "docs", "assets")
B64 = json.load(open(os.path.join(ROOT, "_assets_b64.json")))

NAVY = "#010D25"
MINT = "#6CF3D2"
BLUE = "#5A96EB"

PNG_SIZES = [16, 32, 48, 64, 128, 180, 192, 256, 512]
MASTER = 1024  # render PNGs by downscaling from this master size for crispness

EMBLEM_DATA = "data:image/png;base64," + B64["emblem"]

def font_face(family, b64):
    return (f"@font-face{{font-family:'{family}';"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');"
            f"font-weight:400 900;font-style:normal;}}")

FONT_DEFS = (font_face("Playfair Display", B64["playfair"]) +
             font_face("EB Garamond", B64["ebgaramond"]))

def grad_def():
    return (f'<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{MINT}"/>'
            f'<stop offset="1" stop-color="{BLUE}"/></linearGradient>')

# ---- Treatment definitions ----
# A=Navy bg / White fg / Playfair
# B=Navy bg / Gradient fg / Playfair
# C=Transparent bg / White fg / Playfair
# D=White bg / Navy fg / Playfair
# E=Navy bg / White fg / EB Garamond
TREATMENTS = {
    "A": dict(bg=NAVY, fg="#FFFFFF", font="Playfair Display", grad=False),
    "B": dict(bg=NAVY, fg="grad",    font="Playfair Display", grad=True),
    "C": dict(bg=None,  fg="#FFFFFF", font="Playfair Display", grad=False),
    "D": dict(bg="#FFFFFF", fg=NAVY,  font="Playfair Display", grad=False),
    "E": dict(bg=NAVY, fg="#FFFFFF", font="EB Garamond",       grad=False),
}

def bg_rect(t, S, r):
    if t["bg"] is None:
        return ""
    return f'<rect x="0" y="0" width="{S}" height="{S}" rx="{r}" fill="{t["bg"]}"/>'

def fg_paint(t):
    return "url(#g)" if t["fg"] == "grad" else t["fg"]

# ---------- EMBLEM ONLY ----------
def svg_emblem(key, t):
    S = 512
    r = int(S*0.18)
    # emblem occupies a centered square; scale slightly for padding
    pad = S*0.12
    e = S - 2*pad
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
<defs><style>{FONT_DEFS}</style>{grad_def()}</defs>
{bg_rect(t,S,r)}
<image x="{pad}" y="{pad}" width="{e}" height="{e}" href="{EMBLEM_DATA}"/>
</svg>'''

# ---------- LLA ONLY ----------
def svg_lla(key, t):
    S = 512
    r = int(S*0.18)
    paint = fg_paint(t)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
<defs><style>{FONT_DEFS}</style>{grad_def()}</defs>
{bg_rect(t,S,r)}
<text x="{S/2}" y="{S/2}" font-family="{t['font']}" font-weight="700" font-size="230" fill="{paint}" text-anchor="middle" dominant-baseline="central" letter-spacing="2">LLA</text>
</svg>'''

# ---------- LOCKUP (emblem + LLA) ----------
from PIL import ImageFont
_FONT_PATHS = {
    "Playfair Display": "/home/user/workspace/fonts/PlayfairDisplay.ttf",
    "EB Garamond": "/home/user/workspace/fonts/EBGaramond.ttf",
}
def _text_width(text, family, px, tracking=0):
    f = ImageFont.truetype(_FONT_PATHS[family], int(px))
    w = f.getlength(text)
    return w + tracking * (len(text) - 1)

def svg_lockup(key, t):
    # Balanced horizontal lockup, proportions modeled on the real logo.
    H = 512
    pad = H * 0.16                 # generous outer padding (top/bottom + sides)
    em = H - 2 * pad               # emblem fits within padded height
    ex = pad
    ey = pad
    # cap height of LLA tuned so the text reads at the emblem's optical size,
    # not taller than it. Playfair cap-height ~0.70em, so font px ~ capH/0.70.
    capH = em * 0.62
    fpx = capH / 0.70
    track = 4
    paint = fg_paint(t)
    gap1 = H * 0.085               # emblem -> divider gap
    gap2 = H * 0.095               # divider -> text gap
    divx = ex + em + gap1
    txx = divx + 3 + gap2
    tw = _text_width("LLA", t["font"], fpx, track)
    W = txx + tw + pad             # right padding mirrors left
    r = int(H * 0.16)
    divcol = "#FFFFFF" if t["bg"]==NAVY else (NAVY if t["bg"]=="#FFFFFF" else "#FFFFFF")
    if t["fg"]=="grad": divcol="url(#g)"
    elif t["fg"]!="grad": divcol=t["fg"]
    divh = capH * 1.25
    divy = (H - divh) / 2
    bg = "" if t["bg"] is None else f'<rect x="0" y="0" width="{W:.1f}" height="{H}" rx="{r}" fill="{t["bg"]}"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H}" viewBox="0 0 {W:.1f} {H}">
<defs><style>{FONT_DEFS}</style>{grad_def()}</defs>
{bg}
<image x="{ex:.1f}" y="{ey:.1f}" width="{em:.1f}" height="{em:.1f}" href="{EMBLEM_DATA}"/>
<rect x="{divx:.1f}" y="{divy:.1f}" width="3" height="{divh:.1f}" fill="{divcol}" opacity="0.5"/>
<text x="{txx:.1f}" y="{H/2}" font-family="{t['font']}" font-weight="700" font-size="{fpx:.1f}" fill="{paint}" dominant-baseline="central" letter-spacing="{track}">LLA</text>
</svg>'''

BUILDERS = {"emblem": svg_emblem, "lla": svg_lla, "lockup": svg_lockup}

import re
def svg_dims(svg_str):
    w = float(re.search(r'width="([\d.]+)"', svg_str).group(1))
    h = float(re.search(r'height="([\d.]+)"', svg_str).group(1))
    return w, h

def render_png(svg_str, out_path, w, h):
    cairosvg.svg2png(bytestring=svg_str.encode(), write_to=out_path,
                     output_width=int(round(w)), output_height=int(round(h)))

def main():
    for group in ("emblem", "lla", "lockup"):
        for tk, t in TREATMENTS.items():
            name = f"{group}_{tk}"
            d = os.path.join(ASSETS, name)
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
            svg = BUILDERS[group](tk, t)
            # save SVG (with embedded fonts + emblem)
            with open(os.path.join(d, f"{name}.svg"), "w") as f:
                f.write(svg)
            vw, vh = svg_dims(svg)
            ar = vw / vh   # true aspect ratio from the SVG
            # PNG icon sizes: 's' is the height; width follows aspect ratio
            for s in PNG_SIZES:
                render_png(svg, os.path.join(d, f"{name}-{s}.png"), s*ar, s)
            # hi-res full renders
            for mult, tag in [(1,"1x"),(2,"2x"),(4,"4x")]:
                base = 512*mult
                render_png(svg, os.path.join(d, f"{name}-full-{tag}.png"), base*ar, base)
            # ICO must be square -> render emblem-style square version for lockup ICO
            ico_imgs = []
            for s in [16,32,48,64,128,256]:
                if abs(ar - 1.0) < 0.01:
                    p = os.path.join(d, f"{name}-{s}.png")
                    ico_imgs.append(Image.open(p).convert("RGBA"))
                else:
                    # paste wide render onto a square transparent canvas
                    tmp = os.path.join(d, f"_tmp-{s}.png")
                    render_png(svg, tmp, s*ar, s)
                    wide = Image.open(tmp).convert("RGBA")
                    sq = Image.new("RGBA", (max(wide.size), max(wide.size)), (0,0,0,0))
                    sq.alpha_composite(wide, (0, (sq.height-wide.height)//2))
                    sq = sq.resize((s, s), Image.LANCZOS)
                    ico_imgs.append(sq)
                    os.remove(tmp)
            ico_imgs[0].save(os.path.join(d, f"{name}.ico"),
                             sizes=[(im.width, im.height) for im in ico_imgs])
            print(f"built {name}  ({vw:.0f}x{vh:.0f}, ar={ar:.2f})")
    print("DONE")

if __name__ == "__main__":
    main()
