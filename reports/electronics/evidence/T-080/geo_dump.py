import pcbnew, sys
b=pcbnew.LoadBoard(sys.argv[1]); M=pcbnew.ToMM; out=[]
for fp in b.GetFootprints():
    for p in fp.Pads():
        out.append("pad %s %s %.3f %.3f %.3f %.3f %.3f %s"%(fp.GetReference(),p.GetNumber(),M(p.GetPosition().x),M(p.GetPosition().y),M(p.GetSize(pcbnew.F_Cu).x),M(p.GetSize(pcbnew.F_Cu).y),M(p.GetDrillSize().x),p.GetNetname()))
    for m in fp.Models(): out.append("model %s %s %.4f %.4f %.4f"%(fp.GetReference(),m.m_Filename,m.m_Scale.x,m.m_Scale.y,m.m_Scale.z))
for t in b.GetTracks():
    out.append("trk %.3f %.3f %.3f %.3f %.3f %s"%(M(t.GetStart().x),M(t.GetStart().y),M(t.GetEnd().x),M(t.GetEnd().y),M(t.GetWidth()),t.GetNetname()))
for d in b.GetDrawings():
    bb=d.GetBoundingBox(); out.append("drw %s %.3f %.3f %.3f %.3f"%(d.GetLayerName(),M(bb.GetLeft()),M(bb.GetTop()),M(bb.GetRight()),M(bb.GetBottom())))
print("\n".join(sorted(out)))
