"""Minimal KiCad s-expression parser and PCB geometry extraction (T-108 review)."""
import math, re, sys

def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in '()':
            yield c; i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == '\\':
                    buf.append(s[j+1]); j += 2
                else:
                    buf.append(s[j]); j += 1
            yield ('S', ''.join(buf)); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()':
                j += 1
            yield s[i:j]; i = j

def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1] if isinstance(t, tuple) else t)
    return stack[0][0]

def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def first(node, name):
    r = find(node, name)
    return r[0] if r else None

def walk(node, name):
    out = []
    if isinstance(node, list):
        if node and node[0] == name:
            out.append(node)
        for c in node:
            out += walk(c, name)
    return out

def rot(x, y, deg):
    a = math.radians(deg)
    # KiCad: positive angle rotates counter-clockwise on screen (y down) -> use -a
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c

def load(path):
    pcb = parse(open(path).read())
    nets = {}
    fps = []
    for fp in find(pcb, 'footprint'):
        at = first(fp, 'at'); fx, fy = float(at[1]), float(at[2]); fr = float(at[3]) if len(at) > 3 else 0.0
        ref = None
        for p in find(fp, 'property'):
            if p[1] == 'Reference': ref = p[2]
        pads = []
        for pd in find(fp, 'pad'):
            pat = first(pd, 'at'); px, py = float(pat[1]), float(pat[2]); pr = float(pat[3]) if len(pat) > 3 else 0.0
            sz = first(pd, 'size'); w, h = float(sz[1]), float(sz[2])
            dx, dy = rot(px, py, fr)
            layers = first(pd, 'layers')[1:]
            net = first(pd, 'net')
            netname = net[-1] if net else ''
            drill = first(pd, 'drill')
            rr = first(pd, 'roundrect_rratio')
            pads.append(dict(ref=ref, num=pd[1], type=pd[2], shape=pd[3], x=fx + dx, y=fy + dy, w=w, h=h,
                             rot=(pr) % 360, layers=layers, net=netname, drill=drill, rr=float(rr[1]) if rr else 0))
        graphics = []
        for kind in ('fp_line', 'fp_rect', 'fp_circle', 'fp_poly', 'fp_text'):
            for g in find(fp, kind):
                lay = first(g, 'layer')
                graphics.append((kind, lay[1] if lay else None, g))
        fps.append(dict(ref=ref, lib=fp[1], x=fx, y=fy, rot=fr, pads=pads, graphics=graphics, node=fp))
    segs = []
    for sg in find(pcb, 'segment'):
        st = first(sg, 'start'); en = first(sg, 'end'); w = first(sg, 'width'); lay = first(sg, 'layer'); net = first(sg, 'net')
        segs.append(dict(x1=float(st[1]), y1=float(st[2]), x2=float(en[1]), y2=float(en[2]), w=float(w[1]),
                         layer=lay[1], net=net[-1] if net else ''))
    grs = []
    for kind in ('gr_line', 'gr_rect', 'gr_circle', 'gr_arc', 'gr_poly', 'gr_text'):
        for g in find(pcb, kind):
            lay = first(g, 'layer')
            grs.append((kind, lay[1] if lay else None, g))
    zones = walk(pcb, 'zone')
    vias = find(pcb, 'via')
    return pcb, fps, segs, grs, zones, vias
