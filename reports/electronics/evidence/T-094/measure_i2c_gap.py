#!/usr/bin/env python3
"""T-094: measure, on the generated board, the smallest edge-to-edge distance from every I2C track to the A2 electrode pads.
Run with KiCad Python. CALCULATION (design file)."""
import math
import pcbnew

b = pcbnew.LoadBoard("/Users/rod/fruta-midi-controller/hardware/frutamidi.kicad_pcb")


def pad_rect(p):
    c, s = p.GetPosition(), p.GetSize()
    return pcbnew.ToMM(c.x), pcbnew.ToMM(c.y), pcbnew.ToMM(s.x) / 2, pcbnew.ToMM(s.y) / 2


def seg_rect_gap(ax, ay, bx, by, w, cx, cy, hw, hh):
    # sampled distance, track as a segment of half width w/2
    n = max(2, int(math.hypot(bx - ax, by - ay) / 0.02))
    best = 1e9
    for i in range(n + 1):
        t = i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        dx = max(abs(x - cx) - hw, 0)
        dy = max(abs(y - cy) - hh, 0)
        best = min(best, math.hypot(dx, dy))
    return best - w / 2


fp = b.FindFootprintByReference("A2")
pads = {p.GetNumber(): pad_rect(p) for p in fp.Pads()}
e_pads = {str(i): pads[str(i)] for i in range(2, 14)}   # module pins 2..13 = E0..E11
nets = {}
for t in b.GetTracks():
    if not isinstance(t, pcbnew.PCB_TRACK) or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    nets.setdefault(t.GetNetname(), []).append(t)

print("# measure_i2c_gap.py  CALCULATION (design file) on hardware/frutamidi.kicad_pcb")
for name in sorted(nets):
    if "SDA" not in name and "SCL" not in name:
        continue
    best = (1e9, None)
    for t in nets[name]:
        ax, ay = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        bx, by = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
        w = pcbnew.ToMM(t.GetWidth())
        for pn, (cx, cy, hw, hh) in e_pads.items():
            g = seg_rect_gap(ax, ay, bx, by, w, cx, cy, hw, hh)
            if g < best[0]:
                best = (g, pn)
    print("net %-10s smallest gap to any E0-E11 pad of A2: %.3f mm (pad %s)" % (name, best[0], best[1]))
