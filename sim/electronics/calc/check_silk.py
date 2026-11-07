#!/usr/bin/env python3
"""T-073 / C2-010: MEASUREMENT (design file) of the gap between board-level silkscreen texts (F.SilkS) and pads.
T-076: also the visible footprint reference designators on F.SilkS (R16 / SW1 overlapped before T-076), and every
pair of silkscreen texts (bounding boxes must not overlap: gap >= 0, criterion ASSUMPTION, legibility only).

Runs with the KiCad Python (pcbnew). Each text is taken as its bounding box (conservative: the glyph strokes lie
inside it); each pad as its KiCad polygon (maxError 1 um). The gap is edge to edge, 0 if they overlap.
Criterion (ASSUMPTION, home etch / hand transfer of the optional silkscreen): >= 0.2 mm, so no label touches a
pad that will be soldered. Prints every text, the worst one and PASS / FAIL.
"""
import os
import sys

import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
MIN_GAP = 0.2
TOMM = 1e-6


def seg_d(p, a, b):
    ab = (b[0] - a[0], b[1] - a[1])
    L = ab[0] ** 2 + ab[1] ** 2
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / L))
    return ((p[0] - a[0] - t * ab[0]) ** 2 + (p[1] - a[1] - t * ab[1]) ** 2) ** 0.5


def rect_poly_gap(r, poly):
    x0, y0, x1, y1 = r
    if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in poly):
        return 0.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    inside = False                                   # rectangle centre inside the pad polygon (ray casting)
    for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]):
        if (ya > cy) != (yb > cy) and cx < xa + (cy - ya) * (xb - xa) / (yb - ya):
            inside = not inside
    if inside:
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    edges = list(zip(corners, corners[1:] + corners[:1]))
    best = min(seg_d(c, a, b) for c in corners for a, b in zip(poly, poly[1:] + poly[:1]))
    best = min(best, min(seg_d(p, a, b) for p in poly for a, b in edges))
    return best


def main():
    board = pcbnew.LoadBoard(PCB)
    o = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = o.x * TOMM, o.y * TOMM
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, pcbnew.B_Cu, 0, 1000, pcbnew.ERROR_INSIDE)
            for k in range(ps.OutlineCount()):
                ol = ps.Outline(k)
                pads.append(("%s pad %s" % (fp.GetReference(), p.GetNumber()),
                             [(ol.CPoint(i).x * TOMM - ox, ol.CPoint(i).y * TOMM - oy) for i in range(ol.PointCount())]))
    print("# check_silk.py  MEASUREMENT on %s (KiCad %s); criterion >= %.1f mm (ASSUMPTION)"
          % (os.path.relpath(PCB, ROOT), pcbnew.Version(), MIN_GAP))
    worst = (float("inf"), "")
    n = 0
    texts = [d for d in board.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.F_SilkS]
    texts += [fp.Reference() for fp in board.GetFootprints()
              if fp.Reference().IsVisible() and fp.Reference().GetLayer() == pcbnew.F_SilkS]   # T-076
    boxes = []
    for d in texts:
        bb = d.GetBoundingBox()
        r = (bb.GetLeft() * TOMM - ox, bb.GetTop() * TOMM - oy, bb.GetRight() * TOMM - ox, bb.GetBottom() * TOMM - oy)
        g, name = min(((rect_poly_gap(r, poly), name) for name, poly in pads), key=lambda t: (round(t[0], 4), t[1]))
        n += 1
        print("  %-55r size %.2f  bbox (%.2f,%.2f)-(%.2f,%.2f)  nearest %-10s %5.2f mm  %s"
              % (d.GetText(), d.GetTextHeight() * TOMM, *r, name, g, "PASS" if g >= MIN_GAP else "FAIL"))
        if g < worst[0]:
            worst = (g, "%r <-> %s" % (d.GetText(), name))
        boxes.append((d.GetText(), r))
    # T-076: text-to-text overlap (bounding boxes)
    tt = (float("inf"), "")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (na, a), (nb, b) = boxes[i], boxes[j]
            dx = max(a[0] - b[2], b[0] - a[2], 0.0)
            dy = max(a[1] - b[3], b[1] - a[3], 0.0)
            gap = (dx * dx + dy * dy) ** 0.5 if (dx > 0 or dy > 0) else -min(a[2] - b[0], b[2] - a[0], a[3] - b[1], b[3] - a[1])
            if gap < tt[0]:
                tt = (gap, "%r <-> %r" % (na, nb))
    print("%s worst silkscreen text-to-text gap %.2f mm (%s; negative = overlap), criterion >= 0"
          % ("PASS" if tt[0] >= 0 else "FAIL", tt[0], tt[1]))
    print("%s worst silkscreen-text to pad gap %.2f mm (%s), %d texts" %
          ("PASS" if worst[0] >= MIN_GAP else "FAIL", worst[0], worst[1], n))
    return 0 if worst[0] >= MIN_GAP and tt[0] >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
