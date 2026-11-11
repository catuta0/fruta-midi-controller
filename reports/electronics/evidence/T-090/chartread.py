#!/usr/bin/env python3
"""Minimal PNG decoder and chart column scan (no third-party modules).

Usage: chartread.py <png> <x0_px> <x1_px> <y_top_px> <y_bot_px> <x_left_R> <x_right_R> <y_top_V> <y_bot_V> <R> <r> <g> <b> <tol>
Reports pixel rows matching colour (r,g,b) within tol in the column of resistance R, averaged over 5 columns.
Calibration pixels are passed in explicitly so the reading is reproducible.
"""
import math
import struct
import sys
import zlib


def load(path):
    b = open(path, "rb").read()
    pos = 8
    idat = bytearray()
    while pos < len(b):
        n = struct.unpack(">I", b[pos:pos + 4])[0]
        t = b[pos + 4:pos + 8]
        if t == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", b[pos + 8:pos + 18])
        elif t == b"IDAT":
            idat += b[pos + 8:pos + 8 + n]
        elif t == b"IEND":
            break
        pos += 12 + n
    channels = {2: 3, 6: 4, 0: 1}[ctype]
    bpp = channels * depth // 8
    raw = zlib.decompress(bytes(idat))
    stride = w * bpp
    rows = []
    prev = bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            up = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + up) & 255
            elif f == 3:
                line[i] = (line[i] + (a + up) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(up - c), abs(a - c), abs(a + up - 2 * c)
                pr = a if pa <= pb and pa <= pc else (up if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        rows.append(line)
        prev = line
    return w, h, bpp, rows


def main():
    a = sys.argv
    png = a[1]
    x0, x1, yt, yb = map(float, a[2:6])
    rl, rr, vt, vb, R = map(float, a[6:11])
    target = tuple(map(int, a[11:14]))
    tol = int(a[14])
    w, h, bpp, rows = load(png)
    xc = x0 + (x1 - x0) * (math.log10(R) - math.log10(rl)) / (math.log10(rr) - math.log10(rl))
    hits = {}
    for x in range(int(xc) - 2, int(xc) + 3):
        run = []
        for y in range(int(yt), int(yb) + 1):
            px = rows[y][x * bpp:x * bpp + 3]
            if all(abs(px[i] - target[i]) <= tol for i in range(3)):
                run.append(y)
            else:
                if run:
                    hits.setdefault(round(sum(run) / len(run)), 0)
                    hits[round(sum(run) / len(run))] += 1
                    run = []
    print("image", w, h, "column", round(xc, 1), "for R =", R)
    for y in sorted(hits):
        if hits[y] < 2:
            continue
        v = vt * 10 ** (-(y - yt) / (yb - yt) * (math.log10(vt) - math.log10(vb)))
        print("  y_px", y, "count", hits[y], "V", round(v))


main()
