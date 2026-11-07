#!/usr/bin/env python3
"""T-060 / CR-002: MEASUREMENT (on the design file) of the copper gaps that an ESD strike on an electrode could arc
across, compared with the CALCULATION rule of calc_flashover.py.

Runs with the KiCad Python (pcbnew):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      sim/electronics/calc/check_gap.py > sim/electronics/calc/check_gap.out

What is measured on hardware/frutamidi.kicad_pcb (B.Cu copper: pads and tracks; edge-to-edge distance):
  (a) ELEx <-> Ex, same channel x (copper around the series resistor);
  (b) Ex <-> every copper item of another net that leads to the MPR121 or the Pico (ELEy of any channel, S1..S7,
      SDA/SCL, 3V3, button, pot ...), i.e. every net except E0..E11 and GND;
  (c) reported only: Ex <-> Ey (an arc between two electrodes still passes a series resistor) and Ex <-> GND
      (an arc to GND bypasses no IC pin; it diverts the discharge to ground).
Lead geometry of the resistors (not copper) is derived from the footprint pitch and the datasheet lead diameter.
Pads are converted to polygons by KiCad (maxError 1 um); tracks are capsules. Distances in mm.
"""
import math
import os
import re
import sys

import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")   # optional: other board file
RULE_4KV, RULE_8KV = 3.5, 7.5          # mm, from calc_flashover.out (CALCULATION)
LEAD_D = 0.8                           # mm, MBE/SMA 0414 lead (SOURCE EE-S17)
TOMM = 1e-6


def seg_seg(a, b, c, d):
    """distance between segments ab and cd (points as (x, y))."""
    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1]

    def p_seg(p, a, b):
        ab = (b[0] - a[0], b[1] - a[1])
        L = dot(ab, ab)
        t = 0.0 if L == 0 else max(0.0, min(1.0, dot((p[0] - a[0], p[1] - a[1]), ab) / L))
        q = (a[0] + t * ab[0], a[1] + t * ab[1])
        return math.hypot(p[0] - q[0], p[1] - q[1])

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(p_seg(a, c, d), p_seg(b, c, d), p_seg(c, a, b), p_seg(d, a, b))


class Item:
    def __init__(self, net, desc, segs, r):
        self.net, self.desc, self.segs, self.r = net, desc, segs, r   # segs: list of segments; r: inflation


def items(board):
    out = []
    for t in board.GetTracks():
        if t.GetLayer() != pcbnew.B_Cu:
            continue
        a, b = t.GetStart(), t.GetEnd()
        out.append(Item(t.GetNetname(), "track (%.2f,%.2f)-(%.2f,%.2f)" % (a.x * TOMM, a.y * TOMM, b.x * TOMM, b.y * TOMM),
                        [((a.x * TOMM, a.y * TOMM), (b.x * TOMM, b.y * TOMM))], t.GetWidth() * TOMM / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(pcbnew.B_Cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue                                   # mounting holes carry no copper
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, pcbnew.B_Cu, 0, 1000, pcbnew.ERROR_INSIDE)
            segs = []
            for k in range(ps.OutlineCount()):
                ol = ps.Outline(k)
                pts = [(ol.CPoint(i).x * TOMM, ol.CPoint(i).y * TOMM) for i in range(ol.PointCount())]
                segs += list(zip(pts, pts[1:] + pts[:1]))
            out.append(Item(p.GetNetname(), "%s pad %s" % (fp.GetReference(), p.GetNumber()), segs, 0.0))
    return out


def dist(i, j):
    best = float("inf")
    for a, b in i.segs:
        for c, d in j.segs:
            best = min(best, seg_seg(a, b, c, d))
    return max(0.0, best - i.r - j.r)


def chan(net):
    m = re.fullmatch(r"/(ELE|E)(\d+)", net)
    return (m.group(1), int(m.group(2))) if m else (None, None)


def main():
    board = pcbnew.LoadBoard(PCB)
    its = items(board)
    origin = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = origin.x * TOMM, origin.y * TOMM
    e_items = [i for i in its if chan(i.net)[0] == "E"]
    others = [i for i in its if chan(i.net)[0] != "E"]
    print("# check_gap.py  MEASUREMENT on the design file %s (KiCad %s)" % (os.path.relpath(PCB, ROOT), pcbnew.Version()))
    print("# rule (calc_flashover.out): 4 kV %.1f mm, 8 kV %.1f mm; coordinates relative to the board corner" % (RULE_4KV, RULE_8KV))
    worst = {"a": (float("inf"), None), "b": (float("inf"), None), "EE": (float("inf"), None), "GND": (float("inf"), None)}
    per_ch = {}
    for e in e_items:
        _, ch = chan(e.net)
        for o in others:
            kind, och = chan(o.net)
            if o.net == "GND":
                key = "GND"
            elif kind == "ELE" and och == ch:
                key = "a"
            else:
                key = "b"
            d = dist(e, o)
            if d < worst[key][0]:
                worst[key] = (d, "%s [%s] <-> %s [%s]" % (e.desc, e.net, o.desc, o.net))
            if key == "a":
                per_ch[ch] = min(per_ch.get(ch, float("inf")), d)
        for o in e_items:
            if o.net != e.net:
                d = dist(e, o)
                if d < worst["EE"][0]:
                    worst["EE"] = (d, "%s [%s] <-> %s [%s]" % (e.desc, e.net, o.desc, o.net))
    for ch in sorted(per_ch):
        print("  channel E%-2d  ELE%-2d <-> E%-2d copper gap %6.2f mm" % (ch, ch, ch, per_ch[ch]))

    def fmt(s):           # convert absolute coordinates in the description to board coordinates
        return re.sub(r"\(([-\d.]+),([-\d.]+)\)", lambda m: "(%.2f,%.2f)" % (float(m.group(1)) - ox, float(m.group(2)) - oy), s)
    print()
    for key, name in (("a", "(a) ELEx <-> Ex same channel"), ("b", "(b) Ex <-> any MPR121/Pico net (other ELE, I2C, 3V3...)"),
                      ("EE", "(c) Ex <-> Ey (reported)"), ("GND", "(c) Ex <-> GND (reported)")):
        d, w = worst[key]
        print("%-58s min %6.2f mm   %s" % (name, d, fmt(w or "")))
    # resistor leads: bent down at the pads; the two leads of one resistor are pitch - lead diameter apart
    pitches = []
    for fp in board.GetFootprints():
        if re.fullmatch(r"R([1-9]|1[0-2])", fp.GetReference()):
            p = {q.GetNumber(): q.GetPosition() for q in fp.Pads()}
            pitches.append(math.hypot((p["1"].x - p["2"].x) * TOMM, (p["1"].y - p["2"].y) * TOMM))
    lead_gap = min(pitches) - LEAD_D
    print("%-58s min %6.2f mm   (pitch %.2f mm - lead %.1f mm, %d resistors)" %
          ("lead <-> lead of one resistor (geometry)", lead_gap, min(pitches), LEAD_D, len(pitches)))
    print()
    ok = True
    for key, name in (("a", "(a)"), ("b", "(b)")):
        d = worst[key][0]
        for rule, lvl in ((RULE_4KV, "4 kV"), (RULE_8KV, "8 kV")):
            res = "PASS" if d >= rule else "FAIL"
            if lvl == "4 kV" and res == "FAIL":
                ok = False
            print("%s %s gap %.2f mm vs rule %.1f mm (%s)" % (res, name, d, rule, lvl))
    res = "PASS" if lead_gap >= RULE_4KV else "FAIL"
    print("%s leads gap %.2f mm vs rule %.1f mm (4 kV); %s vs %.1f mm (8 kV)" %
          (res, lead_gap, RULE_4KV, "PASS" if lead_gap >= RULE_8KV else "FAIL", RULE_8KV))
    print("SUMMARY: %s" % ("PASS (4 kV rule met for (a), (b) and leads)" if ok and res == "PASS" else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
