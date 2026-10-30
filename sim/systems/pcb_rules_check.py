"""T-008 inspection of hardware/frutamidi.kicad_pcb against the proposed home-etch requirements
(REQ-027..REQ-029). Read-only parse of the KiCad file; this is not a DRC replacement."""
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

# Annular ring per pad: (min(size) - drill) / 2 ; rule from gen_pcb.py docstring: ring >= 0.4 mm
worst = {}
for fp in re.finditer(r'\n\t\(footprint "([^"]+)"(.*?)\n\t\)', t, re.S):
    name = fp.group(1)
    for m in re.finditer(r'\(pad "([^"]*)" thru_hole (\w+).*?\(size ([\d.]+) ([\d.]+)\)\s*\(drill (?:oval )?([\d.]+)', fp.group(2), re.S):
        num, shape, sx, sy, dr = m.groups()
        ring = (min(float(sx), float(sy)) - float(dr)) / 2
        key = name.split(":")[1]
        if key not in worst or ring < worst[key][0]:
            worst[key] = (ring, "pad %s %s %sx%s drill %s" % (num, shape, sx, sy, dr))
for k, (ring, d) in sorted(worst.items()):
    check("REQ-029 annular ring >= 0.4 mm [%s]" % k, ring >= 0.4 - 1e-9, "min ring %.2f mm (%s)" % (ring, d))
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(res), res.count(True), res.count(False)))
