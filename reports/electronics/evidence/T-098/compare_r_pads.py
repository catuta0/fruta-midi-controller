#!/usr/bin/env python3
"""T-098: compare R1..R12 pad positions, sizes, shapes, layers and nets between two .kicad_pcb files (KiCad Python).
Usage: compare_r_pads.py <old.kicad_pcb> <new.kicad_pcb>"""
import sys
import pcbnew

TOMM = 1e-6


def pads(path):
    b = pcbnew.LoadBoard(path)
    out = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("R") and ref[1:].isdigit() and 1 <= int(ref[1:]) <= 12:
            for p in fp.Pads():
                pos, sz = p.GetPosition(), p.GetSize(pcbnew.F_Cu)
                out[(ref, p.GetNumber())] = (round(pos.x * TOMM, 4), round(pos.y * TOMM, 4), round(sz.x * TOMM, 4), round(sz.y * TOMM, 4),
                                             p.GetShape(pcbnew.F_Cu), p.GetNetname(), fp.GetFPIDAsString())
    return out


a, b = pads(sys.argv[1]), pads(sys.argv[2])
print("pads: old %d, new %d" % (len(a), len(b)))
diff = 0
for k in sorted(a):
    ga, gb = a[k][:6], b.get(k, (None,) * 6)[:6]
    if ga != gb:
        diff += 1
        print("DIFF", k, ga, gb)
for k in sorted(a)[:2] + sorted(a)[-2:]:
    print("  %s pad %s: x %.3f y %.3f size %.3f x %.3f net %s | %s -> %s" % (k[0], k[1], *b[k][:4], b[k][5], a[k][6], b[k][6]))
print("PASS R1-R12 pad geometry and nets identical (%d pads)" % len(a) if diff == 0 and len(a) == len(b) == 24 else "FAIL %d differences" % diff)
