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
      (an arc to GND bypasses no IC pin; it diverts the discharge to ground, see calc_gnd_bounce.py).
T-073 / C2-002, top side (component side, no copper): the closest metal of a resistor lying flat is its end caps.
  (d) E cap <-> ELE cap of the same resistor and E cap of Rk <-> ELE cap of any other Rm (cross-channel), with a
      bounded sweep of the unknown dimensions (CALCULATION from the footprint pad positions):
        body length L: 11.9 mm = Lmax (SOURCE EE-S17b dimensions table) and 11.0 mm (ASSUMPTION: no Lmin given;
          check with a caliper on the first parts);
        cap length Lc: 1.5 ... 3.5 mm (ASSUMPTION: the Vishay drawing gives no cap length; check on a part);
        cap diameter = Dmax 4.2 mm (SOURCE; worst case for the cross-channel gap);
        axial placement error of a hand-fitted body: 0, +-0.25 and +-0.5 mm per part (ASSUMPTION), worst sign per pair;
        the protective lacquer over the caps (SOURCE EE-S17b, description) is ignored (bare metal, conservative).
      The leads leave each cap axially outwards (towards its own pad), so they are never closer than the caps.
  (e) floating metal at the mounting holes H1..H4 (screw head / washer on top, spacer on the bottom), radius
      2.8 ... 3.5 mm (ASSUMPTION: ISO 7045 M3 pan head dk 5.6 mm, ISO 7089 M3 washer 7.0 mm): an arc
      ELEx -> screw -> Ex bypasses Rx; reported as the sum of the two gaps (ASSUMPTION: two series gaps need
      at least the breakdown of one gap of the summed length), worst channel, top (caps) and bottom (copper).
Pads are converted to polygons by KiCad (maxError 1 um); tracks are capsules. Distances in mm.
Ties in the worst pair are broken by reference, then pad (C2-011), so the reported pair is deterministic.
"""
import math
import os
import re
import sys

import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")   # optional: other board file
RULE_4KV, RULE_8KV = 3.5, 7.5          # mm, from calc_flashover.out (CALCULATION)
D_MAX, L_MAX = 4.2, 11.9               # mm, MBE/SMA 0414 Dmax, Lmax (SOURCE EE-S17b)
L_SWEEP = (11.0, L_MAX)                # mm, body length (11.0 ASSUMPTION, see docstring)
LC_SWEEP = (1.5, 2.0, 2.5, 3.0, 3.5)   # mm, cap length (ASSUMPTION)
DELTAS = (0.0, 0.25, 0.5)              # mm, axial placement error per part (ASSUMPTION; README asks for <= 0.25)
SCREW_R = (2.8, 3.5)                   # mm, screw head / washer / spacer radius (ASSUMPTION)
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


def natkey(desc):
    """reference, then pad number, numerically (C2-011 tie-break)."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", desc)]


def better(d, pair, cur):
    """True if (d, pair) is a smaller worst case than cur = (d, pair); ties within 1 um broken by name."""
    if cur[1] is None or d < cur[0] - 1e-3:
        return True
    return abs(d - cur[0]) <= 1e-3 and (natkey(pair[0]), natkey(pair[1])) < (natkey(cur[1][0]), natkey(cur[1][1]))


def rect(x0, y0, x1, y1):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return list(zip(pts, pts[1:] + pts[:1]))


def circle(cx, cy, r, n=72):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return list(zip(pts, pts[1:] + pts[:1]))


def segdist(sa, sb):
    """distance between two closed outlines (0 if one lies inside the other is not needed here: shapes are disjoint
    or touching in every case checked; an overlap is reported as 0 through the segment-crossing test)."""
    return min(seg_seg(a, b, c, d) for a, b in sa for c, d in sb)


def resistors(board, ox, oy):
    """R1..R12: channel, pad 1 (ELE) and pad 2 (E) centres in board coordinates."""
    out = []
    for fp in board.GetFootprints():
        m = re.fullmatch(r"R([1-9]|1[0-2])", fp.GetReference())
        if m:
            p = {q.GetNumber(): (q.GetPosition().x * TOMM - ox, q.GetPosition().y * TOMM - oy) for q in fp.Pads()}
            out.append((int(m.group(1)) - 1, fp.GetReference(), p["1"], p["2"]))
    return sorted(out)


def caps(p1, p2, L, Lc, shift):
    """ELE cap and E cap outlines of a body of length L centred between p1 (ELE) and p2 (E), moved `shift` mm
    along the axis towards p2. The footprints are vertical (checked)."""
    if abs(p1[0] - p2[0]) > 1e-6:
        raise SystemExit("resistor axis not vertical")
    x, yc = p1[0], (p1[1] + p2[1]) / 2 + shift
    s = 1 if p2[1] > p1[1] else -1
    top, bot = yc - s * L / 2, yc + s * L / 2
    ele = rect(x - D_MAX / 2, min(top, top + s * Lc), x + D_MAX / 2, max(top, top + s * Lc))
    e = rect(x - D_MAX / 2, min(bot, bot - s * Lc), x + D_MAX / 2, max(bot, bot - s * Lc))
    return ele, e


def main():
    board = pcbnew.LoadBoard(PCB)
    its = items(board)
    origin = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = origin.x * TOMM, origin.y * TOMM
    e_items = sorted([i for i in its if chan(i.net)[0] == "E"], key=lambda i: natkey(i.desc))
    others = sorted([i for i in its if chan(i.net)[0] != "E"], key=lambda i: natkey(i.desc))
    print("# check_gap.py  MEASUREMENT on the design file %s (KiCad %s)" % (os.path.relpath(PCB, ROOT), pcbnew.Version()))
    print("# rule (calc_flashover.out): 4 kV %.1f mm, 8 kV %.1f mm; coordinates relative to the board corner" % (RULE_4KV, RULE_8KV))
    print("# copper = B.Cu pads and tracks (MEASUREMENT); caps/screws = CALCULATION with the ASSUMPTIONS in the header")
    worst = {k: (float("inf"), None) for k in ("a", "b", "EE", "GND")}
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
            pair = ("%s [%s]" % (e.desc, e.net), "%s [%s]" % (o.desc, o.net))
            if better(d, pair, worst[key]):
                worst[key] = (d, pair)
            if key == "a":
                per_ch[ch] = min(per_ch.get(ch, float("inf")), d)
        for o in e_items:
            if o.net != e.net:
                d = dist(e, o)
                pair = ("%s [%s]" % (e.desc, e.net), "%s [%s]" % (o.desc, o.net))
                if better(d, pair, worst["EE"]):
                    worst["EE"] = (d, pair)
    for ch in sorted(per_ch):
        print("  channel E%-2d  ELE%-2d <-> E%-2d copper gap %6.2f mm" % (ch, ch, ch, per_ch[ch]))

    def fmt(s):           # convert absolute coordinates in the description to board coordinates
        return re.sub(r"\(([-\d.]+),([-\d.]+)\)", lambda m: "(%.2f,%.2f)" % (float(m.group(1)) - ox, float(m.group(2)) - oy), s)
    print()
    for key, name in (("a", "(a) ELEx <-> Ex same channel, copper"), ("b", "(b) Ex <-> any MPR121/Pico net, copper"),
                      ("EE", "(c) Ex <-> Ey copper (reported)"), ("GND", "(c) Ex <-> GND copper (reported)")):
        d, w = worst[key]
        print("%-44s min %6.2f mm   %s" % (name, d, fmt(" <-> ".join(w)) if w else ""))

    # ---- (d) end caps of the flat resistors (top side)
    rs = resistors(board, ox, oy)
    print()
    print("(d) end caps of R1..R12 lying flat (top side), D = %.1f mm, %d resistors; gap in mm" % (D_MAX, len(rs)))
    print("    %-6s %-6s %-6s %12s %12s   worst cross-channel pair" % ("L", "Lc", "delta", "same-ch", "cross-ch"))
    cap_rows = []
    for L in L_SWEEP:
        for Lc in LC_SWEEP:
            for delta in DELTAS:
                same = (float("inf"), None)
                cross = (float("inf"), None)
                shifts = (-delta, 0.0, delta) if delta else (0.0,)
                for ch, ref, p1, p2 in rs:
                    ele, e = caps(p1, p2, L, Lc, 0.0)
                    d = segdist(ele, e)
                    if better(d, (ref, ref), same):
                        same = (d, (ref, ref))
                for ch, ref, p1, p2 in rs:
                    for ch2, ref2, q1, q2 in rs:
                        if ref2 == ref or abs(p1[0] - q1[0]) > 15.0:
                            continue                      # only near neighbours can be closest (5.08 mm row pitch)
                        for sa in shifts:
                            for sb in shifts:
                                d = segdist(caps(p1, p2, L, Lc, sa)[1], caps(q1, q2, L, Lc, sb)[0])
                                pair = ("%s E-cap" % ref, "%s ELE-cap" % ref2)
                                if better(d, pair, cross):
                                    cross = (d, pair)
                cap_rows.append((L, Lc, delta, same[0], cross[0]))
                print("    %-6.1f %-6.1f %-6.2f %12.2f %12.2f   %s <-> %s" % (L, Lc, delta, same[0], cross[0], *cross[1]))

    # ---- (e) floating metal at the mounting holes
    print()
    print("(e) floating metal at H1..H4 (radius %.1f / %.1f mm): bypass ELEx -> metal -> Ex = sum of the two gaps, worst channel"
          % SCREW_R)
    holes = sorted([(fp.GetReference(), fp.GetPosition().x * TOMM - ox, fp.GetPosition().y * TOMM - oy)
                    for fp in board.GetFootprints() if re.fullmatch(r"H\d", fp.GetReference())])
    hole_rows = []
    for r in SCREW_R:
        for href, hx, hy in holes:
            sc = circle(hx, hy, r)
            # top side: caps at the worst sweep corner (longest caps, shortest body, no shift)
            top_best = (float("inf"), None)
            for ch, ref, p1, p2 in rs:
                ele, e = caps(p1, p2, min(L_SWEEP), max(LC_SWEEP), 0.0)
                s_ = segdist(sc, ele) + segdist(sc, e)
                if s_ < top_best[0]:
                    top_best = (s_, "%s caps: ELE %.2f + E %.2f" % (ref, segdist(sc, ele), segdist(sc, e)))
            # bottom side: spacer vs copper; ELEx (or any non-E sensitive net) + Ex
            hc = Item("", "", sc, 0.0)
            bot_best = (float("inf"), None)
            for ch in range(12):
                de = min([dist(hc, i) for i in e_items if i.net == "/E%d" % ch] or [float("inf")])
                dl = min([dist(hc, i) for i in others if i.net == "/ELE%d" % ch] or [float("inf")])
                if de + dl < bot_best[0]:
                    bot_best = (de + dl, "ELE%d %.2f + E%d %.2f" % (ch, dl, ch, de))
            hole_rows.append((r, href, top_best[0], bot_best[0]))
            print("    r %.1f %-3s at (%.2f,%.2f): top %6.2f mm (%s); bottom %6.2f mm (%s)"
                  % (r, href, hx, hy, top_best[0], top_best[1], bot_best[0], bot_best[1]))

    # ---- verdicts
    print()
    ok = True
    for key, name in (("a", "(a) copper"), ("b", "(b) copper")):
        d = worst[key][0]
        for rule, lvl in ((RULE_4KV, "4 kV"), (RULE_8KV, "8 kV")):
            res = "PASS" if d >= rule else "FAIL"
            ok &= not (lvl == "4 kV" and res == "FAIL")
            print("%s %s gap %.2f mm vs rule %.1f mm (%s)" % (res, name, d, rule, lvl))
    cap_nom = min(min(r[3], r[4]) for r in cap_rows if r[2] == 0.0)
    cap_all = min(min(r[3], r[4]) for r in cap_rows)
    cap_by_d = [(min(min(r[3], r[4]) for r in cap_rows if r[2] == dl), "placement error +-%.2f mm" % dl) for dl in DELTAS]
    for v, what in cap_by_d:
        print("%s (d) caps worst %.2f mm vs rule %.1f mm (4 kV); %s vs %.1f mm (8 kV)   [%s, L %.1f-%.1f, Lc %.1f-%.1f mm]"
              % ("PASS" if v >= RULE_4KV else "FAIL", v, RULE_4KV, "PASS" if v >= RULE_8KV else "FAIL", RULE_8KV,
                 what, min(L_SWEEP), max(L_SWEEP), min(LC_SWEEP), max(LC_SWEEP)))
    for rule, lvl in ((RULE_4KV, "4 kV"), (RULE_8KV, "8 kV")):
        good = [lc for lc in LC_SWEEP if all(min(r[3], r[4]) >= rule for r in cap_rows if r[1] == lc)]
        print("    (d) %s rule met at every swept L and placement error: %s" %
              (lvl, "for Lc <= %.1f mm" % max(good) if good else "for none of the swept Lc"))
    hole_min = min(min(r[2], r[3]) for r in hole_rows)
    print("%s (e) floating-metal bypass worst %.2f mm vs rule %.1f mm (4 kV); %s vs %.1f mm (8 kV)"
          % ("PASS" if hole_min >= RULE_4KV else "FAIL", hole_min, RULE_4KV, "PASS" if hole_min >= RULE_8KV else "FAIL", RULE_8KV))
    # caps: PASS if the rule holds over the whole sweep, PARTIAL if it fails only with the placement error, else FAIL
    cap_st = "PASS" if cap_all >= RULE_4KV else ("PARTIAL" if cap_nom >= RULE_4KV else "FAIL")
    print("SUMMARY: copper %s (4 kV rule, (a) and (b)); end caps %s at 4 kV over the swept ASSUMPTIONS; mounting metal %s"
          % ("PASS" if ok else "FAIL", cap_st, "PASS" if hole_min >= RULE_4KV else "FAIL"))
    print("SUMMARY 8 kV: copper %s; end caps %s (worst %.2f mm vs %.1f mm)"
          % ("PASS" if min(worst["a"][0], worst["b"][0]) >= RULE_8KV else "FAIL",
             "PASS" if cap_all >= RULE_8KV else "FAIL", cap_all, RULE_8KV))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
