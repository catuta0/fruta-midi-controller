# T-096 — electronics-engineer

Status: PASS for the design checks (ERC, DRC with schematic parity, run_all.sh, land fit, 4 kV gap rule, sensitivity at ±1 %). The pulse capability of R1-R12 is NOT PROVEN (ADR-026 accepted). 8 kV stays FAIL. None of this is hardware validation.

Scope as amended by the coordinator: R1-R12 = YAGEO RC2512FK-073K3L (ADR-026, supersedes ADR-025 and the HPWC/CMB/MELF work). No MELF change was ever written. The HPWC multimeter-selection work (ADR-025) was removed before the final build.

## Requirements addressed
- BOM all at Mouser: the LCSC field is replaced by a Mouser field in the schematic generator and the BOM export.
- R1-R12 land check against the YAGEO datasheet. The land is unchanged (G 5.0 mm, pad 1.9 x 3.35 mm).
- Sensitivity at ±1 %: no selection needed.
- Pulse capability reported as NOT PROVEN, with an energy comparison.
- RV1 PTV09A re-check, knob, optional silicone paragraph, README parts list.

## Inputs (path @ revision)
- Branch change/CR-003 @ 04edcc9, working tree dirty (uncommitted T-096 changes below).
- YAGEO RC_L datasheet V.11 (sha256 6b39ec0f684d3204922ac8587f7a3cc6b9751bb693659a24d5253fbda9c3a197), `reports/electronics/evidence/T-096/datasheets/yageo_rc_group51.pdf`, text in `.../T-096/text/`. The yageo.com links returned 404, so this is the copy hosted by rcscomponents.kiev.ua.
- Bourns PTV09 datasheet (sha256 411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558), `.../T-096/datasheets/bourns_ptv09.pdf`.
- Mouser Portugal product pages, read 2026-11-11.

## Outputs
- Generators:
  - `hardware/scripts/gen_schematic.py`: Mouser fields, R1-R12 YAGEO 3k3, RV1 Bourns, YAGEO 1206 parts.
  - `hardware/scripts/gen_pcb.py`: F.Fab text, 2512 body outline 6.35 x 3.1 mm, footprint description. The footprint name `R_2512_HPWC_G5.0mm` is kept because it is in INTERFACES.json and sim/systems.
  - `hardware/scripts/build_all.sh`: BOM column changed from LCSC to Mouser.
- Generated files: `hardware/frutamidi.kicad_sch`, `.kicad_pcb`, `hardware/fabrication/*` (rebuilt), `hardware/build/erc.rpt`, `drc.rpt`.
- Calculations:
  - `sim/electronics/calc/sim_electrode.py`: ±1 % verdict lines.
  - `calc_pulse_rated.py`: RC2512 NOT PROVEN section.
  - `calc_flashover.py`: R 3333 Ω, termination gap from the datasheet.
  - `check_gap.py`, `check_smd.py`: RC2512 L, W, I1, I2.
  - `calc_esd_variants.py`, `calc_power.py`, `calc_gnd_bounce.py`: 3k3.
  - `calc_pot_rc.py`: ADC loading and residual resistance.
  - `calc_r011_offboard_pot.py`: header updated.
  - All `.out` files regenerated.
- Docs: `hardware/README.md` (Mouser parts list, cost line, knob, RV1 wiring note, optional silicone, safety text) and `reports/electronics/SOURCES_EE.md` (T96 sources).
- Evidence in `reports/electronics/evidence/T-096/`: `build_all.log`, `run_all.log`, `compare_copper.py/.out`, `p1.png` (transfer PDF render), `text/`, `datasheets/`.

## Checks performed (command · version · result line)
- `"$HOME/bin/pcgate" chat2 sh -c 'sh hardware/scripts/build_all.sh ...'` · KiCad 10.0.4 · build_all.log "OK: ERC and DRC without violations"; "build exit 0".
- ERC: `hardware/build/erc.rpt` "** ERC messages: 0  Errors 0  Warnings 0".
- DRC with `--schematic-parity`: `hardware/build/drc.rpt` "** Found 0 DRC violations **", "** Found 0 unconnected pads **", "** Found 0 Footprint errors **".
- `sh sim/electronics/calc/run_all.sh` (pcgate) · run_all.log "run_all exit 0".
- check_smd.out "SUMMARY: 43 checks, 43 PASS, 0 FAIL", including "PASS  RC2512 termination lands on the pad at all L, A (CALCULATION) :: termination inner edge 2.33..2.93, outer edge 3.12..3.23; pad 2.50..4.40 mm".
- check_gap.out:
  - "PASS (d) terminations worst 4.65 mm vs rule 3.5 mm (4 kV); FAIL vs 7.5 mm (8 kV) [placement error +-0.00 mm]"
  - "... worst 4.08 mm ... [placement error +-0.50 mm]"
  - "SUMMARY: copper PASS (4 kV rule, (a) and (b)); terminations PASS at 4 kV ...; mounting metal PASS; spark gap PASS"
  - "SUMMARY 8 kV: copper FAIL; terminations FAIL (worst 4.08 mm vs 7.5 mm)"
- sim_electrode.out: "PASS -1 % corner 3267 ohm: worst 0.904 vs 0.90", "PASS nominal 3300 ohm: worst 0.904", "PASS +1 % corner 3333 ohm: worst 0.904".
- calc_pulse_rated.out: "RC2512FK-073K3L pulse capability at IEC 4 kV: NOT PROVEN (...) 8 kV: NOT PROVEN."
- BOM `hardware/fabrication/bom-kicad.csv`: "R1-R12","3k3","FrutaMIDI:R_2512_HPWC_G5.0mm","YAGEO","RC2512FK-073K3L","603-RC2512FK-073K3L","12".
- Holes: `hardware/fabrication/gerbers/frutamidi.drl` has 4 hits, tool "T1C3.200".
- Copper unchanged against HEAD: compare_copper.out "PASS copper operations identical" (657 operations).
- Render inspection:
  - board-top.png: 12 resistors in one row, no track under the bodies, J2 row with the GND edge track, 4 holes.
  - Transfer PDF page 1 (p1.png): mirrored copper, outline and 4 hole marks.
- sim/systems checks: NOT RUN (owned by systems). They reference the footprint name and the old MPN.

## Numerical findings
- RC2512 dimensions (SOURCE YAGEO RC_L V.11 Table 1): L 6.35 ±0.10, W 3.10 ±0.15, H 0.55 ±0.10, I1 0.60 ±0.20, I2 0.50 ±0.20 mm.
- RC2512 1 W ratings (SOURCE, Table 2): max working 200 V, max overload 500 V, dielectric withstanding 500 V. No pulse, surge or ESD figure.
- Land: copper gap 5.00 mm (MEASUREMENT, check_smd). Conductor gap between terminations L min - 2·I1 max = 4.65 mm (CALCULATION). It is 4.08 mm with ±0.5 mm hand placement (CALCULATION, ASSUMPTION placement). Against the rule (CALCULATION): ≥ 3.5 mm at 4 kV PASS; 7.5 mm at 8 kV FAIL.
- Bottom-termination inner edge 2.33 mm from the land centre against the pad edge at 2.50 mm (CALCULATION): the termination may overhang into the gap by up to 0.17 mm. The governing gap is the 4.65 mm termination figure above.
- V across R at IEC 4 kV (CALCULATION): 3633 / 3636 / 3640 V at 3267 / 3300 / 3333 Ω. That is 7.3x the 500 V overload. At 8 kV it is 7273 V.
- Pin current at 4 kV (CALCULATION): 1.10 A at 3300 Ω, 1.11 A at 3267 Ω, against the 1.33 A ASSUMPTION limit (margin 1.20-1.22). At 8 kV: 2.20 A, FAIL.
- Pulse context (CALCULATION, assumptions in calc_pulse_rated.py):
  - Energy into R: 1.09 mJ at 4 kV, 4.36 mJ at 8 kV. τ 0.544 µs. Peak power 4007 W (4 kV) and 16028 W (8 kV).
  - The old 1.2/50 µs criterion energy was 182 mJ (MBE0414 curve) and 231 mJ (HPWC 4596 V), 167x and 212x one 4 kV strike.
  - Adiabatic film rise 3.1 K (4 kV) and 12.6 K (8 kV). With an ASSUMED x10 trim hot spot: 31 K and 126 K. Whole-body rise 0.034 K.
  - Mean film field 0.71 kV/mm. The field at the trim kerf is unknown.
- Sensitivity worst ratio at 3267 / 3300 / 3333 Ω: 0.904 (SIMULATION), limit 0.90 unchanged.
- RV1 PTV09A-4015F-B103 (SOURCE Bourns PTV09, Mouser): 10 kΩ ±20 %, linear (taper code B), residual resistance "500 ohms or ±1 % max.", 0.05 W, 20 VDC, insulated flatted shaft 6 mm x 15 mm, horizontal bushingless, 10,000 cycles. No numeric linearity tolerance is published.
  - ADC loading against RIN_ADC 100 kΩ: ≤ 1.46 % FS = 14.9 counts, against zone 205 and hysteresis ~41 counts, PASS (CALCULATION).
  - End residual 6.25 % of travel: zone position 0.31 / 4.69, outer octaves reached, PASS (CALCULATION).
  - Dissipation 1.6 mW worst against 50 mW (CALCULATION).
- Mouser one-board total, 2026-11-11 (CALCULATION from SOURCE prices): 13.84 EUR, excl. shipping and tax.
  - 358-SC0915 3.44, 485-1982 6.84, 603-RC1206FR-074K7L 2 x 0.086, 603-RC1206FR-07220RL 2 x 0.086, 187-CL31B104KBCNNNC 0.12, 653-B3S-1000 0.697, 652-PTV09A-4015FB103 0.765, 179-SPK-016A 0.327, 603-RC2512FK-073K3L 12 x 0.109.
- Stock 2026-11-11 (SOURCE): RC2512FK-073K3L 13, with 68,000 on order expected 18 May 2027. 1982: 168. PTV09A: 752. SC0915: 9,200.

## Assumptions
- Thick-film geometry, heat capacities, alumina diffusivity and the x10 trim factor (calc_pulse_rated.py).
- Placement error ±0.25 / ±0.5 mm.
- I_LIM 1.33 A for an IEC-shaped pulse.
- The Bourns terminal 1 is the CCW end, inferred from the taper chart. The README says to swap the outer wires if the direction is wrong.

## Errors
- The first run_all after the format-string fix was superseded by ADR-026. All outputs quoted above come from the final build of 2026-11-11.
- Mouser showed a device-verification page once. It cleared by itself after a wait; nothing was bypassed.

## Open decisions for manager
1. R1-R12 stock is 13 for 12 needed: one spare. No alternative is required (stock ≥ 12), but the stock is tight.
2. The footprint name `R_2512_HPWC_G5.0mm` now carries a YAGEO part. Renaming it is an interface change (INTERFACES.json, sim/systems).
3. sim/systems checks need the systems owner to update to RC2512FK-073K3L / 603- numbers.
4. Knob 179-SPK-016A: its bore against the flatted shaft is NOT CONFIRMED.
5. Silicone: no product was confirmed. 910-EGS10C-20G was seen earlier, but its cure type is NOT CONFIRMED, so the README names no product.

## Next actions
- Manager: commit when accepted.
- An ESD-gun test (4 kV contact) is the only way to move the resistor and the spark gap from NOT PROVEN.
