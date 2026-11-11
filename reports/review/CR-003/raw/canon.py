import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); T = pcbnew.ToMM; out = []
for fp in b.GetFootprints():
    out.append("FP %s %s %.3f %.3f %.1f %s" % (fp.GetReference(), fp.GetFPIDAsString(), T(fp.GetPosition().x), T(fp.GetPosition().y), fp.GetOrientationDegrees(), fp.GetValue()))
    for p in fp.Pads():
        s = p.GetSize(pcbnew.F_Cu)
        out.append("PAD %s.%s %.3f %.3f %.3f %.3f %s %s drill=%.2f" % (fp.GetReference(), p.GetNumber(), T(p.GetPosition().x), T(p.GetPosition().y), T(s.x), T(s.y), p.GetNetname(), p.GetLayerSet().FmtHex(), T(p.GetDrillSize().x)))
for t in b.GetTracks():
    out.append("TRK %s %.3f %.3f %.3f %.3f %.2f %s" % (t.GetClass(), T(t.GetStart().x), T(t.GetStart().y), T(t.GetEnd().x), T(t.GetEnd().y), T(t.GetWidth()), t.GetNetname()))
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT": out.append("TXT %s %s %.2f %.2f" % (d.GetLayerName(), d.GetText(), T(d.GetPosition().x), T(d.GetPosition().y)))
print("\n".join(sorted(out)))
