#!/usr/bin/env python3
"""T-091 / CR-003: MEASUREMENT on the design file of the single-layer SMD rules, the Pico keep-outs and the footprint fit.

Runs with the KiCad Python (pcbnew). Optional arguments: board file, drill file.
Criteria: REQ-029 (home-etch rules), ADR-023 (F.Cu only, 4 holes, no vias, no pour), REQ-031 (pin map), T-090 land geometry.
Dimension labels are in the rows. Not a DRC replacement, and DRC is not hardware validation.
"""
import math
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_gap import items, seg_seg, dist, Item, TOMM, ROOT, W_MAX, W_LABEL

PICO_X = 4.5                                        # pin 1 column, board coordinates (gen_pcb.py PICO)

PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
GB = os.path.join(ROOT, "hardware", "fabrication", "gerbers")
DRL = sys.argv[2] if len(sys.argv) > 2 else os.path.join(GB, "frutamidi.drl")  # kicad-cli writes one merged drill file
res = []


def check(name, ok, detail):
    res.append(bool(ok))
    print("%s  %s :: %s" % ("PASS" if ok else "FAIL", name, detail))


def in_rect(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def rect_segs(r):
    pts = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    return list(zip(pts, pts[1:] + pts[:1]))


def rect_margin(it, r):
    """Edge distance from copper item `it` to rectangle r; negative if it enters r."""
    for a, b in it.segs:
        for q in (a, b):
            if in_rect(q, r):
                return -1.0
    d = min(seg_seg(a, b, c, e) for a, b in it.segs for c, e in rect_segs(r))
    d -= it.r
    return d


board = pcbnew.LoadBoard(PCB)
o = board.GetDesignSettings().GetAuxOrigin()
ox, oy = o.x * TOMM, o.y * TOMM
print("# check_smd.py  MEASUREMENT on %s (KiCad %s); board coordinates (mm) from the corner" % (os.path.relpath(PCB, ROOT), pcbnew.Version()))

# 1. layers, vias, zones, holes
tracks = list(board.GetTracks())
vias = [t for t in tracks if t.GetClass() == "PCB_VIA"]
segs = [t for t in tracks if t.GetClass() != "PCB_VIA"]
layers = sorted({board.GetLayerName(t.GetLayer()) for t in segs})
check("ADR-023 tracks only on F.Cu", layers == ["F.Cu"], "%d segments on %s" % (len(segs), layers))
check("ADR-023 no vias", not vias, "%d vias" % len(vias))
zones = list(board.Zones())
fp_zones = [z for fp in board.GetFootprints() for z in fp.Zones()]
filled = [z for z in zones + fp_zones if not z.GetIsRuleArea()]
check("ADR-023 no copper pour (rule areas only)", not filled, "%d board zones, %d footprint rule areas, %d copper zones" % (len(zones), len(fp_zones), len(filled)))
pads = [(fp, p) for fp in board.GetFootprints() for p in fp.Pads()]
thru = [(fp.GetReference(), p.GetNumber()) for fp, p in pads if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
npth = [(fp.GetReference(), pcbnew.ToMM(p.GetDrillSize().x)) for fp, p in pads if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
bcu = [(fp.GetReference(), p.GetNumber()) for fp, p in pads if p.IsOnLayer(pcbnew.B_Cu) and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
check("ADR-023 only SMD pads plus NPTH mounting holes", not thru and not bcu, "plated/through %s, on B.Cu %s" % (thru, bcu))
check("ADR-023 exactly 4 M3 holes in the board file", len(npth) == 4 and all(abs(d - 3.2) < 1e-6 for _, d in npth), "NPTH %s" % sorted(npth))
for label, path, want in (("merged", DRL, 4),):
    if os.path.isfile(path):
        t = open(path, encoding="utf-8", errors="replace").read()
        hits = re.findall(r"^X[-\d.]+Y[-\d.]+\s*$", t, re.M)
        check("drill file %s holes" % label, len(hits) == want, "%d hits in %s (expected %d)" % (len(hits), os.path.relpath(path, ROOT), want))
    else:
        print("NOT RUN  drill file %s :: %s absent" % (label, path))

# 2. track widths (REQ-029)
NET_PWR = {"GND", "+3V3", "/S1", "/S7", "AGND"}      # AGND carries the pot current only; 1.0 mm allowed, not classed as power
NET_PWR.discard("AGND")
widths = {}
stubs = []
for t in segs:
    w = t.GetWidth() * TOMM
    n = t.GetNetname()
    widths.setdefault(n, set()).add(round(w, 3))
    if w < 0.999:
        L = math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) * TOMM
        stubs.append((n, round(w, 2), round(L, 2)))
check("REQ-029 min track width >= 0.8 mm", min(min(v) for v in widths.values()) >= 0.8 - 1e-9, "min %.2f mm" % min(min(v) for v in widths.values()))
check("REQ-029 power >= 1.2 mm", all(min(widths[n]) >= 1.2 - 1e-9 for n in NET_PWR if n in widths), {n: sorted(widths[n]) for n in NET_PWR if n in widths})
check("REQ-029 signal >= 1.0 mm except short stubs", all(x[2] <= 6.0 for x in stubs), "%d stub segments below 1.0 mm, longest %.2f mm; nets %s" % (len(stubs), max([x[2] for x in stubs] or [0]), sorted({x[0] for x in stubs})))

# 3. Pico keep-outs: tracks and every F.Cu pad (independent of the DRC rule area)
KO = {"TP/USB (T-090)": (9.52, 0.48, 17.27, 14.98), "SWD pads": (9.45, 47.83, 17.33, 52.23)}
its = items(board)
for it in its:
    it.segs = [((a[0] - ox, a[1] - oy), (b[0] - ox, b[1] - oy)) for a, b in it.segs]
for name, r in KO.items():
    m = [(rect_margin(it, r), it.desc, it.net) for it in its]
    m.sort(key=lambda x: x[0])
    check("copper outside Pico keep-out %s" % name, m[0][0] >= 0.0, "nearest copper margin %.2f mm: %s [%s]; rectangle %s" % (m[0][0], m[0][1], m[0][2], r))

# 4. no track under R1-R12 bodies between the pads
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
under = []
for i in range(1, 13):
    fp = fps["R%d" % i]
    pp = {p.GetNumber(): (p.GetPosition().x * TOMM - ox, p.GetPosition().y * TOMM - oy) for p in fp.Pads()}
    x, y1, y2 = pp["1"][0], pp["1"][1] + 0.95, pp["2"][1] - 0.95
    r = (x - W_MAX / 2, y1, x + W_MAX / 2, y2)
    for it in its:
        if it.desc.startswith("R%d pad" % i):
            continue
        if rect_margin(it, r) < 0.0:
            under.append(("R%d" % i, it.desc, it.net))
check("ADR-023 no copper under R1-R12 bodies between the pads", not under, "%d intrusions %s (body width %.1f mm, %s)" % (len(under), under[:4], W_MAX, W_LABEL))

# 5. footprint fit
def pad_rect(p):
    bb = p.GetBoundingBox()
    return (bb.GetLeft() * TOMM - ox, bb.GetTop() * TOMM - oy, bb.GetRight() * TOMM - ox, bb.GetBottom() * TOMM - oy)


a1 = {p.GetNumber(): p for p in fps["A1"].Pads()}
r1, r40 = pad_rect(a1["1"]), pad_rect(a1["40"])
inner = r40[0] - r1[2]
outer = r40[2] - r1[0]
check("A1 inner land width 16.18 mm (SOURCE RP-008307-DS-2 Fig. 5)", abs(inner - 16.18) < 0.01, "%.3f mm" % inner)
check("A1 outer edge = module edge + 1.79 mm (21 + 2*1.79 = 24.58)", abs(outer - 24.58) < 0.01, "%.3f mm" % outer)
check("A1 40 pads 1.6 x 4.2 mm", len(a1) == 40 and all(abs(p.GetSize(pcbnew.F_Cu).x * TOMM - 4.2) < 1e-3 and abs(p.GetSize(pcbnew.F_Cu).y * TOMM - 1.6) < 1e-3 for p in a1.values()), "%d pads" % len(a1))
gap = pad_rect(a1["2"])[1] - pad_rect(a1["1"])[3]
check("A1 pad gap >= 0.6 mm", gap >= 0.6, "%.2f mm" % gap)
check("A1 outer land edge inside board >= 0.5 mm", r1[0] >= 0.5, "%.2f mm" % r1[0])

a2 = {p.GetNumber(): p for p in fps["A2"].Pads()}
pos = lambda p: (p.GetPosition().x * TOMM - ox, p.GetPosition().y * TOMM - oy)
check("A2 20 pads, pitch 2.54, rows 15.24 mm", len(a2) == 20 and abs(pos(a2["2"])[0] - pos(a2["1"])[0] - 2.54) < 1e-3 and abs(pos(a2["1"])[1] - pos(a2["14"])[1] - 15.24) < 1e-3, "%d pads, rows %.3f mm" % (len(a2), pos(a2["1"])[1] - pos(a2["14"])[1]))
check("A2 pad 1.8 x 2.4 mm, gap >= 0.6", all(abs(p.GetSize(pcbnew.F_Cu).x * TOMM - 1.8) < 1e-3 and abs(p.GetSize(pcbnew.F_Cu).y * TOMM - 2.4) < 1e-3 for p in a2.values()), "gap %.2f mm" % (2.54 - 1.8))

r1p = {p.GetNumber(): p for p in fps["R1"].Pads()}
g = pad_rect(r1p["2"])[1] - pad_rect(r1p["1"])[3]
check("R1-R12 land gap G = 5.0 mm (ADR-023)", abs(g - 5.0) < 1e-3, "%.3f mm" % g)
L_T = (6.2, 6.8)
A_T = (0.3, 0.9)
pad_inner, pad_outer = 2.5, 4.4
term_in = min(L_T) / 2 - max(A_T)
term_out = max(L_T) / 2
check("HPWC2512 termination lands on the pad at all L, A (CALCULATION)", term_in <= pad_outer and term_out <= pad_outer and max(L_T) / 2 - min(A_T) >= pad_inner, "termination inner edge %.2f..%.2f, outer edge %.2f..%.2f; pad %.2f..%.2f mm" % (term_in, max(L_T) / 2 - min(A_T), min(L_T) / 2, term_out, pad_inner, pad_outer))

sw = {p.GetNumber() + ("L" if pos(p)[0] < fps["SW1"].GetPosition().x * TOMM - ox else "R"): pos(p) for p in fps["SW1"].Pads()}
check("SW1 land 9.5 / 6.4 / 4.5 / 1.3 (SOURCE Omron B3S p.2): rows 4.5, centres 7.95", abs(sw["2L"][1] - sw["1L"][1] - 4.5) < 1e-3 and abs(sw["1R"][0] - sw["1L"][0] - 7.95) < 1e-3, str(sorted(sw.items())))
check("JP1 gap >= 1.8 mm", abs(pos({p.GetNumber(): p for p in fps["JP1"].Pads()}["1"])[1] - pos({p.GetNumber(): p for p in fps["JP1"].Pads()}["2"])[1] - 3.81) < 1e-3, "pitch 3.81, pad 1.94, gap 1.87 mm (CALCULATION)")

# 6. pin map (REQ-031), net by pad
want = {"31": "/SDA_PICO", "32": "/SCL_PICO", "29": "/BTN", "34": "/POT", "33": "/AGND", "36": "+3V3", "3": "GND", "8": "GND", "13": "GND", "18": "GND", "23": "GND", "28": "GND", "38": "GND"}
got = {n: a1[n].GetNetname() for n in want}
check("REQ-031 A1 pin map unchanged", all(got[n] == want[n] for n in want), str(got))
used = sum(1 for p in a1.values() if p.GetNetname() and not p.GetNetname().startswith("unconnected"))
check("A1 connected pads = 13 (6 signal/power + 7 GND)", used == 13, "%d" % used)
# 7. mounting holes (T-092): spread, USB end, head / washer clearance
holes = {fp.GetReference(): pos_fp for fp, pos_fp in ((f, (f.GetPosition().x * TOMM - ox, f.GetPosition().y * TOMM - oy)) for f in board.GetFootprints()) if re.fullmatch(r"H\d", fp.GetReference())}
print("# mounting holes (MEASUREMENT, design file): %s" % {k: (round(v[0], 2), round(v[1], 2)) for k, v in sorted(holes.items())})
W, H = 100.0, 70.0
quad = sorted(("L" if x < W / 2 else "R") + ("T" if y < H / 2 else "B") for x, y in holes.values())
check("T-092 one hole per board quadrant", quad == ["LB", "LT", "RB", "RT"], str(quad))
names = sorted(holes)
pairs = [(math.hypot(holes[a][0] - holes[b][0], holes[a][1] - holes[b][1]), a, b) for i, a in enumerate(names) for b in names[i + 1:]]
dmin = min(pairs)
check("T-092 min distance between holes >= 45 mm (criterion chosen in T-092; T-091 had 10.6 mm)", dmin[0] >= 45.0, "%.2f mm (%s-%s)" % dmin)
cx, cy = sum(v[0] for v in holes.values()) / 4, sum(v[1] for v in holes.values()) / 4
ring = sorted(holes.values(), key=lambda v: math.atan2(v[1] - cy, v[0] - cx))
area = abs(sum(ring[i][0] * ring[(i + 1) % 4][1] - ring[(i + 1) % 4][0] * ring[i][1] for i in range(4))) / 2
check("T-092 area of the hole quadrilateral >= 60 % of the board (criterion chosen in T-092)", area / (W * H) >= 0.60, "%.0f mm2 = %.1f %% of %.0f mm2" % (area, 100 * area / (W * H), W * H))
USB_END = (PICO_X + 8.89, 0.63)                    # centre of the Pico USB end: pin 1 column + 8.89, module end y 2.0 - 1.37 (SOURCE RP-008307-DS-2 via T-090)
d_usb = sorted((math.hypot(v[0] - USB_END[0], v[1] - USB_END[1]), k) for k, v in holes.items())
check("T-092 nearest hole <= 20 mm from the centre of the Pico USB end (criterion chosen in T-092; T-091 had 63.6 mm)", d_usb[0][0] <= 20.0, "%s at %.2f mm; next %s at %.2f mm" % (d_usb[0][1], d_usb[0][0], d_usb[1][1], d_usb[1][0]))
BOARD_T = 1.6                                       # ASSUMPTION standard FR-4
HOLE_R, WASHER, HEAD = 1.6, 3.5, 2.8               # drill (SOURCE ISO 273 fine) ; ISO 7089 washer, ISO 7045 pan head radius (ASSUMPTION, recalled)
hc = {}
for k, (x, y) in sorted(holes.items()):
    edge = min(x, W - x, y, H - y) - HOLE_R
    near = sorted((dist(Item("", "", [((x, y), (x, y))], 0.0), it), it.desc, it.net) for it in its)
    near = list(near[0])
    near[1] = re.sub(r"\(([-\d.]+),([-\d.]+)\)", lambda m: "(%.2f,%.2f)" % (float(m.group(1)) - ox, float(m.group(2)) - oy), near[1])
    crt = []
    for fp in board.GetFootprints():
        if fp.GetReference() == k:
            continue
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_CrtYd and g.GetClass() == "PCB_SHAPE" and g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                a, b = g.GetStart(), g.GetEnd()
                crt.append((seg_seg((x, y), (x, y), (a.x * TOMM - ox, a.y * TOMM - oy), (b.x * TOMM - ox, b.y * TOMM - oy)), fp.GetReference()))
    crt = min(crt)
    hc[k] = (near[0], crt[0])
    check("T-092 %s drill edge to board edge >= board thickness %.1f mm" % (k, BOARD_T), edge >= BOARD_T - 1e-6, "%.2f mm" % edge)
    check("T-092 %s washer r %.1f mm clear of copper >= 0.6 mm" % (k, WASHER), near[0] - WASHER >= 0.6 - 1e-3, "washer %.2f mm, pan head r %.1f %.2f mm, nearest %s [%s]" % (near[0] - WASHER, HEAD, near[0] - HEAD, near[1], near[2]))
    check("T-092 %s washer r %.1f mm clear of part courtyards" % (k, WASHER), crt[0] - WASHER >= 0.0, "washer %.2f mm, pan head %.2f mm, nearest courtyard %s" % (crt[0] - WASHER, crt[0] - HEAD, crt[1]))

# 8. assembly map: reference designators do not touch each other (T-092; replaces the retired check_silk.py)
boxes = []
for fp in board.GetFootprints():
    cand = [fp.Reference()] if fp.Reference().IsVisible() else []
    cand += [g for g in fp.GraphicalItems() if g.GetClass() == "PCB_TEXT" and "REFERENCE" in g.GetText()]
    for t in cand:
        if t.GetLayer() == pcbnew.F_Fab:
            bb = t.GetBoundingBox()
            boxes.append((fp.GetReference(), bb.GetLeft() * TOMM - ox, bb.GetTop() * TOMM - oy, bb.GetRight() * TOMM - ox, bb.GetBottom() * TOMM - oy))
def box_gap(p, q):
    dx = max(p[1] - q[3], q[1] - p[3], 0.0)
    dy = max(p[2] - q[4], q[2] - p[4], 0.0)
    return math.hypot(dx, dy)
gaps = sorted((box_gap(p, q), p[0], q[0]) for i, p in enumerate(boxes) for q in boxes[i + 1:])
sw_r16 = [g for g in gaps if {g[1], g[2]} == {"R16", "SW1"}]
check("T-092 SW1 and R16 designators >= 2.0 mm apart on the assembly map (criterion chosen in T-092)", sw_r16 and sw_r16[0][0] >= 2.0, "gap %.2f mm" % sw_r16[0][0])
check("T-092 all reference designators apart >= 0.2 mm on the assembly map (F.Fab)", gaps[0][0] >= 0.2, "%d designators; worst %.2f mm (%s, %s)" % (len(boxes), gaps[0][0], gaps[0][1], gaps[0][2]))

print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(res), res.count(True), res.count(False)))
sys.exit(0 if all(res) else 1)
