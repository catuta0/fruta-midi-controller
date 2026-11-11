# T-094 — electronics-engineer

Status: PARTIAL. R-017 re-route PASS. LCSC fields PASS for R13-R16, C1, SW1, RV1. R1-R12 FAIL: no LCSC part meets every criterion, nothing implemented for R1-R12, user decision needed. Pico and MPR121 module not sourced at LCSC, user decision. No hardware measured.

Requirements addressed: R-016 (R1-R12 availability, open), R-017 (I2C near A2, re-routed), REQ-038 (still [PHYSICAL]), R-011 (RV1 insulated shaft).

Inputs: hardware/scripts/*, sim/electronics/calc/* @ 410933d-dirty; ADR-019, ADR-023; handoffs T-090, T-092, T-093.

Outputs:
- hardware/scripts/gen_schematic.py (R13-R16, C1, SW1, RV1 MPN and LCSC fields), hardware/scripts/gen_pcb.py (Y_S1, Y_SCL, Y_SDA = 15.74, 18.9, 20.9; ORIG legend moved to 74.0, 13.2), hardware/scripts/build_all.sh (LCSC BOM column); regenerated hardware/ files; hardware/README.md
- sim/electronics/calc/calc_i2c_coupling.py and .out (new), sim_electrode.py (R sweep extended), run_all.sh
- reports/electronics/SOURCES_EE.md (T94-S1..S7)
- reports/electronics/evidence/T-094/ (distributor_pages.txt, datasheets/, render/, build_all.log, run_all.log, erc.rpt, drc.rpt, bom-kicad.csv, frutamidi.drl, measure_i2c_gap.py and .out, copies of the .out files)

## Checks performed (KiCad 10.0.4, all through pcgate chat2, after the last generator change)

| Check | Command | Result line | Status |
|---|---|---|---|
| Build | sh hardware/scripts/build_all.sh | "OK: ERC and DRC without violations; files in hardware/fabrication", EXIT=0 | PASS |
| ERC | erc.rpt | "ERC messages: 0  Errors 0  Warnings 0" | PASS |
| DRC with parity | drc.rpt | "Found 0 DRC violations", "Found 0 unconnected pads", "Found 0 Footprint errors" | PASS |
| Holes | frutamidi.drl | T1C3.200, 4 hits: X5.0Y-65.0, X29.8Y-4.0, X96.0Y-4.0, X96.5Y-58.0 (MEASUREMENT) | PASS |
| Calculations | sh sim/electronics/calc/run_all.sh | EXIT=0; check_smd "SUMMARY: 43 checks, 43 PASS, 0 FAIL" | PASS |
| Gap at 4 kV | check_gap.out | "copper PASS (4 kV rule, (a) and (b)); terminations PASS at 4 kV over the swept ASSUMPTIONS; mounting metal PASS; spark gap PASS" | PASS |
| Gap at 8 kV | check_gap.out | "SUMMARY 8 kV: copper FAIL; terminations FAIL (worst 3.79 mm vs 7.5 mm)" (unchanged, 4 kV is the project rule) | FAIL |
| I2C gap | measure_i2c_gap.py on the .kicad_pcb | "/SDA ... 3.300 mm (pad 2)", "/SCL_PICO ... 5.300 mm (pad 2)" | PASS |
| sim/systems checks | owned by systems engineer | | NOT RUN |

ERC and DRC passing is not hardware validation.

## R1-R12 candidates (ranked; all prices SOURCE, 2026-11-09)

Pulse limit needed: about 3.6 kV. Current limit 1.33 A (ASSUMPTION, inferred). Sensitivity limit 0.90 worst choice (ADR-019).

| Rank | Part, shop | Stock, price for 12 | R and worst corner (SIMULATION) | Pulse 1.2/50 µs | Gap | Result |
|---|---|---|---|---|---|---|
| 1 | TT HPWC2512-3K3JT1, Mouser PT (not LCSC) | 2,381, min 1, EUR 1.25 at 10, EUR 15.00 | 3k3 ±5 %: 3465 Ω worst 0.885, nominal 0.903; current 1.11 A or less (CALCULATION) | About 4596 V at 3300 Ω, chart reading T-090; margin about 1.26 (CALCULATION) | B min 4.4 mm SOURCE | Fails only sensitivity at +5 % (0.885 vs 0.90); best engineering option |
| 2 | TE CRGP2512F3K3, LCSC C2082816 | 130, min 1, 10+ $0.3359, $4.03 | 3k3 ±1 %: 3333 Ω worst 0.904 PASS | No 1.2/50 data. Only 50 rectangular impulses, about 2000 W up to 10 µs (chart reading), sqrt(P·R) = 2.57 kV CALCULATION, not a rating; max overload 1000 V SOURCE | 4.55 mm CALCULATION | FAIL, pulse unproven |
| 3 | Vishay CRCW25123K00FKEGHP, LCSC C1710378 (stock 0), Mouser 2,397, EUR 6.96 | LCSC cannot supply now | 3k0 ±1 % PASS | Chart Umax 1750 V for t up to about 1 ms, different pulse form, margin 0.49 | 4.5 mm CALCULATION | FAIL, pulse |
| - | LCSC C2082813 CRGP 2k7 | stock 5 | 2673 Ω: 1.332 A vs 1.33 A | as rank 2 | | FAIL |
| - | LCSC C1702735, C2075738, C1722297, C876889 | stock 0 | | no 1.2/50 chart | | FAIL, not available |
| - | LCSC C2934109 FRC2512J302 TS, 20+ $0.0182 | 20,240 | 3k0 ±5 % | no pulse data | | FAIL, unproven |
| - | HPWC2512 at LCSC | "0 results" | | | | not sold |
| - | HPWC2512-3K0JT1 Mouser | non-stocked, MOQ 3000 | | | | not purchasable in small quantity |

3k3 needs a tolerance of ±3 % or better for worst 0.90: 3366 Ω 0.901, 3399 Ω 0.901, 3465 Ω 0.885 (SIMULATION, sim_electrode.out). sim_electrode's own printed rule is 0.90 nominal and 0.80 worst, which 3465 Ω meets; the task criterion is stricter.

## LCSC BOM, one board (SOURCE, 2026-11-09, pages opened; USD, ex shipping)

| Line | LCSC | MPN | Stock | Min / mult | Unit | Line total | State |
|---|---|---|---|---|---|---|---|
| R13-R14 | C2907387 | FOJAN FRC1206F4701TS | 502,700 | 100 / 100 | 0.0040 | 0.40 | Implemented |
| R15-R16 | C2933642 | FOJAN FRC1206F2200TS | 61,400 | 100 / 100 | 0.0046 | 0.46 | Implemented |
| C1 | C24497 | Samsung CL31B104KBCNNNC | 448,600 | 20 / 20 | 0.0143 | 0.29 | Implemented |
| SW1 | C2733655 | Omron B3S-1000 | 2,705 | 5 / 5 | 0.365 | 1.83 | Implemented |
| RV1 | C361173 | Alps RK09D1130C2P | 12,164 | 1 / 1 | 0.7417 | 0.74 | Implemented |
| A2 header | C7501270 | ZX-PZ2.54-1-16PZZ | 282,515 | 5 / 5 | 0.0774 | 0.39 | Not in BOM; optional, module ships with header |
| Knob | none | | | | | | Not in stock at LCSC |
| R1-R12 | see above | | | | | | Not implemented |
| A1 Pico | SC0915 "No results" | | | | | | User decision |
| A2 module | C17523394 Adafruit 1982 | | 0 | Pre/New | 21.6846 | | Not available now |

One-board total at LCSC, excluding R1-R12, A1, A2 and shipping: 0.40 + 0.46 + 0.29 + 1.83 + 0.74 + 0.39 = $4.11 CALCULATION ($3.72 without the optional header; $8.14 with CRGP2512F3K3, which is not a passing part). Shipping to Portugal: NOT CONFIRMED (not readable without a cart).

RV1: C470295 RK09K1130AP5 was tried first and replaced, because the Alps page lists its shaft as "Driver". RK09D1130C2P: insulated shaft series, shaft type Flat, LM1 25 mm, 10 kΩ, taper 1B, 0.05 W, 20 V DC (SOURCE, Alps product page). Dissipation 3.3^2 / 10k = 1.09 mW (CALCULATION).

Cheaper switch C25168849 ($0.58) not used: lead span 6.7 mm needs a different land.

Pico alternatives, none confirmed as drop-in, footprint not changed: C41407547 Pico 2 $9.3787, stock 356; C7203003 Pico W $12.8614, stock 270; C20110268 SC0919 $9.4018, stock 7, variant not confirmed. A Pico 2 or Pico W has firmware impact. No generic MPR121 breakout at LCSC; bare C91322 rejected in ADR-023.

## R-017 re-route

| | SDA gap to E pads | C(SDA to pad) | SDA step on pin node | SCL gap | C(SCL to pad) |
|---|---|---|---|---|---|
| Before (T-092) | 0.65 mm | 71.07 fF | 13.03 mV = 4.06 counts | 3.15 mm | 19.74 fF |
| After | 3.30 mm | 33.04 fF | 6.06 mV = 1.89 counts | 5.30 mm | 13.80 fF |

Gaps after: MEASUREMENT on the generated board. Before: layout values. Capacitances and steps: CALCULATION, method of moments, 0.4 mm mesh (0.6 to 0.4 mm within about 2 %). Ratio 0.465, a factor of 2.15 lower. Firmware touch threshold 12 counts (from sim_electrode.py).

SDA is about 1.8 mm diagonally from the pin 1 GND pad of A2, which is not an electrode (layout value).

## Assumptions
eps_eff 2.75; 18 mm window, 5 pads, module and header pins not modelled; pin node 18 pF with the external electrode ignored; SDA full swing 3.3 V; pin current limit 1.33 A inferred; IEC 61000-4-2 source 150 pF / 330 Ω (standard not opened); chart readings about ±5 %.

## Not opened / not confirmed
TME (bot-verification page, left), DigiKey (browser refused), Farnell (timeout, redirect), RS (not attempted). Manufacturer datasheets for FOJAN FRC1206, Samsung CL31 and the header: not opened, LCSC listing only. Alps PDF catalogue: not opened, Alps product web page only. Knob and shipping: not confirmed.

## Errors
A stray "pcgate --help" call from my earlier compound command (ba2lmi0cc) stayed open with empty output; I stopped it. No job was killed by pcgate. The numpy absence forced a pure-Python solver.

## Open decisions for manager / user
1. R1-R12: (a) HPWC2512-3K3JT1 from Mouser, EUR 15.00, pulse proven, 0.885 vs 0.90 at the +5 % corner, requires accepting that limit and a second shop; (b) CRGP2512F3K3 from LCSC, $4.03, all in one shop, 1.2/50 µs pulse capability unproven; (c) keep HPWC2512-3K0JT18, which cannot be bought in small quantity. Any resistor value change needs interface and requirement updates.
2. Pico: LCSC does not list SC0915. Buy elsewhere, or accept a Pico 2 / Pico W after footprint and firmware confirmation.
3. MPR121 module: Adafruit 1982 has zero stock at LCSC. Buy elsewhere.
4. Knob: none at LCSC.
5. RV1 Alps cautions, read on the sibling RK09K page and stated as common to the series: all metal lugs to be soldered into a substrate before use (the design wires RV1 off-board), and output-side impedance more than 100 times total resistance, 1 MΩ for 10 kΩ (ADC input not checked against this in T-094).

## Next actions
Manager decides item 1; systems engineer re-runs sim/systems against the new layout (NOT RUN here); REQ-038 I2C noise comparison stays a physical test. Nothing committed.
