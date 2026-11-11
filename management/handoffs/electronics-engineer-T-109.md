# T-109: electronics-engineer

## Status
PASS for the documentation and label fixes F4-001..F4-010 (electronics files). There is no copper change: the copper is identical to f0c016b. None of this is hardware validation.

## Requirements addressed
The T-108 findings F4-001..F4-010, applied under ADR-029 D-1..D-4. All changes are in hardware/README.md unless stated.

- **F4-001.** Step 6 now reads "Epoxy beside the USB end":
  - one bead along each long side, over pins 1-3 and pins 38-40;
  - no epoxy on the USB end face and none beyond the board edge;
  - after curing, check again that the plug seats fully;
  - "module" corrected to "Pico".
  - The Mounting paragraph now says "epoxy beads".
- **F4-002.** Section 6:
  - corrected: only pad 39 is 0.94 mm from GND pad 38; pad 40 is 3.48 mm from it (CALCULATION, design file);
  - new check: pad 37 (3V3_EN) to pad 38 must not beep;
  - new troubleshooting row for a 37-38 or 39-38 bridge.
- **F4-003.**
  - The section 4 step order changed: step 7 is now JP1, before the module; step 8 the module; step 9 the configuration wires; then RV1 and J2.
  - Section 5 step 1 now identifies the pads by position (bottom pad = ORIG, top pad = QT) and says the ORIG label is hidden once the module is fitted.
- **F4-004.** Module step:
  - the 7-pin row stands 2.54 mm inside the module edge, against 1.27 mm for the 13-pin row, so solder and inspect it from a low angle;
  - new continuity check from each S pad to its own module-top pin (beeps) and to the neighbouring pin (no beep).
- **F4-005.** The RV1 BOM row now gives a mounting method for the bushless pot:
  - solder the pot onto a perfboard piece of about 20 x 15 mm;
  - drill a 7 mm panel hole for the shaft;
  - fix the perfboard behind the panel with hot-melt, epoxy or two screws;
  - keep glue off the shaft.
- **F4-006.** Rework now says the Pico is soldered flat and the module stands on its header pins; cut through the epoxy beads first.
- **F4-007.** Geometry read from the design file is now labelled "CALCULATION (design file)" instead of MEASUREMENT in:
  - check_smd.py, check_gap.py, calc_gnd_bounce.py, calc_mechanical.py, calc_flashover.py, calc_smd_feasibility.py, calc_usb_pry.py;
  - evidence/T-094/measure_i2c_gap.py;
  - analysis.md (including 7.3 and 8.4) and smd_feasibility.md.
  - The re-run .out files match. The old-revision raw outputs check_gap_old_*.out are historical and were not re-run.
- **F4-008.** The stale "y 0.63" is now marked as T-092 history, with 0.11 since T-103: the gen_pcb.py comment near line 372 (comment only) and analysis.md line 175.
- **F4-009.** Design-rule table: the 0.8 mm S2-S6 stubs lie entirely inside the S-row pads and S pads, so no 0.8 mm track is exposed.
- **F4-010.** A1 row: the 1.2 mm USB overhang comes from the Pico drawing, not a Pico 2 drawing, so do the plug-seat check with the Pico 2 before soldering it.

## Inputs
- change/CR-003 at f0c016b, working tree dirty.
- reports/review/CR-003/findings-T-108.md.
- management/DECISIONS.md, ADR-029.

## Outputs
- Documents: hardware/README.md, reports/electronics/analysis.md, reports/electronics/smd_feasibility.md.
- Generator: hardware/scripts/gen_pcb.py (comment only).
- Check scripts: sim/electronics/calc/{check_smd,check_gap,calc_gnd_bounce,calc_mechanical,calc_flashover,calc_smd_feasibility,calc_usb_pry}.py and their .out files; reports/electronics/evidence/T-094/measure_i2c_gap.py.
- Regenerated: hardware board, schematic and fabrication files.
- Evidence: reports/electronics/evidence/T-109/ (build_all.log, run_all.log, erc.rpt, drc.rpt, check_smd.out, check_gap.out, compare_copper.out).

## Checks performed
All run through pcgate chat2 with kicad-cli 10.0.4.

| Check | Result line |
|---|---|
| ERC | "ERC messages: 0  Errors 0  Warnings 0" |
| DRC | "Found 0 DRC violations", "Found 0 unconnected pads" |
| Schematic parity (build_all.log) | "Found 0 schematic parity issues", "build exit 0" |
| run_all | "run_all exit 0" |
| check_smd | header "# check_smd.py  CALCULATION (design file) on hardware/frutamidi.kicad_pcb"; "SUMMARY: 65 checks, 65 PASS, 0 FAIL" |
| check_gap | "PASS (f) spark gap: 12 electrode pads, min 1.401 / max 1.401 mm" |
| compare_copper.py f0c016b | "operations at f0c016b: 657; working tree: 657", "PASS copper operations identical" |

## Numerical findings
- Pad 40 to pad 38: 3.48 mm (CALCULATION, design file: 2 x 2.54 - 1.6).
- Pads 39-38 and 37-38: 0.94 mm (CALCULATION, design file).
- S-row pin centres 2.54 mm inside the module outline, electrode row 1.27 mm (CALCULATION, design file).

## Assumptions
- The RV1 mounting method has not been tried.
- Panel hole 7 mm for the 6 mm shaft (ASSUMPTION).

## Errors
None.

## Open decisions for the manager
None new.

## Next actions
- Documentation: carry F4-001, F4-003 and F4-005 into the root README and MANUAL.
- Systems: R-013 wording for the epoxy beads.

## Locks
management/locks/*-t109.lock released. Nothing committed.
