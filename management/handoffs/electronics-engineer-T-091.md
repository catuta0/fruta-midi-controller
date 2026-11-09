# T-091 — electronics-engineer

Status: PARTIAL. The SMD board is designed, routed on one layer and passes ERC, DRC and schematic parity. Nothing is built, soldered or tested. sim/systems checks fail where they encode the V1.2 through-hole rules (expected, owned by systems). Open items below. ERC/DRC passing is not hardware validation.

Requirements addressed: REQ-023 (4 kV flashover geometry, re-derived; 8 kV stays FAIL), REQ-025, REQ-027 (needs rewrite by systems), REQ-028, REQ-029, REQ-030 (J2 pads, wording needs rewrite), REQ-031 (pin map unchanged), REQ-036 (hardware/README.md only), R-011 (analysis). CR-003 items for hardware.

Inputs (path @ revision): changes/CR-003.md, management/DECISIONS.md ADR-023, reports/electronics/smd_feasibility.md, management/handoffs/electronics-engineer-T-090.md @ 8c89555-dirty (dirty before this task: .claude/ and CLAUDE.md only). Datasheets: T-090 evidence folder (TT HPWC 09.23, Omron B3S, Vishay 28950, Pico RP-008307-DS-2).

Outputs (uncommitted):
- hardware/scripts/gen_schematic.py, gen_pcb.py, build_all.sh; generated hardware/frutamidi.kicad_sch, .kicad_pcb, FrutaMIDI.pretty/, FrutaMIDI.kicad_sym, fabrication/
- hardware/README.md
- sim/electronics/calc/check_gap.py (rewritten for SMD), check_smd.py (new), calc_r011_offboard_pot.py (new), calc_gnd_bounce.py (3k0 constant), run_all.sh; .out files
- reports/electronics/evidence/T-091/ (erc.rpt, drc.rpt, build_all.log, frutamidi.drl, bom-kicad.csv, keepout_negative_test.rpt/.log, transfer_pdf_render.png, assembly_map_render.png, systems_*.out, copies of the check outputs)

Checks performed (KiCad 10.0.4, kicad-cli through pcgate chat2, `sh hardware/scripts/build_all.sh`, exit 0):
- ERC, evidence erc.rpt: ` ** ERC messages: 0  Errors 0  Warnings 0`
- DRC with parity, evidence drc.rpt: `** Found 0 DRC violations **`, `** Found 0 unconnected pads **`, `** Found 0 Footprint errors **` (build log `OK: ERC and DRC without violations`). `--severity-all`, no rule or exclusion changes; hardware/frutamidi.kicad_pro not edited.
- Holes, evidence frutamidi.drl: one tool `T1C3.200`, 4 hits: X8.0Y-64.0, X88.5Y-30.5, X95.0Y-5.0, X96.0Y-38.0. check_smd: `PASS  drill file merged holes :: 4 hits`.
- Keep-out negative test: 2 tracks injected into the two Pico rule areas on a scratch copy; DRC reported `[items_not_allowed]` at exactly those two tracks (keepout_negative_test.rpt; the other 31 entries of that run are dangling tracks and library-table warnings of the scratch copy).
- Mirroring: exported 1-copper-for-transfer.pdf rendered with PDFKit and inspected: "FrutaMIDI v1.3" reads reversed, Pico on the right (transfer_pdf_render.png, MEASUREMENT by visual inspection).
- check_smd.py: `SUMMARY: 25 checks, 25 PASS, 0 FAIL` (single layer, 0 vias, 0 copper zones, pad fit, keep-out margins, pin map REQ-031).
- check_gap.py: `SUMMARY: copper PASS (4 kV rule, (a) and (b)); terminations PASS at 4 kV over the swept ASSUMPTIONS; mounting metal PASS; spark gap PASS`; `SUMMARY 8 kV: copper FAIL; terminations FAIL (worst 3.79 mm vs 7.5 mm)`.
- sim/systems read-only: pcb_rules_check `SUMMARY: 9 checks, 4 PASS, 5 FAIL`; interface_check `SUMMARY: 85 checks, 80 PASS, 5 FAIL`.

Numerical findings:
- ELEx to Ex copper 5.00 mm MEASUREMENT (design file) vs 3.5 mm rule at 4 kV CALCULATION: PASS; vs 7.5 mm at 8 kV: FAIL.
- Ex to other MPR121/Pico nets 5.29 mm MEASUREMENT: PASS 4 kV, FAIL 8 kV. Ex to Ey 1.66 mm MEASUREMENT (reported, passes a series R).
- Terminations (L 6.5 ±0.3, A 0.6 ±0.3, W 3.2 ±0.2 mm SOURCE TT HPWC 09.23; placement ±0.5 mm ASSUMPTION): worst 4.40 mm (no error), 4.25 mm (±0.25), 3.79 mm (±0.5) CALCULATION; all PASS at 4 kV, FAIL at 8 kV.
- Spark gap, 12 electrode pads to GND edge track: 1.401 mm MEASUREMENT vs 1.40 ±0.05: PASS.
- Mounting-metal bypass worst sum 17.71 mm CALCULATION (radius ASSUMPTION): PASS.
- Keep-out margins: TP/USB 1.52 mm, SWD pads 2.05 mm MEASUREMENT (rule-area clearance already included in the rectangle).
- Pico land inner 16.18 mm, outer 24.58 mm, pad gap 0.94 mm, outer edge 1.10 mm from board edge MEASUREMENT. Track widths: min 0.80 mm (5 S-row stubs, longest 5.08 mm), signals 1.0, power 1.2 mm MEASUREMENT.
- Holes 133 to 4 MEASUREMENT (drill file).
- GND paths J2 pad 1 to Pico pin 23 21.99 mm, module GND to Pico pin 23 30.90 mm MEASUREMENT; worst module-Pico bounce 318 V / ~1 ns CALCULATION on ASSUMPTION inductances (calc_gnd_bounce.py; socket/pin inductance kept, conservative for a castellation).
- R-011 (off-board pot, calc_r011_offboard_pot.out, CALCULATION, order of magnitude): 4 kV charge 0.60 µC, 15 A first peak; C1 holds a wiper strike to about 6 V at 4 kV, 12 V at 8 kV; wire L 40-360 nH (ASSUMPTION length, per metre) gives 600 V to source voltage across the wire. Hard copper frame-to-AGND link of V1.2 is gone, but a metal shaft is still not protected: internal gap 0.5-2 mm (ASSUMPTION) is below 3.5 mm and no wire has a series R. Remaining unquantified: RP2040 ADC/AGND pad rating and latch-up (R-010), bought-pot internal gap, wire length, any metal enclosure. Physical ESD step 2b stays.

Changed from or added to ADR-023 (none changes pinout, nets or firmware):
- J2 pad centre row y 63.75 mm so the 3.0 x 4.5 mm SMD copper occupies the same area as the V1.2 terminal copper (spark gap kept).
- Added a second Pico keep-out for the 3 SWD pads (T-090 union covered only TP1-6 and USB pads).
- R1-R12 row at pad y 49.0 / 55.9 mm, close to J2; I2C runs moved to y 21.05 / 23.55 mm so the ORIG copper legend fits; SW1 at (31.5, 30.23); RV1 pads at x 34.5 mm; C1 at (30, 17.24). Only placement.
- J2 excluded from BOM (copper only; wire listed in README). Symbol J2 changed to Conn_01x14 (same pin numbers).
- RV1 symbol changed from R_Potentiometer_MountingPin to R_Potentiometer (no MP pin).
- check_silk.py retired from run_all.sh (no silkscreen on the board); check_silk.out is stale.
Routing: every net on one layer; no new wire bridges. Same two configuration wires and JP1 as V1.2.

Assumptions: stand-off about 2.5 mm (T-090); hot-melt clear of the spark gap (manual); copper peel assumptions unchanged from T-090; IEC 61000-4-2 and F.2 recalled, not opened; 1206 parts generic (datasheets not opened); KEMET C1 datasheet not opened; HPWC MPN by pattern, stock/price not confirmed.

Errors and corrections during the task:
- First gen run failed: J3 still pointed at the old WireHoles footprint; fixed.
- First DRC: 1 violation (ORIG text 0.44 mm from JP1 pad), fixed by moving the I2C runs; rules unchanged.
- check_smd first run: 2 FAIL. One was real (S1/S7 stubs 0.8 mm on power-capable nets; widened to 1.2 mm in the generator). The other was a bug in the check (counted KiCad "unconnected-" nets as connected).
- A patch script of mine failed with a syntax error and a job started with old sources; stopped that own task and re-ran.
- Running sim/systems/budgets.py rewrites reports/systems/budgets.md (outside my paths): git diff shows no change, so it is byte-identical; budgets.out likewise unchanged.
- pcgate exit codes: no 75 or 143 observed.

Open decisions for manager:
1. Systems: REQ-027 rewrite, REQ-030 wording, sim/systems checks. Current FAILs and why: pcb_rules_check: REQ-027 tracks on B.Cu; REQ-027 through-hole only; ADR-021 JP1 gap and J2 pads and ADR-020 spark gap (parser expects thru_hole pads and B.Cu tracks). interface_check: AGND membership and RV1 MP (off-board pot, ADR-023); label v1.2; R1_R12 footprint and MPN (expects DIN0414 / MBE0414). Spark gap, JP1 gap and J2 pads pass in check_gap/check_smd on the SMD geometry.
2. R-011: confirm insulated shaft and knob as the requirement for RV1 (README states it).
3. Not updated by me, outside scope: management/metrics.json, reports/electronics/analysis.md, calc scripts that still model 3k3 (calc_flashover, calc_pulse_rated, calc_esd_variants, sim_electrode; T-090 calc_smd_feasibility covers 3k0), SOURCES_EE.md (T-090 sources are in smd_feasibility section 9), INTERFACES.json.

Next actions: systems rewrites REQ-027 and the checks; independent review of the SMD outputs; user trial etch and hand-solder trial (Pico castellations, butted module pins) and physical ESD test plan REQ-023/R-011.
