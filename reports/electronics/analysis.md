# Electronics analysis — T-050 / T-052

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
