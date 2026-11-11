import sys; sys.path.insert(0,'.')
from sx import *
pcb, fps, segs, grs, zones, vias = load('/Users/rod/fruta-midi-controller/hardware/frutamidi.kicad_pcb')
for f in fps:
    print(f"FP {f['ref']} {f['lib']} at ({f['x']},{f['y']}) rot {f['rot']} npads={len(f['pads'])}")
    for p in f['pads']:
        print(f"   pad {p['num']:>3} {p['type']:8} {p['shape']:9} ({p['x']:.3f},{p['y']:.3f}) {p['w']}x{p['h']} r{p['rot']} {p['layers']} net={p['net']} rr={p['rr']}")
print('segments', len(segs), 'layers', set(s['layer'] for s in segs), 'widths', sorted(set(s['w'] for s in segs)))
print('vias', len(vias))
for k,l,g in grs:
    if l in ('Edge.Cuts','F.Cu','B.Cu'):
        print(k,l,[x for x in g[1:] if isinstance(x,list) and x[0] in ('start','end','at','center','pts','width','stroke')][:4] if k!='gr_text' else g[1])
