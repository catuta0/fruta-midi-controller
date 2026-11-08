"""T-076 MEASUREMENT on the design file: JP1 pad gaps, J2 pad shape and gaps, C1/RV1 copper neighbours."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
T = 1e-6
fps = {f.GetReference(): f for f in b.GetFootprints()}
def poly(item):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, pcbnew.B_Cu, 0, 1000, pcbnew.ERROR_INSIDE)
    return ps
def gap(a, b_):
    pa, pb = poly(a), poly(b_)
    # edge-to-edge: min over the vertices of one outline to the other outline (maxError 1 um polygons)
    sa = pa.Outline(0); sb = pb.Outline(0)
    best = min(sa.SquaredDistance(sb.CPoint(k)) for k in range(sb.PointCount())) ** 0.5
    best = min(best, min(sb.SquaredDistance(sa.CPoint(k)) for k in range(sa.PointCount())) ** 0.5)
    return best * T
jp = {p.GetNumber(): p for p in fps["JP1"].Pads()}
print("JP1 pad centres (mm, board):", [(n, round(p.GetPosition().x*T-50, 2), round(p.GetPosition().y*T-50, 2)) for n, p in sorted(jp.items())])
print("JP1 copper gap pad1-pad2 %.2f mm, pad2-pad3 %.2f mm, pad1-pad3 %.2f mm" % (gap(jp["1"], jp["2"]), gap(jp["2"], jp["3"]), gap(jp["1"], jp["3"])))
j2 = {p.GetNumber(): p for p in fps["J2"].Pads()}
p2 = j2["2"]
bb = p2.GetBoundingBox()
print("J2 pad 2 size %.2f x %.2f mm, drill %.2f, hole y %.2f, copper y %.2f..%.2f" % (
    p2.GetSize(pcbnew.F_Cu).x*T, p2.GetSize(pcbnew.F_Cu).y*T, p2.GetDrillSize().x*T, p2.GetPosition().y*T-50, bb.GetTop()*T-50, bb.GetBottom()*T-50))
print("J2 adjacent pad gap (2-3) %.2f mm" % gap(j2["2"], j2["3"]))
# J2 pad to GND edge track and to R pads
for t in b.GetTracks():
    if t.GetNetname() == "GND" and abs(t.GetStart().y - t.GetEnd().y) < 10 and abs(t.GetStart().y*T - 50 - 68.0) < 1e-3 \
            and abs(t.GetStart().x - t.GetEnd().x) > 10**7:
        edge = t
print("J2 pad 2 (E0) to GND edge track %.2f mm" % gap(j2["2"], edge))
r1 = {p.GetNumber(): p for p in fps["R1"].Pads()}; r2 = {p.GetNumber(): p for p in fps["R2"].Pads()}
print("J2 pad 2 (E0) to R1 pad 2 (E0, same net) %.2f mm; J2 pad 3 (E1) to R1 pad 2 (E0) %.2f mm; J2 pad 2 to R2 pad 2 (E1) %.2f mm"
      % (gap(j2["2"], r1["2"]), gap(j2["3"], r1["2"]), gap(j2["2"], r2["2"])))
c1 = {p.GetNumber(): p for p in fps["C1"].Pads()}
rv = list(fps["RV1"].Pads())
print("C1 pads:", [(n, p.GetNetname(), round(p.GetPosition().x*T-50, 2), round(p.GetPosition().y*T-50, 2)) for n, p in sorted(c1.items())])
print("RV1 pads:", [(p.GetNumber(), p.GetNetname()) for p in rv])
