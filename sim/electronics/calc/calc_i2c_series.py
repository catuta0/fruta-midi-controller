#!/usr/bin/env python3
"""T-055 / ADR-009 D-9: 220R series resistors between the Pico I2C pins and the bus. CALCULATION.

Topology (hardware @ T-055): Pico GP26/GP27 -> R16/R15 220R -> bus node (J1 hole, R13/R14 4k7 to 3V3)
-> hand wire -> module host side (10k to VIN = 3V3) -> BSS138 -> MPR121 (10k to its 3.3 V out).
Inputs: MPR121 VOL <= 0.5 V at 6 mA, VIL = 0.3*VDD (SOURCE EE-S01); module 10k pull-ups (EE-S02/S03);
RP2040 VIL max 0.8 V and VOL <= 0.4 V at the drive current (ASSUMPTION, RP2040 data sheet not opened);
BSS138 RDS(on) <= 10 ohm at VGS ~3 V (ASSUMPTION); Pico 3V3 3.2..3.4 V (ASSUMPTION).
"""
RS = 220.0
V = 3.4                                     # worst case for currents
R_BUS = 1 / (1 / 4.7e3 + 1 / 10e3)          # PCB 4k7 || module host-side 10k
I_CHIP = V / 10e3                           # module chip-side 10k, flows through the BSS138 when low
print("# calc_i2c_series.py  CALCULATION")
print("Bus pull-up R = 4k7 || 10k = %.0f ohm" % R_BUS)

i_low = V / R_BUS + I_CHIP
print("\n## Pico drives low (master: START, SCL, address/data bits)")
print("  sink current through 220R = %.2f mA" % (i_low * 1e3))
v_bus = 0.4 + i_low * RS
v_chip = v_bus + I_CHIP * 10                # + BSS138 drop
for vdd in (3.10, 3.295):
    print("  bus/module low level = 0.4 + %.2f mA * 220 = %.3f V; at MPR121 %.3f V vs VIL = 0.3*%.3f = %.3f V -> margin %.3f V %s"
          % (i_low * 1e3, v_bus, v_chip, vdd, 0.3 * vdd, 0.3 * vdd - v_chip, "PASS" if v_chip < 0.3 * vdd else "FAIL"))
print("  note: I2C spec VOL 0.4 V applies at the driver pin (Pico), which is unchanged; the receiver threshold is what matters")

print("\n## MPR121 drives low (ACK, read data)")
i_mod = V / R_BUS + I_CHIP
vol_mod_lin = 0.5 * i_mod / 6e-3            # VOL scaled from 0.5 V @ 6 mA (ASSUMPTION: resistive output)
for name, vol in (("datasheet bound 0.5 V", 0.5), ("scaled to %.2f mA" % (i_mod * 1e3), vol_mod_lin)):
    v_pico = vol + i_mod * 10 + 0.0          # no pull-up current through 220R (pull-ups on the bus side); Pico input leakage only
    print("  %-26s Pico pin sees %.3f V vs RP2040 VIL 0.8 V (ASSUMPTION) -> margin %.3f V %s"
          % (name, v_pico, 0.8 - v_pico, "PASS" if v_pico < 0.8 else "FAIL"))

print("\n## Rise time at 400 kHz (t_r = 0.8473 * R * C, limit 300 ns, SOURCE EE-S01 Table 7)")
c_pico = 5e-12                               # ASSUMPTION, behind the 220R
for cb in (20e-12, 40e-12, 60e-12):
    tr_bus = 0.8473 * R_BUS * cb
    tr_pico = tr_bus + 2.2 * RS * c_pico      # extra RC seen at the Pico pin
    print("  C_bus %2.0f pF: bus t_r = %5.1f ns, at Pico pin <= %5.1f ns -> %s"
          % (cb * 1e12, tr_bus * 1e9, tr_pico * 1e9, "PASS" if tr_pico <= 300e-9 else "FAIL"))

print("\n## Fault: J1 hand wire placed on a supply pin (S1/S2 original = VIN/3V3o, S6/S7 QT = 3V3o/VCC)")
print("  Pico drives low into 3.4 V: I = 3.4 / 220 = %.1f mA (+ bus pull-ups shorted to the rail: no current)" % (V / RS * 1e3))
print("  Without R15/R16 the current is limited only by the pad driver (not bounded by any figure in hand).")
print("  Wire on GND (S3 orig / S5 QT): bus held low, pull-up current %.2f mA, no damage; I2C fails -> firmware 'not found' LED." % (V / R_BUS * 1e3))
print("  Wire on IRQ/INT/ADDR: no supply contact, I2C fails or address changes; no damage.")
