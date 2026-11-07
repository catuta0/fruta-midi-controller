#!/usr/bin/env python3
"""T-060 / CR-002: pulse rating of candidate 3k3 THT resistors vs one IEC 61000-4-2 contact discharge.

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
print("Energy check: the 1.2/50 us test pulse at the 0414 rating puts about %.0f mJ into 3k3 (V^2/R * 1.44 * 50 us),"
      % (u0414 ** 2 / R * 1.44 * 50e-6 * 1e3))
print("  vs %.2f mJ for one IEC 4 kV strike -> the IEC pulse is far inside the energy limit; voltage is the binding limit."
      % (0.5 * C_IEC * 4000 ** 2 * R / (R + R_IEC) * 1e3))
print("SELECTED: Vishay MBE/SMA 0414, 3k3 1 %% (MBE04140C3301FC100): %.0f V >= %.0f V at 4 kV (PASS), < %.0f V at 8 kV (FAIL)"
      % (u0414, need[4000.0], need[8000.0]))
print("ALTERNATIVE for 8 kV: Vishay LSR37 3k3 10 % (LSR3700003301KA100), ESD 12 kV rated; tolerance +-10 % and up to"
      " +-20 % drift after 100 strikes")
