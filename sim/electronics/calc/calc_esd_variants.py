#!/usr/bin/env python3
"""T-050, updated T-096 for the SMD board (R1-R12 = RC2512FK-073K3L 3k3 +-1 %, ADR-026): ESD current limiting and variant
comparison for the electrode path. CALCULATION.

Inputs (labels):
  IEC 61000-4-2 human-metal model: 150 pF, 330 ohm; first peak 3.75 A/kV contact (SOURCE IEC 61000-4-2 Table 4).
  MPR121 HBM rating +-2000 V (SOURCE MPR121 datasheet Table 4); HBM network 100 pF / 1500 ohm (SOURCE JS-001).
  Equivalent pin current limit = 2000 V / 1500 ohm = 1.33 A (CALCULATION). Using it for an IEC-shaped
  pulse is an ASSUMPTION (pulse width and charge differ; see charge ratio printed below).
  Series resistor bypass of the sub-ns first peak by parasitic capacitance is ignored (ASSUMPTION).
"""
import math

C_IEC, R_IEC = 150e-12, 330.0
C_HBM, R_HBM, V_HBM = 100e-12, 1500.0, 2000.0
I_LIM = V_HBM / R_HBM
LEVELS = [2000, 4000, 6000, 8000]          # IEC contact levels 1..4 (SOURCE IEC 61000-4-2 Table 1)
R_SWEEP = [0, 1e3, 2.2e3, 2.7e3, 2.85e3, 3.0e3, 3.267e3, 3.3e3, 3.333e3, 4.7e3, 6.8e3, 10e3, 22e3, 47e3, 100e3]


def ipk(v, r):
    if r == 0:
        return 3.75 * v / 1000             # IEC first peak, A
    return v / (R_IEC + r)


print("# calc_esd_variants.py  CALCULATION")
print("# HBM-equivalent pin current limit I_lim = %.0f V / %.0f ohm = %.2f A" % (V_HBM, R_HBM, I_LIM))
print("# Charge per IEC discharge Q = 150 pF * V; HBM 2 kV charge = %.2f uC" % (C_HBM * V_HBM * 1e6))
print()
print("%-7s" % "R" + "".join("%12s" % ("Ipk@%dkV" % (v // 1000)) for v in LEVELS) + "%14s%14s" % ("tau@R (us)", "E_R@8kV (mJ)"))
for r in R_SWEEP:
    tau = (R_IEC + r) * C_IEC * 1e6
    e_r = 0.5 * C_IEC * 8000 ** 2 * (r / (R_IEC + r)) * 1e3
    print("%-7s" % ("%gk" % (r / 1e3) if r else "0") + "".join("%11.2fA" % ipk(v, r) for v in LEVELS) +
          "%14.3f%14.2f" % (tau, e_r))
print()
for v in LEVELS:
    rmin = max(0.0, v / I_LIM - R_IEC)
    print("R_min for Ipk <= %.2f A at %d kV contact: %.0f ohm   (charge %.2f uC = %.1f x HBM 2 kV charge)" %
          (I_LIM, v // 1000, rmin, C_IEC * v * 1e6, C_IEC * v / (C_HBM * V_HBM)))

# ---------------------------------------------------------------- object capacitance (fruit) CALCULATION
EPS0 = 8.854e-12
print()
print("# Self-capacitance of an isolated conductive sphere C = 4*pi*eps0*r (CALCULATION):")
for name, r in (("cherry tomato r=1.5 cm", 0.015), ("apple r=4 cm", 0.04), ("melon r=8 cm", 0.08), ("watermelon r=15 cm", 0.15)):
    print("  %-24s %.1f pF" % (name, 4 * math.pi * EPS0 * r * 1e12))
print("  Human body to earth: 100-200 pF (SOURCE: HBM uses 100 pF; IEC 61000-4-2 uses 150 pF).")
print("  Sweep 10 pF..1000 pF covers object + 1 m wire (ASSUMPTION 30-50 pF/m) untouched and a hand in")
print("  contact (+100..300 pF) with margin; 2000 pF is the MPR121 datasheet upper bound (SOURCE).")

# ---------------------------------------------------------------- variant comparison
R_SEL = 3.3e3            # ADR-026, RC2512FK-073K3L 3k3
R_LOW = R_SEL * 0.99     # -1 % tolerance (SOURCE Mouser / YAGEO RC_L): worst for the current
print()
print("# Variant comparison at identical inputs (IEC contact 4 kV and 8 kV, CDC_min = 1 uA, C_ext 10..1000 pF)")
LEAK_1N4148 = 25e-9      # A, max at VR = 20 V, 25 C (SOURCE Vishay 1N4148 datasheet); value at <=3.3 V is lower (ASSUMPTION: use the bound)
C_1N4148 = 4e-12         # F, at VR = 0 V (SOURCE Vishay 1N4148)
LEAK_TPD = 10e-9         # A max (SOURCE TI TPD4E05U06 product page)
C_TPD = 0.5e-12          # F typ (SOURCE TI TPD4E05U06 product page)
variants = [
    ("a) none", 0, 0, 0, "n/a", "yes (no parts)"),
    ("b) series R 3k3 2512 (selected)", R_SEL, 0, 0, "RC2512", "yes, as routed (T-091)"),
    ("b1) series R 3k3 at -1 %", R_LOW, 0, 0, "RC2512", "yes, as routed (T-091)"),
    ("b') series R 10k", 10e3, 0, 0, "2512", "yes"),
    ("c) R 3k3 + TPD4E05U06 x3 to GND", R_SEL, C_TPD, LEAK_TPD, "SMD USON-10 2.5x1 mm", "no: 0.5 mm pitch vs 0.6 mm clearance rule"),
    ("d) R 3k3 + 2x1N4148 to 3V3/GND", R_SEL, 2 * C_1N4148, 2 * LEAK_1N4148, "DO-35 or SOD", "partial: 3V3 bus crosses 12 tracks (no bridges on one layer)"),
]
print("%-36s %9s %9s %10s %11s %-22s %s" % ("variant", "Ipk@4kV", "Ipk@8kV", "C_add pF", "leak/1uA %", "parts", "single-layer home-etch"))
for name, r, c_add, leak, parts, layout in variants:
    i4, i8 = ipk(4000, r), ipk(8000, r)
    if leak:
        # with an external clamp the residual current into the pin is set by the clamp, not by R (ASSUMPTION:
        # the clamp conducts first; pin sees the clamp voltage through R)
        pass
    print("%-36s %8.2fA %8.2fA %10.1f %11.1f %-22s %s" %
          (name, i4, i8, c_add * 1e12, leak / 1e-6 * 100, parts, layout))
print()
print("# Current / I_lim = %.2f A:  a) %.1fx over at 4 kV  b) 3k3 %.2fx (4 kV), %.2fx (8 kV)  b1) 3267 ohm %.2fx (4 kV), %.2fx (8 kV)  b') %.2fx (8 kV)" %
      (I_LIM, ipk(4000, 0) / I_LIM, ipk(4000, R_SEL) / I_LIM, ipk(8000, R_SEL) / I_LIM,
       ipk(4000, R_LOW) / I_LIM, ipk(8000, R_LOW) / I_LIM, ipk(8000, 10e3) / I_LIM))
print("# Margin I_lim / Ipk at 4 kV: 3k3 %.2f, 3267 ohm %.2f, 3333 ohm %.2f (CALCULATION; I_lim is an ASSUMPTION for an IEC-shaped pulse)"
      % (I_LIM / ipk(4000, R_SEL), I_LIM / ipk(4000, R_LOW), I_LIM / ipk(4000, 3333.0)))
print("# Sensitivity: see sim_electrode.out, rows 3.267k / 3.3k / 3.333k (selected part) and 10k (b').")
