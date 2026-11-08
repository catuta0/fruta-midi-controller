"""T-008 inspection of hardware/frutamidi.kicad_pcb against the proposed home-etch requirements
(REQ-027..REQ-029), the ADR-021 JP1/J2 pad rules (T-077) and the ADR-020 Ex <-> GND edge-track spark gap (T-081, F2-006).
Read-only parse of the KiCad file; this is not a DRC replacement.
Usage: python3 sim/systems/pcb_rules_check.py [path/to/board.kicad_pcb]   (default hardware/frutamidi.kicad_pcb)"""
import math, os, re, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
t = open(PCB, encoding="utf-8").read()
res = []
def check(n, ok, d):
    res.append(ok); print("%s  %s :: %s" % ("PASS" if ok else "FAIL", n, d))

segs = re.findall(r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)', t)
layers = sorted(set(s[5] for s in segs))
widths = sorted(set(float(s[4]) for s in segs))
check("REQ-027 tracks only on B.Cu", layers == ["B.Cu"], "%d segments, layers %s" % (len(segs), layers))
check("REQ-027 no vias", "(via " not in t and "(via\n" not in t, "via objects: %d" % len(re.findall(r'\n\t\(via', t)))
zones = len(re.findall(r'\n\t\(zone', t))
check("REQ-027 no copper zones (no ground pour)", zones == 0, "zones: %d" % zones)
smd = re.findall(r'\(pad "[^"]*" smd', t)
check("REQ-027 through-hole only (no SMD pads)", not smd, "smd pads: %d" % len(smd))
check("REQ-029 track width >= 0.8 mm (stubs) / signal 1.0 / power 1.2", min(widths) >= 0.8, "widths used %s mm" % widths)

edge = re.findall(r'\(gr_line\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\).*?\(layer "Edge.Cuts"\)', t, re.S)
xs = [float(v) for e in edge for v in (e[0], e[2])]; ys = [float(v) for e in edge for v in (e[1], e[3])]
if edge:
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    check("REQ-028 board outline 100 x 70 mm", abs(w - 100) < 1e-6 and abs(h - 70) < 1e-6, "outline %.3f x %.3f mm (%d Edge.Cuts lines)" % (w, h, len(edge)))
else:
    check("REQ-028 board outline 100 x 70 mm", False, "no gr_line on Edge.Cuts found by parser")

# Annular ring per pad, offset-aware (T-077: J2 drills are offset 0.75 mm in the 4.5 mm oval):
# ring = min((size_x - drill)/2 - |offset_x|, (size_y - drill)/2 - |offset_y|); rule from gen_pcb.py docstring: ring >= 0.4 mm
PAD_RE = re.compile(r'\(pad "([^"]*)" thru_hole (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\).*?\(size ([\d.]+) ([\d.]+)\)\s*'
                    r'\(drill (?:oval )?([\d.]+)(?:\s+\(offset ([-\d.]+) ([-\d.]+)\))?', re.S)
worst = {}
fps = {}
for fp in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', t, re.S):
    name = fp.group(1)
    ref = re.search(r'\(property "Reference" "([^"]+)"', fp.group(2)).group(1)
    fang = float((re.search(r'^\s*\(layer "[^"]+"\)\s*\(uuid "[^"]+"\)\s*\(at [-\d.]+ [-\d.]+(?: ([-\d.]+))?\)', fp.group(2)) or [None, None])[1] or 0)
    pads = []
    for m in PAD_RE.finditer(fp.group(2)):
        num, shape, px, py, pa, sx, sy, dr, ox, oy = m.groups()
        sx, sy, dr = float(sx), float(sy), float(dr)
        ox, oy = abs(float(ox or 0)), abs(float(oy or 0))
        ring = min((sx - dr) / 2 - ox, (sy - dr) / 2 - oy)
        pads.append(dict(num=num, shape=shape, x=float(px), y=float(py), rel=(float(pa or 0) - fang) % 180, sx=sx, sy=sy, dr=dr, oy=oy))
        key = name.split(":")[1]
        if key not in worst or ring < worst[key][0]:
            worst[key] = (ring, "pad %s %s %sx%s drill %s offset %s/%s" % (num, shape, sx, sy, dr, ox, oy))
    fps[ref] = (name, pads)
for k, (ring, d) in sorted(worst.items()):
    check("REQ-029 annular ring >= 0.4 mm [%s]" % k, ring >= 0.4 - 1e-9, "min ring %.2f mm (%s)" % (ring, d))

# JP1 3-pad solder jumper (T-077, ADR-021): copper gap between adjacent pads >= 1.8 mm, so that an accidental
# bridge across all three pads (3V3 to S1 and S7 together) is unlikely. Pads lie on the footprint-local x axis;
# extent along x is size_x when the pad is not rotated relative to the footprint, else size_y.
if "JP1" in fps:
    name, pads = fps["JP1"]
    pads = sorted(pads, key=lambda q: q["x"])
    ext = lambda q: q["sx"] if abs(q["rel"]) < 1e-6 or abs(q["rel"] - 180) < 1e-6 else q["sy"]
    gaps = [round((b["x"] - a["x"]) - (ext(a) + ext(b)) / 2, 3) for a, b in zip(pads, pads[1:])]
    pitch = [round(b["x"] - a["x"], 3) for a, b in zip(pads, pads[1:])]
    check("ADR-021 JP1 pad gap >= 1.8 mm", len(pads) == 3 and min(gaps) >= 1.8 - 1e-9,
          "%s: pitch %s mm, pad-to-pad copper gaps %s mm" % (name.split(":")[1], pitch, gaps))
else:
    check("ADR-021 JP1 pad gap >= 1.8 mm", False, "JP1 not found")

# J2 terminal pads (T-077, ADR-021): 3.0 x 4.5 mm oval/rect pads, 14 of them
if "J2" in fps:
    name, pads = fps["J2"]
    sizes = sorted({(q["sx"], q["sy"]) for q in pads})
    check("ADR-021 J2 pads 3.0 x 4.5 mm", len(pads) == 14 and sizes == [(3.0, 4.5)],
          "%d pads, sizes %s, shapes %s, drill offsets %s mm" % (len(pads), sizes, sorted({q["shape"] for q in pads}), sorted({q["oy"] for q in pads})))
else:
    check("ADR-021 J2 pads 3.0 x 4.5 mm", False, "J2 not found")
# Ex <-> GND edge-track spark gap (T-081, F2-006; ADR-020 / C2-005): every electrode terminal pad of J2 shall be
# 1.40 +/- 0.05 mm (copper edge to copper edge) from the nearest GND track. The gap is intentional: a strike on a
# terminal should arc to GND instead of reaching Rx and the MPR121 pin. DRC alone does not catch a change (a J2
# drill offset with the wrong sign gives 0.65 mm and still meets the 0.6 mm clearance rule).
# Geometry (KiCad convention): pad copper centre = pad position + drill offset (rotated with the pad); an oval pad is
# a stadium = core segment along its long axis with radius min(size)/2; a rect pad is approximated by its stadium
# (only used if an electrode pad is rect, which is reported); a track is a capsule = segment with radius width/2.
# distance(stadium, capsule) = segment-to-segment distance - r_pad - width/2 (exact for stadium and capsule).
SPARK_NOM, SPARK_TOL = 1.40, 0.05
def _rot(x, y, deg):
    a = math.radians(deg); return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)
def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
def _seg_seg(a, b, c, d):
    def orient(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0) and 0 not in (o1, o2, o3, o4): return 0.0
    return min(_pt_seg(a, c, d), _pt_seg(b, c, d), _pt_seg(c, a, b), _pt_seg(d, a, b))
fpm = None
for fp in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', t, re.S):
    if re.search(r'\(property "Reference" "J2"', fp.group(2)): fpm = fp
gnd_tracks = [tuple(map(float, m.groups()[:5])) for m in re.finditer(
    r'\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)\s+\(width ([\d.]+)\)\s+\(layer "B.Cu"\)\s+\(net "GND"\)', t)]
edge_y = max(ys) if edge else None
gaps = []
if fpm and gnd_tracks:
    body = fpm.group(2)
    fx, fy, fa = re.search(r'^\s*\(layer "[^"]+"\)\s*\(uuid "[^"]+"\)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', body).groups()
    fx, fy, fa = float(fx), float(fy), float(fa or 0)
    for m in re.finditer(r'\(pad "([^"]*)" thru_hole (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)(.*?)\(net "([^"]*)"\)', body, re.S):
        num, shape, px, py, pa, rest, net = m.groups()
        if not re.fullmatch(r"/?E\d+", net): continue
        sx, sy = map(float, re.search(r'\(size ([\d.]+) ([\d.]+)\)', rest).groups())
        off = re.search(r'\(offset ([-\d.]+) ([-\d.]+)\)', rest)
        ox, oy = (float(off.group(1)), float(off.group(2))) if off else (0.0, 0.0)
        pang = float(pa) if pa is not None else fa          # KiCad stores the absolute pad angle
        lx, ly = float(px), float(py)
        cx, cy = _rot(ox, oy, pang - fa); lx, ly = lx + cx, ly + cy  # shape centre in footprint frame
        gx, gy = _rot(lx, ly, fa); cxy = (fx + gx, fy + gy)
        r, half = min(sx, sy) / 2, (max(sx, sy) - min(sx, sy)) / 2
        ux, uy = _rot(*((1.0, 0.0) if sx >= sy else (0.0, 1.0)), pang)
        a, b = (cxy[0] - half * ux, cxy[1] - half * uy), (cxy[0] + half * ux, cxy[1] + half * uy)
        best = min(((_seg_seg(a, b, (x1, y1), (x2, y2)) - r - w / 2), (x1, y1, x2, y2, w)) for x1, y1, x2, y2, w in gnd_tracks)
        on_edge = edge_y is not None and abs(best[1][1] - best[1][3]) < 1e-6 and edge_y - best[1][1] < 3.0
        gaps.append((net.lstrip("/"), num, shape, round(best[0], 3), on_edge))
    gaps.sort(key=lambda g: int(g[0][1:]))
    okall = len(gaps) == 12 and all(abs(g[3] - SPARK_NOM) <= SPARK_TOL + 1e-9 and g[4] for g in gaps)
    check("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", okall,
          "%d electrode pads; gap min %.3f / max %.3f mm; nearest GND track is the edge track for %d of %d; per pad %s"
          % (len(gaps), min(g[3] for g in gaps) if gaps else float("nan"), max(g[3] for g in gaps) if gaps else float("nan"),
             sum(g[4] for g in gaps), len(gaps), ", ".join("%s=%.3f" % (g[0], g[3]) for g in gaps)))
else:
    check("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", False, "J2 or GND tracks not found by parser")
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(res), res.count(True), res.count(False)))
