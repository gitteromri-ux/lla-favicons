#!/usr/bin/env python3
"""Generate the LLA emblem as a TRUE VECTOR (real SVG paths, no raster).
Recreates: gradient orbit ring with gap, solid mint node + stem,
DNA double-helix (two sine strands + rungs), and accent dots.

Coordinate system: 512x512 viewBox, emblem centered.
Returns an SVG <g> fragment so it can be dropped into any treatment,
plus standalone builders.
"""
import math

# ---- Geometry constants (tuned to the original logo) ----
CX, CY = 256, 256          # emblem center
R_RING = 196               # orbit ring radius
RING_W = 9                 # ring stroke width

# Gap in the ring at top-right (degrees, 0=east, CCW positive in math;
# we use standard screen coords where +y is down, so we compute manually)
# Ring opening sits at the top-right where the node is.

def pol(cx, cy, r, deg):
    """Point on circle. deg measured clockwise from 12 o'clock (top)."""
    a = math.radians(deg - 90)  # -90 so 0deg -> top
    return (cx + r * math.cos(a), cy + r * math.sin(a))

def arc_path(cx, cy, r, start_deg, end_deg, sweep=1):
    """Build an arc path from start_deg to end_deg (clockwise from top)."""
    x0, y0 = pol(cx, cy, r, start_deg)
    x1, y1 = pol(cx, cy, r, end_deg)
    delta = (end_deg - start_deg) % 360
    large = 1 if delta > 180 else 0
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} {sweep} {x1:.2f} {y1:.2f}"

# ---------- DNA double helix ----------
# Helix parameters (shared)
HELIX_L = 270
HELIX_AMP = 34
HELIX_WAVES = 1.75
# Start/end the parametric curve OFF the crossing points so the two strand
# ends sit apart (open ends, like the original) rather than meeting in a loop.
HELIX_T0 = 0.12
HELIX_T1 = 0.90

def helix_strand(phase):
    """One sine-wave strand of the helix along the diagonal axis.
    The helix runs along a diagonal from upper-right to lower-left.
    We build it in a local (axis u, transverse v) frame then rotate.
    """
    L = HELIX_L; amp = HELIX_AMP; waves = HELIX_WAVES
    pts = []
    N = 120
    for i in range(N + 1):
        t = HELIX_T0 + (HELIX_T1 - HELIX_T0) * (i / N)
        u = -L/2 + t * L
        v = amp * math.sin(2 * math.pi * waves * t + phase)
        pts.append((u, v))
    return pts

def transform_pts(pts, angle_deg, cx, cy):
    """Rotate local (u,v) points by angle and translate to (cx,cy)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for (u, v) in pts:
        x = u * ca - v * sa + cx
        y = u * sa + v * ca + cy
        out.append((x, y))
    return out

def smooth_path(pts):
    """Catmull-Rom -> cubic bezier smooth path through pts."""
    if not pts:
        return ""
    d = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else p2
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d.append(f"C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    return " ".join(d)

def build_emblem_group(stroke="url(#embGrad)", node_fill="url(#embGrad)",
                       dot_fill="url(#embGrad)", sw=9):
    """Return SVG markup (string) drawing the emblem with given paint."""
    HELIX_ANGLE = 70   # tilt (deg from horizontal) - mostly upright, leans left
    N = 120
    # center the helix slightly left of true center (matches original)
    hcx, hcy = CX - 8, CY + 6
    # --- helix strands ---
    s1 = transform_pts(helix_strand(0.0), HELIX_ANGLE, hcx, hcy)
    s2 = transform_pts(helix_strand(math.pi), HELIX_ANGLE, hcx, hcy)
    p1 = smooth_path(s1)
    p2 = smooth_path(s2)

    # --- rungs: connect strand1[i] to strand2[i] at sampled points ---
    # Only draw rungs where the two strands are reasonably far apart (the
    # 'open ladder' look), skipping the crossing points where they meet.
    rungs = []
    for frac in [0.06,0.18,0.30,0.42,0.54,0.66,0.78,0.92]:
        i = int(frac * N)
        a1 = s1[i]; a2 = s2[i]
        dx = a2[0]-a1[0]; dy = a2[1]-a1[1]
        gap = math.hypot(dx, dy)
        if gap < 22:   # too close to a crossing -> skip (would look like a blob)
            continue
        mx = (a1[0]+a2[0])/2; my=(a1[1]+a2[1])/2
        k = 0.66
        rx1 = mx + (a1[0]-mx)*k; ry1 = my + (a1[1]-my)*k
        rx2 = mx + (a2[0]-mx)*k; ry2 = my + (a2[1]-my)*k
        rungs.append(f'<line x1="{rx1:.2f}" y1="{ry1:.2f}" x2="{rx2:.2f}" y2="{ry2:.2f}" '
                     f'stroke="{stroke}" stroke-width="{sw*0.58:.1f}" stroke-linecap="round"/>')

    # --- orbit ring with a gap at top-right (node sits in the gap) ---
    # main ring: from ~40deg clockwise around to ~25deg (gap between 25 and 40)
    ring_main = arc_path(CX, CY, R_RING, 42, 18 + 360, sweep=1)
    # small accent arc segment on the right (the short open arc in original)
    ring_accent = arc_path(CX, CY, R_RING, 26, 40, sweep=1)

    # --- node + stem ---
    node_deg = 32
    nx, ny = pol(CX, CY, R_RING, node_deg)
    node_r = 21
    # stem: a short smooth curve from node down into the very top of the helix
    # pick the topmost (smallest y) point across both strand starts
    htop = min([s1[0], s1[-1], s2[0], s2[-1]], key=lambda p: p[1])
    stem = (f'<path d="M {nx:.2f} {ny:.2f} '
            f'C {nx-10:.2f} {ny+28:.2f} {htop[0]+18:.2f} {htop[1]-24:.2f} '
            f'{htop[0]:.2f} {htop[1]:.2f}" '
            f'fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')

    # --- accent dots: 2 left, 3 right (vertical groups) ---
    dots = []
    # left pair
    for (dx, dy, rr) in [(-120, 22, 7), (-120, 54, 7)]:
        dots.append(f'<circle cx="{CX+dx}" cy="{CY+dy}" r="{rr}" fill="{dot_fill}"/>')
    # right triple (varied sizes, descending)
    for (dx, dy, rr) in [(116, -38, 7), (122, 0, 8.5), (114, 38, 6)]:
        dots.append(f'<circle cx="{CX+dx}" cy="{CY+dy}" r="{rr}" fill="{dot_fill}"/>')

    parts = [
        f'<path d="{ring_main}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>',
        f'<path d="{ring_accent}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>',
        stem,
        f'<path d="{p1}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>',
        f'<path d="{p2}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>',
        *rungs,
        *dots,
        f'<circle cx="{nx:.2f}" cy="{ny:.2f}" r="{node_r}" fill="{node_fill}"/>',
    ]
    return "\n".join(parts)

if __name__ == "__main__":
    grad = ('<linearGradient id="embGrad" x1="0.85" y1="0" x2="0.1" y2="1">'
            '<stop offset="0" stop-color="#6CF3D2"/>'
            '<stop offset="1" stop-color="#5A96EB"/></linearGradient>')
    g = build_emblem_group()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
           f'viewBox="0 0 512 512"><defs>{grad}</defs>'
           f'<rect width="512" height="512" rx="92" fill="#010D25"/>{g}</svg>')
    open("/home/user/workspace/site/_emblem_preview.svg","w").write(svg)
    print("wrote preview")
