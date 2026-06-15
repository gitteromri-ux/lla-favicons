#!/usr/bin/env python3
"""Extract the LLA emblem from the original logo, exact shape, transparent bg."""
from PIL import Image
import numpy as np

SRC = "/home/user/workspace/uploaded_attachments/18cbc44887e8409bb1c8410d311b7ecf/44-1.jpg"
im = Image.open(SRC).convert("RGB")
a = np.asarray(im).astype(int)

# detected tight emblem bbox
x0, y0, x1, y1 = 138, 202, 461, 528
# add small symmetric padding to keep circle from touching edges
pad = 16
x0p, y0p = x0 - pad, y0 - pad
x1p, y1p = x1 + pad, y1 + pad
crop = im.crop((x0p, y0p, x1p, y1p))

# make square (it's ~ square already); pad to exact square centered
cw, ch = crop.size
S = max(cw, ch)
sq = Image.new("RGB", (S, S), (1, 13, 37))
sq.paste(crop, ((S - cw)//2, (S - ch)//2))

# key out navy -> alpha. Navy bg approx (1,13,37). Colored strokes are mint/blue.
arr = np.asarray(sq).astype(int)
navy = np.array([1, 13, 37])
dist = np.sqrt(((arr - navy) ** 2).sum(axis=2))  # 0 at navy, larger at strokes
# alpha ramps from 0 (navy) to 255 (bright stroke)
lo, hi = 55, 135
alpha = np.clip((dist - lo) / (hi - lo), 0, 1)
alpha = (alpha * 255).astype(np.uint8)

# keep original stroke RGB (don't recolor) so gradient is preserved
rgba = np.dstack([np.asarray(sq).astype(np.uint8), alpha])
out = Image.fromarray(rgba, "RGBA")

# upscale to 1024 master with high-quality resampling
out = out.resize((1024, 1024), Image.LANCZOS)
out.save("/home/user/workspace/site/emblem_master.png")
print("saved emblem_master.png", out.size)
