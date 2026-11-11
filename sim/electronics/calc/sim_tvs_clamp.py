#!/usr/bin/env python3
"""T-097 study: effect of a TVS/ESD clamp diode from each electrode pad Ex (terminal side) to GND on MPR121 sensing.

SIMULATION, same closed-form model as sim_electrode.py (imported, unchanged):
  CDC current source -> node P (C_pin 17 pF) -> R_series -> node E (C_ext + C_d of the clamp).
  The clamp adds its capacitance C_d to node E (SOURCE values per candidate, at 0 V bias: worst, C_d falls with bias).
  Leakage: modelled as a constant current I_leak drawn from the charge current during the charge phase
  (ASSUMPTION, worst bound: the datasheet leakage is specified at V_RWM = 5 V, the electrode swings 0 ... 3.3 V).
  Ratio = worst-case sensitivity with R and the clamp / worst-case sensitivity with R = 0 and no clamp, same C_ext
  (the ADR-019 limit 0.90 is on this ratio, as in sim_electrode.py).
Run with any Python 3 from this directory: python3 sim_tvs_clamp.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim_electrode as se  # noqa: E402

C_EXT = [10e-12, 20e-12, 50e-12, 100e-12, 200e-12, 500e-12, 1000e-12]
LIMIT = 0.90
CAND = [  # name, C_d max at 0 V (F), I_leak max at V_RWM (A); all SOURCE (datasheets in reports/electronics/evidence/T-097)
    ("none", 0.0, 0.0),
    ("Bourns CDSOD323-T05LC (1.0 pF typ, 5 uA max)", 1.0e-12, 5e-6),
    ("Nexperia PESD5V0U1BA (3.5 pF max, 100 nA max)", 3.5e-12, 100e-9),
    ("Nexperia PESD5V0S1BA (45 pF max, 100 nA max)", 45e-12, 100e-9),
]


def measure_leak(I, T, R, Ce, il):
    vp = ve = 0.0
    acc = 0.0
    for _ in range(se.FFI):
        vp, ve = se.charge(0.0, ve, max(I - il, 0.0), T, R, Ce)
        acc += min(vp, se.VDD) / se.VDD * 1024
        vp, ve = se.discharge(ve, T, R, Ce)
    return acc / se.FFI


def worst_sens(R, Ce, il):
    best = None
    for T in se.CDT_SET:
        for I in se.CDC_SET:
            c = measure_leak(I, T, R, Ce, il)
            if se.LSL <= c / 4 <= se.USL:
                s = c - measure_leak(I, T, R, Ce + 1e-12, il)
                best = s if best is None or s < best else best
    return best


def worst_ratio(R, cd, il):
    out = []
    for ce in C_EXT:
        ref = worst_sens(0.0, ce, 0.0)
        w = worst_sens(R, ce + cd, il)
        out.append(None if (ref is None or w is None) else w / ref)
    return out


def main():
    print("# sim_tvs_clamp.py  SIMULATION (model of sim_electrode.py). Worst-case ratio vs R=0 without clamp, C_ext 10..1000 pF")
    print("%-52s %-6s %s" % ("clamp", "R", "  ".join("%6.0fpF" % (c * 1e12) for c in C_EXT)) + "   min   verdict")
    for name, cd, il in CAND:
        for R in (100.0, 330.0, 1000.0, 3300.0):
            r = worst_ratio(R, cd, il)
            ok = [x for x in r if x is not None]
            mn = min(ok) if len(ok) == len(r) else float("nan")
            print("%-52s %-6.0f %s   %.3f %s" % (name, R, "  ".join("%8s" % ("OOR" if x is None else "%.3f" % x) for x in r), mn,
                                               "PASS" if mn >= LIMIT else "FAIL"))
    print()
    print("# Capacitance sweep at R = 3300 and R = 330 ohm, no leakage: largest C_d keeping the ratio >= %.2f" % LIMIT)
    for R in (3300.0, 330.0):
        last = None
        for cd_pf in (0, 1, 2, 3.5, 5, 10, 20, 45, 100):
            r = worst_ratio(R, cd_pf * 1e-12, 0.0)
            mn = min(x for x in r if x is not None) if all(x is not None for x in r) else float("nan")
            print("  R %-5.0f C_d %5.1f pF: min ratio %.3f %s" % (R, cd_pf, mn, "PASS" if mn >= LIMIT else "FAIL"))
            if mn >= LIMIT:
                last = cd_pf
        print("  -> R %.0f ohm: largest swept C_d with PASS = %s pF" % (R, last))
    print()
    print("# Leakage sweep at R = 3300 ohm, C_d = 0: largest I_leak keeping the ratio >= %.2f" % LIMIT)
    last = None
    for il_na in (0, 5, 100, 300, 1000, 3000, 5000):
        r = worst_ratio(3300.0, 0.0, il_na * 1e-9)
        mn = min(x for x in r if x is not None) if all(x is not None for x in r) else float("nan")
        print("  I_leak %5.0f nA: min ratio %.3f %s" % (il_na, mn, "PASS" if mn >= LIMIT else "FAIL"))
        if mn >= LIMIT:
            last = il_na
    print("  -> largest swept I_leak with PASS = %s nA (constant leakage only; a leakage that changes faster than the baseline"
          " filter is not covered)" % last)
    # counts shift caused by the leakage at the autoconfig nominal pair (offset, absorbed by the baseline if slow)
    print()
    print("# Offset in counts from leakage at the nominal pair, R 3300 ohm, C_d 0 (CALCULATION on the model)")
    for ce in (10e-12, 100e-12, 1000e-12):
        a = se.analyse(3300.0, ce)
        I, T, _ = a["nominal"]
        for il_na in (5, 100, 1000, 5000):
            d = se.measure(I, T, 3300.0, ce) - measure_leak(I, T, 3300.0, ce, il_na * 1e-9)
            print("  C_ext %5.0f pF CDC %2.0f uA CDT %4.1f us: I_leak %5.0f nA -> %6.1f counts (touch threshold %d)"
                  % (ce * 1e12, I * 1e6, T * 1e6, il_na, d, se.TOUCH_THRESHOLD))


if __name__ == "__main__":
    main()
