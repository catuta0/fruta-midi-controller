"""T-009 system budgets for FrutaMIDI (systems-engineer).

Every input carries a label: SOURCE (id in requirements/SOURCES_SYSTEMS.md), ASSUMPTION (with the
reason) or a CALCULATION from those. Ranges are carried as (low, high) and propagated as
worst-case intervals. Run with the project venv:

    .venv/bin/python sim/systems/budgets.py > sim/systems/budgets.out

The script asserts its own arithmetic on known cases and prints PASS/FAIL per budget check.
"""
import itertools
import math
import sys

checks = []


def check(name, ok, detail):
    checks.append(ok)
    print("%s  %s :: %s" % ("PASS" if ok else "FAIL", name, detail))


def rng(lo, hi=None):
    return (lo, lo if hi is None else hi)


def add(*rs):
    return (sum(r[0] for r in rs), sum(r[1] for r in rs))


def fmt(r, unit, nd=3):
    return "%.*f .. %.*f %s" % (nd, r[0], nd, r[1], unit)


# =============================================================================================
# (a) Current budget: 3V3 rail (Pico 3V3(OUT), pin 36) and VBUS
# =============================================================================================
print("=" * 90)
print("(a) CURRENT BUDGET")
print("=" * 90)
V33 = 3.3                                    # V, SOURCE S-02 (3V3(OUT) 3.3 V regulated output)

loads = []                                   # (name, (lo, hi) mA, label)


def load(name, r, label):
    loads.append((name, r, label))


# MPR121 IC: SOURCE S-04 Table 5, run mode @ 1 ms sample period, CDC = 63 uA, 13 channels: 393 uA.
# Firmware uses ESI = 1 ms (CONFIG2 = 0x20, SOURCE S-08 library line 95). Lower bound ASSUMPTION
# 0.10 mA (smaller CDC chosen by autoconfig); upper bound = peak measurement current 1 mA (S-04).
load("MPR121 IC (ESI 1 ms)", rng(0.10, 1.0), "SOURCE S-04 (393 uA avg, 1 mA peak); low end ASSUMPTION")
# Module LDO quiescent current (MIC5225 original / AP2112K-3.3 QT, part numbers SOURCE S-06/S-07).
# Values not fetched: ASSUMPTION 0.02..0.10 mA (typical LDO Iq class), to be read from the LDO datasheets.
load("Module LDO quiescent", rng(0.02, 0.10), "ASSUMPTION (LDO datasheets not fetched)")
# Module power LED: R7 = 1 kOhm on the 3.3V net (SOURCE S-06/S-07). LED Vf ASSUMPTION 1.8..2.2 V.
load("Module power LED (R7 1k)", ((V33 - 2.2) / 1.0, (V33 - 1.8) / 1.0), "CALCULATION (3.3-Vf)/1k, Vf ASSUMPTION")
# IRQ/INT LED: lit while INT is low (10 kOhm, SOURCE S-06 R1). ASSUMPTION Vf 1.8 V; worst case always low.
load("Module IRQ LED (10k)", rng(0.0, (V33 - 1.8) / 10.0), "CALCULATION, worst case INT held low")
# I2C pull-ups: 10 kOhm on the host side (to VIN = 3V3) and 10 kOhm on the 3.3 V side, per line
# (SOURCE S-06/S-07). Worst case: both lines held low = 4 resistors conducting.
load("I2C pull-ups (4 x 10k, lines low)", rng(0.0, 4 * V33 / 10.0), "CALCULATION, worst case")
# RP2040 internal pull-ups enabled by Wire.begin (SOURCE S-09 gpio_pull_up). Value ASSUMPTION 50..80 kOhm.
load("RP2040 I2C internal pull-ups", rng(0.0, 2 * V33 / 50.0), "CALCULATION, R ASSUMPTION 50 kOhm min")
# Octave potentiometer 10 kOhm (gen_schematic.py RV1 '10k lin'), tolerance ASSUMPTION +-20 %.
load("Octave pot 10k +-20 %", (V33 / 12.0, V33 / 8.0), "CALCULATION V/R")
# Button: internal pull-up (INPUT_PULLUP) when pressed, R ASSUMPTION >= 50 kOhm.
load("Button pull-up (pressed)", rng(0.0, V33 / 50.0), "CALCULATION, R ASSUMPTION")

ext_1 = add(*[r for _, r, _ in loads])
for n, r, lab in loads:
    print("  %-36s %-22s %s" % (n, fmt(r, "mA"), lab))
print("  %-36s %s  CALCULATION (sum)" % ("External 3V3 load, 1 sensor", fmt(ext_1, "mA")))
# Second MPR121 option (24 pads): repeat module loads except pot/button/RP2040 pull-ups;
# the second module's host-side pull-ups appear in parallel (worst case adds 2 x 0.33 mA more).
module_only = add(loads[0][1], loads[1][1], loads[2][1], loads[3][1], loads[4][1])
ext_2 = add(ext_1, module_only)
print("  %-36s %s  CALCULATION" % ("External 3V3 load, 2 sensors", fmt(ext_2, "mA")))

I33_LIMIT = 300.0       # mA, SOURCE S-03 "recommended to keep the load less than 300mA" (secondary; S-01 to confirm)
margin = 1 - ext_2[1] / I33_LIMIT
check("A1 3V3 external load <= 300 mA", ext_2[1] <= I33_LIMIT,
      "worst %.2f mA (2 sensors) vs %.0f mA recommendation, margin %.1f %%" % (ext_2[1], I33_LIMIT, 100 * margin))

# Pico board's own consumption from VBUS. The Pico datasheet power table (S-01) could not be read
# (PDF > 10 MB for the fetch tool). ASSUMPTION ranges, to be replaced by S-01 values or by MEASUREMENT:
PICO_BOARD_MA = {
    "Pico (RP2040, USB active)": rng(20.0, 45.0),
    "Pico W (CYW43 present, radio unused)": rng(25.0, 60.0),
    "Pico 2 (RP2350, USB active)": rng(20.0, 50.0),
    "Pico 2 W (CYW43 present, radio unused)": rng(25.0, 65.0),
}
# Conversion of the external 3V3 load to VBUS current through the Pico buck-boost:
#   I_vbus = V33 * I33 / (eta * V_sys),  V_sys = V_bus - V_diode
ETA = rng(0.80, 0.90)          # ASSUMPTION buck-boost efficiency at light load (S-01 not read)
VDIODE = rng(0.25, 0.45)       # ASSUMPTION VBUS->VSYS Schottky drop
VBUS = rng(4.40, 5.50)         # SOURCE S-10: 4.40 V (low-power port min), 5.50 V (ECN VBUS max)
vsys = (VBUS[0] - VDIODE[1], VBUS[1] - VDIODE[0])
print("  VSYS range = %s  CALCULATION VBUS - Vdiode" % fmt(vsys, "V", 2))
I_DECLARED = 100.0             # mA, SOURCE S-11 (Adafruit TinyUSB USB_CONFIG_POWER 100, bus powered)
for name, pico in PICO_BOARD_MA.items():
    ext_vbus_hi = V33 * ext_2[1] / (ETA[0] * vsys[0])
    ext_vbus_lo = V33 * ext_1[0] / (ETA[1] * vsys[1])
    tot = (pico[0] + ext_vbus_lo, pico[1] + ext_vbus_hi)
    check("A2 VBUS current <= 100 mA declared [%s]" % name, tot[1] <= I_DECLARED,
          "%s (board %s ASSUMPTION + external %.2f..%.2f mA) ; margin %.0f %%"
          % (fmt(tot, "mA", 1), fmt(pico, "mA", 0), ext_vbus_lo, ext_vbus_hi, 100 * (1 - tot[1] / I_DECLARED)))

# Supply range: VSYS must stay inside the regulator input range 1.8..5.5 V (SOURCE S-03, secondary).
check("A3 VSYS within 1.8..5.5 V over USB VBUS range", vsys[0] >= 1.8 and vsys[1] <= 5.5,
      "VSYS %s" % fmt(vsys, "V", 2))
# MPR121 supply: 3V3 into module VIN/VCC -> LDO -> MPR121 VDD. LDO dropout at ~1 mA ASSUMPTION 0..0.1 V.
vdd = (V33 * 0.97 - 0.10, V33 * 1.03)    # Pico 3V3 tolerance +-3 % ASSUMPTION
check("A4 MPR121 VDD inside 2.0..3.6 V (S-04 Table 5)", vdd[0] >= 2.0 and vdd[1] <= 3.6, "VDD %s" % fmt(vdd, "V", 2))
# Known-answer self-test of the arithmetic used above (smoke case T-006).
assert abs(V33 / 10.0 - 0.33) < 1e-12

# =============================================================================================
# (b) Touch-to-MIDI latency budget (device side: touch -> USB IN packet available to host)
# =============================================================================================
print()
print("=" * 90)
print("(b) LATENCY BUDGET")
print("=" * 90)
# MPR121 settings written by Adafruit_MPR121::begin() (SOURCE S-08, library 1.2.1):
FFI = 6            # CONFIG1 = 0x10 -> FFI = 00 -> 6 samples (S-04 Table 8)
SFI = 4            # CONFIG2 = 0x20 -> SFI = 00 -> 4 samples (S-04 Table 8)
ESI_MS = 1.0       # CONFIG2 = 0x20 -> ESI = 000 -> 1 ms (S-04 Table 8)
DT = 0             # DEBOUNCE register 0x5B = 0 (S-08 line 93)
N_CH = 12          # ECR = 0x8C -> 12 electrodes, proximity off (S-08 line 103)
print("  MPR121: FFI=%d SFI=%d ESI=%.0f ms DT=%d channels=%d  SOURCE S-08 + S-04" % (FFI, SFI, ESI_MS, DT, N_CH))

# Effective sample interval (S-04 section 5.8): if scanning all channels takes longer than ESI,
# the scan time overrides ESI. Scan time = FFI * (2 * CDT) * N_ch (S-04 worked example 34 x 64 us x 13).
assert abs(34 * (32e-3 + 32e-3) * 13 - 28.288) < 1e-9     # S-04 example gives "28 mS"
CDT_US = [0.5, 1, 2, 4, 8, 16, 32]                        # S-04 Table 8, 2^(n-2) us


def esi_eff(cdt_us):
    return max(ESI_MS, FFI * 2 * cdt_us * N_CH / 1000.0)


# Autoconfiguration chooses CDC/CDT so the electrode voltage reaches the target level
# TL = 180/256 * VDD (S-08 lines 152-154). Q = I*T = C*V -> T = C*V/I with I <= 63 uA (S-04).
# Electrode + wire + object capacitance: ASSUMPTION sweep 20 pF (bare pad) .. 1000 pF (large fruit/water, long lead).
V_TL = 180 / 256 * V33
I_MAX = 63e-6
V_LSL = 130 / 256 * V33
C_MAX_MEAS = I_MAX * 32e-6 / V_LSL
print("  Largest capacitance the MPR121 can charge to LSL with CDC=63 uA, CDT=32 us: %.0f pF  CALCULATION"
      % (C_MAX_MEAS * 1e12))


def cdt_for(c_pf):
    t_us = c_pf * 1e-12 * V_TL / I_MAX * 1e6
    for c in CDT_US:
        if c >= t_us:
            return c
    return None


# Firmware loop timing (SOURCE: FrutaMIDI.ino loop(); Adafruit_BusIO register reads, S-08).
# Bit times per transaction (write register address, repeated start, read n bytes):
#   START + 2 bytes x 9 bits + Sr + (1 + n) bytes x 9 bits + STOP  ~= 18 + 9 * (1 + n) + 3
def i2c_read_us(n_bytes, f_scl, sw_overhead_us):
    bits = 18 + 9 * (1 + n_bytes) + 3
    return bits / f_scl * 1e6 + sw_overhead_us


SW_OVH = rng(10.0, 40.0)      # us per BusIO transaction, ASSUMPTION (software + FIFO handling)
F_SCL = 400e3                 # Hz, firmware I2C_BUS.setClock(400000) (SOURCE FrutaMIDI.ino)
t_touched = (i2c_read_us(2, F_SCL, SW_OVH[0]), i2c_read_us(2, F_SCL, SW_OVH[1]))
t_pad_at = (i2c_read_us(1, F_SCL, SW_OVH[0]) + i2c_read_us(2, F_SCL, SW_OVH[0]),
            i2c_read_us(1, F_SCL, SW_OVH[1]) + i2c_read_us(2, F_SCL, SW_OVH[1]))
t_batch = (i2c_read_us(39, F_SCL, SW_OVH[0]), i2c_read_us(39, F_SCL, SW_OVH[1]))
print("  touched() read          : %s  CALCULATION" % fmt(t_touched, "us", 0))
print("  aftertouch per pad      : %s  CALCULATION (baseline 1 B + filtered 2 B)" % fmt(t_pad_at, "us", 0))
print("  batch read 0x04..0x2A   : %s  CALCULATION (39 B, design-rule alternative)" % fmt(t_batch, "us", 0))
T_MISC_US = rng(20.0, 100.0)      # ASSUMPTION: midiTask, button, pot, LED, MIDI enqueue per loop
loop_idle = (t_touched[0] + T_MISC_US[0], t_touched[1] + T_MISC_US[1])
loop_at12 = (loop_idle[0] + 12 * t_pad_at[0], loop_idle[1] + 12 * t_pad_at[1])
print("  loop period, no touch   : %s  CALCULATION" % fmt(loop_idle, "us", 0))
print("  loop period, 12 pads AT : %s  CALCULATION (aftertouch pass, every AT_INTERVAL_MS = 15 ms)" % fmt(loop_at12, "us", 0))

T_USB_MS = rng(0.0, 1.0)     # ASSUMPTION: bulk IN packet picked up within the next 1 ms full-speed frame
T_DEBOUNCE_FIRST_EDGE = 0.0  # firmware lockout only after an accepted change (fm_debounce.h): CALCULATION
TARGET_MS = 10.0             # SOURCE S-12 (Wessel & Wright 2002: 10 ms latency, 1 ms jitter guideline)
JITTER_TARGET_MS = 1.0


def latency(c_pf, pads_with_at):
    cdt = cdt_for(c_pf)
    if cdt is None:
        return None
    e = esi_eff(cdt)
    # Sensing: status updates every ESI_eff x SFI (S-04 5.3). A touch is seen at the first update
    # whose window is fully past the threshold: between 1 and 2 update periods (ASSUMPTION on the
    # filter's block-averaging behaviour; to be MEASURED), plus DT x ESI x SFI debounce (DT = 0).
    sense = (SFI * e, 2 * SFI * e + DT * SFI * e)
    lp = (loop_idle[0] + pads_with_at * t_pad_at[0], loop_idle[1] + pads_with_at * t_pad_at[1])
    lp_ms = (0.0, lp[1] / 1000.0)        # touch-status poll phase: 0 .. one loop period
    tot = (sense[0] + lp_ms[0] + T_DEBOUNCE_FIRST_EDGE + T_USB_MS[0],
           sense[1] + lp_ms[1] + T_DEBOUNCE_FIRST_EDGE + T_USB_MS[1])
    return cdt, e, sense, lp_ms, tot


print()
print("  %-8s %-6s %-8s %-16s %-14s %-16s %-14s" % ("C [pF]", "CDT", "ESIeff", "sense [ms]", "loop [ms]", "total [ms]", "jitter [ms]"))
rows = []
for c_pf in (20, 50, 100, 200, 300, 500, 700, 1000):
    for pads in (1, 12):
        r = latency(c_pf, pads)
        if r is None:
            print("  %-8d %-6s out of MPR121 range (> %.0f pF) CALCULATION" % (c_pf, "-", C_MAX_MEAS * 1e12))
            continue
        cdt, e, sense, lp, tot = r
        rows.append((c_pf, pads, tot))
        print("  %-8d %-6s %-8.2f %-16s %-14s %-16s %-6.2f  (pads with aftertouch: %d)"
              % (c_pf, "%gus" % cdt, e, fmt(sense, "", 2), fmt(lp, "", 2), fmt(tot, "", 2), tot[1] - tot[0], pads))

worst_bare = max(t[1] for c, p, t in rows if c <= 100)
check("B1 worst-case latency <= 10 ms, electrode C <= 100 pF", worst_bare <= TARGET_MS,
      "worst %.2f ms (CALCULATION, includes 2 x SFI x ESIeff sensing bound)" % worst_bare)
fruit = [t[1] for c, p, t in rows if 100 < c <= 300]
check("B2 worst-case latency <= 10 ms, electrode C 100..300 pF", max(fruit) <= TARGET_MS,
      "worst %.2f ms" % max(fruit))
big = [t[1] for c, p, t in rows if c > 300]
check("B3 worst-case latency <= 10 ms, electrode C > 300 pF", max(big) <= TARGET_MS, "worst %.2f ms" % max(big))
jit = max(t[1] - t[0] for c, p, t in rows if c <= 100)
check("B4 latency jitter <= 1 ms (C <= 100 pF)", jit <= JITTER_TARGET_MS, "jitter %.2f ms" % jit)

# Mitigation M1 (firmware): one 39-byte burst read of filtered+baseline data per aftertouch pass
# instead of 2 reads per pad. Worst case for C <= 100 pF (ESIeff = 1 ms):
m1 = SFI * 2 * ESI_MS + (loop_idle[1] + t_batch[1]) / 1000.0 + T_USB_MS[1]
check("B1-M1 worst-case latency <= 10 ms with burst read (C <= 100 pF)", m1 <= TARGET_MS,
      "worst %.2f ms (sense 8.00 + loop %.2f + USB 1.00)" % (m1, (loop_idle[1] + t_batch[1]) / 1000.0))
mean_typ = SFI * 1.5 * ESI_MS + loop_idle[1] / 2000.0 + 0.5
print("  Mid-range estimate (C <= 100 pF, 1 pad): %.2f ms  CALCULATION (1.5 x SFI x ESI + loop/2 + 0.5 ms USB)" % mean_typ)

# Design rule from the sweep: largest per-channel CDT that keeps ESIeff = ESI = 1 ms
cdt_rule = max(c for c in CDT_US if esi_eff(c) <= ESI_MS)
c_rule = cdt_rule * 1e-6 * I_MAX / V_TL * 1e12
print("  DESIGN RULE: ESIeff stays at 1 ms while CDT <= %g us, i.e. electrode C <= %.0f pF (CALCULATION)"
      % (cdt_rule, c_rule))

# Blocking user-interface actions (SOURCE FrutaMIDI.ino blink()/nextScale()/recalibrate()):
NUM_SCALES = 6
blink_next_max = NUM_SCALES * 2 * 90       # ms, blink(scaleIdx+1, 90)
blink_recal = 3 * 2 * 60                   # ms, blink(3, 60)
print("  Loop blocked by nextScale(): up to %d ms; by recalibrate(): >= %d ms + sensor begin()  CALCULATION"
      % (blink_next_max, blink_recal))
check("B5 no loop blocking > 10 ms during play", blink_next_max <= TARGET_MS,
      "nextScale blink blocks %d ms (touches and note-offs wait)" % blink_next_max)

# I2C rise time at 400 kHz (fast mode t_r <= 300 ns, SOURCE S-13 UM10204; 0.8473 RC for 30 %..70 %)
R_HOST = 1 / (1 / 10e3 + 1 / 50e3)           # 10 k module pull-up || 50 k RP2040 pull-up (ASSUMPTION)
cb_max_fm = 300e-9 / (0.8473 * R_HOST)
cb_max_sm = 1000e-9 / (0.8473 * R_HOST)
print("  I2C: R_pullup_eff = %.2f kOhm; max bus C for t_r<=300 ns (400 kHz) = %.1f pF; for t_r<=1000 ns (100 kHz) = %.1f pF"
      % (R_HOST / 1e3, cb_max_fm * 1e12, cb_max_sm * 1e12))
CB = rng(20e-12, 60e-12)     # ASSUMPTION: PCB traces + sockets + module + pins (breadboard upper end)
tr = (0.8473 * R_HOST * CB[0] * 1e9, 0.8473 * R_HOST * CB[1] * 1e9)
check("B6 I2C rise time <= 300 ns at 400 kHz (C_b 20..60 pF ASSUMPTION)", tr[1] <= 300.0, "t_r %s" % fmt(tr, "ns", 0))

# =============================================================================================
# (c) BOM cost (PCB build, 1 sensor, 12 pads)
# =============================================================================================
print()
print("=" * 90)
print("(c) BOM COST")
print("=" * 90)
# Price ranges in EUR. Unless a SOURCE is named, values are the repository's own estimates
# (hardware/README.md bill of materials) and therefore ASSUMPTION.
BOM = [
    ("A1 Raspberry Pi Pico H (or Pico/W/2/2W + headers)", 1, rng(5.0, 8.0), "ASSUMPTION (hardware/README.md)", True),
    ("A2 Adafruit MPR121 breakout 1982", 1, rng(9.0, 12.0),
     "ASSUMPTION; SOURCE S-05 USD 7.95 list price (1-9 pcs) before EU shipping/VAT", True),
    ("Female header 1x20 (Pico socket)", 2, rng(0.5, 0.5), "ASSUMPTION (README: 1 EUR for two)", True),
    ("Female header 1x13", 1, rng(0.5, 0.5), "ASSUMPTION", True),
    ("Female header 1x7", 1, rng(0.4, 0.4), "ASSUMPTION", True),
    ("J2 screw terminal 2-way 5.08 mm, interlocking", 7, rng(2.0 / 7, 3.0 / 7), "ASSUMPTION (README 2-3 EUR for 7)", True),
    ("SW1 tactile switch 6x6 mm", 1, rng(0.2, 0.2), "ASSUMPTION", True),
    ("RV1 10k linear pot 9 mm + knob", 1, rng(1.0, 1.5), "ASSUMPTION (README 1 / 1.5 EUR)", True),
    ("Single-sided copper clad 100x70 mm", 1, rng(1.0, 3.0), "ASSUMPTION (not in repository BOM)", True),
    ("Etchant/toner/consumables share per board", 1, rng(0.5, 2.0), "ASSUMPTION (not in repository BOM)", True),
    ("Micro-USB data cable", 1, rng(3.0, 3.0), "ASSUMPTION (README)", True),
    ("Crocodile leads (12)", 1, rng(5.0, 10.0), "ASSUMPTION (README: 5 EUR per 10-pack, 2 packs)", False),
    ("M3 screws + spacers (4)", 1, rng(2.0, 2.0), "ASSUMPTION (README, optional)", False),
]
core = (0.0, 0.0)
full = (0.0, 0.0)
for name, q, (lo, hi), lab, in_core in BOM:
    line = (q * lo, q * hi)
    full = add(full, line)
    if in_core:
        core = add(core, line)
    print("  %-52s x%-2d %-18s %s%s" % (name, q, fmt(line, "EUR", 2), lab, "" if in_core else "  [optional]"))
print("  %-56s %s  CALCULATION" % ("Core BOM (board + parts + cable)", fmt(core, "EUR", 2)))
print("  %-56s %s  CALCULATION" % ("With optional leads and mounting", fmt(full, "EUR", 2)))
TARGET_EUR = (25.0, 30.0)       # ASSUMPTION from PROJECT_DEFINITION.md
check("C1 core BOM upper bound <= 30 EUR", core[1] <= TARGET_EUR[1], "core %s vs target <= %.0f EUR" % (fmt(core, "EUR", 2), TARGET_EUR[1]))
check("C2 core BOM lower bound <= 30 EUR (target reachable)", core[0] <= TARGET_EUR[1], "lowest %.2f EUR" % core[0])

# =============================================================================================
# (d) MIDI note range per scale (interface data for INTERFACES.json)
# =============================================================================================
print()
print("=" * 90)
print("(d) MIDI NOTE RANGES (CALCULATION from fm_scales.h note_for_pad)")
print("=" * 90)
SCALES = [("Drum Rack", 36, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], True),
          ("Major pentatonic", 48, [0, 2, 4, 7, 9], False),
          ("Minor pentatonic", 48, [0, 3, 5, 7, 10], False),
          ("Major", 48, [0, 2, 4, 5, 7, 9, 11], False),
          ("Natural minor", 48, [0, 2, 3, 5, 7, 8, 10], False),
          ("Chromatic", 48, list(range(12)), False)]


def note_raw(root, steps, fixed, octv, pad):
    o = 0 if fixed else octv
    return root + 12 * o + steps[pad % len(steps)] + 12 * (pad // len(steps))


assert note_raw(36, list(range(12)), True, 2, 11) == 47      # known answer: Drum Rack pad 11 -> 47
for pads in (12, 24):
    for name, root, steps, fixed in SCALES:
        vals = [note_raw(root, steps, fixed, o, p) for o in range(-2, 3) for p in range(pads)]
        clamped = sum(1 for v in vals if v < 0 or v > 127)
        print("  pads=%d %-18s raw notes %3d..%3d  clamped=%d" % (pads, name, min(vals), max(vals), clamped))

print()
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(checks), checks.count(True), checks.count(False)))
