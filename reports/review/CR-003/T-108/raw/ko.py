import sys; sys.path.insert(0,'.')
from geom import *
pcb,fps,segs,grs,zones,items=load_items('/Users/rod/fruta-midi-controller/hardware/frutamidi.kicad_pcb')
for z in zones:
    pts=[(float(p[1]),float(p[2])) for p in walk(z,'xy')]
    zi=Item('z',pts,0,'ko','ko')
    best=min((dist(zi,it),it.label) for it in items)
    print('keepout',pts[0],pts[2],'nearest copper %.2f mm'%best[0],best[1])
# A2 lands vs module outline and pin positions
for f in fps:
    if f['ref']=='A2':
        for p in f['pads']:
            n=int(p['num']); y0,y1=p['y']-p['h']/2,p['y']+p['h']/2
            out = y1-77.17 if n<=13 else 58.12-y0
            pin_y = 67.645+8.255 if n<=13 else 67.645-6.985
            edge_to_pin = abs((77.17 if n<=13 else 58.12)-pin_y)
            if n in (1,13,14,20): print(f"A2.{n} land y {y0:.3f}..{y1:.3f}  beyond outline {out:.3f} mm  pin centre {edge_to_pin:.3f} mm inside outline")
