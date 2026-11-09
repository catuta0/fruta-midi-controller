# T-092 — electronics-engineer

Status: PASS for the five T-092 items at design-file level. Nothing is built, soldered or tested; ERC/DRC passing is not hardware validation. Requirement status unchanged: REQ-023 PARTIAL (8 kV FAIL, R-006 open).

Requirements addressed: ADR-023 D-4 (holes), REQ-023 (re-derived for 3k0), REQ-029, REQ-031 (pin map unchanged), R-011 input (pot RC), CR-003 items for hardware.

Inputs (path @ revision): hardware/scripts/gen_pcb.py, gen_schematic.py, sim/electronics/calc/* @ f3a718a-dirty (dirty before this task: .claude/, CLAUDE.md; sim/systems changes during the task are the systems engineer's, T-093). management/handoffs/electronics-engineer-T-091.md; DECISIONS.md ADR-023; T-090 evidence.

Outputs (uncommitted):
- hardware/scripts/gen_pcb.py; regenerated hardware/frutamidi.kicad_pcb (sha256 3071ad1d...b671), frutamidi.kicad_sch (8a9fbe55...0079, only the random UUIDs differ between runs), FrutaMIDI.pretty/, fabrication/; hardware/README.md (mounting note)
- sim/electronics/calc: calc_flashover, calc_pulse_rated, calc_esd_variants, sim_electrode, calc_pot_rc, calc_power, calc_gnd_bounce, check_smd (holes, designators), calc_usb_pry (new), run_all.sh; retired/ (check_silk, calc_pulse, README)
- reports/electronics/analysis.md (section 7, scope note), SOURCES_EE.md (T-090 sources, not-opened list)
- reports/electronics/evidence/T-092/ (erc.rpt, drc.rpt, build_all.log, run_all.log, frutamidi.drl, bom-kicad.csv, *.out, assembly_map_render.png, transfer_pdf_render.png, board_top_render.png)

Checks performed (KiCad 10.0.4, kicad-cli, all through pcgate chat2, exit 0; no 75 or 143 observed):
- `sh hardware/scripts/build_all.sh`, build_all.log `OK: ERC and DRC without violations`, `EXIT=0`
- ERC, erc.rpt: ` ** ERC messages: 0  Errors 0  Warnings 0`
- DRC with parity, `--severity-all`, drc.rpt: `** Found 0 DRC violations **`, `** Found 0 unconnected pads **`, `** Found 0 Footprint errors **`. No rule or exclusion change.
- Holes, frutamidi.drl: one tool `T1C3.200`, 4 hits: X5.0Y-65.0, X29.8Y-4.0, X96.0Y-4.0, X96.5Y-58.0. MEASUREMENT.
- `sh sim/electronics/calc/run_all.sh`, run_all.log `EXIT=0`, outputs opened.
- check_smd.out: `SUMMARY: 43 checks, 43 PASS, 0 FAIL`
- check_gap.out: `SUMMARY: copper PASS (4 kV rule, (a) and (b)); terminations PASS at 4 kV over the swept ASSUMPTIONS; mounting metal PASS; spark gap PASS`; `SUMMARY 8 kV: copper FAIL; terminations FAIL (worst 3.79 mm vs 7.5 mm)`
- Assembly map and mirrored copper PDFs rendered and inspected (MEASUREMENT by eye): FrutaMIDI v1.3 reads reversed, 4 drill marks.
- NOT RUN: sim/systems checks (systems is changing them in T-093).

Numerical findings:
Holes, mm from top-left corner (MEASUREMENT); washer r 3.5 / pan head r 2.8 ASSUMPTION (ISO not opened):
- H1 (5.0, 65.0): drill to edge 3.40; washer to copper 10.44; head 11.14
- H2 (96.0, 4.0): 2.40; 2.86 (R14 pad 1, 3V3); 3.56
- H3 (96.5, 58.0): 1.90; 1.08 (J2 pad 14, GND); 1.78; washer to J2 courtyard 0.17
- H4 (29.8, 4.0): 2.40; 0.60 (3V3 riser, Pico lands 0.62); 1.30; washer to A1 courtyard 0.30
Spread (criteria chosen in T-092): one hole per quadrant PASS; min pair 54.20 mm vs >= 45 (T-091 10.6) PASS; quadrilateral 4491 mm2 = 64.2 % vs >= 60 % PASS; nearest hole to centre of Pico USB end 16.75 mm vs <= 20 (T-091 63.6) PASS. MEASUREMENT.
USB end: H4 is the closest achievable. Left of or above the module is impossible (lands to x 25.68, module end y 0.63). Routing changed: 3V3 riser x 27.2 to x 34.5, via RV1 pad 1. No other route changed.
USB pull (calc_usb_pry.out, CALCULATION, plate model, E 22 GPa, nu 0.15, t 1.6 mm ASSUMPTION, Pico not modelled): deflection at USB end 0.319 to 0.0266 mm/N, factor 12.0; at 30 N about 9.6 to 0.80 mm; largest screw force 108 to 35.3 N (H4, 1.18x applied). p 12 to 14 within 1 %; 10x screw stiffness changes current w by 5 %. Use the ratio, not the absolute values.
Castellation peel margin 0.57-0.75 at 30 N (T-090) does NOT change: rigid-carrier model, independent of holes. Extra peel from carrier curvature: NOT QUANTIFIED.
Mounting-metal bypass, worst 8.26 mm CALCULATION (H3, r 3.5): PASS 4 kV (3.5) and 8 kV (7.5); was 17.71 mm in T-091, 15.36 mm in V1.2.

Changed against V1.2 (all CALCULATION, SIMULATION where stated):
- V across R 3636 / 7273 V to 3604 / 7207 V (3621 / 7241 V at 3150 ohm). Rule 3.5 / 7.5 mm unchanged.
- Pin current 4 / 8 kV 1.10 / 2.20 A to 1.20 / 2.40 A (1.26 / 2.52 A at 2850 ohm); margin against the ASSUMED 1.33 A limit at 4 kV 1.21 to 1.11, 1.06 worst.
- Pulse rating margin 4 kV 1.12 to 1.24 (min 1.21 over tolerance; 1.15 with -5 % chart reading); 8 kV 0.56 to 0.62, FAIL.
- Sensitivity min (SIMULATION, nominal/worst): 0.904/0.904 to 3k0 0.925/0.904, 2850 ohm 0.926/0.905, 3150 ohm 0.905/0.904. PASS against 0.90/0.80. Rejected 3465 ohm: 0.903 / 0.885 (T-090 interpolated 0.899).
- Copper (a) 13.04 to 5.00 mm, (b) 10.92 to 5.29 mm MEASUREMENT: PASS 4 kV, FAIL 8 kV (V1.2 copper passed 8 kV). Terminations 3.13 (caps, +-0.5) to 3.79 mm: PASS 4 kV.
- GND bounce worst 339 V (V1.2) / 318 V (T-091) to 236 V / ~1 ns on ASSUMPTION 3.4-6.4 nH without sockets; I2C line <= 1.06 A, 0.64 nC.
- calc_pot_rc: 2.89 ms vs 30 ms, 10.4x, numbers unchanged; inputs now ASSUMPTION (C1 1206 datasheet not opened, pot not chosen).

Assumptions: hardware radii (ISO recalled); board thickness 1.6 mm; hole-spread thresholds (chosen in T-092); FR-4 modulus; inductances in calc_gnd_bounce; earlier ones unchanged (T-090, T-091).

Errors and corrections:
- First check_smd after the move: 1 FAIL, H3 washer -0.00 mm from the J2 courtyard at y 58.2. Fixed by moving H3 to y 58.0; no criterion changed.
- First run_all stopped with EXIT=1 on that FAIL; re-run EXIT=0 after the fix.
- One smoke test wrote to /tmp/x (removed). One stray `pcgate` call with no arguments (printed usage, ran nothing).

Open decisions for manager:
1. management/INTERFACES.json placement record (H1-H4) and management/metrics.json need the new values; outside my paths. Systems is holding the INTERFACES lock.
2. Bolting the Pico through its own two USB-end 2.1 mm holes (T-090) is the mounting option that would act on the joints directly. It adds 2 holes against ADR-023 D-4. Not done.
3. Criteria in check_smd section 7 are my choices; accept or set others.

Next actions: systems re-runs its checks on this board; independent review; user trial etch and solder; physical ESD plan (REQ-023, R-011) and a USB-pull check.
