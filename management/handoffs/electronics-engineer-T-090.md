# T-090 — electronics-engineer

Status: PARTIAL (feasibility and part selection done against datasheets; no layout run, nothing measured on hardware)

Requirements addressed: REQ-023 (re-derivation of the electrode path, analysis only), REQ-025, REQ-027 (needs rewrite by systems), REQ-028, REQ-029, REQ-031 (unchanged pin map). CR-003 items 1-6.

Inputs (path @ revision): `changes/CR-003.md`, `hardware/fabrication/bom-kicad.csv`, `hardware/scripts/gen_pcb.py`, `reports/electronics/analysis.md`, `sim/electronics/calc/calc_flashover.py`, `calc_pulse_rated.py`, `check_gap.out` @ 8e5f595-dirty (dirty files are `.claude/` and `CLAUDE.md` only). Datasheets: section 9 of the report.

Outputs: `reports/electronics/smd_feasibility.md`; `sim/electronics/calc/calc_smd_feasibility.py` and `.out`; `reports/electronics/evidence/T-090/` (datasheets, chartread.py, pdfpages.swift, charts/chartread_raw.txt).

Checks performed (command · version · result line):
- `python3 sim/electronics/calc/calc_smd_feasibility.py` · system Python 3 · `A HPWC2512 3k0 5 %  3000  1  4472  3604  1.24  0.62  4.40  3.29  1.34  7.38  0.60`
- `chartread.py` on rendered datasheet charts · `y_px 158 count 5 V 4472` at R = 3000 (top curve, 2512; charts/chartread_raw.txt)
- Render helper compiled once: `pcgate chat2 swiftc -O` (swift, macOS PDFKit); also one render run through pcgate.
- ERC/DRC NOT RUN: no hardware change in this task.

Numerical findings (value unit LABEL):
- HPWC2512 3k0 5 %: 1.2/50 µs rating 4472 V SOURCE (chart, ±5 % reading ASSUMPTION); conductor gap 4.4 mm SOURCE (B min); margins 1.24 (rating) and 1.34 (gap) at 4 kV CALCULATION; 0.62 and 0.60 at 8 kV CALCULATION.
- V1.2: 4083 V, margin 1.12; worst cap gap 3.61 mm (assumed cap), margin 1.08.
- 2 × HPWC2512 1k6: margins 1.96 / 3.10 at 4 kV, 0.98 / 1.33 at 8 kV CALCULATION.
- MMB 0207 3k3: 1736 V SOURCE, margin 0.48 at 4 kV (FAIL). CMB 0207 3k3: 5175 V SOURCE, margin 1.42; L1 min 3.2 mm SOURCE, gap margin 0.96 at 4 kV (FAIL against the rule).
- Pico land 1.6 × 3.2 mm SOURCE; proposed 1.6 × 4.2 mm; gap 0.94 mm PASS vs 0.6 mm CALCULATION. Keep-out x 9.52-17.27, y 0.48-14.98 mm CALCULATION (V1.2 coordinates). USB shell 0.67 mm past board edge CALCULATION.
- MPR121 QFN pitch 0.40 mm, terminal 0.20 mm SOURCE: FAIL vs 0.6 mm.
- Holes 133 to 4 (M3): CALCULATION; or 9 with THT pot.
- Pry peel margins: Pico 10 N 1.7-2.2, 30 N 0.57-0.75; module 5 N 2.5-3.2 CALCULATION on ASSUMPTION inputs.

Assumptions: peel strength 0.8-1.05 N/mm (not opened); IEC 60664-1 F.2 recalled; series sharing is quasi-static (first ns unquantified); header strip stand-off about 2.5 mm; STEMMA QT bottom side same as original.

Errors: KEMET site TLS certificate expired (C1 datasheet not opened); WAGO, Yageo and PWC datasheets not opened; first Mouser HPWC URL timed out and another copy was used. `management/metrics.json` and `SOURCES_EE.md` not edited (outside task scope, lists are in the report). Handoff path follows the task, not the agent default folder.

Open decisions for manager:
1. R1-R12 topology: one 3k0 5 % HPWC2512 (recommended) or two 1k6 in series (24 parts, near 8 kV). User's call.
2. RV1: off-board pot (recommended, 0 holes, R-011 re-derivation needed) or keep 5 THT holes. Depends on whether an enclosure exists.
3. J2: solder-wire pads (recommended) against WAGO push-in terminals.
4. Mounting holes: keep 4 M3 (recommended) or 0.
5. Interface: J1/JP1 change to surface pads and Pico pin map unchanged; firmware not affected.

Next actions: on approval, systems rewrites REQ-027 and SMD pad rules; electronics implements the generators (new footprints, F.Cu, mirror), re-runs check_gap for the new R positions, ERC/DRC with parity; order and solder-trial notes are for the user.
