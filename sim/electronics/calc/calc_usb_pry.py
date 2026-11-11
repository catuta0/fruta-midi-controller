#!/usr/bin/env python3
"""T-092 / CR-003: effect of the M3 hole positions on a pull at the Pico USB plug. Thin-plate model, CALCULATION.

Runs with the KiCad Python (pcbnew reads the hole positions of the current board). Pure Python otherwise.
Question: with a force on the USB plug, how much does the carrier board itself bend and how is the load shared by the
screws, for the T-091 hole set and for the current one?

Model (Ritz, Kirchhoff plate): rectangle 100 x 70 mm, free edges, Legendre polynomials of total degree <= p, screws as
stiff point springs (w only, no clamping moment, conservative for the screw). Force normal to the board, on the board
plane at the centre of the Pico USB end (13.39, 0.11) mm (T-103; 0.63 before). The Pico is not modelled: it stiffens the board locally, so the
absolute deflections are upper-side values; only the ratio between hole sets is used. Linear, no contact, no spacer
compliance. Convergence: printed for several p.

Inputs: board 100 x 70 x 1.6 mm (MEASUREMENT outline; thickness ASSUMPTION standard FR-4), E = 22 GPa, nu = 0.15
(ASSUMPTION, typical FR-4 values, not from a laminate datasheet; deflection scales with 1/E), screw spring 1e6 N/m
(ASSUMPTION; result insensitive, printed), F = 10 and 30 N (T-090 pry cases, ASSUMPTION).

What this does NOT give: the peel margin of the castellation joints. T-090 (0.57-0.75 at 30 N, rigid carrier and module,
calc_smd_feasibility.out) does not depend on the hole positions, so those margins are unchanged by moving the holes. The
peel added by board curvature is not quantified.
"""
import math
import os
import re
import sys

import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
A, B, T = 0.100, 0.070, 1.6e-3
E, NU, KS = 22e9, 0.15, 1e6
LOAD = (13.39e-3, 0.11e-3)         # T-103 (F3-002): Pico USB end at y 1.48 - 1.37 = 0.11 mm (was 0.63)
OLD = [(8.0, 64.0), (95.0, 5.0), (96.0, 38.0), (88.5, 30.5)]        # T-091 positions (frutamidi.drl, evidence T-091)
D = E * T ** 3 / (12 * (1 - NU ** 2))


def legendre(n, x):
    """P_0..P_n and first and second derivatives at x."""
    p = [1.0, x]
    d1 = [0.0, 1.0]
    d2 = [0.0, 0.0]
    for k in range(1, n):
        p.append(((2 * k + 1) * x * p[k] - k * p[k - 1]) / (k + 1))
        d1.append((2 * k + 1) * p[k] + d1[k - 1])
        d2.append((2 * k + 1) * d1[k] + d2[k - 1])
    return p[:n + 1], d1[:n + 1], d2[:n + 1]


def gauss(n):
    xs, ws = [], []
    for i in range(n):
        x = math.cos(math.pi * (i + 0.75) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, x
            for k in range(1, n):
                p0, p1 = p1, ((2 * k + 1) * x * p1 - k * p0) / (k + 1)
            dp = n * (x * p1 - p0) / (x * x - 1)
            dx = p1 / dp
            x -= dx
            if abs(dx) < 1e-15:
                break
        xs.append(x)
        ws.append(2 / ((1 - x * x) * dp * dp))
    return xs, ws


def tables(p):
    xs, ws = gauss(p + 3)
    vals = [legendre(p, x) for x in xs]
    n = p + 1
    I = {}
    for r in range(3):
        for s in range(3):
            I[(r, s)] = [[sum(w * v[r][i] * v[s][j] for w, v in zip(ws, vals)) for j in range(n)] for i in range(n)]
    return I


def solve(M, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(M)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            if f:
                for k in range(c, n + 1):
                    M[r][k] -= f * M[c][k]
    x = [0.0] * n
    for c in range(n - 1, -1, -1):
        x[c] = (M[c][n] - sum(M[c][k] * x[k] for k in range(c + 1, n))) / M[c][c]
    return x


def phi(basis, p, x, y):
    px = legendre(p, 2 * x / A - 1)[0]
    py = legendre(p, 2 * y / B - 1)[0]
    return [px[i] * py[j] for i, j in basis]


def plate(holes_mm, p, ks=KS):
    basis = [(i, j) for i in range(p + 1) for j in range(p + 1 - i)]
    I = tables(p)
    ax, ay = 2 / A, 2 / B
    jac = A * B / 4
    n = len(basis)
    K = [[0.0] * n for _ in range(n)]
    for a, (i, j) in enumerate(basis):
        for b, (k, l) in enumerate(basis):
            K[a][b] = D * jac * (ax ** 4 * I[(2, 2)][i][k] * I[(0, 0)][j][l]
                                 + ay ** 4 * I[(0, 0)][i][k] * I[(2, 2)][j][l]
                                 + NU * ax ** 2 * ay ** 2 * (I[(2, 0)][i][k] * I[(0, 2)][j][l] + I[(0, 2)][i][k] * I[(2, 0)][j][l])
                                 + 2 * (1 - NU) * ax ** 2 * ay ** 2 * I[(1, 1)][i][k] * I[(1, 1)][j][l])
    sup = [phi(basis, p, x * 1e-3, y * 1e-3) for x, y in holes_mm]
    for f in sup:
        for a in range(n):
            for b in range(n):
                K[a][b] += ks * f[a] * f[b]
    load = phi(basis, p, *LOAD)
    c = solve(K, load)                                     # response to 1 N
    w = sum(u * v for u, v in zip(c, load))
    reac = [ks * sum(u * v for u, v in zip(c, f)) for f in sup]
    return w, reac


def holes_now():
    board = pcbnew.LoadBoard(PCB)
    o = board.GetDesignSettings().GetAuxOrigin()
    out = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        if re.fullmatch(r"H\d", fp.GetReference()):
            out.append((fp.GetPosition().x * 1e-6 - o.x * 1e-6, fp.GetPosition().y * 1e-6 - o.y * 1e-6))
    return out


def report(name, holes):
    print("== %s: holes %s mm" % (name, [(round(x, 2), round(y, 2)) for x, y in holes]))
    dmin = min(math.hypot(x - LOAD[0] * 1e3, y - LOAD[1] * 1e3) for x, y in holes)
    print("   nearest hole to the USB end centre (%.2f, %.2f) mm: %.2f mm (CALCULATION)" % (LOAD[0] * 1e3, LOAD[1] * 1e3, dmin))
    res = None
    for p in (8, 10, 12, 14):
        w, r = plate(holes, p)
        print("   p = %2d: w at load %.4f mm/N; screw force per N applied %s (sum %.3f)" % (p, w * 1e3, [round(v, 3) for v in r], sum(r)))
        res = (w, r)
    w2, _ = plate(holes, 14, ks=1e7)
    print("   sensitivity, screw spring 1e7 N/m at p = 14: w at load %.4f mm/N" % (w2 * 1e3))
    return res, dmin


print("# calc_usb_pry.py  CALCULATION (T-092); plate D = %.2f N m; inputs and limits in the header" % D)
(ow, or_), od = report("T-091 hole set", OLD)
(nw, nr), nd = report("current hole set", holes_now())
print()
for F in (10.0, 30.0):
    print("F = %.0f N: deflection at the USB end, linear model: T-091 %.2f mm; current %.2f mm; ratio %.1f" % (F, F * ow * 1e3, F * nw * 1e3, ow / nw))
    print("   largest screw force: T-091 %.1f N; current %.1f N" % (F * max(abs(v) for v in or_), F * max(abs(v) for v in nr)))
print("RESULT: board deflection at the USB end reduced by a factor %.1f by the new hole set (ratio, CALCULATION on ASSUMPTION inputs)" % (ow / nw))
print("NOT CHANGED: castellation peel margin 0.57-0.75 at 30 N (T-090, rigid carrier and module) does not depend on hole positions")
print("NOT QUANTIFIED: extra joint peel caused by carrier curvature; the Pico stiffening the carrier; in-plane plug forces")
