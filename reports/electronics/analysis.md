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
- Dissipation: pot 1.16 mW vs 50 mW (EE-S13); series R 13 µW at 63 µA; one 8 kV IEC strike ≈4.36 mJ into 3.3k — resistor pulse rating not checked (open).
- Clearance: max steady 3.3 V needs 0.1 mm (IPC-2221B B2); rule 0.6 mm. ESD may flash over gaps < ≈1.3/2.7 mm at 4/8 kV (≈3 kV/mm ASSUMPTION); each path still has its series R.
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
**Design rule 2.7 kΩ ≤ R ≤ 3.3 kΩ; chosen 3.3 kΩ (Yageo MFR-12FTF52-3K3).**

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
