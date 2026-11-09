#!/usr/bin/env python3
"""T-090 / CR-003: SMD feasibility numbers. CALCULATION unless labelled.

Run with any Python 3. Outputs calc_smd_feasibility.out. No hardware file is read or changed.

Inputs
  IEC 61000-4-2 150 pF / 330 ohm source, as calc_flashover.py (EE-S16, recalled, standard not opened).
  Flashover model: worst of M4 (eta = 0.3 x empirical air, ASSUMPTION) and IEC 60664-1 F.2 case A
  (EE-S25, recalled, ASSUMPTION), both identical to calc_flashover.py. The V1.2 rule is 3.5 mm at 4 kV.
  Chart ratings: read from the datasheet 1.2/50 us charts (reports/electronics/evidence/T-090/charts/chartread_raw.txt);
  datasheet SOURCE, reading uncertainty +-5 % (ASSUMPTION, same as T-060). HPWC is a raster chart, Vishay is rendered vector.
  Part gaps: HPWC B min (TT HPWC 09.23), Vishay L1 min (docs 28956, 28963). All SOURCE.
  Pico: datasheet RP-008307-DS-2 Figures 3 and 5. KiCad RaspberryPi_Pico_SMD footprint is used only to name the TPs.
  Peel strength: 1.05 N/mm (ASSUMPTION: typical IPC-4101 FR-4 1 oz figure, recalled, not opened). Home-etched and
  iron-heated copper may be weaker; 0.8 N/mm is also shown.
"""
import math

R_IEC, C_IEC = 330.0, 150e-12
LEVELS = (4000.0, 8000.0)


def v_empirical_kv(d_mm, p_bar=1.013):
    pd = p_bar * d_mm / 10.0
    return 24.36 * pd + 6.72 * math.sqrt(pd)


def solve(f, target, lo=1e-3, hi=100.0):
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


F2 = [(0.33, 0.01, 0.01), (0.5, 0.04, 0.04), (0.8, 0.1, 0.1), (1.5, 0.5, 0.3), (2.5, 1.5, 0.6),
      (4.0, 3.0, 1.2), (6.0, 5.5, 2.0), (8.0, 8.0, 3.0), (12.0, 14.0, 4.5)]


def f2a(u_kv):
    for (u0, a0, _), (u1, a1, _) in zip(F2, F2[1:]):
        if u0 <= u_kv <= u1:
            t = (math.log(u_kv) - math.log(u0)) / (math.log(u1) - math.log(u0))
            return math.exp(math.log(a0) + t * (math.log(a1) - math.log(a0)))
    return float("nan")


def req_gap(v):
    """Required gap for voltage v across one gap: worst of M4 eta=0.3 and F.2 case A."""
    return max(solve(lambda d: 0.3 * v_empirical_kv(d) * 1000, v), f2a(v / 1000))


print("# calc_smd_feasibility.py  CALCULATION (T-090, CR-003)")
print("# V1.2 rule: >= 3.5 mm at 4 kV; required gap below = worst of M4 eta=0.3 and IEC 60664-1 F.2 case A at the voltage across that gap")
print()
print("== 1. Electrode resistor options ==")
print("%-34s %6s %3s %8s %8s %8s %8s %7s %7s %7s %7s %7s" % (
    "option", "R_tot", "N", "rate/pt", "V/pt@4k", "m_v@4k", "m_v@8k", "gap", "req@4k", "m_g@4k", "req@8k", "m_g@8k"))
#         name, R_part, N, rating V per part (chart), part conductor gap mm (SOURCE)
opts = [
    ("V1.2 MBE0414 3k3 (caps worst .25)", 3300, 1, 4083, 3.61),
    ("A HPWC2512 3k0 5 %", 3000, 1, 4472, 4.4),
    ("A' HPWC2512 3k3 5 %", 3300, 1, 4596, 4.4),
    ("B HPWC2010 3k3 5 %", 3300, 1, 3797, 3.0),
    ("C HPWC1206 3k3 5 %", 3300, 1, 1722, 1.7),
    ("D MMB0207 3k3 1 %", 3300, 1, 1736, 3.2),
    ("E CMB0207 3k3 1 %", 3300, 1, 5175, 3.2),
    ("E' CMB0207 3k0 1 %", 3000, 1, 4991, 3.2),
    ("F 2x CMB0207 1k65 1 %", 1650, 2, 3689, 3.2),
    ("G 2x HPWC2512 1k6 5 %", 1600, 2, 3547, 4.4),
    ("H 3x MMB0207 1k1 1 %", 1100, 3, 1008, 3.2),
    ("I 3x HPWC1206 1k1 5 %", 1100, 3, 1025, 1.7),
]
rows = {}
for name, r, n, rate, gap in opts:
    rt = r * n
    res = []
    for v in LEVELS:
        vtotal = v * rt / (rt + R_IEC)
        vp = vtotal / n
        rq = req_gap(vp)
        res.append((vp, rate / vp, rq, gap / rq))
    print("%-34s %6d %3d %8d %8.0f %8.2f %8.2f %7.2f %7.2f %7.2f %7.2f %7.2f" % (
        name, rt, n, rate, res[0][0], res[0][1], res[1][1], gap, res[0][2], res[0][3], res[1][2], res[1][3]))
    rows[name] = res
print("# columns: rate/pt V chart rating per part; V/pt V across one part; m_v rating margin; gap mm conductor gap per part;")
print("# req mm required per-gap; m_g gap margin. margin >= 1.0 meets the criterion. Equal sharing assumed for N > 1 (see report).")
print()
print("Rule 3.5 mm: V1.2 caps ", "PASS" if 3.61 >= 3.5 else "FAIL",
      "(3.61 mm, +-0.25 mm placement, ASSUMPTION cap length); +-0.5 mm 3.13 mm FAIL")
print("Rule 3.5 mm: 2512 B min 4.4 mm PASS; 2010 B min 3.0 mm FAIL; 1206 B min 1.7 mm FAIL; MELF 0207 L1 min 3.2 mm FAIL")
print("Rule 3.5 mm, 2x series: per-gap requirement at 4 kV (V/2) is below 3.2 and 4.4 mm -> PASS for both (see table)")
print()

print("== 2. Land patterns (copper gap G, pad length along axis Y, pad width X, overall Z, mm) ==")
for name, g, y, x in [("2512 HPWC, hand solder (proposed)", 5.0, 1.9, 3.35),
                       ("CMB 0207 MELF (IPC G 3.2 widened to 3.6)", 3.6, 2.2, 2.4),
                       ("1206 (Vishay 28950 IPC)", 1.75, 1.15, 1.80)]:
    z = g + 2 * y
    print("  %-42s G %.2f  Y %.2f  X %.2f  Z %.2f  ; adjacent lane gap at 5.08 mm pitch %.2f mm" % (name, g, y, x, z, 5.08 - x))
print("  2512 termination spans L/2 - A .. L/2 from centre: inner %.2f .. %.2f mm, outer %.2f .. %.2f mm (L 6.2..6.8, A 0.3..0.9); pad spans 2.50 .. 4.40 mm: every termination lands on the pad; conductor gap is set by B min 4.4 mm, not by the 5.0 mm copper gap" % (6.2/2-0.9, 6.8/2-0.3, 6.2/2, 6.8/2))
dx = 5.08 - 3.35
print("  rule (b) Ex <-> ELEy diagonal, 2512 lanes at 5.08 mm: sqrt(%.2f^2 + 5.00^2) = %.2f mm vs 3.5 mm" % (dx, math.hypot(dx, 5.0)))
print("  2 x 2512 in line: Z = 1.9 + 5.0 + 3.0 + 5.0 + 1.9 = %.1f mm" % (1.9 + 5.0 + 3.0 + 5.0 + 1.9))
print()

print("== 3. Pico land (datasheet Figure 5) ==")
pitch, w = 2.54, 1.6
print("  pad width 1.6 mm (R0.8), pad length (22.58 - 16.18) / 2 = %.2f mm, pitch %.2f mm" % ((22.58 - 16.18) / 2, pitch))
print("  pad-to-pad gap = %.2f mm vs 0.6 mm rule: %s" % (pitch - w, "PASS" if pitch - w >= 0.6 else "FAIL"))
print("  track between adjacent pads needs 1.0 + 2 x 0.6 = 2.2 mm, available %.2f mm: not possible" % (pitch - w))
print("  datasheet pad overhang beyond module edge 0.79 mm; proposed hand-solder land length 4.2 mm, overhang %.2f mm" % (0.79 + 1.0))
inner = 16.18
for clearance, track, name in [(0.6, 1.0, "1.0 mm signal")]:
    print("  interior width between pad rows %.2f mm, usable %.2f mm, %s tracks fitting (track + clearance) = %d" % (
        inner, inner - 2 * clearance, name, int((inner - 2 * clearance + clearance) / (track + clearance))))
# Board coordinates: pin 1 at (4.5, 2.0); datasheet origin bottom left, y up, USB at top
xo, yo = 2.89, 51.63
print("  Exposed underside features in V1.2 board coordinates (x = %.2f + x_d, y = %.2f - y_d), keep-out square side = pad + 2 x 0.6 mm:" % (xo, yo))
features = [("TP1 GND (KiCad name)", 10.5, 46.5, 1.5, 1.5), ("TP2 USB DM (KiCad name)", 11.5, 49.8, 1.5, 1.5), ("TP3 USB DP (KiCad name)", 9.5, 49.8, 1.5, 1.5),
            ("TP4 GPIO23 (KiCad name)", 8.0, 43.0, 1.5, 1.5), ("TP5 GPIO25 (KiCad name)", 8.0, 40.5, 1.5, 1.5), ("TP6 BOOTSEL (KiCad name)", 8.0, 38.0, 1.5, 1.5),
            ("A USB shell", 7.775, 49.5, 1.1, 1.8), ("B USB shell", 13.225, 49.5, 1.1, 1.8), ("C USB shell", 8.075, 46.47, 1.05, 1.45), ("D USB shell", 12.925, 46.47, 1.05, 1.45)]
xs, ys = [], []
for name, xd, yd, sx, sy in features:
    bx, by = xo + xd, yo - yd
    print("    %-26s datasheet (%.3f, %.3f) -> board (%.3f, %.3f), size %.2f x %.2f" % (name, xd, yd, bx, by, sx, sy))
    xs += [bx - sx / 2 - 0.6, bx + sx / 2 + 0.6]
    ys += [by - sy / 2 - 0.6, by + sy / 2 + 0.6]
print("  union keep-out rectangle: x %.2f .. %.2f, y %.2f .. %.2f (width %.2f, height %.2f mm)" % (min(xs), max(xs), min(ys), max(ys), max(xs) - min(xs), max(ys) - min(ys)))
inner_l, inner_r = xo + (21 - 16.18) / 2, xo + 21 - (21 - 16.18) / 2
print("  interior between pad rows on board: x %.2f .. %.2f; left channel beside keep-out %.2f mm, right channel %.2f mm (minus 0.6 clearance to the pads)" % (
    inner_l, inner_r, min(xs) - inner_l - 0.6, inner_r - max(xs) - 0.6))
print("  USB shell front at y = 2.0 - 1.37 - 1.3 = %.2f mm (board edge y = 0): overhangs the board edge by %.2f mm, plug cannot foul the board" % (2.0 - 1.37 - 1.3, 1.3 - (2.0 - 1.37)))
print("  outer pad edge to board edge: datasheet land %.2f mm; proposed land %.2f mm" % (2.89 - 0.79, 2.89 - 0.79 - 1.0))
# Pry estimate
for peel in (1.05, 0.8):
    ds = [1.37 + 2.54 * k for k in range(20)]
    denom = 2 * sum(d * d for d in ds)
    for F in (10.0, 30.0):
        lever = 52.0
        f1 = F * lever * ds[-1] / denom
        print("  Pry: F = %.0f N upward on the USB plug, lever %.0f mm about the far pad row, rigid module, 40 pads: first pad %.2f N vs peel %.2f N/mm x 1.6 mm = %.2f N (margin %.2f)" % (
            F, lever, f1, peel, peel * 1.6, peel * 1.6 / f1))
print()

print("== 4. Module A2 mechanical ==")
# rocking about one row of the 13/7 pin layout; simplified: 20 joints, force at far end (ASSUMPTION rigid module)
rows_y = [8.255] * 13 + [-6.985] * 7
for peel in (1.05, 0.8):
    F = 5.0
    lever = 15.24 + 8.0  # ends of module beyond outer row, approx
    # force in the outermost joints of 13-row by rocking about 7-row: sum of moments
    ds = [abs(y - (-6.985)) for y in rows_y if y != -6.985]
    dsum = sum(d * d for d in ds)
    f1 = F * lever * max(ds) / dsum
    print("  Pry F = 5 N at the module end, lever %.1f mm, 13-row joints: %.3f N per joint vs peel %.2f N/mm x 1.8 mm = %.2f N (margin %.1f)" % (
        lever, f1, peel, peel * 1.8, peel * 1.8 / f1))
print("  Butt joint gross area: pin 0.64 x 0.64 mm (ASSUMPTION, common 2.54 mm header) = %.2f mm2 x 20 = %.1f mm2; side fillet adds lap area" % (0.64**2, 20 * 0.64**2))
print()

print("== 5. Bare MPR121 versus home-etch rules ==")
pitch, width = 0.4, 0.2
print("  QFN-20 3 x 3 mm: terminal width %.2f, pitch %.2f (SOURCE) -> gap between terminals %.2f mm vs 0.6 mm rule (ratio %.2f); pitch alone is below the 0.6 mm clearance" % (width, pitch, pitch - width, (pitch - width) / 0.6))
print()

print("== 6. Hole count ==")
print("  V1.2: 133 drilled holes (MEASUREMENT, CR-003 frutamidi.drl). Proposal: 4 M3 holes -> %.1f %% fewer" % (100 * (133 - 4) / 133))
print()

print("== 7. Other values ==")
print("  C1: V working 3.3 V on 50 V rated -> %.1f %% of rating" % (100 * 3.3 / 50))
print("  R +5 %% on 3k3 = %.0f ohm; sensitivity interpolated between 3.3k 0.904 and 4.7k 0.887 (typical column, analysis.md) = %.3f" % (3300 * 1.05, 0.904 - (0.904 - 0.887) * (3465 - 3300) / 1400))
print("  3k0 5 %% range: %.0f .. %.0f ohm, inside the 2.7..3.3 kOhm design rule; V_R 4 kV = %.0f V" % (3000 * 0.95, 3000 * 1.05, 4000 * 3000 / 3330))
print("  ESD energy into R at 4 kV (3k0): %.2f mJ" % (0.5 * C_IEC * 4000**2 * 3000 / 3330 * 1e3))
print("  Peak current with arc around R: 4 kV/330 = %.1f A; through 3k0: %.2f A" % (4000 / 330, 4000 / 3330))
print("  B3S pad gap on same side (4.5 - 1.3) = %.1f mm; across pads = 6.4 mm" % (4.5 - 1.3))
print("  Worst-choice sensitivity at 3465 ohm, interpolated between 3.3k 0.904 and 4.7k 0.861 = %.3f" % (0.904 - (0.904 - 0.861) * (3465 - 3300) / 1400))
print("  Peak current through 2850 ohm at 4 kV: %.2f A; margin against the 1.33 A inferred pin limit %.2f; V1.2 3k3: %.2f A, margin %.2f" % (4000 / 3180, 1.33 / (4000 / 3180), 4000 / 3630, 1.33 / (4000 / 3630)))
