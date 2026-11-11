# T-098 — electronics-engineer

Status: PASS. This is a rename only; the geometry is unchanged. ERC/DRC passing is not hardware validation.

## Requirements addressed
The R1-R12 footprint is renamed from `R_2512_HPWC_G5.0mm` to the part-neutral `R_2512_HomeEtch_G5.0mm`.

## Inputs
change/CR-003 @ 1f858f0.

## Outputs
- `hardware/scripts/gen_pcb.py`: name and comment.
- `hardware/scripts/gen_schematic.py`: footprint id.
- `hardware/FrutaMIDI.pretty/R_2512_HomeEtch_G5.0mm.kicad_mod` added. The old `R_2512_HPWC_G5.0mm.kicad_mod` is removed (git rm, staged; not committed).
- Regenerated `hardware/frutamidi.kicad_sch`, `.kicad_pcb`, `hardware/fabrication/*`, `sim/electronics/calc/*.out`.
- Evidence in `reports/electronics/evidence/T-098/`:
  - `build_all.log`, `run_all.log`
  - `compare_r_pads.py` / `.out`, `compare_copper.out`
  - `frutamidi_HEAD.kicad_pcb` (reference copy of the board at 1f858f0)
- No sim/electronics script, README or reports/electronics file named the footprint (grep found none), so none was edited.
- sim/systems/ and management/INTERFACES.json are untouched (T-099). Their checks will fail on the name until then: NOT RUN.

## Checks performed
- **KiCad app:** before writing, `lsof -p 676` showed 0 open files under /Users/rod/fruta-midi-controller, and there were no KiCad lock files in hardware/. The same check after the build also showed 0. The KiCad app (PID 676) was not touched.
- **Build:** `"$HOME/bin/pcgate" chat2 sh -c 'sh hardware/scripts/build_all.sh ...'` · KiCad 10.0.4 · "OK: ERC and DRC without violations"; "build exit 0".
- **ERC:** erc.rpt "ERC messages: 0  Errors 0  Warnings 0".
- **DRC with schematic parity:** drc.rpt "Found 0 DRC violations", "Found 0 unconnected pads", "Found 0 Footprint errors".
- **Calculations:** run_all.sh "run_all exit 0"; check_smd "SUMMARY: 43 checks, 43 PASS, 0 FAIL"; check_gap 4 kV SUMMARY PASS (8 kV FAIL, as before); sim_electrode ±1 % corners PASS at 0.904.
- **Holes:** 4 hits in frutamidi.drl, tool T1C3.200.
- **BOM:** "R1-R12","3k3","FrutaMIDI:R_2512_HomeEtch_G5.0mm","YAGEO","RC2512FK-073K3L","603-RC2512FK-073K3L","12".
- **Copper:** compare_copper.out "PASS copper operations identical" (657 against HEAD).
- **R1-R12 pads:** compare_r_pads.out "PASS R1-R12 pad geometry and nets identical (24 pads)", e.g. "R1 pad 1: x 83.350 y 99.000 size 1.900 x 3.350 net /ELE0".
- **Footprint file:** the diff against the old file, ignoring uuid, is only line 1 (the footprint name). The other .kicad_mod files changed only in their uuid lines.

## Numerical findings
Land unchanged: pads 1.900 x 3.350 mm at 6.900 mm pitch (gap 5.0 mm), MEASUREMENT from the board file.

## Assumptions
None new.

## Errors
None. KiCad Python prints wx debug lines at the top of compare_r_pads.out; they are harmless.

## Open decisions for manager
T-099 (systems): update INTERFACES.json and sim/systems to `R_2512_HomeEtch_G5.0mm`.

## Next actions
Commit when accepted.
