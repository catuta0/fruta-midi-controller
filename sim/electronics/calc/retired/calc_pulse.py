#!/usr/bin/env python3
"""T-053: series resistor (Yageo MFR-12, 3.3k) vs one IEC 61000-4-2 contact discharge. CALCULATION.

SOURCE (Yageo leaded resistors datasheet, MFR series table, read 2026-11-03; EE-S14b):
  MFR-12: 1/6 W at 70 C, max working voltage 200 V, max overload voltage 400 V, dielectric withstanding 300 V;
  short-time overload 2.5 x RCWV for 5 s; pulse overload 4 x RCWV, 10000 cycles (1 s on / 25 s off).
  No short-pulse (ns-us), surge or ESD rating or pulse-load curve is published.
IEC model 150 pF / 330 ohm (EE-S16).
"""
import math
P, R = 1 / 6, 3.3e3
V_OVL, V_WORK = 400.0, 200.0
rcwv = min(math.sqrt(P * R), V_WORK)
print("# calc_pulse.py  CALCULATION")
print("RCWV = min(sqrt(P*R), 200 V) = %.2f V" % rcwv)
e_sto = (2.5 * rcwv) ** 2 / R * 5
e_po = (4 * rcwv) ** 2 / R * 1
print("Short-time overload (2.5 x RCWV, 5 s): %.2f V, %.2f J   Pulse overload (4 x RCWV, 1 s): %.2f V, %.2f J per pulse"
      % (2.5 * rcwv, e_sto, 4 * rcwv, e_po))
for v in (4000, 8000):
    ipk = v / (330 + R)
    vr = ipk * R
    e = 0.5 * 150e-12 * v ** 2 * R / (R + 330)
    tau = (R + 330) * 150e-12
    print("IEC %d kV: Ipk %.2f A, peak voltage across R %.0f V = %.1f x max overload 400 V; energy %.2f mJ in tau %.2f us "
          "= 1/%.0f of one 1-s pulse-overload pulse" % (v // 1000, ipk, vr, vr / V_OVL, e * 1e3, tau * 1e6, e_po / e))
print("Verdict: energy is far below the 1-s ratings, but those ratings do not cover us pulses (adiabatic film heating),")
print("and the peak voltage exceeds the 400 V max overload voltage at both levels -> not supported by datasheet data.")
