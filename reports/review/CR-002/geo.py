import pcbnew,sys,math
b=pcbnew.LoadBoard(sys.argv[1]); T=1e-6
o=b.GetDesignSettings().GetAuxOrigin(); ox,oy=o.x*T,o.y*T
print("KiCad",pcbnew.Version())
for fp in b.GetFootprints():
    r=fp.GetReference()
    pads=[(p.GetNumber(),round(p.GetPosition().x*T-ox,3),round(p.GetPosition().y*T-oy,3),p.GetNetname(),round(p.GetSizeX()*T,2),round(p.GetDrillSizeX()*T,2)) for p in fp.Pads()]
    cy=fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else None
    cys = "(%.2f,%.2f)-(%.2f,%.2f)"%(cy.GetLeft()*T-ox,cy.GetTop()*T-oy,cy.GetRight()*T-ox,cy.GetBottom()*T-oy) if cy else "none"
    print(r, fp.GetFPIDAsString(), "pos(%.2f,%.2f) rot %.0f"%(fp.GetPosition().x*T-ox,fp.GetPosition().y*T-oy,fp.GetOrientationDegrees()), "crtyd",cys)
    if r[0] in "RJH" or r in("JP1",):
        for q in pads[:16]: print("   ",q)
print("TRACKS")
for t in b.GetTracks():
    print("  %-28s w%.2f (%.2f,%.2f)-(%.2f,%.2f)"%(t.GetNetname(),t.GetWidth()*T,t.GetStart().x*T-ox,t.GetStart().y*T-oy,t.GetEnd().x*T-ox,t.GetEnd().y*T-oy))
