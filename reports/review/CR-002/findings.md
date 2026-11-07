# CR-002 independent re-review (T-071): findings

Reviewer: independent-reviewer, inputs at 8394b41 (branch change/CR-002). The harness refused the reviewer's write of this file; the manager recorded the findings from the reviewer's hand-back report without changing their substance. Raw outputs and scripts: this folder (erc.rpt, drc.rpt, check_gap_rerun.*, interface_check_rerun.out, pcb_rules_check_rerun.out, budgets_rerun.out, chart_check.py/.out, geo.py, geo_dump.out). Nothing here is a hardware measurement; "MEASUREMENT (design file)" means read from the KiCad file.

Datasheets: vishay_mbxsma_28766.pdf sha256 201a7ea8e35843345975a100b4b98802df0b3a56cf57805e881ecd93b9973cff; lsr37_bc.pdf sha256 cd74dacdd3304934151d475ee1f2bb51ad5961b90744728402d545be4bd8f8ad (match EE-S17b, EE-S24).

## Checks reproduced (all PASS)
ERC 0; DRC 0 / unconnected 0 / parity 0; rules file unchanged; check_gap.py PASS (copper only); calc_flashover/calc_pulse_rated byte-identical; interface_check 80/80 (committed .out stale, 79/80); pcb_rules_check 16/16; budgets byte-identical (23.78–37.72 EUR); chart readings at 3.3 kΩ 4086 / 1740 / 1469 V (0414/0207/0204); dimensions MBE 0414 D 4.2, L 11.9, d 0.8, Mmin 15.0 mm; drill counts 131 = README; BOM consistent; no copper under R bodies; JP1 orientation and silkscreen agree; H4 clear; routing continuous; config wires 21.1–32.1 mm.

## Findings
| ID | Sev. | Finding | Suggested fix |
|---|---|---|---|
| C2-001 | minor | README:145 asks for a lead bend ≥ 1.5 mm from the body; at 15.24 mm pitch the lead centre is 1.67 mm from the body end, a 1.5 mm bend needs 15.70 mm (r = 0) or 17.30 mm (r = 0.8 mm) pitch (CALCULATION). | Reword (bend close to the cap, check fit) or larger pitch (needs relayout). |
| C2-002 | minor | Closest metal of a flat resistor is cap to cap, ≈6–8 mm with an assumed 2–3 mm cap length, not the 13 mm copper gap; cross-channel cap gap similar. check_gap measures copper only; its lead↔lead line is meaningless for flat parts. 8 kV gap claims (analysis §5, R-006, README "13 mm", "cannot") overreach. 4 kV passes if cap length ≤ 4.2 mm. | Add cap-to-cap checks with a sourced or bounded cap length; limit 8 kV statements to copper; reword README. |
| C2-003 | minor | Pulse energy overstated ≈2× (≈185 mJ, not 364 mJ): script used ∫V dt form. At 3.3 kΩ the chart is energy-limited (slope 0.496), voltage plateau ≈5.06 kV from ≈5.07 kΩ. Conclusions unchanged (PASS 4 kV, FAIL 8 kV). | Correct formula and wording. |
| C2-004 | info | Independent chart reading confirms 4086/1740/1469 V; dimensions, LSR37 data, MPN agree. | None. |
| C2-005 | minor | Every E terminal pad is 1.40 mm from the GND edge track: below every breakdown model at 4 kV, so a strike most likely arcs to GND; ≈12 A peak through the GND trunk to Pico/module/USB is not analysed (pre-existing path). | Treat as intentional spark gap and estimate bounce, or move the track; add "arc to GND" to the REQ-023 test. |
| C2-006 | minor | Stale evidence: committed interface_check.out 79/80; REQ-028/029, requirements.csv, INTERFACES.json frozen-4 notes describe 3a3684b. | Re-run and commit; update texts; frozen-5 or erratum. |
| C2-007 | minor | README offers a resistor lead off-cut for JP1 (0.8 mm holes); R1–R12 leads are 0.8 mm (0 clearance). Only R13–R16 off-cuts (0.5 mm) fit. | Say so. |
| C2-008 | info | 1.0 mm drill for a 0.8 mm lead sits exactly on the 0.2 mm fit threshold, no lead tolerance; comment "0.2 mm around" is diametral. | 1.1 mm drill or record zero margin; fix comment. |
| C2-009 | info | Courtyard gaps 0.06 mm (R row↔J2), 0.09 mm (R12↔H3); M3 head ≈0.5–0.9 mm from R12 body, ≈1.3 mm from the ELE11 cap. | Recommend nylon hardware at H3. |
| C2-010 | info | Terminal labels "10", "11" touch R10/R11 pad 2 (≈0.1 mm). | Move or shrink. |
| C2-011 | info | check_gap.py worst-pair name not deterministic on ties. | Tie-break by reference. |
| C2-012 | info | I2C relayout under the module (SDA 3.2 mm from electrode pads over ≈31 mm, loop ≈800 mm²) not analysed; bus capacitance margin fine. | Add I2C-traffic vs baseline-noise test (REQ-038/P-4) or estimate mutual C. |
| C2-013 | info | IEC 60664-1 F.2 values recalled, M3 coefficients ≈4 % off Kuffel form; the 3.5 mm rule comes from model M4 (η = 0.3). | Read F.2 once or drop it from the rule. |

## Requirement cross-check
REQ-023 PARTIAL (agree; 8 kV gap unproven C2-002; GND path C2-005). REQ-027 PASS. REQ-028/029 PASS (evidence text stale, C2-006). REQ-032 FAIL (arithmetic reproduced). REQ-036 should be PARTIAL until C2-001 and C2-007 are fixed.

## Dispositions (manager)
Filled in after the fixes; see section "Dispositions" appended below.
