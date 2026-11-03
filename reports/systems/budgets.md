# Revision 3 (T-011, 2026-11-03)

Script `sim/systems/budgets.py` (revision 3); output `sim/systems/budgets.out`, ending with `SUMMARY: 29 checks, 25 PASS, 4 FAIL`.

## Aftertouch burst plan

The plan is the run-based burst read in `fm_mpr121.h` (`mpr121_next_run`, MPR121_MERGE_GAP = 1), evaluated over all 4095 non-empty pad masks.

| Case | Mask | Transactions | Bus bytes |
| --- | --- | --- | --- |
| Worst | 0x925 | 8 (6/3/2/1/2/1/2/1 data bytes) | 42 (asserted ≤ 42, as the header states) |
| All 12 pads | 0xFFF | 2 (24 B + 12 B) | 42 |

The old per-pad path took 45 B for the worst mask (CALCULATION).

## Latency (CALCULATION, C ≤ 100 pF, 400 kHz)

| Sensors | Worst | Jitter | Worst loop |
| --- | --- | --- | --- |
| 1 | 10.59 ms | 6.59 ms | 1.59 ms |
| 2 | 12.07 ms | 8.07 ms | — |

Both meet the ADR-007 targets. The remaining FAILs:
- 100 kHz with 2 sensors (informative only; ADR-008 keeps 400 kHz).
- A3b: the USB low-power port minimum of 4.40 V is below the Pico's recommended 4.50 V.
- BOM: 20.42–30.40 EUR, now including R15/R16.

## I2C with R15/R16 220 Ω

Sources: S-17 RP2040 Table 625 and S-04 Table 5.

| Case | Level | Limit | Margin |
| --- | --- | --- | --- |
| Pico drives low, MPR121 receives | bus ≤ 0.742 V + 0.05 V shifter | VIL 0.93 V | 0.138 V |
| MPR121 drives low, Pico receives | pad ≤ 0.565 V | VIL 0.8 V | 0.235 V |
| High at the Pico | 3.3 V | VIH 2.0 V | 1.30 V |
| High at the MPR121 | VDD (module side) | VIH 0.7·VDD | ≥ 0.93 V |

- Fault current: 15.5 mA per line, 30.9 mA for both lines, against the 50 mA IIOVDD limit.
- Rise time: 156 ns at 60 pF. The RPU of 80 kΩ is SOURCE S-17, and 80 kΩ is the slowest-edge case.
- Breadboard without the 4.7 kΩ pull-ups: 452 ns at 60 pF, failing 300 ns above 39.8 pF.

---

# FrutaMIDI system budgets, revision 2 (T-010, 2026-11-03)

Revision 2 replaces the T-009 numbers below wherever the two differ. Script `sim/systems/budgets.py` (revision 2); raw output `sim/systems/budgets.out`, ending with `SUMMARY: 24 checks, 19 PASS, 5 FAIL`.

## What changed

- **Datasheets read.** Pico (S-01, local copy) and Pico 2 (S-16), read with pypdf 6.21.4.
  - The 3V3 load limit of "less than 300 mA" is now SOURCE S-01 §2.1.
  - VSYS 1.8–5.5 V and VBUS 5 V ± 10 % are SOURCE.
  - The board-current lower bounds are SOURCE: Pico BOOTSEL with USB active 9.9 mA; Pico 2 hello_usb 12.74 mA. The upper bounds stay ASSUMPTIONs, because neither datasheet covers a busy USB-MIDI loop at the default 200 MHz.
  - The diode drop and regulator efficiency stay ASSUMPTIONs: S-01 names the Schottky D1 and the RT6150 but gives no values.
  - ADC offset 30 mV (S-01 §4.3), which is 6.5 % of the pot hysteresis.
- **VBUS finding.** The USB low-power-port minimum of 4.40 V is below the Pico's recommended VBUS minimum of 4.50 V (check A3b FAIL). The resulting VSYS of 3.95 V is still far above 1.8 V.
- **Current budget.** Including the PCB pull-ups: 3V3 worst case 10.15 mA. VBUS worst case 55.6 / 70.6 / 60.6 / 75.6 mA for Pico / Pico W / Pico 2 / Pico 2 W, against 100 mA (CALCULATION).

## Latency

The firmware's actual transactions are counted below:

| When | Call | Bus traffic |
| --- | --- | --- |
| Every loop | `touched()` → `readRegister16(0x00)` | write 1 B register, repeated start, read 2 B (BusIO `write_then_read`, `stop = false`) |
| Aftertouch pass | `readRegisters(addr, 0x04, filt, 24)` and `readRegisters(addr, 0x1E, base, 12)` | `endTransmission(false)` then `requestFrom(addr, n)` |

The bit model is 9·(3 + n) + 3 bit times per read (48, 246 and 138 bits for n = 2, 24 and 12). Results for C ≤ 100 pF (CALCULATION):

| Clock | Worst, 1 sensor | Jitter, 1 sensor | Worst, 2 sensors | Loop with aftertouch pass |
| --- | --- | --- | --- | --- |
| 400 kHz | 10.30 ms | 6.30 ms | 11.50 ms | 1.13–1.30 ms |
| 100 kHz | 13.54 ms | 9.54 ms | 17.98 ms (FAIL) | 4.37–4.54 ms |

ADR-007 targets: worst case ≤ 15 ms, jitter ≤ 10 ms. The design limit at which both targets still hold (1 sensor) is C ≤ 210 pF at 400 kHz and C ≤ 100 pF at 100 kHz.

## D-5 recommendation (closed by ADR-008 as 400 kHz)

Keep 400 kHz. The 100 kHz option meets the targets only for 1 sensor, with a jitter margin of only 0.46 ms that rests on ASSUMPTIONs. It fails for 2 sensors and halves the usable electrode capacitance. The PCB pull-ups remove the rise-time reason for the change: 153 ns at 60 pF, C_b limit 117.8 pF.

The breadboard build still FAILs at 400 kHz above 42.5 pF (REQ-041). Document 4.7 kΩ pull-ups there (decision D-11).

## Other results

- **Recalibration:** 178 I2C transactions per sensor, 16.8–22.1 ms at 400 kHz (CALCULATION). It is user-requested.
- **Series 3.3 kΩ resistors:** τ/CDT ≤ 0.10 and an I·R offset of 0.208 V (CALCULATION). Negligible for latency.
- **BOM** (ADR-007 core definition, now including R1–R14): 20.38–30.30 EUR. FAIL by 0.30 EUR at the upper bound; the prices are ASSUMPTIONs.

---

# Revision 1 (T-009), kept for history

Author: systems-engineer · 2026-10-30. Inputs are at git e4668d4 with a dirty working tree; the input checksums are in `requirements/SOURCES_SYSTEMS.md`.

Script: `sim/systems/budgets.py`, run with `.venv/bin/python` (Python 3.9.6). Raw output: `sim/systems/budgets.out`. It ends with `SUMMARY: 16 checks, 8 PASS, 8 FAIL`.

Every number below is labelled. Ranges are worst-case intervals. "S-xx" refers to `requirements/SOURCES_SYSTEMS.md`. All results are analysis only: nothing here has been measured.

## Status per requirement

| Req | Check | Result | Status |
| --- | --- | --- | --- |
| REQ-020 | External 3V3 load ≤ 300 mA | Worst case 8.75 mA with 2 sensors, 97.1 % margin | PASS (A) |
| REQ-019 | VBUS current ≤ 100 mA declared | 54.1 / 69.1 / 59.1 / 74.1 mA worst case for Pico / Pico W / Pico 2 / Pico 2 W | PARTIAL: the board current is an ASSUMPTION |
| REQ-018 | VSYS inside the 1.8–5.5 V regulator range | 3.95–5.25 V | PARTIAL: diode drop is an ASSUMPTION; the regulator range is from a secondary source |
| REQ-021 | MPR121 VDD inside 2.0–3.6 V | 3.10–3.40 V | PASS (A) |
| REQ-014 | Latency ≤ 10 ms worst case, C ≤ 100 pF | 12.83 ms (12 pads sending aftertouch), 9.56 ms (1 pad) | FAIL (A) |
| REQ-014 | Same, with mitigation M1 (burst read) | 10.25 ms | FAIL (A) |
| REQ-015 | Jitter ≤ 1 ms | 5.56–8.83 ms | FAIL (A) |
| REQ-016 | No loop blocking > 10 ms during play | 1080 ms during the scale-change blink | FAIL (A) |
| REQ-026 | I2C rise time ≤ 300 ns at 400 kHz | 141–424 ns for C_b 20–60 pF | FAIL (A) |
| REQ-032 | Core BOM ≤ 30 EUR | 23.60–34.60 EUR | FAIL (A) on the upper bound; the target is reachable at the lower bound |

## (a) Current budget

The external loads below are on the Pico 3V3(OUT) pin (pin 36).

| Load | mA | Label |
| --- | --- | --- |
| MPR121 IC, ESI 1 ms | 0.10–1.00 | SOURCE S-04 (393 µA average with CDC = 63 µA, 1 mA peak). The lower end is an ASSUMPTION |
| Module LDO quiescent (MIC5225 / AP2112K) | 0.02–0.10 | ASSUMPTION (the LDO datasheets were not read) |
| Module power LED, R7 = 1 kΩ | 1.10–1.50 | CALCULATION (3.3 − Vf)/1 kΩ, with Vf 1.8–2.2 V as an ASSUMPTION |
| IRQ LED, 10 kΩ | 0–0.15 | CALCULATION, worst case with INT held low |
| I2C pull-ups, 4 × 10 kΩ | 0–1.32 | CALCULATION, worst case with both lines low |
| RP2040 internal pull-ups | 0–0.13 | CALCULATION, R ≥ 50 kΩ is an ASSUMPTION |
| Octave pot, 10 kΩ ± 20 % | 0.28–0.41 | CALCULATION V/R |
| Button pull-up, while pressed | 0–0.07 | CALCULATION |
| **Total, 1 sensor** | **1.50–4.68** | CALCULATION |
| **Total, 2 sensors** | **2.72–8.75** | CALCULATION |

- **3V3 limit:** 300 mA (SOURCE S-03, "keep the load less than 300mA"; secondary source). The worst-case margin is 97.1 % (CALCULATION).
- **VBUS:** I_vbus = I_board + 3.3·I_ext / (η·V_sys).
  - η = 0.80–0.90 (ASSUMPTION).
  - V_sys = VBUS − V_D, with V_D = 0.25–0.45 V (ASSUMPTION).
  - VBUS = 4.40–5.50 V (SOURCE S-10).
  - The external load adds 1.04–9.14 mA at VBUS (CALCULATION).
- **Pico board current** (ASSUMPTION; the S-01 power table could not be read):
  - Pico: 20–45 mA
  - Pico W: 25–60 mA
  - Pico 2: 20–50 mA
  - Pico 2 W: 25–65 mA
- **VBUS worst case:** 54.1 / 69.1 / 59.1 / 74.1 mA against the 100 mA declared in the configuration descriptor (SOURCE S-11). The margin is 26 % or more (CALCULATION).
- **To close REQ-019:** take the board current from the S-01 table, or MEASURE it with a USB inline meter on built hardware (physical plan item P-3).

## (b) Touch-to-MIDI latency budget (device side)

Settings in use (SOURCE S-08, library 1.2.1, written by `begin()`):
- FFI = 6
- SFI = 4
- ESI = 1 ms
- MPR121 debounce = 0
- 12 channels

Datasheet behaviour (SOURCE S-04):
- §5.3: the filtered data and touch status update every ESI × SFI.
- §5.8: if scanning all channels takes FFI × 2·CDT × N_ch, and that is longer than ESI, the scan time replaces ESI. The datasheet's worked example (34 × 64 µs × 13 = 28.288 ms) is reproduced by an assert in the script.

Budget terms:

| Term | Value | Label |
| --- | --- | --- |
| Sensing | 1 to 2 update periods = 4–8 ms at ESIeff = 1 ms | CALCULATION. Assumes block averaging by the second filter (ASSUMPTION, to be MEASURED) |
| Firmware debounce, first edge | 0 ms | CALCULATION. The lockout applies only after an accepted change (`fm_debounce.h`) |
| `touched()` read | 130–160 µs | CALCULATION at 400 kHz, plus 10–40 µs software overhead (ASSUMPTION) |
| Loop period, no touch | 150–260 µs | CALCULATION, plus 20–100 µs miscellaneous (ASSUMPTION) |
| Aftertouch pass | 238–298 µs per touched pad; 12 pads 3.00–3.83 ms | CALCULATION |
| Burst read of 0x04–0x2A (39 B) | 962–992 µs | CALCULATION. This is mitigation M1 |
| USB | 0–1 ms | ASSUMPTION: the next full-speed frame. `tud_task` is IRQ-driven (S-11) |
| Host OS, browser and audio buffer | excluded | Not a device term. Physical plan item P-2 measures it end to end |

Sweep over electrode capacitance (ASSUMPTION range 20–1000 pF). Autoconfiguration needs a charge time of about C·TL/I_max, with TL = 180/256 × 3.3 V and I_max = 63 µA:

| C [pF] | CDT | ESIeff [ms] | Worst, 1 pad AT [ms] | Worst, 12 pads AT [ms] |
| --- | --- | --- | --- | --- |
| 20–100 | 1–4 µs | 1.00 | 9.56 | 12.83 |
| 200 | 8 µs | 1.15 | 10.77 | 14.05 |
| 300 | 16 µs | 2.30 | 19.99 | 23.26 |
| 500–700 | 32 µs | 4.61 | 38.42 | 41.69 |
| 1000 | out of range (> 1203 pF limit at LSL) | | | |

The last row is labelled CALCULATION; all other rows come from `budgets.out`.

**Design rules** (CALCULATION):
1. ESIeff stays at 1 ms only while every channel's CDT ≤ 4 µs, which means an electrode with its lead at ≤ 109 pF. Larger objects (big fruit, water) raise latency in proportion. The firmware could cap the scan time by enabling fewer electrodes or by lowering FFI, which trades noise for latency.
2. The MPR121 alone sets a floor of SFI × ESI = 4 ms on latency and on jitter. A 1 ms jitter target cannot be met with this sensor at any setting (SFI ≥ 4, ESI ≥ 1 ms; SOURCE S-04 Table 8).
3. Read aftertouch data with one burst read per sensor (M1). This removes up to 2.8 ms from the 12-pad loop.
4. Do not block the loop. `nextScale()` blinks for up to 1080 ms, and `recalibrate()` for 360 ms or more (CALCULATION from `blink()` arguments). Make the LED feedback non-blocking (firmware action).

**I2C rise time** (S-13, not read: t_r ≈ 0.8473·R·C ≤ 300 ns in fast mode):
- The effective pull-up is 10 kΩ ∥ 50 kΩ = 8.33 kΩ (CALCULATION; the 50 kΩ is an ASSUMPTION).
- C_b ≤ 42.5 pF is allowed at 400 kHz, and C_b ≤ 141.6 pF at 100 kHz (CALCULATION).
- For an assumed C_b of 20–60 pF, t_r = 141–424 ns. This FAILs at the upper end.
- At 100 kHz with M1, a `touched()` read takes about 0.5 ms and a burst read about 3.8 ms (CALCULATION, same model). This is decision D-5.

## (c) BOM cost

| Item | Qty | EUR | Label |
| --- | --- | --- | --- |
| Raspberry Pi Pico H (or W / 2 / 2 W) | 1 | 5.00–8.00 | ASSUMPTION (hardware/README.md) |
| Adafruit MPR121 1982 | 1 | 9.00–12.00 | ASSUMPTION. SOURCE S-05 gives the USD 7.95 list price, before EU shipping and VAT |
| Female headers 1x20 ×2, 1x13, 1x7 | 4 | 1.90 | ASSUMPTION |
| Screw terminals 2-way 5.08 mm | 7 | 2.00–3.00 | ASSUMPTION |
| Tactile switch | 1 | 0.20 | ASSUMPTION |
| Pot 10 k + knob | 1 | 1.00–1.50 | ASSUMPTION |
| Copper clad 100 × 70 mm, single-sided | 1 | 1.00–3.00 | ASSUMPTION (not in the repository BOM) |
| Etchant / toner share | 1 | 0.50–2.00 | ASSUMPTION (not in the repository BOM) |
| Micro-USB data cable | 1 | 3.00 | ASSUMPTION |
| **Core total** | | **23.60–34.60** | CALCULATION |
| Crocodile leads ×12, M3 hardware (optional) | | +7.00–12.00 | ASSUMPTION |
| **With options** | | **30.60–46.60** | CALCULATION |

- **Result:** the 25–30 EUR target (an ASSUMPTION from PD) is reachable only with low-end prices. The worst case exceeds 30 EUR, so REQ-032 is FAIL on its upper bound.
- **To close:** use quoted prices from one named EU supplier, with VAT and shipping (decision D-7).

## (d) MIDI note ranges

CALCULATION from `fm_scales.h`. With 12 pads and octave −2..+2:

| Scale | Notes |
| --- | --- |
| Drum Rack | 36–47 |
| Major pentatonic | 24–98 |
| Minor pentatonic | 24–99 |
| Major | 24–91 |
| Natural minor | 24–91 |
| Chromatic | 24–83 |

No note is clamped. With 24 pads the pentatonic scales reach 127 exactly, still with no clamping.

## Assumptions to retire (and how)

| Assumption | How to retire it |
| --- | --- |
| Pico board currents | Read the S-01 table, or MEASURE (P-3) |
| Buck-boost efficiency, diode drop | Read S-01 |
| LDO Iq, LED Vf | Read the MIC5225 and AP2112K datasheets; MEASURE |
| Second-filter averaging model, USB 0–1 ms | MEASURE latency with a logic analyser on SDA/SCL and USB (P-2) |
| Electrode capacitance range | MEASURE with an LCR meter on typical objects plus leads (P-1) |
| I2C bus capacitance | MEASURE the rise time with an oscilloscope (P-4) |
| RP2040 pull-up resistance | Read the RP2040 datasheet |
| All prices | Get supplier quotes |
