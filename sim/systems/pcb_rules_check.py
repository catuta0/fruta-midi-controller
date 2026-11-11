"""Rules inspection of hardware/frutamidi.kicad_pcb for the v1.3 SMD board (T-093, CR-003, ADR-023).
Originally T-008 (through-hole, B.Cu); rewritten for copper on F.Cu, surface-mount parts and 4 M3 holes.
Covers REQ-027 (one copper side, SMD, 4 holes, no vias, no pour, wire links), REQ-028 (outline), REQ-029 (home-etch and
SMD land rules), REQ-023 (R1-R12 land gap), ADR-020 (Ex <-> GND edge-track spark gap), ADR-021 (JP1, J2 pads).

A plain-text parse of the KiCad file: it does not use pcbnew, so it is independent of sim/electronics/calc/check_smd.py.
It is not a DRC replacement: etched copper text (gr_text on F.Cu) is not in the clearance sweep and is left to DRC.
A design-file check says nothing about etched, soldered or powered hardware.
Usage: python3 sim/systems/pcb_rules_check.py [board.kicad_pcb [drill.drl]]
       Defaults: hardware/frutamidi.kicad_pcb and hardware/fabrication/gerbers/frutamidi.drl
Exit status: 0 if every check passes, 1 otherwise."""
import math, os, re, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
DRL = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "hardware", "fabrication", "gerbers", "frutamidi.drl")
t = open(PCB, encoding="utf-8").read()
res = []
def check(n, ok, d):
    res.append(bool(ok)); print("%s  %s :: %s" % ("PASS" if ok else "FAIL", n, d))

# ---- parsing -------------------------------------------------------------------------------------------------
def masked(text):
    """Text with the contents of quoted strings blanked (same length), so that parentheses inside descriptions are ignored."""
    return re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: '"' + " " * (len(m.group()) - 2) + '"', text)

def blocks(text, head):
    """Balanced-parenthesis S-expression blocks that start with '(head' + whitespace (quoted strings ignored)."""
    mask, out = masked(text), []
    for m in re.finditer(r'\(%s\s' % re.escape(head), mask):
        d, j = 0, m.start()
        while True:
            if mask[j] == "(":
                d += 1
            elif mask[j] == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append(text[m.start():j + 1])
    return out

def rot(x, y, deg):
    """KiCad rotation (y down, positive angle counter-clockwise on screen)."""
    a = math.radians(deg); return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)

class Item:
    """Copper shape: segments plus a radius (capsule/stadium) or a closed polygon (rect, radius 0)."""
    def __init__(s, kind, net, desc, segs, r=0.0, poly=None):
        s.kind, s.net, s.desc, s.segs, s.r, s.poly = kind, net, desc, segs, r, poly

segments = []
for m in re.finditer(r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+\(net "([^"]*)"\)', t):
    x1, y1, x2, y2, w, lay, net = m.groups()
    segments.append(dict(a=(float(x1), float(y1)), b=(float(x2), float(y2)), w=float(w), layer=lay, net=net))
arcs = len(re.findall(r'\n\t\(arc\s', t))

FP_AT = re.compile(r'\(footprint "[^"]+"\s*\(layer "([^"]+)"\)\s*\(uuid "[^"]+"\)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)')
PAD = re.compile(r'^\(pad "([^"]*)" (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([\d.]+) ([\d.]+)\)')
fps, pads = {}, []
for blk in blocks(t, "footprint"):
    name = re.match(r'\(footprint "([^"]+)"', blk).group(1)
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    flay, fx, fy, fa = FP_AT.match(blk).groups()
    fx, fy, fa = float(fx), float(fy), float(fa or 0)
    fpads = []
    for pb in blocks(blk, "pad"):
        num, typ, shape, px, py, pa, sx, sy = PAD.match(pb).groups()
        sx, sy = float(sx), float(sy)
        gx, gy = rot(float(px), float(py), fa)
        cx, cy = fx + gx, fy + gy                # KiCad stores the pad angle as an absolute angle
        ang = float(pa) if pa is not None else 0.0
        dr = re.search(r'\(drill (?:oval )?([\d.]+)', pb)
        off = re.search(r'\(drill[^)]*\(offset ([-\d.]+) ([-\d.]+)\)', pb)
        net = re.search(r'\(net "([^"]*)"\)', pb)
        lays = re.search(r'\(layers ([^)]*)\)', pb).group(1).replace('"', "").split()
        p = dict(ref=ref, num=num, typ=typ, shape=shape, c=(cx, cy), ang=ang, sx=sx, sy=sy, drill=float(dr.group(1)) if dr else None,
                 offset=bool(off), net=net.group(1) if net else "", layers=lays, fp=name)
        fpads.append(p); pads.append(p)
    fps[ref] = dict(name=name, pads=fpads, layer=flay, at=(fx, fy), ang=fa, joined_dups="(duplicate_pad_numbers_are_jumpers yes)" in blk)

def pad_item(p):
    """Rect pads become exact polygons; circle and oval pads become exact stadiums. Other shapes are refused."""
    desc = "%s.%s" % (p["ref"], p["num"])
    if p["shape"] == "rect":
        hx, hy = p["sx"] / 2, p["sy"] / 2
        pts = []
        for ux, uy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            ox, oy = rot(ux, uy, p["ang"]); pts.append((p["c"][0] + ox, p["c"][1] + oy))
        return Item("pad", p["net"], desc, list(zip(pts, pts[1:] + pts[:1])), 0.0, pts)
    if p["shape"] in ("circle", "oval"):
        r, half = min(p["sx"], p["sy"]) / 2, (max(p["sx"], p["sy"]) - min(p["sx"], p["sy"])) / 2
        ux, uy = rot(*((1.0, 0.0) if p["sx"] >= p["sy"] else (0.0, 1.0)), p["ang"])
        a, b = (p["c"][0] - half * ux, p["c"][1] - half * uy), (p["c"][0] + half * ux, p["c"][1] + half * uy)
        return Item("pad", p["net"], desc, [(a, b)], r)
    raise SystemExit("unsupported pad shape %s on %s" % (p["shape"], desc))

def pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
def seg_seg(a, b, c, d):
    def orient(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and 0 not in (o1, o2, o3, o4): return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))
def inside(pt, poly):
    n, s = len(poly), 0
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        v = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        if v != 0:
            if s == 0: s = 1 if v > 0 else -1
            elif (v > 0) != (s > 0): return False
    return True
def dist(i1, i2):
    """Copper edge-to-edge distance; <= 0 means the two shapes touch or overlap."""
    for u, v in ((i1, i2), (i2, i1)):
        if u.poly and any(inside(q, u.poly) for s in v.segs for q in s): return -1.0
    return min(seg_seg(a, b, c, d) for a, b in i1.segs for c, d in i2.segs) - i1.r - i2.r
def seg_item(s, k):
    return Item("track", s["net"], "track#%d (%.2f,%.2f)-(%.2f,%.2f) w%.2f" % (k, *s["a"], *s["b"], s["w"]), [(s["a"], s["b"])], s["w"] / 2)

copper_pads = [p for p in pads if p["typ"] != "np_thru_hole"]
items = [pad_item(p) for p in copper_pads] + [seg_item(s, k) for k, s in enumerate(segments)]

# ---- REQ-027: one copper side, surface-mount only, no vias, no pour --------------------------------------------
layers = sorted(set(s["layer"] for s in segments))
check("REQ-027 tracks only on F.Cu", layers == ["F.Cu"] and arcs == 0, "%d segments, layers %s, %d arcs" % (len(segments), layers, arcs))
bcu = len(re.findall(r'\(layer "B\.Cu"\)', t))
bpads = [p["ref"] + "." + p["num"] for p in copper_pads if "B.Cu" in p["layers"] or "*.Cu" in p["layers"]]
check("REQ-027 no copper object on B.Cu", bcu == 0 and not bpads, "objects with (layer \"B.Cu\"): %d; copper pads on B.Cu or *.Cu: %s" % (bcu, bpads))
vias = len(re.findall(r'\(via[\s(]', masked(t)))
check("REQ-027 no vias", vias == 0, "via objects: %d" % vias)
zones = blocks(t, "zone")
keepouts = [z for z in zones if "(keepout" in z]
pours = [z for z in zones if "(keepout" not in z]
check("REQ-027 no copper pour (only rule areas)", not pours, "%d zones: %d keep-out rule areas, %d copper zones" % (len(zones), len(keepouts), len(pours)))
not_smd = sorted("%s.%s(%s)" % (p["ref"], p["num"], p["typ"]) for p in copper_pads if p["typ"] != "smd" or "F.Cu" not in p["layers"])
drilled = sorted("%s.%s" % (p["ref"], p["num"]) for p in copper_pads if p["drill"] is not None)
check("REQ-027 every copper pad is surface-mount on F.Cu with no drill", not not_smd and not drilled,
      "%d copper pads; not smd on F.Cu: %s; drilled: %s" % (len(copper_pads), not_smd, drilled))
fp_lay = sorted(r for r, f in fps.items() if f["layer"] != "F.Cu")
check("REQ-027 every part on the copper side", not fp_lay, "footprints not on F.Cu: %s" % fp_lay)

# ---- REQ-027: holes -----------------------------------------------------------------------------------------
edge = re.findall(r'\(gr_line\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\).*?\(layer "Edge.Cuts"\)', t, re.S)
xs = [float(v) for e in edge for v in (e[0], e[2])]; ys = [float(v) for e in edge for v in (e[1], e[3])]
holes = [p for p in pads if p["typ"] == "np_thru_hole"]
hole_refs = sorted(p["ref"] for p in holes)
all_drills = [p for p in pads if p["drill"] is not None]
check("REQ-027 exactly 4 holes, all M3 NPTH on H1..H4", len(all_drills) == 4 and len(holes) == 4 and hole_refs == ["H1", "H2", "H3", "H4"]
      and all(abs(p["drill"] - 3.2) < 1e-6 for p in holes),
      "%d drilled pads; NPTH %s drill %s mm" % (len(all_drills), hole_refs, sorted({p["drill"] for p in holes})))
if os.path.isfile(DRL) and xs:
    d = open(DRL, encoding="utf-8", errors="replace").read()
    tools = re.findall(r'^T(\d+)C([\d.]+)', d, re.M)
    hits = [(float(a), float(b)) for a, b in re.findall(r'^X([-\d.]+)Y([-\d.]+)\s*$', d, re.M)]
    ox, oy = min(xs), min(ys)
    want = sorted((round(p["c"][0] - ox, 2), round(-(p["c"][1] - oy), 2)) for p in holes)
    got = sorted((round(a, 2), round(b, 2)) for a, b in hits)
    check("REQ-027 drill file has the same 4 holes as the board", got == want and all(abs(float(c) - 3.2) < 1e-6 for _, c in tools) and len(tools) == 1,
          "tools %s; drill hits %s; board holes %s" % (tools, got, want))
else:
    check("REQ-027 drill file has the same 4 holes as the board", False, "drill file or outline not found: %s" % DRL)

# ---- REQ-027: wire links --------------------------------------------------------------------------------------
# Every multi-pad net must be a single copper island on F.Cu, so nothing needs a bridge. The only open connection is by
# design: J1 (SCL, SDA) to two pads of J3 (S1..S7), the 2 I2C configuration links. JP1 is a solder bridge on etched pads.
parent = list(range(len(items)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        if items[i].net and items[i].net == items[j].net and dist(items[i], items[j]) <= 1e-6:
            parent[find(i)] = find(j)
# Same-numbered pads of a part flagged duplicate_pad_numbers_are_jumpers (SW1: the switch joins them inside) count as one node, as in KiCad.
anchors = []
for r, f in fps.items():
    if f["joined_dups"]:
        for num in {p["num"] for p in f["pads"]}:
            idx = [k for k, p in enumerate(copper_pads) if p["ref"] == r and p["num"] == num]
            for k in idx[1:]:
                anchors.append(items[k].desc)
                parent[find(idx[0])] = find(k)
nets = {}
for i, it in enumerate(items):
    if it.net and not it.net.startswith("unconnected"):
        nets.setdefault(it.net, set()).add(find(i))
multi = {n for n in nets if sum(1 for p in copper_pads if p["net"] == n) >= 2}
split = sorted("%s(%d islands)" % (n, len(nets[n])) for n in multi if len(nets[n]) != 1)
check("REQ-027 every multi-pad net is one F.Cu island (no extra wire bridge needed)", not split and bool(multi),
      "%d multi-pad nets; split: %s; same-number pads joined inside the part only: %s" % (len(multi), split, sorted(anchors)))
j1 = sorted((p["num"], p["net"].lstrip("/")) for p in fps.get("J1", dict(pads=[]))["pads"])
j3 = sorted(p["net"].lstrip("/") for p in fps.get("J3", dict(pads=[]))["pads"])
link_fps = sorted(r for r in fps if re.match(r"(J|W|X|TP|BR)\d*$", r) or r.startswith("JP"))
check("REQ-027 wire links limited to the 2 I2C configuration links (J1 SCL/SDA to J3 S1..S7)",
      j1 == [("1", "SCL"), ("2", "SDA")] and j3 == ["S%d" % k for k in range(1, 8)] and link_fps == ["J1", "J2", "J3", "JP1"],
      "J1 %s; J3 %s; connection footprints %s (J2 = electrode wires, JP1 = solder bridge)" % (j1, j3, link_fps))

# ---- REQ-028 --------------------------------------------------------------------------------------------------
if edge:
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    check("REQ-028 board outline 100 x 70 mm", abs(w - 100) < 1e-6 and abs(h - 70) < 1e-6, "outline %.3f x %.3f mm (%d Edge.Cuts lines)" % (w, h, len(edge)))
else:
    check("REQ-028 board outline 100 x 70 mm", False, "no gr_line on Edge.Cuts found by parser")

# ---- REQ-029: tracks, clearance, edges, holes ---------------------------------------------------------------
POWER = {"GND", "+3V3", "/S1", "/S7"}
STUB_MAX = 6.0                       # mm; ASSUMPTION carried from sim/electronics/calc/check_smd.py (definition of "short stub")
widths = sorted(set(s["w"] for s in segments))
check("REQ-029 track width >= 0.8 mm everywhere", min(widths) >= 0.8 - 1e-9, "widths used %s mm" % widths)
weak = sorted({s["net"] for s in segments if s["net"] in POWER and s["w"] < 1.2 - 1e-9})
check("REQ-029 power tracks >= 1.2 mm", not weak, "power nets %s; below 1.2 mm: %s" % (sorted(POWER), weak))
narrow = [(s["net"], s["w"], round(math.hypot(s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]), 2)) for s in segments if s["w"] < 1.0 - 1e-9]
long_n = [n for n in narrow if n[2] > STUB_MAX + 1e-9]
check("REQ-029 signal tracks >= 1.0 mm except stubs <= %.1f mm" % STUB_MAX, not long_n,
      "%d segments below 1.0 mm, longest %.2f mm, nets %s; too long: %s" % (len(narrow), max([n[2] for n in narrow] or [0]), sorted({n[0] for n in narrow}), long_n))
worst = (1e9, "", "")
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i], items[j]
        if a.net != b.net or not a.net:
            d = dist(a, b)
            if d < worst[0]: worst = (d, a.desc + " [" + a.net + "]", b.desc + " [" + b.net + "]")
check("REQ-029 copper clearance >= 0.6 mm between different nets (pads and tracks)", worst[0] >= 0.6 - 1e-6,
      "minimum %.3f mm between %s and %s (etched text excluded, see DRC)" % worst)
SEGS_EDGE = [((min(xs), min(ys)), (max(xs), min(ys))), ((max(xs), min(ys)), (max(xs), max(ys))), ((max(xs), max(ys)), (min(xs), max(ys))), ((min(xs), max(ys)), (min(xs), min(ys)))] if xs else []
e_w = min((min(seg_seg(a, b, c, d) for a, b in it.segs for c, d in SEGS_EDGE) - it.r, it.desc) for it in items) if xs else (float("nan"), "")
check("REQ-029 copper >= 0.5 mm from the board edge (min_copper_edge_clearance, hardware/frutamidi.kicad_pro)", e_w[0] >= 0.5 - 1e-6, "minimum %.3f mm at %s" % e_w)
h_w = []
for p in holes:
    hole = Item("hole", "", p["ref"], [(p["c"], p["c"])], p["drill"] / 2)
    h_w.append(min((dist(hole, it), it.desc) for it in items) + (p["ref"],))
check("REQ-029 remaining holes: drill >= 0.8 mm, copper >= 0.5 mm from the hole edge (min_hole_clearance, frutamidi.kicad_pro)",
      all(p["drill"] >= 0.8 for p in holes) and min(x[0] for x in h_w) >= 0.5 - 1e-6,
      "per hole (nearest copper): %s" % ", ".join("%s %.2f mm to %s" % (x[2], x[0], x[1]) for x in h_w))
HEAD_R = (2.8, 3.5)   # mm; ASSUMPTION, M3 pan-head and washer radii, same values as sim/electronics/calc/check_gap.py (e)
print("INFO  M3 metal head/washer overlap, nearest copper from hole centre minus radius %s mm: %s" % (HEAD_R, ", ".join(
      "%s head %+.2f / washer %+.2f mm" % (x[2], x[0] + 1.6 - HEAD_R[0], x[0] + 1.6 - HEAD_R[1]) for x in h_w)))

# ---- REQ-029: SMD lands -------------------------------------------------------------------------------------
LAND_MIN = 1.0                       # mm in both directions: the signal-track width of REQ-029 (undercut)
small = sorted({(p["fp"].split(":")[1], p["sx"], p["sy"]) for p in copper_pads if min(p["sx"], p["sy"]) < LAND_MIN - 1e-9})
check("REQ-029 every SMD land >= %.1f mm in both directions" % LAND_MIN, not small and bool(copper_pads),
      "smallest land %.2f mm; below the rule: %s" % (min(min(p["sx"], p["sy"]) for p in copper_pads), small))
LANDS = {"A1": (40, (4.2, 1.6)), "A2": (20, (1.8, 2.4)), "J3": (7, (1.8, 1.8)), "J1": (2, (2.2, 2.2)), "RV1": (3, (3.0, 3.0)), "SW1": (4, (1.55, 1.3)),
         "C1": (2, (1.15, 1.8)), "R13": (2, (1.15, 1.8)), "R14": (2, (1.15, 1.8)), "R15": (2, (1.15, 1.8)), "R16": (2, (1.15, 1.8))}
for r in range(1, 13): LANDS["R%d" % r] = (2, (1.9, 3.35))
bad = []
for ref, (n, size) in sorted(LANDS.items()):
    ps = fps.get(ref, dict(pads=[]))["pads"]
    if len(ps) != n or any((p["sx"], p["sy"]) != size for p in ps):
        bad.append((ref, len(ps), sorted({(p["sx"], p["sy"]) for p in ps})))
check("REQ-029 land sizes match the v1.3 table (A1, A2, J1, J3, RV1, SW1, C1, R1..R16)", not bad, "%d parts compared; mismatches: %s" % (len(LANDS), bad))
if len(keepouts) == 2:
    viol = []
    for z in keepouts:
        pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', z)]
        ko = Item("ko", "", "keepout", list(zip(pts, pts[1:] + pts[:1])), 0.0, pts)
        for it in items:
            if dist(ko, it) <= 1e-6: viol.append(it.desc)
    check("REQ-029 no bare copper in the 2 Pico keep-out rule areas", not viol, "2 keep-out polygons; copper inside: %s" % viol)
else:
    check("REQ-029 no bare copper in the 2 Pico keep-out rule areas", False, "expected 2 keep-out rule areas, found %d" % len(keepouts))

# ---- REQ-023: R1-R12 land gap -------------------------------------------------------------------------------
R_EL_FP = "R_2512_HomeEtch_G5.0mm"   # T-098; the YAGEO RC2512FK-073K3L (ADR-026) sits on the unchanged 2512 land
bad_fp = sorted(r for r in ("R%d" % k for k in range(1, 13)) if fps.get(r, dict(name=""))["name"].split(":")[-1] != R_EL_FP)
check("ADR-026 R1-R12 on footprint %s" % R_EL_FP, not bad_fp, "R1..R12 not on it: %s" % bad_fp)
gaps = {}
for r in range(1, 13):
    ps = fps.get("R%d" % r, dict(pads=[]))["pads"]
    gaps["R%d" % r] = round(dist(pad_item(ps[0]), pad_item(ps[1])), 3) if len(ps) == 2 else None
check("REQ-023 R1-R12 land gap >= 3.5 mm (4 kV rule) and = 5.0 mm (ADR-023)", all(g is not None and abs(g - 5.0) < 0.01 for g in gaps.values()),
      "land gaps %s mm" % sorted(set(gaps.values()), key=str))

# ---- ADR-021: JP1 and J2 ------------------------------------------------------------------------------------
if "JP1" in fps:
    ps = sorted(fps["JP1"]["pads"], key=lambda q: q["num"])
    ok_type = len(ps) == 3 and all(p["typ"] == "smd" and p["drill"] is None and (p["sx"], p["sy"]) == (1.94, 2.4) for p in ps)
    gp = [round(dist(pad_item(a), pad_item(b)), 3) for a, b in zip(ps, ps[1:])]
    pitch = [round(math.hypot(b["c"][0] - a["c"][0], b["c"][1] - a["c"][1]), 3) for a, b in zip(ps, ps[1:])]
    check("ADR-021/ADR-023 JP1 is a 3-pad SMD bridge, pads 1.94 x 2.4 mm, pitch 3.81 mm, gap >= 1.8 mm",
          ok_type and min(gp) >= 1.8 - 1e-9 and all(abs(q - 3.81) < 1e-6 for q in pitch),
          "%s: types %s, pitch %s mm, gaps %s mm" % (fps["JP1"]["name"].split(":")[1], sorted({p["typ"] for p in ps}), pitch, gp))
else:
    check("ADR-021/ADR-023 JP1 is a 3-pad SMD bridge, pads 1.94 x 2.4 mm, pitch 3.81 mm, gap >= 1.8 mm", False, "JP1 not found")
if "J2" in fps:
    ps = sorted(fps["J2"]["pads"], key=lambda q: int(q["num"]))
    sizes = sorted({(q["sx"], q["sy"]) for q in ps})
    pitch = sorted({round(b["c"][0] - a["c"][0], 3) for a, b in zip(ps, ps[1:])})
    ok = len(ps) == 14 and sizes == [(3.0, 4.5)] and all(q["typ"] == "smd" and q["drill"] is None for q in ps) and pitch == [5.08]
    check("ADR-023 J2 is 14 SMD solder-wire pads 3.0 x 4.5 mm at 5.08 mm pitch", ok,
          "%d pads, sizes %s, types %s, shapes %s, pitch %s mm" % (len(ps), sizes, sorted({q["typ"] for q in ps}), sorted({q["shape"] for q in ps}), pitch))
else:
    check("ADR-023 J2 is 14 SMD solder-wire pads 3.0 x 4.5 mm at 5.08 mm pitch", False, "J2 not found")

# ---- ADR-020: spark gap -------------------------------------------------------------------------------------
# Every electrode pad of J2 shall be 1.40 +/- 0.05 mm (copper edge to copper edge) from the nearest GND track, and that
# track shall be the board-edge GND track. A larger gap removes the intended arc path; a smaller one may close when etched.
SPARK_NOM, SPARK_TOL = 1.40, 0.05
gnd = [(seg_item(s, k), s) for k, s in enumerate(segments) if s["net"] == "GND" and s["layer"] == "F.Cu"]
edge_y = max(ys) if ys else None
sg = []
if "J2" in fps and gnd:
    for p in fps["J2"]["pads"]:
        if not re.fullmatch(r"/?E\d+", p["net"]): continue
        pit = pad_item(p)
        d, _, s = min(((dist(pit, g), k, g2) for k, (g, g2) in enumerate(gnd)), key=lambda q: (q[0], q[1]))
        on_edge = edge_y is not None and abs(s["a"][1] - s["b"][1]) < 1e-6 and edge_y - s["a"][1] < 3.0
        sg.append((p["net"].lstrip("/"), round(d, 3), on_edge))
    sg.sort(key=lambda g: int(g[0][1:]))
    okall = len(sg) == 12 and all(abs(g[1] - SPARK_NOM) <= SPARK_TOL + 1e-9 and g[2] for g in sg)
    check("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", okall,
          "%d electrode pads; gap min %.3f / max %.3f mm; nearest GND track is the edge track for %d of %d; per pad %s"
          % (len(sg), min(g[1] for g in sg), max(g[1] for g in sg), sum(g[2] for g in sg), len(sg), ", ".join("%s=%.3f" % (g[0], g[1]) for g in sg)))
else:
    check("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", False, "J2 or GND tracks not found by parser")

# ---- information for REQ-038 --------------------------------------------------------------------------------
i2c = [it for it in items if it.net.lstrip("/") in ("SDA", "SCL", "SDA_PICO", "SCL_PICO")]
ele = [it for it in items if re.fullmatch(r"/?(ELE|E)\d+", it.net)]
if i2c and ele:
    d = min((dist(a, b), a.desc + " [" + a.net + "]", b.desc + " [" + b.net + "]") for a in i2c for b in ele)
    print("INFO  nearest I2C copper to electrode copper (REQ-038): %.2f mm between %s and %s" % d)
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(res), res.count(True), res.count(False)))
sys.exit(0 if all(res) else 1)
