#!/usr/bin/env python3
"""LLA emblem as TRUE VECTOR — the ORIGINAL artwork traced to real SVG paths.
This preserves the exact original emblem (orientation, helix direction, ring
gap, node, dots) with NO redesign. Source: traced from the official logo
(emblem_paths.json), recolored only.
"""
import json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATHS = json.load(open(os.path.join(_HERE, "emblem_paths.json")))
SRC_SIZE = 2048   # the trace was produced at 2048x2048

CX, CY = 256, 256  # for compatibility with callers (512 box center)

def build_emblem_group(stroke="url(#embGrad)", node_fill=None, dot_fill=None,
                       sw=None, box=512):
    """Return an SVG <g> drawing the original-traced emblem, scaled into a
    `box`-sized square, filled with `stroke` (path fill color/gradient).
    node_fill/dot_fill/sw are accepted for signature compatibility but ignored
    because the traced artwork already contains node + dots as one shape set.
    """
    scale = box / SRC_SIZE
    inner = "".join(_PATHS)
    return (f'<g fill="{stroke}" fill-rule="nonzero" '
            f'transform="scale({scale:.6f})">{inner}</g>')
