#!/usr/bin/env python3
"""T-060 / CR-002: pulse rating of candidate 3k3 THT resistors vs one IEC 61000-4-2 contact discharge (V1.2 record).
T-092 / ADR-023: section for the selected SMD part HPWC2512 3k0 +-5 % at the end of the output.

Requirement (CR-002): datasheet single-pulse / overload voltage >= V_R = V * R / (R + 330) = 3636 V at 4 kV
(7273 V at 8 kV reported).  CALCULATION unless labelled.

SOURCE EE-S17: Vishay Beyschlag "MBA/SMA 0204, MBB/SMA 0207, MBE/SMA 0414 - Professional", doc. 28766,
  rev. 11-Jul-2018, page 10, figure "1.2/50 Pulse": pulse load rating per IEC 60115-1 4.27, 1.2 us / 50 us,
  5 pulses at 12 s intervals, permissible change 0.5 % R + 0.05 ohm. The curves are vector paths; their
  coordinates were read from the PDF content stream (PDF points) and are reproduced below. Axis calibration
  from the same stream: x major grid lines 10 ohm = 156.04 pt ... 10 Mohm = 450.60 pt (49.09 pt/decade);
  y major grid lines 100 V = 603.42 pt, 1 kV = 643.49 pt, 10 kV = 683.55 pt (40.07 pt/decade).
  Legend (same stream): 2.0 pt line = MBE/SMA 0414, 1.0 pt = MBB/SMA 0207, 0.5 pt = MBA/SMA 0204.
  Reading uncertainty: the paths are exact, so the result is limited by the drawing itself (ASSUMPTION
  +-5 % on the voltage).
  Same document, test table: ESD (HBM, IEC 61340-3-1, 3 pos + 3 neg): 0204 2 kV, 0207 4 kV, 0414 6 kV;
  dimensions D max / L max / lead d / min. pitch M: 0207 2.5/6.5/0.6/10.0 mm, 0414 4.2/11.9/0.8/15.0 mm.
SOURCE EE-S18: Vishay BCcomponents LSR37 "High Voltage Surge Resistor", doc. 28735, rev. 21-Feb-08:
  1 k..10 k E12, +-10 % / +-20 %, 0.5 W; "ESD contact discharge 12 kV; 100 pulses; dR/R max +-20 %
  (typical +-10 %)"; D 4.0, L1 9.0, L2 10.0, lead 0.7 mm; minimum pitch for automatic insertion 15 mm.
SOURCE EE-S14b (calc_pulse.py): Yageo MFR-12: max overload voltage 400 V, no short-pulse rating.
SOURCE T90-S2 TT Electronics HPWC Series 09.23: 1.2/50 us chart, raster, read in T-090 (reports/electronics/evidence/T-090/
  charts/chartread_raw.txt, top curve = 2512): 2850 ohm 4352-4472 V, 3000 ohm 4472 V, 3150 ohm 4596 V. Reading uncertainty
  +-5 % (ASSUMPTION). It is a 1.2/50 us rating, not an IEC 61000-4-2 ESD rating (same basis as ADR-019).
"""
import math

R, R_IEC, C_IEC = 3300.0, 330.0, 150e-12
X10, XDEC = 156.04, 49.09          # x of 10 ohm, pt per decade
Y100, YDEC = 603.42, 40.07         # y of 100 V, pt per decade

# polylines (x, y) in PDF points: start, knee, end of plateau
CURVES = {
    "MBE/SMA 0414": [(156.03, 617.90), (288.84, 671.684), (465.37, 671.537)],
    "MBB/SMA 0207": [(156.03, 603.42), (303.51, 662.702), (465.37, 662.745)],
    "MBA/SMA 0204": [(156.03, 595.79), (292.43, 655.782), (450.57, 655.702)],
}


def x_of(r):
    return X10 + XDEC * math.log10(r / 10.0)


def v_of(y):
    return 100.0 * 10 ** ((y - Y100) / YDEC)


def umax(curve, r):
    x = x_of(r)
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            return v_of(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    raise ValueError("R outside the graph")


print("# calc_pulse_rated.py  CALCULATION (T-060, CR-002)")
need = {v: v * R / (R + R_IEC) for v in (4000.0, 8000.0)}
for v, vr in need.items():
    e = 0.5 * C_IEC * v ** 2 * R / (R + R_IEC)
    print("IEC %.0f kV contact: V_R = %.0f V, energy in R = %.2f mJ, tau = %.2f us" % (v / 1000, vr, e * 1e3, (R + R_IEC) * C_IEC * 1e6))
print()
print("%-16s %-30s %10s %9s %9s  %s" % ("part", "rating basis", "rating", "4 kV", "8 kV", "size (D x L, pitch)"))
rows = []
size = {"MBE/SMA 0414": "4.2 x 11.9 mm, >= 15.0 mm", "MBB/SMA 0207": "2.5 x 6.5 mm, >= 10.0 mm",
        "MBA/SMA 0204": "1.6 x 3.6 mm, >= 5.0 mm"}
for name, c in CURVES.items():
    u = umax(c, R)
    rows.append((name, "1.2/50 us graph @3k3", u, size[name]))
rows.append(("Vishay LSR37", "ESD contact 12 kV (on R alone)", 12000 * R / (R + R_IEC), "4.0 x 10.0 mm, >= 15 mm"))
rows.append(("Yageo MFR-12", "max overload voltage", 400.0, "1.8 x 3.3 mm (0204)"))
for name, basis, u, sz in rows:
    print("%-16s %-30s %8.0f V %9s %9s  %s" % (name, basis, u, "PASS" if u >= need[4000.0] else "FAIL",
                                               "PASS" if u >= need[8000.0] else "FAIL", sz))
u0414 = umax(CURVES["MBE/SMA 0414"], R)
print()
print("MBE/SMA 0414 3k3: margin at 4 kV = %.2f (rating / V_R); with -5 %% reading error %.2f" %
      (u0414 / need[4000.0], 0.95 * u0414 / need[4000.0]))
print("HBM equivalence (100 pF / 1500 ohm on R alone): 0414 6 kV -> %.0f V across 3k3; 0207 4 kV -> %.0f V"
      % (6000 * R / (R + 1500), 4000 * R / (R + 1500)))
# T-073 / C2-003: energy of the rating pulse = (1/R) * integral V(t)^2 dt (the T-060 version used the integral of V,
# 1.44 * 50 us, which overstated the energy about 2x). Standard 1.2/50 us double exponential (IEC 60060-1 form,
# ASSUMPTION for the generator used by Vishay): V(t) = k * Vpk * (exp(-t/T2) - exp(-t/T1)), T1 = 0.4074 us,
# T2 = 68.22 us, k = 1/max(...) (CALCULATION below). Single-exponential cross-check: tail T = 50 us / ln 2,
# integral V^2 dt = Vpk^2 * T / 2.
T1, T2 = 0.4074e-6, 68.22e-6
tpk = math.log(T2 / T1) * T1 * T2 / (T2 - T1)
k = 1.0 / (math.exp(-tpk / T2) - math.exp(-tpk / T1))
i_v2 = k ** 2 * (T2 / 2 + T1 / 2 - 2 * T1 * T2 / (T1 + T2))          # integral of (V/Vpk)^2 dt, s
i_v2_exp = 50e-6 / math.log(2) / 2
e_rate = u0414 ** 2 / R * i_v2
print("Rating pulse energy: integral (V/Vpk)^2 dt = %.2f us (double exp.; single exp. %.2f us) -> %.0f mJ into 3k3 at %.0f V"
      % (i_v2 * 1e6, i_v2_exp * 1e6, e_rate * 1e3, u0414))
c = CURVES["MBE/SMA 0414"]
slope = ((c[1][1] - c[0][1]) / YDEC) / ((c[1][0] - c[0][0]) / XDEC)
r_knee = 10.0 * 10 ** ((c[1][0] - X10) / XDEC)
v_plat = v_of(c[1][1])
print("MBE/SMA 0414 chart: log-log slope below the knee %.3f (0.5 = constant V^2/R, energy-limited); knee at %.0f ohm;"
      " plateau %.0f V (voltage-limited above the knee)" % (slope, r_knee, v_plat))
print("  energy at the knee %.0f mJ (same constant as at 3k3 -> 3k3 lies on the energy-limited branch)"
      % (v_plat ** 2 / r_knee * i_v2 * 1e3))
e4 = 0.5 * C_IEC * 4000 ** 2 * R / (R + R_IEC)
print("  one IEC 4 kV strike puts %.2f mJ into R (%.0fx less than the rating pulse) and %.0f V across it, below the"
      " %.0f V plateau (%.2fx); the 3k3 chart value %.0f V is used as the acceptance limit (conservative: it is an"
      " energy limit for a pulse whose tail T = %.0f us is %.0fx the IEC tau %.2f us)"
      % (e4 * 1e3, e_rate / e4, need[4000.0], v_plat, v_plat / need[4000.0], u0414, 50 / math.log(2),
         50e-6 / math.log(2) / ((R + R_IEC) * C_IEC), (R + R_IEC) * C_IEC * 1e6))
print("  8 kV: %.0f V across R exceeds both the 3k3 chart value and the %.0f V plateau -> FAIL either way"
      % (need[8000.0], v_plat))
print("V1.2 (superseded by ADR-023): Vishay MBE/SMA 0414, 3k3 1 %% (MBE04140C3301FC100): %.0f V >= %.0f V at 4 kV (PASS), < %.0f V at 8 kV (FAIL)"
      % (u0414, need[4000.0], need[8000.0]))
print("V1.2 alternative for 8 kV: Vishay LSR37 3k3 10 % (LSR3700003301KA100), ESD 12 kV rated; tolerance +-10 % and up to"
      " +-20 % drift after 100 strikes")

# ---- T-092: selected SMD part (ADR-023 D-1)
print()
print("# SMD board: TT Electronics HPWC2512 3k0 +-5 %; ratings SOURCE T90-S2 chart read (T-090), +-5 % reading ASSUMPTION")
HPWC = ((2850.0, 4352.0), (3000.0, 4472.0), (3150.0, 4596.0))
print("%-9s %10s %11s %11s %9s %9s %10s %10s %10s" % ("R ohm", "rating V", "V_R@4kV", "V_R@8kV", "m@4kV", "m@8kV", "m@4kV -5%", "E@4kV mJ", "Ipk@4kV A"))
worst4 = float("inf")
for r_h, rate in HPWC:
    v4, v8 = 4000.0 * r_h / (r_h + R_IEC), 8000.0 * r_h / (r_h + R_IEC)
    worst4 = min(worst4, rate / v4)
    print("%-9.0f %10.0f %11.0f %11.0f %9.2f %9.2f %10.2f %10.2f %10.2f" % (
        r_h, rate, v4, v8, rate / v4, rate / v8, 0.95 * rate / v4, 0.5 * C_IEC * 4000.0 ** 2 * r_h / (r_h + R_IEC) * 1e3, 4000.0 / (r_h + R_IEC)))
print("SELECTED: HPWC2512 3k0: rating margin at 4 kV >= %.2f over the tolerance band -> %s; at 8 kV margin %.2f -> FAIL (R-006 open)"
      % (worst4, "PASS" if worst4 >= 1.0 else "FAIL", 4472.0 / (8000.0 * 3000.0 / 3330.0)))
print("  with -5 %% chart reading error, worst margin at 4 kV: %.2f (%s)" % (0.95 * worst4, "PASS" if 0.95 * worst4 >= 1.0 else "FAIL"))
