import sys; sys.path.insert(0,'.')
from geom import *
pcb,fps,segs,grs,zones,items=load_items('/Users/rod/fruta-midi-controller/hardware/frutamidi.kicad_pcb')
for i,s in enumerate(segs): print(i, s['net'], s['w'], (s['x1'],s['y1']),(s['x2'],s['y2']))
