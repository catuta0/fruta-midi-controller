import sys; sys.path.insert(0,'.')
from geom import *
pcb,fps,segs,grs,zones,items=load_items(sys.argv[1])
res=[]
for a,b in itertools.combinations(items,2):
    if a.net==b.net and a.net and not a.net.startswith('unconnected'): continue
    d=dist(a,b); res.append((d,a.label,b.label))
res.sort()
print("min different-net copper gaps (mm, CALCULATION):")
for r in res[:40]: print(f"  {r[0]:.3f}  {r[1]}  <->  {r[2]}")
print("count < 0.6:", sum(1 for r in res if r[0]<0.6-1e-6), " count < 0.5:", sum(1 for r in res if r[0]<0.5-1e-6))
# edges
E=[((50,50),(150,50)),((150,50),(150,120)),((150,120),(50,120)),((50,120),(50,50))]
ed=[]
for it in items:
    d=min(segdist(e[0],e[1],x[0],x[1]) for e in E for x in it.edges())-it.r
    ed.append((d,it.label))
ed.sort(); print("min copper-to-board-edge (mm, CALCULATION):")
for r in ed[:12]: print(f"  {r[0]:.3f} {r[1]}")
tw=sorted(set((s['w'],s['net']) for s in segs)); 
print("track widths by net:"); 
from collections import defaultdict
d=defaultdict(set)
for s in segs: d[s['w']].add(s['net'])
for w in sorted(d): print(" ",w,sorted(d[w]))
