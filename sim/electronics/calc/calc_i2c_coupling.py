#!/usr/bin/env python3
"""T-094 / R-017: mutual capacitance from the SDA and SCL runs to the A2 electrode pads, before and after the re-route.

CALCULATION: method of moments in free space with an effective permittivity, coplanar copper on one face.
Conductors: 13 pads of the module electrode row (1.8 x 2.4 mm, 2.54 mm pitch, top edge y = 24.7 mm, pin 1 is GND),
the SDA run and the SCL run (1.0 mm wide), the S1 supply run (1.2 mm wide, y = 15.74 mm) as a neighbouring conductor.
Pure Python (the KiCad Python and system Python have no numpy): N x N LU, N up to about 900.
Layout values are from hardware/scripts/gen_pcb.py.

ASSUMPTIONS, to be checked by the REQ-038 I2C noise comparison on real hardware:
- FR-4 relative permittivity 4.5, thick substrate, so eps_eff = (1 + 4.5) / 2 = 2.75 (a 1.6 mm board gives a little less).
- Only horizontal parts of the runs and the pads are modelled: a window of 18 mm of each run centred on the middle electrode pad and the 5 nearest pads (finite-window error checked by convergence); the pads are the
  closest electrode copper (electrode tracks leave the pads downwards, away from the runs).
- The module, header pins and the carrier underside are not modelled.
- Every conductor other than the driven one is held at 0 V (Maxwell capacitance matrix entry -C_ij).
- Coupled step: SDA swing 3.3 V; electrode node at the MPR121 pin = C_pin 17 pF (sim_electrode.py) + 1 pF pad and track,
  the external electrode behind the 3 kohm resistor is not counted (worst case for the first microseconds).
- ADC step = 3.29 V / 1024 (sim_electrode.py VDD); firmware touch threshold 12 counts (sim_electrode.py).
"""
import math

EPS0 = 8.854e-12
EPS_EFF = 2.75          # ASSUMPTION
PAD_W, PAD_H = 1.8, 2.4
PAD_XC = [44.78 + 2.54 * j for j in range(13)]
PAD_YC = 25.9
MID = 6                 # electrode pad modelled as victim (E5)
WINDOW = 9.0            # half length of each modelled run, mm


def cells_rect(xc, yc, w, h, n, m):
    a, b = w / n, h / m
    return [(xc - w / 2 + a * (i + 0.5), yc - h / 2 + b * (j + 0.5), a, b) for i in range(n) for j in range(m)]


def self_term(a, b):
    return 2 * (a * math.asinh(b / a) + b * math.asinh(a / b))


def solve_multi(A, rhs_list):
    """LU with partial pivoting, solves A x = each right-hand side; returns list of solutions."""
    n = len(A)
    perm = list(range(n))
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(A[i][k]))
        if p != k:
            A[k], A[p] = A[p], A[k]
            perm[k], perm[p] = perm[p], perm[k]
        for i in range(k + 1, n):
            A[i][k] /= A[k][k]
            f = A[i][k]
            rk = A[k]
            ri = A[i]
            for j in range(k + 1, n):
                ri[j] -= f * rk[j]
    out = []
    for rhs in rhs_list:
        b = [rhs[perm[i]] for i in range(n)]
        for i in range(n):
            for j in range(i):
                b[i] -= A[i][j] * b[j]
        for i in range(n - 1, -1, -1):
            for j in range(i + 1, n):
                b[i] -= A[i][j] * b[j]
            b[i] /= A[i][i]
        out.append(b)
    return out


def capacitance(conductors):
    """Maxwell capacitance entries in fF: returns dict (victim index, driven index) -> -C_ij for the driven conductors."""
    cells = [(c, k) for k, cond in enumerate(conductors) for c in cond]
    n = len(cells)
    k_e = 1.0 / (4 * math.pi * EPS0 * EPS_EFF)
    A = []
    for i in range(n):
        xi, yi, ai, bi = cells[i][0]
        row = [0.0] * n
        for j in range(n):
            xj, yj, aj, bj = cells[j][0]
            if i == j:
                row[j] = k_e * self_term(ai * 1e-3, bi * 1e-3) / (ai * 1e-3 * bi * 1e-3)
            else:
                row[j] = k_e / math.hypot((xi - xj) * 1e-3, (yi - yj) * 1e-3)
        A.append(row)
    driven = {"SDA": len(conductors) - 3, "SCL": len(conductors) - 2}
    rhs = []
    names = list(driven)
    for nm in names:
        rhs.append([1.0 if cells[i][1] == driven[nm] else 0.0 for i in range(n)])
    sols = solve_multi(A, rhs)
    result = {}
    for nm, q in zip(names, sols):
        # charge induced on the victim pad (index MID - 4 in the conductor list), per volt on the driven run
        vic = 2  # middle of pads 4..8
        qv = sum(q[i] for i in range(n) if cells[i][1] == vic)
        result[nm] = -qv * 1e15   # fF
    return result


def run(y_sda, y_scl, h):
    pads = PAD_XC[MID - 2:MID + 3]
    xmid = PAD_XC[MID]
    conductors = []
    for xc in pads:
        conductors.append(cells_rect(xc, PAD_YC, PAD_W, PAD_H, max(1, round(PAD_W / h)), max(1, round(PAD_H / h))))
    run_n = int(round(2 * WINDOW / h))
    conductors.append(cells_rect(xmid, y_sda, 2 * WINDOW, 1.0, run_n, max(1, round(1.0 / h))))
    conductors.append(cells_rect(xmid, y_scl, 2 * WINDOW, 1.0, run_n, max(1, round(1.0 / h))))
    conductors.append(cells_rect(xmid, 15.74, 2 * WINDOW, 1.2, run_n, max(1, round(1.2 / h))))
    return capacitance(conductors), sum(len(c) for c in conductors)


def main():
    print("# calc_i2c_coupling.py  T-094 / R-017  CALCULATION; eps_eff=%.2f ASSUMPTION; victim = middle electrode pad" % EPS_EFF)
    cases = (("before (T-092, y_SDA 23.55, y_SCL 21.05)", 23.55, 21.05), ("after  (T-094, y_SDA 20.90, y_SCL 18.90)", 20.90, 18.90))
    lsb_mV = 3.29 / 1024 * 1e3
    C_node = 18e-12
    res = {}
    for name, ys, yc in cases:
        gap_sda = 24.7 - (ys + 0.5)
        gap_scl = 24.7 - (yc + 0.5)
        print("\n%s  edge-to-pad gap SDA %.2f mm, SCL %.2f mm (layout)" % (name, gap_sda, gap_scl))
        for h in (0.6, 0.4):
            r, nc = run(ys, yc, h)
            print("  cell %.2f mm (%d cells): C(SDA to pad) %.2f fF ; C(SCL to pad) %.2f fF" % (h, nc, r["SDA"], r["SCL"]))
        res[name] = r["SDA"]
        dv = 3.3 * r["SDA"] * 1e-15 / C_node
        print("  SDA full-swing step on the MPR121 pin node (%.0f pF): %.3f mV = %.2f ADC counts (touch threshold 12 counts)"
              % (C_node * 1e12, dv * 1e3, dv * 1e3 / lsb_mV))
    b = res[cases[0][0]]
    a = res[cases[1][0]]
    print("\nSDA-to-pad capacitance after / before = %.3f (factor %.2f lower); finest mesh values" % (a / b, b / a))


if __name__ == "__main__":
    main()
