# Independent reviewer T-079: dump pad copper geometry (incl. offsets), courtyards and tracks. Read-only.
import pcbnew,sys,math
b=pcbnew.LoadBoard(sys.argv[1]); T=1e-6
o=b.GetDesignSettings().GetAuxOrigin(); ox,oy=o.x*T,o.y*T
print("KiCad",pcbnew.Version())
for fp in b.GetFootprints():
    r=fp.GetReference()
    cy=fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else None
    cys = "(%.2f,%.2f)-(%.2f,%.2f)"%(cy.GetLeft()*T-ox,cy.GetTop()*T-oy,cy.GetRight()*T-ox,cy.GetBottom()*T-oy) if cy else "none"
    print(r, fp.GetFPIDAsString(), fp.GetValue(), "pos(%.2f,%.2f) rot %.0f"%(fp.GetPosition().x*T-ox,fp.GetPosition().y*T-oy,fp.GetOrientationDegrees()), "crtyd",cys)
    if r in ("C1","RV1","JP1","J2","A1") or r.startswith("R1") and len(r)==3:
        for p in fp.Pads():
            bb=p.GetBoundingBox()
            if r=="A1" and p.GetNumber() not in ("33","34","35","36"): continue
            print("    pad %s %s hole(%.2f,%.2f) drill %.2f copper bbox (%.2f,%.2f)-(%.2f,%.2f) shape %s"%(p.GetNumber(),p.GetNetname(),
                p.GetPosition().x*T-ox,p.GetPosition().y*T-oy,p.GetDrillSizeX()*T,bb.GetLeft()*T-ox,bb.GetTop()*T-oy,bb.GetRight()*T-ox,bb.GetBottom()*T-oy,p.GetShape()))
print("TRACKS")
for t in b.GetTracks():
    print("  %-10s w%.2f (%.2f,%.2f)-(%.2f,%.2f)"%(t.GetNetname(),t.GetWidth()*T,t.GetStart().x*T-ox,t.GetStart().y*T-oy,t.GetEnd().x*T-ox,t.GetEnd().y*T-oy))
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.Edge_Cuts:
        print("  EDGE (%.2f,%.2f)-(%.2f,%.2f)"%(d.GetStart().x*T-ox,d.GetStart().y*T-oy,d.GetEnd().x*T-ox,d.GetEnd().y*T-oy))
