#!/usr/bin/env python3
"""T-091 / ADR-023 D-2: R-011 re-derived for the off-board potentiometer (3 wires, frame not tied to the board).

Every result is CALCULATION from the inputs below; no ESD test exists. Run with any Python 3.
Inputs
  IEC 61000-4-2 contact network 150 pF / 330 ohm, first peak 3.75 A/kV, I(30 ns) 2 A/kV  SOURCE EE-S16 (recalled, standard not opened)
  Wire inductance 0.8 ... 1.2 uH/m (ASSUMPTION, single wire, no return plane)
  Wire length 0.05 ... 0.30 m (ASSUMPTION: builder's choice, no enclosure defined; to be measured on the unit)
  Frame-to-lug clearance inside the pot 0.5 ... 2.0 mm (ASSUMPTION: Alps/panel pot, drawing not opened)
  Flashover rule worst model calc_flashover.py: 3.5 mm at 4 kV (CALCULATION, ASSUMPTION inputs)
  C1 100 nF +-10 % X7R (T-090, datasheet not opened), 3.3 V bias derating ignored (ASSUMPTION, << 50 V rating)
NOT available (stay unquantified): RP2040 ADC/AGND pad ESD rating (R-010: HBM rating found covers digital FT pins only),
latch-up threshold of the analog front end, internal frame-to-lug distance of the bought pot, final wire length.
"""
import math

C_ESD, R_ESD = 150e-12, 330.0
KV = (4.0, 8.0)
C1 = 100e-9
L_PM = (0.8e-6, 1.2e-6)
LEN = (0.05, 0.30)
GAP = (0.5, 2.0)
RULE_4KV = 3.5
print("# calc_r011_offboard_pot.py  CALCULATION (T-091, inputs: SOURCE recalled / ASSUMPTION, see header)")
print("Strike cases (frame not tied to the board):")
print("  A plastic shaft + insulating knob: no conductive contact point; the discharge must find a lug by air or creepage.")
print("  B metal shaft, frame floating: frame-to-lug gap breaks down at far below 4 kV (rule 3.5 mm vs gap %.1f..%.1f mm ASSUMPTION): " % GAP +
      "%s" % ("gap below the 3.5 mm rule at every value in the sweep" if max(GAP) < RULE_4KV else "gap covers part of the rule"))
print("    so the strike is expected to reach a lug: lug 1 (3V3), 2 (wiper) or 3 (AGND), no series resistor on any of the three wires.")
print("  C metal shaft, frame tied to the AGND wire by the builder: V1.2 path with a longer wire (frame to AGND without series R).")
print()
for kv in KV:
    v = kv * 1e3
    q = C_ESD * v
    ipk = 3.75 * kv
    print("%.0f kV: Q = C_esd V = %.2f uC; first peak (IEC) %.1f A; resistive plateau %.1f A; energy 0.5 C V^2 = %.2f mJ"
          % (kv, q * 1e6, ipk, v / R_ESD, 0.5 * C_ESD * v ** 2 * 1e3))
    dv = q / C1
    dvmin = q / (C1 * 1.1)
    print("  strike into the wiper net, all charge into C1: dV_C1 = %.1f V (%.1f V at C1 +10 %%), above the 3.3 V rail by %.1f V; "
          "above the 3.6 V ADC input maximum assumed for RP2040 pads (ASSUMPTION, R-010)" % (dv, dvmin, dv - 3.3))
    print("  so clamping into the ADC pad diodes is expected; peak diode current bounded by the source impedance, not by the board")
    print("  strike into AGND / 3V3 lug: AGND/3V3 wire is in series with Pico pin 33/36, no resistor, no C1 in the path for 3V3")
    for L in (L_PM[0] * LEN[0], L_PM[1] * LEN[1]):
        didt = 0.8 * ipk / 0.8e-9
        print("    wire L %.0f nH: L di/dt (0.8 Ipk / 0.8 ns) = %.0f V, capped by the %.0f V source: %.0f V across the wire before the arc settles"
              % (L * 1e9, L * didt, v, min(L * didt, v)))
print()
print("Result (CALCULATION, order of magnitude only):")
print("  - Moving the pot off the board removes the V1.2 hard copper link from the frame to AGND (tabs) (design fact, ADR-023).")
print("  - A metal shaft is still NOT protected: the discharge finds a lug across a sub-3.5 mm internal gap, then a wire with no series R.")
print("  - The extra wire inductance (40-360 nH) slows the edge but does not limit the 0.6-1.2 uC charge delivered.")
print("  - C1 holds a wiper strike to %.0f-%.0f V (order of magnitude) for that charge; this does not prove the ADC pad survives." % (0.6e-6 / C1, 1.2e-6 / C1))
print("Unquantified, remains open: RP2040 pad rating and latch-up (R-010), bought-pot internal gap, wire length, any metal enclosure.")
print("Recommendation carried to the manual: insulated (plastic) shaft and insulating knob. Physical ESD step 2b (R-011) unchanged.")
