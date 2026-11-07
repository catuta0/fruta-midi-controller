#!/usr/bin/env python3
"""T-060 / CR-002: flashover across the electrode series resistor and between channels. CALCULATION.

Question: what minimum air gap must separate copper (pads, tracks) and leads of net Ex (terminal side,
reached by the discharge) from net ELEx (MPR121 side, same channel) and from any other channel's ELEy,
so that an IEC 61000-4-2 contact discharge cannot arc around the 3k3 series resistor?

Inputs and labels
  IEC 61000-4-2 source: 150 pF / 330 ohm, contact levels 4 kV and 8 kV (SOURCE EE-S16, IEC 61000-4-2).
  R = 3.3 kOhm (design value, reports/electronics/analysis.md).
  The ELE side is held near 0..3.3 V by the MPR121 pin structure (ASSUMPTION: clamp drop << kV), so the
  peak voltage across the gap is V_gap = V * R / (R + 330)  (CALCULATION, resistive divider at t = 0+;
  the series inductance of the gun and the sub-ns first peak are ignored - ASSUMPTION, conservative for
  the divider because the first peak is limited by the 330 ohm + R anyway).
  A different channel's ELE net is also near 0 V, so the cross-channel gap sees the same V_gap
  (ASSUMPTION: the other channel's electrode is not touched at the same time).

Breakdown models (all ASSUMPTION unless stated; the sweep is the point of this script)
  M1 uniform field, E_bd = 2.0 ... 4.5 kV/mm (3 kV/mm is the textbook value for cm gaps; 4.5 kV/mm is the
     usual value near 1 mm; 2 kV/mm is a pessimistic floor for dirty/humid boards).
  M2 Paschen law, Townsend form V = B p d / (ln(A p d) - ln(ln(1 + 1/gamma))), air, A = 15 /(cm Torr),
     B = 365 V/(cm Torr), gamma = 0.01, p = 760 Torr (textbook constants, ASSUMPTION).
  M3 empirical uniform-field air formula V[kV] = 24.36 (p d) + 6.72 sqrt(p d), p d in bar cm
     (Kuffel/Zaengl high-voltage textbook approximation, ASSUMPTION), 20 C, 1.013 bar.
  M4 non-uniform field: breakdown is triggered when the peak field reaches the uniform-field strength;
     V_bd(nonuniform) = eta * V_bd(M3), field utilisation factor eta = 0.3 / 0.5 / 0.7 for round pad
     edges, 35 um copper edges and lead wires (ASSUMPTION; eta from rod-plane / sphere-plane tables of
     the order of 0.3-0.7 for gap/radius ratios 1..10). This is pessimistic: streamer propagation in a
     non-uniform field needs a lower mean field than inception only for long gaps.
  M5 IEC 60664-1 Table F.2 minimum clearance vs rated impulse withstand voltage (1.2/50 us, up to 2000 m),
     case A inhomogeneous / case B homogeneous field. Values RECALLED from the standard, not re-read in
     this task -> ASSUMPTION until checked against the standard text (open item in the T-060 handoff).
  An ESD pulse (ns rise, ~0.5 us tail across R) is much shorter than 1.2/50 us; air needs an overvoltage
  and a statistical time lag to break down at ns time scales, so DC and 1.2/50 values are conservative.

Output: required gap per model and level, and the design rule chosen for the PCB.
"""
import math

C_IEC, R_IEC, R = 150e-12, 330.0, 3300.0
LEVELS = (4000.0, 8000.0)


def v_gap(v):
    return v * R / (R + R_IEC)


def d_uniform(v, e_kv_mm):
    return v / 1000.0 / e_kv_mm


def v_paschen(d_mm, p_torr=760.0, A=15.0, B=365.0, gamma=0.01):
    pd = p_torr * d_mm / 10.0                       # Torr cm
    den = math.log(A * pd) - math.log(math.log(1 + 1 / gamma))
    return B * pd / den if den > 0 else float("inf")


def v_empirical_kv(d_mm, p_bar=1.013):
    pd = p_bar * d_mm / 10.0                        # bar cm
    return 24.36 * pd + 6.72 * math.sqrt(pd)


def solve(f, target, lo=1e-3, hi=100.0):
    """smallest d in [lo, hi] mm with f(d) >= target (f increasing in the range used)."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) >= target:
            hi = mid
        else:
            lo = mid
    return hi


# IEC 60664-1 Table F.2 (rated impulse kV -> clearance mm, case A, case B), RECALLED values (ASSUMPTION)
F2 = [(0.33, 0.01, 0.01), (0.5, 0.04, 0.04), (0.8, 0.1, 0.1), (1.5, 0.5, 0.3), (2.5, 1.5, 0.6),
      (4.0, 3.0, 1.2), (6.0, 5.5, 2.0), (8.0, 8.0, 3.0), (12.0, 14.0, 4.5)]


def iec_f2(u_kv, col):
    for (u0, *c0), (u1, *c1) in zip(F2, F2[1:]):
        if u0 <= u_kv <= u1:
            a, b = c0[col], c1[col]
            t = (math.log(u_kv) - math.log(u0)) / (math.log(u1) - math.log(u0))
            return math.exp(math.log(a) + t * (math.log(b) - math.log(a)))   # log-log interpolation
    return float("nan")


print("# calc_flashover.py  CALCULATION (T-060, CR-002)")
print("# IEC source 150 pF / 330 ohm, R = 3.3 kOhm; V_gap = V * R / (R + 330)")
rows = {}
for v in LEVELS:
    vg = v_gap(v)
    print()
    print("== IEC contact %.0f kV: V_gap = %.0f V (CALCULATION); peak current with arc bypassing R = %.1f A "
          "(= V / 330 ohm), with R in circuit = %.2f A" % (v / 1000, vg, v / R_IEC, v / (R_IEC + R)))
    req = []
    for e in (2.0, 2.5, 3.0, 3.5, 4.5):
        d = d_uniform(vg, e)
        req.append(("M1 uniform %.1f kV/mm" % e, d))
    req.append(("M2 Paschen (Townsend form)", solve(v_paschen, vg)))
    d3 = solve(lambda d: v_empirical_kv(d) * 1000, vg)
    req.append(("M3 empirical uniform air", d3))
    for eta in (0.7, 0.5, 0.3):
        req.append(("M4 non-uniform eta=%.1f" % eta, solve(lambda d: eta * v_empirical_kv(d) * 1000, vg)))
    req.append(("M5 IEC 60664-1 F.2 case B (homog.)", iec_f2(vg / 1000, 1)))
    req.append(("M5 IEC 60664-1 F.2 case A (inhomog.)", iec_f2(vg / 1000, 0)))
    req.append(("M5 F.2 case A at the full level", iec_f2(v / 1000, 0)))
    for name, d in req:
        print("  %-42s required gap %6.2f mm" % (name, d))
    rows[v] = dict(req)

print()
print("# Check of the models at known points (sanity, CALCULATION):")
for d in (0.5, 1.0, 2.0, 5.0, 10.0):
    print("  d = %5.1f mm: Paschen %6.0f V   empirical %6.0f V   (textbook: ~4.5 kV at 1 mm, ~30 kV at 10 mm)"
          % (d, v_paschen(d), v_empirical_kv(d) * 1000))

print()
print("# Old layout (T-050): DIN0204 vertical, 1.6 mm pads on 2.54 mm pitch -> 0.94 mm copper gap ELEx-Ex")
print("#   (CALCULATION from the footprint); vertical lead to opposite end cap ~1 mm (ASSUMPTION).")
for v in LEVELS:
    vg = v_gap(v)
    print("  %.0f kV: V_gap %.0f V vs 0.94 mm gap: uniform 3 kV/mm withstands %.0f V, IEC F.2 case A needs %.2f mm -> %s"
          % (v / 1000, vg, 0.94 * 3000, iec_f2(vg / 1000, 0), "FLASHOVER POSSIBLE" if 0.94 * 3000 < vg else "ok"))

# Design rule: the most pessimistic credible model at 4 kV (M4 eta=0.3 or IEC case A at the full 4 kV level,
# whichever is larger), rounded up to 0.5 mm. 8 kV is reported against IEC case A.
r4 = max(rows[4000.0]["M4 non-uniform eta=0.3"], rows[4000.0]["M5 F.2 case A at the full level"])
rule4 = math.ceil(r4 * 2) / 2
r8 = max(rows[8000.0]["M5 IEC 60664-1 F.2 case A (inhomog.)"], rows[8000.0]["M4 non-uniform eta=0.3"])
rule8 = math.ceil(r8 * 2) / 2
print()
print("DESIGN RULE (a) ELEx <-> Ex same channel, copper and leads:  gap >= %.1f mm  (4 kV, worst of M4 eta=0.3 %.2f mm "
      "and IEC F.2 case A at 4 kV %.2f mm, rounded up)" % (rule4, rows[4000.0]["M4 non-uniform eta=0.3"],
                                                          rows[4000.0]["M5 F.2 case A at the full level"]))
print("DESIGN RULE (b) Ex <-> ELEy any other channel (and any MPR121 / Pico net): gap >= %.1f mm (same V_gap)" % rule4)
print("REPORTED 8 kV: gap >= %.1f mm would be needed (worst of IEC F.2 case A %.2f mm and M4 eta=0.3 %.2f mm)"
      % (rule8, rows[8000.0]["M5 IEC 60664-1 F.2 case A (inhomog.)"], rows[8000.0]["M4 non-uniform eta=0.3"]))
print("NOT COVERED: flashover along the resistor body itself -> resistor pulse/ESD rating (datasheet), see calc_pulse.py")
print("RULE_4KV_MM=%.1f" % rule4)
print("RULE_8KV_MM=%.1f" % rule8)
