#!/usr/bin/env python3
"""T-050: rail currents, track currents, IPC-2221 trace temperature rise, dissipation, clearance. CALCULATION.

The PCB carries only the Pico 3V3 output (pin 36) and GND; VBUS/VSYS stay on the Pico (no track).
"""
import math

V33 = 3.30             # V, Pico 3V3 nominal (SOURCE Pico pinout "3V3 Out")
V33_MAX = 3.40         # V, ASSUMPTION +3 % regulator tolerance (RT6150B not checked: open item)

loads = [  # name, current A (worst case), label/source
    ("MPR121 IDD run, ESI 1 ms, CDC 63 uA", 393e-6, "SOURCE MPR121 Table 5 (typ; no max given)"),
    ("MPR121 peak during measurement", 1e-3, "SOURCE MPR121 Table 5 (peak, used instead of 393 uA)"),
    ("LDO quiescent (AP2112 max 80 uA; MIC5225 ASSUMPTION <=100 uA)", 100e-6, "SOURCE AP2112 / ASSUMPTION"),
    ("Original rev.: red IRQ LED via 1k from 3.3V (Vf 1.8 V ASSUMPTION)", (V33 - 1.8) / 1e3, "CALCULATION"),
    ("STEMMA QT rev.: green power LED via 10k (Vf 2.0 V ASSUMPTION)", (V33 - 2.0) / 10e3, "CALCULATION"),
    ("I2C pull-ups low (2 lines x (10k host + 10k chip side))", 2 * 2 * V33 / 10e3, "CALCULATION, Adafruit schematics"),
    ("Octave pot 10k across 3V3-AGND", V33 / 10e3, "CALCULATION"),
    ("Button pressed: RP2040 internal pull-up (50 k min, ASSUMPTION)", V33 / 50e3, "CALCULATION"),
]
print("# calc_power.py  CALCULATION")
print("## Load on Pico 3V3 (pin 36) through PCB tracks, worst case (both LED variants counted)")
tot = 0.0
for n, i, src in loads:
    if "IDD run" in n:
        print("  %-66s %8.3f mA  (%s; superseded by peak)" % (n, i * 1e3, src))
        continue
    tot += i
    print("  %-66s %8.3f mA  (%s)" % (n, i * 1e3, src))
print("  %-66s %8.3f mA" % ("TOTAL (worst case)", tot * 1e3))
print("  Pico 3V3 pin recommendation < 300 mA (SOURCE pico.pinout.xyz / Pico datasheet): margin %.0fx" % (0.3 / tot))

# ---------------------------------------------------------------- IPC-2221 external layer
K_EXT = 0.048          # SOURCE IPC-2221 (external conductors): I = k * dT^0.44 * A^0.725, A in mil^2
T_CU_MIL = 35e-3 / 0.0254   # 35 um copper in mil


def ipc_dt(i, w_mm):
    area = (w_mm / 0.0254) * T_CU_MIL
    return (i / (K_EXT * area ** 0.725)) ** (1 / 0.44)


def ipc_i(dt, w_mm):
    area = (w_mm / 0.0254) * T_CU_MIL
    return K_EXT * dt ** 0.44 * area ** 0.725


print()
print("## IPC-2221 external layer, 35 um Cu. CALCULATION")
cases = [("3V3/GND power track 1.2 mm", 1.2, tot), ("signal track 1.0 mm (I2C, button, pot)", 1.0, 1e-3),
         ("module S-row stub 0.8 mm", 0.8, tot), ("electrode track 1.0 mm (63 uA charge)", 1.0, 63e-6),
         ("BOUND: 0.8 mm carrying full Pico 3V3 limit 300 mA", 0.8, 0.3)]
for n, w, i in cases:
    print("  %-52s I=%9.4f A  dT=%10.2e C   I(dT=10C)=%.2f A" % (n, i, ipc_dt(i, w), ipc_i(10, w)))

# resistance / voltage drop of the longest power path (ASSUMPTION length 120 mm, 1.2 mm wide)
RHO = 1.72e-8
L, W = 0.120, 1.2e-3
r_tr = RHO * L / (W * 35e-6)
print("  3V3 path 120 mm x 1.2 mm: R = %.1f mOhm, drop at %.1f mA = %.3f mV (CALCULATION, length ASSUMPTION)" %
      (r_tr * 1e3, tot * 1e3, r_tr * tot * 1e3))

# ---------------------------------------------------------------- dissipation
print()
print("## Dissipation. CALCULATION")
print("  Octave pot 10k: P = V^2/R = %.2f mW vs 50 mW rating (SOURCE Alps RK09K1130A5R page) -> margin %.0fx" %
      (V33_MAX ** 2 / 10e3 * 1e3, 50e-3 / (V33_MAX ** 2 / 10e3)))
p_rs = (63e-6) ** 2 * 3.3e3
print("  Series R 3.3k, DC: P = (63 uA)^2 * 3.3k = %.2e W (negligible)" % p_rs)
e8 = 0.5 * 150e-12 * 8000 ** 2 * 3.3e3 / (3.3e3 + 330)
print("  Series R 3.3k, one IEC 8 kV contact pulse: E = %.2f mJ in %.2f us (CALCULATION); pulse rating of the chosen "
      "resistor not verified (open item)" % (e8 * 1e3, (3.3e3 + 330) * 150e-12 * 1e6))
print("  Board total from 3V3: P = %.1f mW" % (V33 * tot * 1e3))

# ---------------------------------------------------------------- clearance vs voltage
print()
print("## Clearance vs voltage")
print("  Highest steady voltage on the PCB: 3.3 V (VBUS stays on the Pico). IPC-2221B Table 6-1, B2 (external,")
print("  uncoated, <= 3050 m), 0-15 V: 0.10 mm minimum (SOURCE). Design rule 0.6 mm -> margin 6x.")
for v in (4000, 8000):
    print("  ESD transient %d kV: uniform-field air breakdown ~3 kV/mm (ASSUMPTION) -> arcs across gaps < %.1f mm;"
          " screw terminal pitch 5.08 mm, electrode track gaps >= 0.6 mm: arcing between adjacent electrode tracks is"
          " possible at %d kV (not damaging by itself; the series R still sits between each track and the MPR121)." %
          (v // 1000, v / 3000, v // 1000))
