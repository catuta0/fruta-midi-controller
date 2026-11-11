import sys, math, itertools; sys.path.insert(0,'.')
from sx import *

def segdist(p1,p2,q1,q2):
    def ptseg(p,a,b):
        ax,ay=a; bx,by=b; px,py=p
        dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
        t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
        return math.hypot(px-ax-t*dx,py-ay-t*dy)
    def ccw(a,b,c): return (c[1]-a[1])*(b[0]-a[0])-(b[1]-a[1])*(c[0]-a[0])
    def inter(a,b,c,d):
        d1,d2,d3,d4=ccw(c,d,a),ccw(c,d,b),ccw(a,b,c),ccw(a,b,d)
        return (d1*d2<0) and (d3*d4<0)
    if inter(p1,p2,q1,q2): return 0.0
    return min(ptseg(p1,q1,q2),ptseg(p2,q1,q2),ptseg(q1,p1,p2),ptseg(q2,p1,p2))

def pip(p,poly):
    x,y=p; c=False
    for (x1,y1),(x2,y2) in zip(poly,poly[1:]+poly[:1]):
        if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c

class Item:
    def __init__(s,kind,core,r,net,label):
        s.kind=kind; s.core=core; s.r=r; s.net=net; s.label=label
    def edges(s):
        c=s.core
        if len(c)==1: return [(c[0],c[0])]
        if len(c)==2: return [(c[0],c[1])]
        return list(zip(c,c[1:]+c[:1]))
def dist(a,b):
    d=min(segdist(e1[0],e1[1],e2[0],e2[1]) for e1 in a.edges() for e2 in b.edges())
    if len(a.core)>2 and pip(b.core[0],a.core): d=0
    if len(b.core)>2 and pip(a.core[0],b.core): d=0
    return d-a.r-b.r

def pad_item(p):
    w,h=p['w'],p['h']; a=p['rot']
    def tr(x,y):
        dx,dy=rot(x,y,a); return (p['x']+dx,p['y']+dy)
    lab=f"{p['ref']}.{p['num']}"
    if p['shape']=='rect' or p['shape']=='roundrect':
        return Item('pad',[tr(-w/2,-h/2),tr(w/2,-h/2),tr(w/2,h/2),tr(-w/2,h/2)],0,p['net'],lab)
    if p['shape']=='circle':
        return Item('pad',[(p['x'],p['y'])],w/2,p['net'],lab)
    if p['shape']=='oval':
        if w>h: r=h/2; return Item('pad',[tr(-(w/2-r),0),tr(w/2-r,0)],r,p['net'],lab)
        r=w/2; return Item('pad',[tr(0,-(h/2-r)),tr(0,h/2-r)],r,p['net'],lab)
    raise Exception(p['shape'])

def load_items(path):
    pcb,fps,segs,grs,zones,vias=load(path)
    items=[]
    for f in fps:
        for p in f['pads']:
            if 'F.Cu' in p['layers'] and p['type']=='smd': items.append(pad_item(p))
    for i,s in enumerate(segs):
        items.append(Item('trk',[(s['x1'],s['y1']),(s['x2'],s['y2'])],s['w']/2,s['net'],f"trk{i}:{s['net']}"))
    return pcb,fps,segs,grs,zones,items
