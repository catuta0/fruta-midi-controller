#!/usr/bin/env python3
"""T-050: supply seen by the MPR121 and I2C levels / rise time, both Adafruit 1982 revisions. CALCULATION.

Topology (SOURCE: adafruit/Adafruit-MPR121-PCB Eagle schematics, nets read 2026-10-30):
  original : JP2.1 VIN -> MIC5225-3.3 (U4) IN+EN; OUT = 3.3V -> MPR121 VDD. BSS138 Q1/Q2 gate = 3.3V,
             source = SDA_3V/SCL_3V (10k R1/R3 to 3.3V), drain = SDA_5V/SCL_5V (10k R2/R4 to VIN) -> JP2.5/6.
  STEMMA QT: JP2.1 VCC -> AP2112K-3.3 (U2) IN+EN; OUT = 3.3V -> MPR121 VDD; dual BSS138 Q3, 10k R8 pack:
             two to VCC (host side), two to 3.3V (chip side).
"""
V_PICO_NOM, V_PICO_MIN, V_PICO_MAX = 3.30, 3.20, 3.40   # ASSUMPTION +-3 % (RT6150B tolerance not verified)
I_LOAD = 3.3e-3                                         # A, worst-case module load (calc_power.py)

# LDO dropout at low current
DROP = {
    "AP2112K-3.3 (STEMMA QT)": (0.005, 0.008, "SOURCE Diodes AP2112 datasheet: 5 typ / 8 max mV at 10 mA"),
    "MIC5225-3.3 (original)": (0.050, 0.100, "SOURCE 50 mV typ at 100 uA (Microchip DS20006683A via search, "
                               "not opened); max 100 mV at <=3.3 mA is ASSUMPTION"),
}
print("# calc_i2c.py  CALCULATION")
print("## MPR121 VDD when the module input is fed from Pico 3V3 (LDO in dropout)")
for name, (typ, mx, src) in DROP.items():
    lo = V_PICO_MIN - mx
    print("  %-26s VDD typ %.3f V, worst-case min %.3f V  (%s)" % (name, V_PICO_NOM - typ, lo, src))
    print("  %-26s MPR121 VDD range 2.0..3.6 V (SOURCE Table 5): margin to 2.0 V = %.2f V; to 3.6 V abs max = %.2f V" %
          ("", lo - 2.0, 3.6 - V_PICO_MAX))
print("  AUTOCONFIG limits are written for VDD=3.3 V (USL 200 = (3.3-0.7)/3.3*256 = %.1f). At VDD=3.10 V Eqn.1 gives "
      "USL=%.1f: library USL 200 is %.1f%% above -> charge field nearer the rail (headroom VDD-0.7 shrinks to %.2f V)."
      % ((3.3 - 0.7) / 3.3 * 256, (3.1 - 0.7) / 3.1 * 256, (200 / ((3.1 - 0.7) / 3.1 * 256) - 1) * 100,
         3.1 - 200 / 256 * 3.1))

print()
print("## I2C idle levels (Pico side = drain side of BSS138)")
for v in (V_PICO_MIN, V_PICO_NOM, V_PICO_MAX):
    print("  Pico 3V3 = %.2f V: SDA/SCL idle on Pico side = VIN = %.2f V (pull-up to the module VIN, which IS the Pico 3V3)"
          " -> never above RP2040 IOVDD (same rail).  MPR121 side idles at its VDD <= %.2f V <= VDD+0.3 limit." %
          (v, v, v))
print("  BSS138 gate = MPR121 VDD ~3.2-3.3 V; VGS(th) 0.8..1.5 V (SOURCE onsemi BSS138): switch conducts when the Pico pulls low."
      " VIH(MPR121) = 0.7*VDD = %.2f V; level shifter passes Pico high = 3.2..3.4 V on drain, chip side pulled to VDD by 10k." %
      (0.7 * 3.29))

# rise time
print()
print("## Rise time on the Pico side, 30 -> 70 %% (t_r = 0.8473 R C), I2C fast mode limit 300 ns at 400 kHz (SOURCE MPR121 Table 7)")
caps = [("RP2040 pad", 5e-12, "ASSUMPTION (RP2040 pin capacitance not verified)"),
        ("Pico trace + header", 3e-12, "ASSUMPTION"),
        ("FrutaMIDI PCB track ~40 mm, single-sided", 2e-12, "ASSUMPTION ~0.5 pF/cm"),
        ("module header + trace", 3e-12, "ASSUMPTION"),
        ("BSS138 drain (Coss 9.75..25 pF @25 V; x1.5 at low VDS)", 25e-12, "SOURCE onsemi BSS138K typ / BSS138L max x ASSUMPTION factor")]
cb = 0
for n, c, s in caps:
    cb += c
    print("  %-56s %5.1f pF  (%s)" % (n, c * 1e12, s))
print("  %-56s %5.1f pF" % ("C_bus (Pico side)", cb * 1e12))
for name, r in (("module 10k only", 10e3), ("module 10k || PCB 4.7k", 1 / (1 / 10e3 + 1 / 4.7e3)),
                ("module 10k || PCB 2.2k", 1 / (1 / 10e3 + 1 / 2.2e3))):
    tr = 0.8473 * r * cb
    print("  %-26s R=%6.0f ohm  t_r = %5.0f ns  -> 400 kHz %s;  100 kHz (1000 ns) %s;  low-level sink = %.2f mA (I2C limit 3 mA)"
          % (name, r, tr * 1e9, "PASS" if tr <= 300e-9 else "FAIL", "PASS" if tr <= 1000e-9 else "FAIL",
             (V_PICO_MAX / r + V_PICO_MAX / 10e3) * 1e3))
for cbx in (20e-12, 50e-12):
    print("  sensitivity: C_bus=%2.0f pF, 10k only -> t_r = %.0f ns" % (cbx * 1e12, 0.8473 * 10e3 * cbx * 1e9))
