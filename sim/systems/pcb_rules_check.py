"""T-008 inspection of hardware/frutamidi.kicad_pcb against the proposed home-etch requirements
(REQ-027..REQ-029) and the ADR-021 JP1/J2 pad rules (T-077). Read-only parse of the KiCad file; this is not a DRC replacement."""
import os, re, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
t = open(os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb"), encoding="utf-8").read()
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
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(res), res.count(True), res.count(False)))
