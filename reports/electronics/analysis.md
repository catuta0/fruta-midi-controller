# Electronics analysis — T-050 / T-052 (updated to T-103)

> **Scope note (T-092).** Sections 1-6 record the through-hole V1.2 design and stay as history. The current SMD design (CR-003, ADR-023) is in **section 7**, which supersedes them wherever they differ (3k3 → 3k0, THT parts, sockets, drills, end caps, H1-H4 positions).

Author: electronics-engineer (content from handoff T-050/T-052; written to file by the manager because the agent's harness refused this path). Inputs: hardware/ and firmware/FrutaMIDI/FrutaMIDI.ino @ e4668d4. Sources: reports/electronics/SOURCES_EE.md (EE-S01..S16, "Read" vs "Search" marked). Raw outputs: sim/electronics/calc/*.out (`sh sim/electronics/calc/run_all.sh`). Nothing here is a measurement on hardware.

## 1. Datasheet checks
| Check | Result | Label |
|---|---|---|
| Pico pins: GP26/GP27 = I2C1 SDA/SCL (pins 31/32), GP22 pin 29, GP28 ADC2 pin 34, AGND 33, 3V3 36; matches firmware FRUTAMIDI_PCB | PASS | SOURCE EE-S08 |
| Pico 3V3 load 4.45 mA vs < 300 mA recommended (67× margin) | PASS | CALCULATION |
| Adafruit 1982 original: MIC5225-3.3 from VIN feeds MPR121 VDD; STEMMA QT: AP2112K-3.3 from VCC; both BSS138 level shifters, 10k pull-ups host side to VIN/VCC and chip side to 3.3 V; electrodes go straight to the header | — | SOURCE (Adafruit Eagle schematics) |
| MPR121 VDD at VIN = 3.3 V: AP2112 ≈3.295 V typ, ≥3.19 V worst; MIC5225 ≈3.25 V typ, ≥3.10 V worst; within 2.0–3.6 V | PASS | CALCULATION (MIC5225 typical dropout from search extract only) |
| SDA/SCL idle on the Pico side = Pico 3V3 (pull-ups to VIN/VCC) | PASS | CALCULATION |
| Feed pin: keep VIN/VCC; feeding 3Vo back-drives the regulator and leaves host pull-ups on a floating VIN | decision | SOURCE EE-S04 |
| AUTOCONFIG USL/TL/LSL fixed 200/180/130 in the library; at VDD 3.10 V the formula gives 198/178/129 (0.9 % high) | PARTIAL | CALCULATION |
| I2C rise time at 400 kHz with module 10k pull-ups, 38 pF bus: 322 ns vs 300 ns (169 ns @20 pF, 424 ns @50 pF) | FAIL at e4668d4 | CALCULATION (bus C partly ASSUMPTION) |
| With added 4k7 pull-ups R13/R14: 103 ns @38 pF, 135 ns @50 pF; sink 1.40 mA < 3 mA | PASS | CALCULATION |

## 2. Calculations
- 3V3 load 4.45 mA worst case (MPR121 1 mA peak, regulator Iq 0.1, IRQ LED 1.5, QT power LED 0.13, I2C held low 1.32, pot 0.33, button 0.07); board power 14.7 mW. CALCULATION.
- IPC-2221 external, 35 µm: 1.2 mm at 4.45 mA → ΔT 4.6e-6 °C; 0.8 mm at 300 mA bound → 0.13 °C; current for ΔT 10 °C: 2.03 A (0.8 mm), 2.39 A (1.0), 2.73 A (1.2). CALCULATION (formula from memory, EE-S15).
- 120 mm × 1.2 mm 3V3 path: 49 mΩ, 0.22 mV drop (length ASSUMPTION).
- Dissipation: pot 1.16 mW vs 50 mW (EE-S13); series R 13 µW at 63 µA; one 8 kV IEC strike ≈4.36 mJ into 3.3k — pulse rating: section 5 (T-060).
- Clearance: max steady 3.3 V needs 0.1 mm (IPC-2221B B2); rule 0.6 mm. ESD flashover: see section 5 (T-060). Correction (CR-002): the earlier statement "each path still has its series R" was wrong for the gap across the resistor itself (0.94 mm pad-to-pad at e4668d4..86866be), where an arc bypasses R.
- Drill vs pin: PASS for resistors, terminals (0.9×0.9 mm pin in 1.3 mm hole, Phoenix data), switch, wire holes, M3. PARTIAL: 1.0 mm holes leave 0.06–0.09 mm around header/pot pins (pin sizes ASSUMPTION). Annular ring fixed in T-052.

## 3. Critical block — electrode path (variant study)
Model `sim_electrode.py` (SIMULATION): constant-current charge into 17 pF pin + series R + external C, 6 samples, discharge = pin grounded for the charge time (ASSUMPTION); every charge current/time pair inside the AUTOCONFIG 130–200 window checked; sweep R 0–100 kΩ, C 10–2000 pF.
Electrode C range 10–1000 pF justified: fruit 1.7 pF (cherry tomato) – 16.7 pF (watermelon), 1 m lead 30–50 pF (ASSUMPTION), hand 100–300 pF, 2000 pF datasheet max.

| R | min. relative sensitivity (typical choice) | worst choice |
|---|---|---|
| 1k | 0.968 | — |
| 2.2k | 0.944 | — |
| **3.3k** | **0.904** | 0.904 |
| 4.7k | 0.887 | 0.861 |
| 10k | 0.679 | 0.435 |
| 22k | 0.264 | — |

At 2000 pF no setting is in range for R ≤ 6.8k (including R = 0). Hand check I·R ≤ 10 % of 2.313 V → R ≤ 3.67k at 63 µA (agrees). With 3.3k the smallest detectable touch is 0.5 pF on 10 pF and 19.9 pF on 1000 pF (19.8 pF without R).
ESD (IEC 150 pF/330 Ω, pin limit 1.33 A inferred from HBM 2 kV — ASSUMPTION): minimum R 1.17k @2 kV, 2.67k @4 kV, 4.17k @6 kV, 5.67k @8 kV.
**Design rule 2.7 kΩ ≤ R ≤ 3.3 kΩ; chosen 3.3 kΩ (Yageo MFR-12FTF52-3K3 at T-050; Vishay MBE04140C3301FC100 pulse-rated DIN0414 since T-060, value and 1 % tolerance unchanged).**

| Variant | Peak 4 kV | Peak 8 kV | Sensitivity | Added C | THT single-layer | Verdict |
|---|---|---|---|---|---|---|
| a) none | 15.0 A | 30.0 A | 1.000 | 0 | yes | FAIL (11× over) |
| **b) 3.3k series (selected)** | 1.10 A | 2.20 A | 0.904 | 0 | yes | PASS 4 kV, PARTIAL 8 kV (1.65× over) |
| b') 10k series | 0.39 A | 0.77 A | 0.679 | 0 | yes | FAIL (sensitivity) |
| c) 3.3k + TPD4E05U06 ×3 | 1.10 A* | 2.20 A* | ≈0.90 | 0.5 pF | no (SMD) | FAIL (constraint) |
| d) 3.3k + 2×1N4148 to rails | 1.10 A* | 2.20 A* | ≈0.90 | 8 pF | partial (12 jumpers) | PARTIAL |
\* current through the resistor; clamp takes the rest.

Firmware impacts: F-1 keep AUTOCONFIG with SCTS = 0; F-2 optional VDD-derived limits; F-3 400 kHz valid with R13/R14; F-4 no pin/address change.

## 4. Implemented (T-050, T-052)
R1–R12 3k3 in series with each electrode (vertical, under the electrode header); R13/R14 4k7 I2C pull-ups; module-side nets renamed ELE0–ELE11 (terminal side keeps E0–E11); pads with ≥0.40 mm ring (Pico 2.4×1.8, header 1.8×2.4, pot 2.6×1.8; gaps 0.70–0.74 mm); JP1 3-pad 3V3 selector (ORIG→S1, QT→S7), J1 = SCL|SDA wire holes; English file names and silkscreen.
Checks (kicad-cli 10.0.4, re-run independently by the manager): ERC 0; DRC 0 / unconnected 0 / parity 0; pcb_rules_check 14/14; interface_check 66/67 (expected FAIL on old J1 definition, to be updated by systems).

## 5. ESD flashover around the series resistor and pulse rating — T-060 / CR-002
Inputs: hardware/scripts/gen_pcb.py, gen_schematic.py @ 86866be (+ T-060 working tree). Raw outputs: `sim/electronics/calc/calc_flashover.out`, `calc_pulse_rated.out`, `check_gap.out`, `check_gap_old_86866be.out`, `calc_mechanical.out`.

**Voltage across R** (CALCULATION, IEC 150 pF / 330 Ω, ELE side held near 0 V by the pin — ASSUMPTION): V_R = V·R/(R+330) = 3636 V at 4 kV, 7273 V at 8 kV. If an arc bypasses R the pin sees 12.1 A / 24.2 A instead of 1.10 A / 2.20 A.

**Breakdown sweep** (calc_flashover.py; every model ASSUMPTION, constants stated in the script):

| Model | gap @ 4 kV (3.64 kV) | gap @ 8 kV (7.27 kV) |
|---|---|---|
| Uniform field 4.5 / 3.0 / 2.0 kV/mm | 0.81 / 1.21 / 1.82 mm | 1.62 / 2.42 / 3.64 mm |
| Paschen (Townsend form, γ = 0.01) | 0.67 mm | 1.56 mm |
| Empirical uniform air (Kuffel) | 0.73 mm | 1.79 mm |
| Non-uniform, η = 0.7 / 0.5 / 0.3 | 1.17 / 1.79 / 3.33 mm | 2.77 / 4.13 / 7.46 mm |
| IEC 60664-1 Table F.2 case A, interpolated (values recalled, not re-read) | 2.61 mm (3.00 mm at the full 4 kV) | 7.07 mm |

**Design rule** (CALCULATION): (a) ELEx ↔ Ex copper/leads of one channel and (b) Ex ↔ any other channel's ELE net or any MPR121/Pico net: **≥ 3.5 mm** for 4 kV (worst of η = 0.3 and F.2 case A, rounded up); 8 kV would need **≥ 7.5 mm**. Ex ↔ Ey and Ex ↔ GND are reported only (an arc there still passes a resistor, or diverts the strike to ground; see the Ex ↔ GND decision below). The rule applies to any metal at those potentials, not only copper: on the component side that is the resistor end caps (T-073).

**Old layout fails** (MEASUREMENT on the design file, check_gap_old_86866be.out): (a) 0.94 mm, (b) 1.99 mm (R2 pad 2 E1 ↔ R3 pad 1 ELE2); the vertical lead ran ≈1 mm from the opposite end cap (ASSUMPTION, CR-002).

**Pulse rating** (calc_pulse_rated.py): the body itself must also hold V_R. 1.2/50 µs ratings at 3.3 kΩ read from the vector chart of Vishay doc. 28766 (EE-S17b, ±5 % reading ASSUMPTION): MBA 0204 1.47 kV, MBB 0207 1.74 kV, **MBE 0414 4.08 kV** (margin 1.12 at 4 kV); Vishay LSR37 is rated for 12 kV ESD contact discharge (≈10.9 kV across 3k3, EE-S24) but is ±10 % and drifts up to ±20 % after 100 strikes; Yageo MFR-12 400 V. **Selected: Vishay MBE04140C3301FC100** (3k3 1 %, keeps the T-050 sensitivity analysis valid): PASS at 4 kV, FAIL at 8 kV (4.08 < 7.27 kV). Energy (T-073 / C2-003, corrected; T-060 used ∫V dt and stated ≈364 mJ): the rating pulse puts (Vpk²/R)·∫(V/Vpk)² dt = 4083²/3300 · 36.1 µs ≈ **182 mJ** into 3k3 (CALCULATION, 1.2/50 µs double exponential; single-exponential cross-check 36.07 µs). The chart below its knee has a log-log slope of 0.496 (CALCULATION from the vector path), i.e. constant V²/R: at 3.3 kΩ the rating is **energy-limited**; above the knee at ≈5.07 kΩ it is voltage-limited at a plateau of ≈5.05 kV (CALCULATION; the reviewer read ≈5.06 kV / ≈5.07 kΩ). One 4 kV IEC strike puts 1.09 mJ and 3636 V into R: 167× below the rating-pulse energy and 1.39× below the plateau. The 3k3 chart value 4083 V stays the acceptance limit (conservative). At 8 kV, 7273 V exceeds both the chart value and the plateau: FAIL either way. Conclusions unchanged. A DIN0414 body (Ø 4.2 mm) needs a 5.08 mm row pitch, which forces a 2.54 → 5.08 mm fan-out before the resistors.

**Layout (T-060)**: R1–R12 lie flat, axis along y, 15.24 mm pitch (datasheet minimum 15.0 mm), pads 2.2 mm / drill 1.0 mm (T-073: now 1.1 mm, see below; lead 0.8 mm), one row at the terminal pitch offset 1.27 mm; ELE fan-out at 45° above the row, E side straight to J2. To make room the MPR121 module moved 15.1 mm up and 2.54 mm right; J1, JP1 (upright), R13–R15 moved to the right of the module; SDA/SCL, S1/S7 run under the module between its two headers; 3V3 runs along the top edge; H4 moved from (70, 6) to (88.5, 30.5). Pinout, nets and J2 row unchanged.

**Measured gaps** (check_gap.out, T-073 re-run). Copper (MEASUREMENT on the design file, B.Cu): (a) 13.04 mm on all 12 channels; (b) 10.92 mm (R1 pad 2 E0 ↔ Pico pad 21) → PASS against 3.5 mm (4 kV) and 7.5 mm (8 kV). Reported: Ex ↔ Ey 2.08 mm (J2 terminal pads), Ex ↔ GND 1.40 mm (J2 pads ↔ GND edge track). The T-060 "lead ↔ lead 14.44 mm" line was removed (C2-002): for a flat resistor the leads leave the caps outwards and are never the closest metal.

**End caps, component side (T-073 / C2-002)** (CALCULATION from the footprint pad positions, check_gap.out section (d)). The Vishay drawing (EE-S17b, EE-S27) gives no cap length, so it is swept as an ASSUMPTION; other inputs: body length 11.9 mm (Lmax, SOURCE) and 11.0 mm (ASSUMPTION, no Lmin given), cap diameter 4.2 mm (Dmax, SOURCE; worst for cross-channel), lacquer over the caps ignored (bare metal), axial placement error of a hand-fitted body 0 / ±0.25 / ±0.5 mm per part (ASSUMPTION, worst sign per pair). Same channel (E cap ↔ ELE cap) = L − 2·Lc; cross-channel (E cap of Rk ↔ ELE cap of Rk±1, 5.08 mm row pitch, 0.88 mm between bodies sideways) is the worst pair.

| Body L / cap Lc (mm) | same channel | cross-channel, no error | ±0.25 mm | ±0.5 mm |
|---|---|---|---|---|
| 11.9 / 1.5 | 8.90 | 8.94 | 8.45 | 7.95 |
| 11.9 / 2.5 | 6.90 | 6.96 | 6.46 | 5.97 |
| 11.0 / 2.5 | 6.00 | 6.06 | 5.57 | 5.08 |
| 11.0 / 3.0 | 5.00 | 5.08 | 4.59 | 4.10 |
| 11.0 / 3.5 (worst) | 4.00 | 4.10 | 3.61 | **3.13** |

(values in mm; full sweep in check_gap.out.) Result: **4 kV rule (3.5 mm) PASS over the whole sweep for placement error ≤ ±0.25 mm (worst 3.61 mm); FAIL only at the corner Lc 3.5 mm, L 11.0 mm with ±0.5 mm (3.13 mm)**; for Lc ≤ 3.0 mm it passes at every swept L and error. Status PARTIAL (rests on assumed cap length). Mitigation: hardware/README asks for the leads to be formed on a gauge, straight lengths equal within ≈0.25 mm; first-article check: measure L and Lc on one part with a caliper (validation plan). **8 kV (7.5 mm): not shown** — met only for short caps (Lc ≤ 1.5 mm at either L with ≤ ±0.25 mm error, or Lc ≤ 2.0 mm on an Lmax body without error); the 8 kV gap statement of T-060 (§5 and R-006, "already meet the 8 kV 7.5 mm rule") applies to copper only.

**Floating metal at the mounting holes (T-073 / C2-009)** (check_gap.out section (e), CALCULATION; screw head / washer / spacer radius 2.8–3.5 mm, ASSUMPTION ISO 7045 pan head 5.6 mm, ISO 7089 washer 7.0 mm; an arc ELEx → metal → Ex counted as the sum of the two gaps, ASSUMPTION). At the old H3 (95, 48) a metal screw head lay 0.18–0.88 mm from the R12 ELE11 cap and 1.76–2.46 mm from the E11 cap: bypass sum **1.94 mm, FAIL** vs 3.5 mm (check_gap_old_1247c44.out). H3 moved to (96, 38), where it faces only the ELE11 cap: worst bypass over H1–H4 **15.36 mm, PASS** at 4 kV and 8 kV. This also clears the 0.09 mm R12 ↔ H3 courtyard gap. Nylon hardware is still recommended in the README. The INTERFACES.json placement record (systems) must be updated for H3.

**Ex ↔ GND 1.40 mm: kept as an intentional spark gap (T-073 / C2-005 decision).** Every J2 electrode pad is 1.40 mm from the GND edge track, below the breakdown distance of every model at 3.64 kV (0.67–3.33 mm), so a 4 kV strike most likely arcs to GND there. That path keeps the strike off Rx and the MPR121 pin, it is the same at every terminal, and moving the track ≥ 3.5 mm away would only send the full 1.1 A into the pin through Rx and still arc at higher levels or with flux residue. What the arc current does on the way to the host (calc_gnd_bounce.out): GND track lengths (MEASUREMENT) terminal GND → Pico pin 23 24.04 mm, module GND pin → pin 23 31.36 mm, shared section only 4.72 mm (node (27.00, 45.18) → pin 23); the edge track and the trunk down to the node are common to module and Pico (whole-board rise, no difference at IC pins). With the IEC 4 kV current (SOURCE EE-S16 from memory: 15 A +15 % first peak, 0.6–1.0 ns rise), 0.7–1.0 nH/mm track and 3–10 nH socket + header pin (ASSUMPTION), the module-GND ↔ Pico-GND bounce is **87–339 V for ≈1 ns**, ≈4.5 V after the first peak (CALCULATION). Through R15/R16 (220 Ω, then the module's BSS138 level shifters) that is ≤ 1.53 A and ≤ 0.92 nC per I²C line: 0.2 % of the charge and 0.57× the peak current of the RP2040's HBM 4 kV rating (SOURCE EE-S28) — but that rating is stated for digital FT pins, and GP26/GP27 are ADC-capable pins whose HBM value was not found (NOT CONFIRMED, escalated). Without the arc the same path would carry 1.10 A (≈22 V bounce) and the pin would take the strike. Residual risk: an I²C pin upset or latch-up from the ≈1 ns bounce (estimate only); the ESD test (REQ-023) should check for an arc to the GND edge track and for I²C errors / resets after each strike.

**Other T-073 changes:** R1–R12 drill 1.0 → **1.1 mm** (C2-008): ring (2.2 − 1.1)/2 = 0.55 mm ≥ 0.40 mm, hole − lead = 0.30 mm diametral (0.15 mm radial) ≥ 0.2 mm rule (calc_mechanical.out PASS; generator comment corrected, the old "0.2 mm around" was diametral). Terminal labels moved midway between the resistor pads, "10"/"11" at 0.9 mm text: worst silkscreen-text ↔ pad gap 0.43 mm (was 0.00 mm), all 24 board texts PASS ≥ 0.2 mm (check_silk.out, MEASUREMENT). check_gap.py worst-pair ties are broken by reference, then pad (C2-011).

Status: copper flashover around R — PASS on design data (4 kV and 8 kV rules); end caps — PARTIAL at 4 kV (assumed cap length and placement), 8 kV not shown; mounting metal — PASS; Ex ↔ GND — intentional spark gap, residual risk estimated, not measured; resistor pulse rating — PASS 4 kV, FAIL 8 kV; REQ-023 stays PARTIAL until an ESD-gun test (nothing here is measured on hardware).

## 6. Design review follow-up — T-076 (JP1 pitch, J2 pad shape, RV1 tabs and C1, silkscreen)

Inputs: branch change/CR-002 at 565ffb5 plus the T-076 generator changes (hardware/scripts/gen_pcb.py, gen_schematic.py). Evidence: reports/electronics/evidence/T-076/.

| Change | Result | Label / evidence |
| --- | --- | --- |
| JP1 pitch 2.54 → 3.81 mm, pads 1.94 × 2.4 mm, drill 0.8 mm (unchanged) | Pad-to-pad copper gap 0.60 → **1.87 mm** (1–2 and 2–3), 1–3 5.68 mm; ring 0.57 mm. Pad 1 stays on the S1 run (y 15.74), pad 3 moved 2.54 mm above the S row (y 8.12): S7 now runs level, 45° up and into pad 3. QT/ORIG labels 0.46 mm from the pads | MEASUREMENT on the design file, measure_t076.out, check_silk.out |
| J2 pads 3.0 mm round → **3.0 × 4.5 mm oval** (pad 1 rectangular), drill 1.4 mm, copper offset 0.75 mm towards the back of the block | Copper area per pad 7.1 → 11.6 mm² (CALCULATION: π·1.5² and π·1.5² + 3.0·1.5); the pad still ends 1.5 mm below the hole, so Ex ↔ GND edge track stays **1.40 mm** (ADR-020 spark gap, unchanged), adjacent pads 2.08 mm (unchanged), pad ↔ resistor pads ≥ 3.15 mm; minimum ring 0.80 mm (unchanged) | MEASUREMENT, measure_t076.out, check_gap.out |
| RV1 tabs (pad "MP") on AGND; symbol Device:R_Potentiometer_MountingPin | Both tabs routed: C1 pad 2 → upper tab → lower tab ← pad 3 | ERC/DRC with parity 0 violations |
| C1 100 nF X7R 50 V, KEMET C322C104K5R5TA, 5.08 mm leads, POT → AGND, above RV1 | 0.8 mm drill, 2.0 mm pad (ring 0.60 mm), lead 0.51 mm nominal (gap 0.29 mm diametral). **T-080 / F2-001:** lead tolerance .020 +.004/−.001 in = 0.48–0.61 mm (SOURCE EE-S29); at 0.8 mm the max lead left 0.19 mm < 0.2 mm, so the drill is now **0.9 mm**: gap 0.9 − 0.61 = 0.29 mm, ring (2.0 − 0.9)/2 = 0.55 mm (CALCULATION); 3D model stretched to the 5.08 mm pitch (F2-007) | SOURCE EE-S29; calc_mechanical.out PASS (max lead) |
| R16 / SW1 designators overlapped; R14 designator 0.16 mm from R13 pad 1 | R16 designator moved above R16 (clear of SW1), R14 designator to the right of R14, JP1 legend line pitch 1.4 → 1.55 mm. check_silk.py now also measures visible footprint designators and text-to-text overlap | check_silk.out: worst text-to-pad 0.35 mm (R13), text-to-text 0.11 mm, PASS |

**ADC settling with C1 (CALCULATION, sim/electronics/calc/calc_pot_rc.out).** The wiper sees the pot Thevenin resistance R·x·(1−x), maximum R/4 = 2.5 kΩ at mid travel (R = 10 kΩ ±20 %, SOURCE EE-S13; worst 3.0 kΩ). τ = 2.5 kΩ × 100 nF = **0.25 ms** nominal, fc = 637 Hz; worst case 3.0 kΩ × 126 nF (C +10 % tolerance, +15 % X7R temperature, SOURCE EE-S29) = **0.38 ms**, fc = 419 Hz. A full-scale step settles to ½ LSB (10-bit, SOURCE fm_pot.h) in ln(2048) = 7.62 τ = 1.91 ms nominal / **2.89 ms** worst, against the pot read period POT_READ_MS = **30 ms** (SOURCE firmware/FrutaMIDI/fm_pot.h): margin **10.4×** worst (79 τ per period). Lag during a 100 ms full turn (ASSUMPTION, fastest flick) = 3.9 counts worst, against 205-count zones and ≈41-count hysteresis: no visible effect on the octave choice. Charge sharing with the RP2040 sample capacitor (value not given in the RP2040 ADC section; ≤ 10 pF ASSUMED) ≤ 0.10 LSB. Status: PASS (CALCULATION); not measured.

**C2 (1 µF +3V3 → GND near JP1 / module GND): NOT ADDED.** There is no GND copper anywhere in the right half of the board above the SDA run (y 21 mm): the module GND enters only through the electrode row (pin 1, x 44.78, y 25.9), and the SCL (y 18.5, to x 85) and SDA (y 21, to x 88.8) runs separate it from the 3V3 drop to JP1 (x 82.5, y 2 → 11.9). On one layer without vias the only route is (a) 3V3 down the right edge, between J1/R14 and the H2 fixing (≤ 0.05 mm from the ASSUMED 3.5 mm washer radius at the minimum 0.6 mm clearance to J1 pad 2), plus (b) a ≈48 mm GND run under the module at y ≈ 23, 1.1 mm from all twelve ELE pins (extra capacitance on every electrode). The cap-to-module loop would be ≈100 mm long (≈100 nH at an ASSUMED 1 nH/mm), i.e. inductive above ≈0.5 MHz (CALCULATION 1/(2π√(LC))): little decoupling benefit, for new parasitics on the sensing inputs and copper at an assumed fixing-metal boundary. Both module revisions carry their own 3.3 V LDO (SOURCE EE-S02/EE-S03), whose input JP1 feeds. Decision left to the manager (risk/benefit), see handoff T-076.

**Unchanged:** check_gap.out is identical to the T-073 run (copper (a) 13.04 mm, (b) 10.92 mm, end caps PARTIAL at 4 kV, mounting metal 15.36 mm, Ex ↔ GND 1.40 mm). Cost delta: C1 ≈ 0.20–0.90 € (SOURCE EE-S30, search, not verified); no other new part (JP1 is copper only; the J2 pad change costs nothing).

Status: ERC 0, DRC 0 (with schematic parity), check_gap unchanged, check_silk PASS — design-file checks only; nothing here is hardware-validated.

## 7. SMD board (CR-003, ADR-023) — T-091 / T-092

Inputs: hardware/scripts/gen_pcb.py, gen_schematic.py @ f3a718a plus the T-092 working tree. Raw outputs: `sim/electronics/calc/*.out` (`sh sim/electronics/calc/run_all.sh`), copies in `reports/electronics/evidence/T-092/`. Nothing here is measured on hardware; "MEASUREMENT" means measured on the design file. ERC/DRC passing is not hardware validation.

### 7.1 What the board is
(At T-091 / T-092; R1-R12 changed in T-096, module and Pico lands in T-103: see section 8.) 100 × 70 mm, copper on F.Cu only, no vias, no pour, 4 holes (M3, NPTH). R1-R12 TT HPWC2512 3k0 ±5 % on a 1.9 × 3.35 mm land with G = 5.0 mm; Pico surface-soldered on castellations with two etched keep-outs (TP/USB and SWD pads); MPR121 module on butted header pins; R13-R16 and C1 in 1206; SW1 Omron B3S-1000; J2 and RV1 as solder-wire pads. Pin map unchanged (check_smd.out REQ-031).

### 7.2 Results that changed with R = 3k3 → 3k0 ±5 % (SUPERSEDED)

> **Superseded (T-096 / ADR-026, recorded in T-103):** R1-R12 are no longer TT HPWC2512 3k0 ±5 %. They are YAGEO RC2512FK-073K3L, 3k3 ±1 %, which has no pulse rating, so the "pulse rating PASS 4 kV" below does **not** apply to the current board. See section 8. The table is kept as the record of the T-091 / T-092 design.

| Quantity | V1.2 (3k3 1 %) | SMD (3k0 ±5 %) | Label |
|---|---|---|---|
| V across R at 4 / 8 kV | 3636 / 7273 V | 3604 / 7207 V nominal; 3621 / 7241 V at 3150 Ω | CALCULATION |
| Flashover rule 4 / 8 kV | 3.5 / 7.5 mm | 3.5 / 7.5 mm, unchanged (η = 0.3: 3.31 / 7.42 mm at 3150 Ω; F.2 case A at full 4 kV 3.00 mm) | CALCULATION on ASSUMPTION models |
| Pin current at 4 / 8 kV | 1.10 / 2.20 A | 1.20 / 2.40 A; 1.26 / 2.52 A at 2850 Ω | CALCULATION |
| Margin against the 1.33 A inferred pin limit, 4 kV | 1.21 | 1.11; 1.06 at 2850 Ω | CALCULATION; the limit is an ASSUMPTION |
| Min R for 1.33 A | 2670 Ω at 4 kV, 5670 Ω at 8 kV | unchanged: 2850 Ω passes 4 kV, 8 kV still needs 5670 Ω | CALCULATION |
| Pulse rating margin at 4 kV | 1.12 (4083 V) | 1.24 at 3k0 (4472 V), min 1.21 at 2850 Ω; 1.15 with −5 % chart reading | CALCULATION from SOURCE chart (T90-S2, raster) |
| Pulse rating margin at 8 kV | 0.56, FAIL | 0.62, FAIL | CALCULATION |
| Energy in R, one 4 kV strike | 1.09 mJ | 1.08 mJ | CALCULATION |
| Sensitivity, min relative (nominal / worst choice, 10-1000 pF) | 0.904 / 0.904 | 3k0: 0.925 / 0.904; 2850 Ω: 0.926 / 0.905; 3150 Ω: 0.905 / 0.904 | SIMULATION sim_electrode.py |
| Smallest touch, 1000 pF | 19.9 pF | 19.9 pF | SIMULATION |

The criterion (ADR-019: nominal ≥ 0.90, worst ≥ 0.80) holds across the 3k0 band. The rejected 3k3 ±5 % at 3465 Ω simulates 0.903 nominal, **0.885 worst choice**; T-090 had interpolated 0.899 from sparser data, same direction. Status: sensitivity PASS (SIMULATION); pulse rating PASS 4 kV, FAIL 8 kV (R-006 stays open); 4 kV pin-current margin thinner than V1.2 (1.06 worst against 1.21), resting on an ASSUMED limit.

### 7.3 Gaps and spark gap (check_gap.out, MEASUREMENT on the design file unless labelled)

| Item | V1.2 | SMD | Status |
|---|---|---|---|
| (a) ELEx ↔ Ex copper | 13.04 mm | 5.00 mm | PASS 4 kV (3.5), FAIL 8 kV (7.5) |
| (b) Ex ↔ any MPR121/Pico net | 10.92 mm | 5.29 mm | PASS 4 kV, FAIL 8 kV |
| Terminations / caps, worst at ±0.25 / ±0.5 mm placement | 3.61 / 3.13 mm (cap length ASSUMED) | 4.25 / 3.79 mm (L, A SOURCE; placement ASSUMPTION; CALCULATION) | PASS 4 kV over the sweep, an improvement; FAIL 8 kV |
| Ex ↔ Ey | 2.08 mm | 1.66 mm | Reported (passes a series R) |
| Ex ↔ GND spark gap (ADR-020) | 1.40 mm | 1.401 mm | PASS against 1.40 ± 0.05 |
| Mounting-metal bypass, worst sum, r 3.5 mm | 15.36 mm | 8.26 mm (H3: ELE11 6.04 + E11 2.21 mm), CALCULATION, radius ASSUMPTION | PASS 4 kV and 8 kV rule. Lower than V1.2 and T-091 (17.71 mm) because H3 moved towards its corner |

So the SMD board gives up the 8 kV copper margin V1.2 had (V1.2 copper met 7.5 mm; its end caps did not), and gains the 4 kV termination margin. REQ-023 stays PARTIAL until an ESD-gun test.

### 7.4 Mounting holes and USB pull (T-092)

Positions (MEASUREMENT, frutamidi.drl), in mm from the top-left corner, with clearances (MEASUREMENT on the design file, hardware radius ASSUMPTION, ISO not opened):

| Hole | Position | Drill edge to board edge | r 3.5 washer to nearest copper | r 2.8 head to nearest copper | r 3.5 washer to nearest courtyard |
|---|---|---|---|---|---|
| H1 | (5.0, 65.0) | 3.40 | 10.44 (A1 pad 20) | 11.14 | 9.20 (A1) |
| H2 | (96.0, 4.0) | 2.40 | 2.86 (R14 pad 1, 3V3) | 3.56 | 2.57 (R14) |
| H3 | (96.5, 58.0) | 1.90 | 1.08 (J2 pad 14, GND) | 1.78 | 0.17 (J2) |
| H4 | (29.8, 4.0) | 2.40 | 0.60 (3V3 track at x 34.5; Pico lands 0.62) | 1.30 | 0.30 (A1) |

Why these: H4 cannot sit left of or above the module, whose lands reach x 25.68 (module edge x 23.89) and whose end is at y 0.63 with 0.63 mm of board beyond it. Its x is the point where a 3.5 mm washer has 0.6 mm to both the Pico lands and the 3V3 riser, which T-092 moved from x 27.2 to x 34.5 to free this area (now routed level from pin 36, 45° to RV1 pad 1, up to the top run). H3 cannot reach the true corner because J2 pad 14 and the spark-gap GND track occupy the bottom edge to x 94.54; at (97.3, 67.0) a pan head would fit but the drill would be 1.1 mm from the edge, weaker than a hand-drilled FR-4 hole should be, and a 7 mm washer would touch the GND pad. H1 and H2 moved towards their corners with no routing change.

Checks in check_smd.py, section 7 (criteria chosen in T-092, ASSUMPTION): one hole per quadrant PASS; min hole-to-hole 54.20 mm (T-091: 10.6 mm) against ≥ 45 mm PASS; hole quadrilateral 4491 mm², 64.2 % of the board against ≥ 60 % PASS; nearest hole to the centre of the Pico USB end 16.75 mm (T-091: 63.6 mm) against ≤ 20 mm PASS.

**USB pull effect (CALCULATION, `calc_usb_pry.out`; thin-plate Ritz model, E 22 GPa, ν 0.15, t 1.6 mm ASSUMPTION, screws as pins, Pico not modelled, converged within about 1 % from p = 12 to 14).** For a force normal to the board at the USB end: deflection there 0.319 mm/N with the T-091 holes, **0.0266 mm/N** with these, a factor **12.0** less (linear, so about 9.6 → 0.8 mm at 30 N); largest screw force 108 N → 35.3 N at 30 N, now on H4 at 1.18× the applied force. Use the ratio, not the absolute values.

**This does not change the joint margin.** The T-090 pry margin of the castellations, 0.57-0.75 at 30 N (rigid carrier and module; peel strength ASSUMPTION), does not depend on hole positions and stays as it was. What H4 removes is the carrier bending under a pull, a load path the T-090 model ignored. The extra joint peel from carrier curvature is **not quantified**. The epoxy bead and a strain-relieved cable remain the measures that act on the joints. Bolting the Pico through its own two 2.1 mm holes at the USB end (T-090) would act on them directly, but is a 2-hole change to ADR-023 D-4.

Hardware: nylon screw and nylon washer recommended, pan head ≤ 5.6 mm, washer ≤ 7 mm (README section 4). A 7 mm metal washer at H4 leaves 0.6 mm only.

### 7.5 Other re-runs
- **calc_pot_rc** with C1 1206 and off-board pot: τ 0.25 ms nominal, 0.38 ms worst, 2.89 ms settling against 30 ms (margin 10.4×), **numbers unchanged** from V1.2, but inputs are now ASSUMPTION rather than SOURCE: C1 datasheet not opened, off-board pot not chosen (CALCULATION, PASS on those inputs).
- **calc_gnd_bounce** for the board without sockets: series elements now castellation 0.5-1.5 nH + butted module pin 2.9-4.9 nH = 3.4-6.4 nH (ASSUMPTION; V1.2 used 3-10 nH). Shared section 3.84 mm (MEASUREMENT; V1.2 4.72 mm). Worst bounce **236 V / ≈1 ns** (V1.2: 339 V; T-091: 318 V), ≤ 1.06 A and ≤ 0.64 nC per I²C line, 0.40× the RP2040 HBM peak (CALCULATION). The ADC-capable-pin HBM value is still NOT CONFIRMED (EE-S28). Status: estimate only.
- **calc_power**, **calc_esd_variants**, **calc_flashover**, **calc_pulse_rated**, **sim_electrode** updated to 3k0. calc_i2c, calc_i2c_series, calc_r011_offboard_pot, calc_smd_feasibility and calc_mechanical now all run from run_all.sh (no input change).
- **Retired:** check_silk.py/.out and calc_pulse.py/.out moved to `sim/electronics/calc/retired/`. check_smd.py section 8 checks the assembly-map designators (SW1 ↔ R16 now 8+ mm apart).

### 7.6 Open
Peel strength on home-etched copper, castellation hand-solder quality, ESD behaviour (REQ-023, R-006, R-010, R-011) and the pot wiring all need a physical build and test. HPWC stock and C1 datasheet not confirmed. (HPWC superseded by RC2512FK-073K3L, section 8.)

## 8. Electrode resistor RC2512FK-073K3L (T-096, T-103)

Inputs: YAGEO RC_L datasheet V.11 (copy in `reports/electronics/evidence/T-096/datasheets/`), `sim/electronics/calc/calc_pulse_rated.out`, `sim_electrode.out`, `check_gap.out`, handoff T-096. ADR-026 accepted that the pulse capability is not proven. Nothing here is measured on hardware.

### 8.1 Part and ratings (SOURCE YAGEO RC_L V.11)
R1-R12 = YAGEO RC2512FK-073K3L, 3.3 kΩ ±1 %, 1 W, 2512 thick film. L 6.35 ±0.10, W 3.10 ±0.15, I1 0.60 ±0.20 mm. Max working voltage 200 V, max overload 500 V, dielectric withstanding 500 V. **No pulse, surge or ESD rating is published.**

### 8.2 Pulse capability: NOT PROVEN
| Quantity | Value | Label |
|---|---|---|
| V across R, IEC 61000-4-2 4 kV contact | 3633 / 3636 / 3640 V at 3267 / 3300 / 3333 Ω; 7.3× the 500 V overload | CALCULATION |
| V across R, 8 kV | 7273 V | CALCULATION |
| Energy into R per strike, 4 / 8 kV | 1.09 / 4.36 mJ; τ = (330 + 3300) Ω × 150 pF = 0.544 µs | CALCULATION |
| Peak power, 4 / 8 kV | 4007 / 16028 W | CALCULATION |
| Energy of the old 1.2/50 µs acceptance pulse (MBE0414 chart 182 mJ; HPWC at 4596 V 231 mJ) | 167× / 212× one 4 kV strike | CALCULATION |
| Adiabatic film temperature rise, 4 / 8 kV | 3.1 / 12.6 K; 31 / 126 K with an ASSUMED ×10 trim hot spot; whole body 0.034 K | CALCULATION on ASSUMPTION |
| Mean field along the film | 0.71 kV/mm; field at the trim kerf unknown | CALCULATION |

The energy comparison says that one 4 kV strike is far below the energy the earlier (rated) parts were accepted against, but it is not a rating for this part: thick-film failure under a fast pulse is governed by the local field and hot spot at the laser trim, which the datasheet does not cover. Status: **NOT PROVEN** at 4 kV and 8 kV. Gaps: no maker surge curve, no test of repeated strikes (resistance drift), no flashover test along the body. Only an ESD-gun test (4 kV contact, repeated, resistance logged before and after) can close it.

### 8.3 Sensor pin current and what the margin compares
Pin current at 4 kV: 1.10 A at 3300 Ω, 1.11 A at 3267 Ω, against the 1.33 A limit inferred from the MPR121 2 kV HBM rating (ASSUMPTION): margin **1.20-1.22** (CALCULATION). 8 kV: 2.20 A, FAIL.

That margin compares **peak current only** (F3-005). The two pulses differ in charge and duration (CALCULATION):
- charge: IEC 4 kV, 150 pF × 4 kV = **600 nC**; HBM 2 kV, 100 pF × 2 kV = **200 nC**: ratio **3.0×**;
- decay time: IEC through 3.3 kΩ, (330 + 3300) Ω × 150 pF = **0.54 µs**; HBM, 1500 Ω × 100 pF = **0.15 µs**: ratio **3.6×**.

So the pin sees a pulse with three times the charge and 3.6 times the duration of the pulse its rating is based on. If the pin's protection fails on charge or energy rather than peak current, the margin of 1.2 does not hold. Status: PASS on peak current against an ASSUMED limit; NOT PROVEN overall.

### 8.4 Gaps around the resistor (MEASUREMENT on the design file, check_gap.out)
Copper gap 5.00 mm, termination gap 4.65 mm (4.08 mm with ±0.5 mm placement): PASS against 3.5 mm (4 kV), FAIL against 7.5 mm (8 kV). Spark gap J2 pad to GND edge track 1.401 mm for all 12 electrodes. Sensitivity worst ratio 0.904 at 3267 / 3300 / 3333 Ω (SIMULATION, limit 0.90).

### 8.5 T-103 layout changes that touch earlier numbers
- **Module (A2) lands, F3-001:** the header strip now sits against the module underside, the pin legs (cut to 3.0 mm, ASSUMPTION) stand on lands 1.8 × 4.2 mm (electrode row) and 1.8 × 5.5 mm (S row) that run 1.73 / 1.78 mm beyond the module outline (CALCULATION, check_smd.out). Inner land edges unchanged: SDA to electrode pads still **3.30 mm**, SCL 5.30 mm (MEASUREMENT, `reports/electronics/evidence/T-103/measure_i2c_gap.out`). SDA-to-pad capacitance with the longer pads 36.6 fF (was 33.0 fF), SDA step on the electrode node 2.09 ADC counts (was 1.89) against the 12-count touch threshold (SIMULATION, calc_i2c_coupling.out, finest mesh).
- **Ground bounce:** the module pin path is longer (3.0 mm leg + 2.5 mm strip + 1.6 mm board = 7.1 mm, ASSUMPTION; was 4.1 mm), so the pin inductance becomes 5.0-8.5 nH (was 2.9-4.9 nH, ASSUMPTION 0.7-1.2 nH/mm). Worst module-to-Pico GND bounce **330 V for about 1 ns** (was 236 V; CALCULATION on ASSUMPTION inputs, calc_gnd_bounce.out). Not measured; the ADC-capable pin HBM value is still NOT CONFIRMED.
- **Pico position, F3-002:** pin 1 column at y 1.48 mm (was 2.0); USB end 0.11 mm inside the board edge, receptacle face 1.19 mm beyond it (CALCULATION from SOURCE 1.30 mm). Fully flush would put the pin 1 / 40 lands 0.495 mm from the etched outline line, below the 0.6 mm rule. calc_usb_pry re-run with the load at (13.39, 0.11) mm.
- **Pico 2 keep-outs, F3-003:** TP7 (1V1) keep-out added; all 11 Pico 2 underside features (Pico 2 datasheet Fig. 5) checked: nearest copper 2.14 mm, TP7 3.66 mm (MEASUREMENT, check_smd.out). Pico W / Pico 2 W are not supported on the PCB until their underside is checked.
- **1206 lands, F3-014:** lengthened outward to 1.775 mm (R) and 1.875 mm (C); copper beyond the body ≥ 1.05 mm (CALCULATION on SOURCE / ASSUMPTION body sizes, check_smd.out).
