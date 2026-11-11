# Handoff: electronics-engineer, T-103 (CR-003 review fixes F3-001..F3-014, electronics part)

## Status
PASS for the design-file checks: ERC 0, DRC 0 with schematic parity 0, run_all.sh exit 0, check_smd 65/65 including the new checks, each new check shown to fail by mutation. PARTIAL against the manager decisions: the Pico is 0.11 mm short of flush (F3-002, reason below), and the etched ORIG label was not moved; the README was corrected instead (F3-006, reason below). None of this is hardware validation. Nothing was built, soldered or measured.

## Requirements and findings addressed
- **F3-001 option (a), done for all 20 pins.** A2 lands are lengthened outward, with the inner edges unchanged:
  - electrode row 1.8 x 4.2 mm, 1.73 mm beyond the module outline;
  - S row 1.8 x 5.515 mm, 1.775 mm beyond the outline, overlapping its own J3 wire pad (same net).
  - E_STUB_Y moved from 27.9 to 30.0 mm, so the fan-out starts below the lands.
  - Spark gap 1.401 mm, SDA 3.300 mm, SCL 5.300 mm, Pico keep-outs and the 4 holes are all unchanged.
  - Module underside about 5.5 mm above the copper (3.0 mm pin ASSUMPTION + 2.5 mm strip ASSUMPTION). Module board top about 7.1 mm (1.6 mm board ASSUMPTION). Both are in the README.
  - The 3D header models are raised 3.0 mm.
  - No pin needed a different method.
- **F3-002.** PICO moved from (4.5, 2.0) to (4.5, 1.48).
  - The Pico end is at y 0.11 mm, i.e. 0.11 mm inside the edge (CALCULATION).
  - The receptacle face is 1.19 mm beyond the edge (CALCULATION from SOURCE 1.30 mm).
  - Why not flush: at y 1.37 the pin 1 and pin 40 lands would be 0.57 mm from the edge, which is 0.495 mm from the etched outline line (0.075 mm half width). That is below the 0.6 mm project clearance, and pin 40 is VBUS.
  - C1, SW1 and the RV1 routing follow the new pin rows.
  - README covers the oversize blank, etching, trimming to the outside of the etched line, and the plug-seat check before soldering.
- **F3-003.** KO_TP7 keep-out added (footprint-local (8.54, 17.78)-(11.24, 20.48)).
  - KO_TP x1 moved from 5.02 to 5.00, to cover Pico 2 shell pad A at its 1.1 mm width.
  - New check: copper is at least 0.6 mm from all 11 Pico 2 features. Worst is 2.14 mm, TP7 is 3.66 mm (MEASUREMENT).
  - README: the PCB supports only the Pico (SC0915) and the Pico 2. Pico W and Pico 2 W are not supported, in the A1 BOM row and in the firmware table.
  - Nothing was downloaded. The local datasheet copy was used, page 10 Fig. 5 rendered in evidence.
- **F3-004.** analysis.md: new section 8 on RC2512FK-073K3L covering ratings, the pulse capability (NOT PROVEN), the energy comparison, gaps and the T-103 changes. Sections 7.1 and 7.2 are marked superseded. The README safety link now points to the section 8 anchor.
- **F3-005.** Charge 600 vs 200 nC (3.0x) and decay time 0.54 vs 0.15 us (3.6x) are stated beside the margin of 1.20-1.22, in the README and in analysis section 8.3.
- **F3-006.** The copper was not moved. Below pad 1 there is 1.69 mm between the pad (y 16.71) and the SCL run (top edge y 18.4). With 0.6 mm clearance on both sides, that leaves 0.49 mm for the text height. Left of pad 1 is the S1 entry track, and right of it are the 3V3 drop and R15. The README now describes the real position: ORIG is etched left of JP1 beside the gap between pads 2 and 1, and means the bottom pad 1, where the S1 track enters.
- **F3-007.** README final checks added:
  - pads 36, 39 and 40 must not beep to GND;
  - the SW1 BTN pad must not beep to pin 30.
- **F3-008.** The "1" mark is level with pin 1 at local (1.8, 0). A 0.9 mm square (F.Fab) is drawn inside pad 1. Checked on the rendered assembly map (render/assembly/zoom_pin1.png).
- **F3-010.**
  - J1 is now excluded from the BOM (gen_schematic in_bom=False, Config_2pads SetExcludedFromBOM). bom-kicad.csv has no J1 line.
  - J1, J2, J3 and JP1 are listed in the README as copper only.
  - The knob stays README-only because it has no symbol; the README says so.
  - SW1: Mouser lists the maker as "Aratas", and the maker page reads "ARATAS, formerly Omron Components", so the part is the genuine B3S-1000 (stock 10,507, 0.697 EUR, 2026-11-11). No replacement is needed.
- **F3-011, F3-012, F3-013.** README now covers: wires leave J2 upward and away from the edge, strip 3-4 mm; check the Pico does not rock before tacking and remove pooled USB-pin solder; "module" changed to "Pico" at the BOOTSEL and common-problems lines.
- **F3-014.** 1206 lands lengthened outward with the inner gap unchanged at 1.75 mm: R 1.775 mm, C 1.875 mm long. Copper beyond the body is at least 1.05 mm. To keep 0.6 mm clearance, R15 moved to y 18.5, R13 and R14 to y 4.9, and C1 0.3 mm up. check_vertical now tests the pad midpoint, column, order and pad containment.
- **ADR-027 D-3.** README alternative: Vishay CRCW25123K30FKEG, Mouser 71-CRCW25123K30FKEG, stock 4,500, 0.424 EUR at 10+ (12 = 5.09 EUR, CALCULATION), read 2026-11-11. Its datasheet was NOT opened, so the body size must be confirmed. The YAGEO RC2512 shows stock 13, with 68,000 due 18 May 2027.
- **New check_smd checks**, each proven by mutation on scratch copies:
  - (A) every hand-soldered land has at least 1.0 mm of copper outside the body or strip outline (A1, A2, SW1, C1, R1-R16);
  - (B) the USB face is at least 1.0 mm beyond the edge (CUT_TOL 1.0 mm = 0.5 transfer + 0.5 trim, ASSUMPTION);
  - (C) Pico 2 features are clear of copper.
  - The keep-out rectangles now follow the A1 position read from the board.

## Inputs
Branch change/CR-003 at fd7140b (working tree). reports/review/CR-003/findings.md and raw/. sim/systems/datasheets/pico-2-datasheet.* (Fig. 5).

## Outputs
- Generators: hardware/scripts/gen_pcb.py, hardware/scripts/gen_schematic.py.
- Regenerated: hardware/frutamidi.kicad_pcb, .kicad_sch, FrutaMIDI.pretty/*, fabrication/*.
- Text: hardware/README.md, reports/electronics/analysis.md, reports/electronics/SOURCES_EE.md.
- Checks: sim/electronics/calc/check_smd.py, calc_gnd_bounce.py, calc_i2c_coupling.py, calc_usb_pry.py and their .out files.
- Evidence in reports/electronics/evidence/T-103/:
  - build_all.log, run_all.log, erc.rpt, drc.rpt, bom-kicad.csv, copies of the .out files, measure_i2c_gap.out;
  - mutation/ (mutate.py, M1-M4 outputs, mutation_summary.out);
  - render/ (board-top.png, board-3d.png, transfer/p1.png, assembly/p1.png, assembly/zoom_pin1.png);
  - pico1/, pico2/ (datasheet page renders).

## Checks performed (kicad-cli 10.0.4, KiCad Python 10.0.4, via pcgate chat2)
- ERC, build/erc.rpt: "ERC messages: 0  Errors 0  Warnings 0".
- DRC, build/drc.rpt: "Found 0 DRC violations", "Found 0 unconnected pads". build_all.log: "Found 0 schematic parity issues".
- build_all.log: "OK: ERC and DRC without violations; files in hardware/fabrication".
- run_all.log: "run_all exit 0".
- check_smd.out: "SUMMARY: 65 checks, 65 PASS, 0 FAIL" (43 before). New rows include:
  - "PASS  T-103 copper >= 0.6 mm from every Pico 2 underside feature (11 features, Fig. 5) :: worst 2.14 mm ... TP7 3.66 mm"
  - "PASS  T-103 USB receptacle face >= 1.0 mm beyond the board edge ... 1.19 mm beyond the edge y 0"
  - land beyond body: A1 1.79, A2 1.73, SW1 1.65, R1 1.17, R13 1.05, C1 1.05 mm
- Mutations, each with one FAIL and all other checks PASS:
  - M1, A2 lands back to 1.8 x 2.4: "FAIL  T-103 A2 every land >= 1.0 mm ... min -1.34 mm (pad 14)".
  - M2, A1 moved 1.0 mm in: "FAIL  T-103 USB receptacle face ... 0.19 mm beyond the edge y 0".
  - M3, track on TP7: "FAIL  T-103 copper >= 0.6 mm from every Pico 2 underside feature ... worst -0.50 mm at TP7 1V1".
  - M4, C1 lands 1.15 mm: "FAIL  T-103 C1 every land ... min 0.32 mm (pad 2)".
- check_gap.out: "PASS (f) spark gap: 12 electrode pads, min 1.401 / max 1.401 mm vs 1.40 +/- 0.05 mm". Terminations 4.65 mm PASS for 4 kV; 8 kV FAIL as before.
- measure_i2c_gap.out: "net /SDA smallest gap to any E0-E11 pad of A2: 3.300 mm"; SCL_PICO 5.300 mm.
- Holes: drill file with 4 hits (check_smd "exactly 4 M3 holes", drill grep count 4).
- Renders inspected:
  - top view: USB beyond the top edge, A2 lands extended, S lands merged with the J3 pads;
  - transfer PDF: mirrored, text reversed, Pico on the right;
  - assembly map: pin-1 mark level, square in pad 1, TP7 box.

## Numerical findings
- Pico pin 1 land top 0.68 mm from the edge; Pico end y 0.11 mm; USB face 1.19 mm beyond (CALCULATION, MEASUREMENT on the design file).
- A2 lands beyond the outline: 1.73 mm (electrode row) and 1.775 mm (S row) (MEASUREMENT on the design file).
- Module height: underside 5.5 mm, board top 7.1 mm (CALCULATION on ASSUMPTIONS 3.0 + 2.5 + 1.6 mm).
- GND bounce worst 330 V for about 1 ns (was 236 V), from the longer module pin path 7.1 mm giving 5.0-8.5 nH (CALCULATION on ASSUMPTIONS).
- SDA-to-pad capacitance 36.6 fF (was 33.0 fF); SDA step 2.09 ADC counts against a 12-count threshold (CALCULATION, calc_i2c_coupling.py; corrected by the manager in T-106).
- USB pry: largest screw force 35.6 N at 30 N; deflection ratio 11.9 (CALCULATION, calc_usb_pry.out with the new load point).

## Assumptions
- Exposed header leg 3.0 mm after cutting, and strip 2.5 mm (standard 2.54 mm header). Not measured on the Adafruit-supplied header.
- Module board 1.6 mm thick.
- C1 body up to 3.4 x 1.8 mm (Samsung datasheet not opened).
- B3S body 6.0 + 0.1 mm.
- Cutting tolerance 1.0 mm.
- Pico 2 shell pads taken as 1.8 mm squares in the clearance check (conservative).

## Errors during the task
- Iteration 1: DRC found 4 violations from the lengthened 1206 lands and the A2 courtyard: C1 against SCL 0.38 mm, R13/R14 against J1 courtyard, A2 against J3 courtyard. Fixed at the root by moving the parts and trimming the J3 courtyard to y 0.5 at the A2 courtyard. No rule was relaxed.
- Iteration 2: 0 violations.
- check_smd float tolerance 1e-6 failed on a 1 nm rounding; set to 1 um.
- calc_gnd_bounce took the A2 land centre as the GND node; it now uses the header pin position.

## Open decisions for the manager
1. F3-002: accept 0.11 mm short of flush, or relax the 0.6 mm clearance to the outline line at the Pico end (not recommended: VBUS at pin 40).
2. F3-006: accept the README correction, or approve a JP1 / R15 / SCL re-layout to place ORIG below pad 1.
3. GND bounce rises to 330 V because of the taller module stand-off (ASSUMPTION inputs). It is a residual risk for the systems budget.
4. Alternative resistor CRCW25123K30FKEG: its datasheet must be opened before it is promoted from the README note.

## Next actions
- Systems: update budgets and requirements for the new A2 lands, module height, Pico position, the 1206 lands and the GND bounce figure.
- Documentation: the manual changes that follow from the README.
- Physical: measure the supplied header strip and pin lengths; do a trial solder of one module row from outside.

Locks: management/locks/{hardware-generators,hardware-readme,electronics-analysis,check-smd}-t103.lock released. Nothing committed.
