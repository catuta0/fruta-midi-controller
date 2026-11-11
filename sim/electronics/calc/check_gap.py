#!/usr/bin/env python3
"""T-091 / CR-003 (SMD board, supersedes the T-060 THT version in git history): CALCULATION (design file) of the
copper gaps that an ESD strike on an electrode could arc across, compared with the CALCULATION rule of calc_flashover.py.

Runs with the KiCad Python (pcbnew):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      sim/electronics/calc/check_gap.py > sim/electronics/calc/check_gap.out

What is measured on hardware/frutamidi.kicad_pcb (F.Cu copper: pads and tracks; edge-to-edge distance):
  (a) ELEx <-> Ex, same channel x (copper around the series resistor);
  (b) Ex <-> every copper item of another net that leads to the MPR121 or the Pico (ELEy of any channel, S1..S7,
      SDA/SCL, 3V3, button, pot, AGND ...), i.e. every net except E0..E11 and GND;
  (c) reported only: Ex <-> Ey (an arc between two electrodes still passes a series resistor) and Ex <-> GND
      (an arc to GND bypasses no IC pin; it diverts the discharge to ground, see calc_gnd_bounce.py).
  (d) metal terminations of the 2512 chips (T-096 / ADR-026: YAGEO RC2512FK-073K3L; CALCULATION from the land positions): E termination
      <-> ELE termination of the same chip and of any other chip, with L 6.35 +-0.10 mm, termination length A = I1 0.60 +-0.20 (top) /
      I2 0.50 +-0.20 (bottom) swept 0.3 ... 0.8 mm, W 3.10 +-0.15 mm (SOURCE YAGEO RC_L V.11 Table 1; L min - 2 I1 max = 4.65 mm)
      and a hand-placement error along the axis 0, +-0.25, +-0.5 mm per part
      (ASSUMPTION), worst sign per pair.
  (e) floating metal at the mounting holes H1..H4 (screw head / washer on the copper side, radius 2.8 ... 3.5 mm,
      ASSUMPTION ISO 7045 M3 pan head dk 5.6 mm, ISO 7089 M3 washer 7.0 mm): an arc ELEx -> screw -> Ex bypasses Rx;
      reported as the sum of the two gaps (ASSUMPTION: two series gaps need at least the breakdown of one gap of the
      summed length), worst channel, against copper and terminations. The reverse side has no copper any more.
  (f) ADR-020 spark gap: each electrode J2 pad <-> GND edge track, 1.40 +/- 0.05 mm.
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
W_MAX = 3.25                           # mm, RC2512 body width upper bound (W_LABEL)
W_LABEL = "SOURCE YAGEO RC_L V.11 Table 1: W 3.10 +- 0.15 mm"
L_SWEEP = (6.25, 6.45)                 # mm, body length (SOURCE YAGEO RC_L V.11: 6.35 +- 0.10)
A_SWEEP = (0.3, 0.8)                   # mm, termination length (SOURCE YAGEO RC_L V.11: I1 0.60 +- 0.20, I2 0.50 +- 0.20)
DELTAS = (0.0, 0.25, 0.5)              # mm, axial placement error per part (ASSUMPTION; hand soldering)
SPARK_NOM, SPARK_TOL = 1.40, 0.05      # mm, ADR-020
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
        if t.GetLayer() != pcbnew.F_Cu:
            continue
        a, b = t.GetStart(), t.GetEnd()
        out.append(Item(t.GetNetname(), "track (%.2f,%.2f)-(%.2f,%.2f)" % (a.x * TOMM, a.y * TOMM, b.x * TOMM, b.y * TOMM),
                        [((a.x * TOMM, a.y * TOMM), (b.x * TOMM, b.y * TOMM))], t.GetWidth() * TOMM / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(pcbnew.F_Cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue                                   # mounting holes carry no copper
            ps = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(ps, pcbnew.F_Cu, 0, 1000, pcbnew.ERROR_INSIDE)
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


def terms(p1, p2, L, A, shift):
    """ELE and E termination outlines of a chip of length L, termination length A, centred between pad centres p1 (ELE)
    and p2 (E), moved `shift` mm along the axis towards p2. The footprints are vertical (checked)."""
    if abs(p1[0] - p2[0]) > 1e-6:
        raise SystemExit("resistor axis not vertical")
    x, yc = p1[0], (p1[1] + p2[1]) / 2 + shift
    s = 1 if p2[1] > p1[1] else -1
    top, bot = yc - s * L / 2, yc + s * L / 2
    ele = rect(x - W_MAX / 2, min(top, top + s * A), x + W_MAX / 2, max(top, top + s * A))
    e = rect(x - W_MAX / 2, min(bot, bot - s * A), x + W_MAX / 2, max(bot, bot - s * A))
    return ele, e


def main():
    board = pcbnew.LoadBoard(PCB)
    its = items(board)
    origin = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = origin.x * TOMM, origin.y * TOMM
    e_items = sorted([i for i in its if chan(i.net)[0] == "E"], key=lambda i: natkey(i.desc))
    others = sorted([i for i in its if chan(i.net)[0] != "E"], key=lambda i: natkey(i.desc))
    print("# check_gap.py  CALCULATION (design file) %s (KiCad %s)" % (os.path.relpath(PCB, ROOT), pcbnew.Version()))
    print("# rule (calc_flashover.out): 4 kV %.1f mm, 8 kV %.1f mm; coordinates relative to the board corner" % (RULE_4KV, RULE_8KV))
    print("# copper = F.Cu pads and tracks (CALCULATION (design file)); terminations/screws = CALCULATION with the ASSUMPTIONS in the header")
    print("# W_MAX = %.1f mm (%s)" % (W_MAX, W_LABEL))
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

    # ---- (d) terminations of the 2512 chips
    rs = resistors(board, ox, oy)
    print()
    print("(d) terminations of R1..R12 (RC2512, W %.2f mm, %d resistors); gap in mm" % (W_MAX, len(rs)))
    print("    %-6s %-6s %-6s %12s %12s   worst cross-channel pair" % ("L", "A", "delta", "same-ch", "cross-ch"))
    cap_rows = []
    for L in L_SWEEP:
        for A in A_SWEEP:
            for delta in DELTAS:
                same = (float("inf"), None)
                cross = (float("inf"), None)
                shifts = (-delta, 0.0, delta) if delta else (0.0,)
                for ch, ref, p1, p2 in rs:
                    ele, e = terms(p1, p2, L, A, 0.0)
                    d = segdist(ele, e)
                    if better(d, (ref, ref), same):
                        same = (d, (ref, ref))
                for ch, ref, p1, p2 in rs:
                    for ch2, ref2, q1, q2 in rs:
                        if ref2 == ref or abs(p1[0] - q1[0]) > 15.0:
                            continue
                        for sa in shifts:
                            for sb in shifts:
                                d = segdist(terms(p1, p2, L, A, sa)[1], terms(q1, q2, L, A, sb)[0])
                                pair = ("%s E-term" % ref, "%s ELE-term" % ref2)
                                if better(d, pair, cross):
                                    cross = (d, pair)
                cap_rows.append((L, A, delta, same[0], cross[0]))
                print("    %-6.2f %-6.2f %-6.2f %12.2f %12.2f   %s <-> %s" % (L, A, delta, same[0], cross[0], *cross[1]))

    # ---- (e) floating metal at the mounting holes (copper side only)
    print()
    print("(e) floating metal at H1..H4 (radius %.1f / %.1f mm): bypass ELEx -> metal -> Ex = sum of the two gaps, worst channel"
          % SCREW_R)
    holes = sorted([(fp.GetReference(), fp.GetPosition().x * TOMM - ox, fp.GetPosition().y * TOMM - oy)
                    for fp in board.GetFootprints() if re.fullmatch(r"H\d", fp.GetReference())])
    hole_rows = []
    wL, wA = min(L_SWEEP), max(A_SWEEP)
    for r in SCREW_R:
        for href, hx, hy in holes:
            sc = circle(hx + ox, hy + oy, r)
            hc = Item("", "", sc, 0.0)
            best = (float("inf"), None)
            for ch in range(12):
                de = min([dist(hc, i) for i in e_items if i.net == "/E%d" % ch] or [float("inf")])
                dl = min([dist(hc, i) for i in others if i.net == "/ELE%d" % ch] or [float("inf")])
                rr = [x for x in rs if x[0] == ch]
                if rr:
                    _, ref, p1, p2 = rr[0]
                    ele, e = terms(p1, p2, wL, wA, 0.0)
                    sc0 = circle(hx, hy, r)
                    dl = min(dl, segdist(sc0, ele))
                    de = min(de, segdist(sc0, e))
                if de + dl < best[0]:
                    best = (de + dl, "ELE%d %.2f + E%d %.2f" % (ch, dl, ch, de))
            hole_rows.append((r, href, best[0]))
            print("    r %.1f %-3s at (%.2f,%.2f): copper side %6.2f mm (%s)" % (r, href, hx, hy, best[0], best[1]))

    # ---- (f) spark gap ADR-020
    print()
    print("(f) ADR-020 spark gap: electrode J2 pad <-> nearest GND copper (should be the edge track at y = 68.0)")
    edge_tracks = [i for i in others if i.net == "GND" and i.desc.startswith("track") and abs(i.segs[0][0][1] - i.segs[0][1][1]) < 1e-3
                   and i.segs[0][0][1] - oy > 65.0]
    gnd_all = [i for i in others if i.net == "GND"]
    spark = []
    for e in e_items:
        if not e.desc.startswith("J2 pad"):
            continue
        d_edge = min(dist(e, g) for g in edge_tracks)
        d_any = min(dist(e, g) for g in gnd_all)
        spark.append((e.net, d_edge, d_any))
    spark.sort(key=lambda x: int(x[0].split("E")[-1]))
    for net, d_edge, d_any in spark:
        print("    %-5s to edge track %.3f mm; to any GND copper %.3f mm" % (net.lstrip("/"), d_edge, d_any))
    spark_ok = len(spark) == 12 and all(abs(d - SPARK_NOM) <= SPARK_TOL + 1e-9 and abs(a - d) < 1e-6 for _, d, a in spark)

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
    for dl in DELTAS:
        v = min(min(r[3], r[4]) for r in cap_rows if r[2] == dl)
        print("%s (d) terminations worst %.2f mm vs rule %.1f mm (4 kV); %s vs %.1f mm (8 kV)   [placement error +-%.2f mm]"
              % ("PASS" if v >= RULE_4KV else "FAIL", v, RULE_4KV, "PASS" if v >= RULE_8KV else "FAIL", RULE_8KV, dl))
    hole_min = min(r[2] for r in hole_rows)
    print("%s (e) floating-metal bypass worst %.2f mm vs rule %.1f mm (4 kV); %s vs %.1f mm (8 kV)"
          % ("PASS" if hole_min >= RULE_4KV else "FAIL", hole_min, RULE_4KV, "PASS" if hole_min >= RULE_8KV else "FAIL", RULE_8KV))
    print("%s (f) spark gap: %d electrode pads, min %.3f / max %.3f mm vs %.2f +/- %.2f mm; nearest GND is the edge track"
          % ("PASS" if spark_ok else "FAIL", len(spark), min(x[1] for x in spark), max(x[1] for x in spark), SPARK_NOM, SPARK_TOL))
    cap_st = "PASS" if cap_all >= RULE_4KV else ("PARTIAL" if cap_nom >= RULE_4KV else "FAIL")
    print("SUMMARY: copper %s (4 kV rule, (a) and (b)); terminations %s at 4 kV over the swept ASSUMPTIONS; mounting metal %s; spark gap %s"
          % ("PASS" if ok else "FAIL", cap_st, "PASS" if hole_min >= RULE_4KV else "FAIL", "PASS" if spark_ok else "FAIL"))
    print("SUMMARY 8 kV: copper %s; terminations %s (worst %.2f mm vs %.1f mm)"
          % ("PASS" if min(worst["a"][0], worst["b"][0]) >= RULE_8KV else "FAIL",
             "PASS" if cap_all >= RULE_8KV else "FAIL", cap_all, RULE_8KV))
    return 0 if ok and spark_ok else 1


if __name__ == "__main__":
    sys.exit(main())
