import sys; sys.path.insert(0,'.')
from geom import *
pcb,fps,segs,grs,zones,items=load_items('/Users/rod/fruta-midi-controller/hardware/frutamidi.kicad_pcb')
feats=[('A',7.775,49.5,1.1,1.8),('B',13.225,49.5,1.1,1.8),('C',8.075,46.47,1.05,1.45),('D',12.925,46.47,1.05,1.45),
 ('TP9.5,49.8',9.5,49.8,1.5,1.5),('TP11.5,49.8',11.5,49.8,1.5,1.5),('TP10.5,46.5',10.5,46.5,1.5,1.5),
 ('TP8,43',8,43,1.5,1.5),('TP8,40.5',8,40.5,1.5,1.5),('TP8,38',8,38,1.5,1.5),('TP7 11.5,30.5',11.5,30.5,1.5,1.5),
 ('SWD block',10.5,0.9,6.68,1.8)]
for dx,dy in [(0,0),(0.8,0),(-0.8,0),(0,0.8),(0,-0.8)]:
    worst=(99,None,None)
    for n,X,Y,w,h in feats:
        bx=54.5+(X-1.61)+dx; by=51.48+(51-Y-1.37)+dy
        f=Item('f',[(bx-w/2,by-h/2),(bx+w/2,by-h/2),(bx+w/2,by+h/2),(bx-w/2,by+h/2)],0,'x',n)
        for it in items:
            if it.label.startswith('A1.'): continue
            d=dist(f,it)
            if d<worst[0]: worst=(d,n,it.label)
    print(f"origin shift ({dx},{dy}) mm: worst feature-to-copper {worst[0]:.2f} mm  {worst[1]} vs {worst[2]}")
