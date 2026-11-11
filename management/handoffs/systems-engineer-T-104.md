# T-104 — systems-engineer

Status: PARTIAL.
- Done: every systems check runs on the T-103 board; budgets, requirements (draft-13), risks, metrics and the INTERFACES frozen-9 proposal are updated. Every new or changed check is mutation-proved, and no mutation survived.
- Why PARTIAL:
  - REQ-036 stays FAIL on two new consistency checks: the manual and the root README do not yet follow T-103.
  - ADR-028 is only a draft, because management/DECISIONS.md is outside my write paths.
- Nothing was raised to PASS on hardware grounds. Nothing is committed. hardware/, sim/electronics/ and reports/electronics/ (the T-103 working tree) were not touched.

Requirements addressed: REQ-023, REQ-025, REQ-027, REQ-029 (statement and evidence), REQ-030, REQ-036, REQ-038. Risks R-010, R-013, R-014, R-016, R-017. Review findings F3-005, F3-009 and F3-010 (systems part).

Inputs (path @ revision): branch change/CR-003 at fd7140b plus the uncommitted T-103 working tree (hardware/, sim/electronics/calc/*.out, hardware/README.md); management/handoffs/electronics-engineer-T-103.md; reports/review/CR-003/findings.md; docs/manual/MANUAL.md and README.md at 7c3cf6e (read only).

Outputs (uncommitted):
- sim/systems/pcb_rules_check.py and .out:
  - land table after T-103 (A2 1.8 × 4.2 / 1.8 × 5.515, R13..R16 1.775 × 1.8, C1 1.875 × 1.8);
  - 3 keep-out areas;
  - new check `ADR-028 D-1 Pico end inside the board and USB face >= 1.0 mm beyond the edge`, derived independently from the A1 F.Fab end line.
- sim/systems/interface_check.py and .out, new checks:
  - `fab.copper_only_excluded_from_bom`; J1 is now copper only;
  - `doc.hw_readme.pico_variants`, `doc.hw_readme.R016_alternative`, `doc.hw_readme.knob_and_sw1_notes`;
  - `doc.manual.JP1_label_position`, `doc.root_readme.pcb_variants`.
- sim/systems/budgets.py (revision 10) and .out; reports/systems/budgets.md:
  - C2 BOM coverage;
  - D1 to D3 board-level items, read from the electronics .out files;
  - INFO line for the R-016 alternative cost;
  - environment variable FM_BUDGETS_ROOT, used by the mutation tests only.
- management/REQUIREMENTS.md draft-13 and requirements/requirements.csv (42 rows; MD and CSV asserted equal).
- management/RISKS.md: R-010, R-013, R-014, R-016, R-017.
- management/INTERFACES.json: frozen-9 proposal.
  - `frozen` false and `frozen_on` "frozen-9 pending manager freeze".
  - The old frozen-6 status_note was moved to `changelog_frozen_6`.
  - Updated: A2 lands, module height, `pico_mounting` (variants, position, 3 keep-outs), 1206 lands, placement, J1 and BOM notes.
- management/metrics.json: 25 new entries (58 in total), every entry labelled.
- requirements/SOURCES_SYSTEMS.md: S-51 and S-52 (second-hand via T-103).
- management/handoffs/systems-engineer/T-104/: mutation_tests.py, mutation_results.txt, ADR-028_draft.md.

Checks performed (Python 3.9.6, no heavy job, so no pcgate use):
- `python3 sim/systems/pcb_rules_check.py`: `SUMMARY: 26 checks, 26 PASS, 0 FAIL`. Key lines:
  - `PASS  ADR-028 D-1 ... A1 at (4.50, 1.48); Pico end 0.11 mm inside the edge; face 1.19 mm beyond it`
  - `PASS  REQ-029 no bare copper in the 3 Pico keep-out rule areas`
  - minimum clearance `0.680 mm between C1.2 [/AGND] and track#93 ... [/SCL_PICO]`; edge clearance `0.680 mm at A1.1`
- `python3 sim/systems/interface_check.py` (exit 1): `SUMMARY hardware/firmware: 90 checks, 90 PASS, 0 FAIL`, `SUMMARY documentation: 31 checks, 29 PASS, 2 FAIL`, `SUMMARY: 121 checks, 119 PASS, 2 FAIL`.
  - FAIL `doc.manual.JP1_label_position`: the manual still says "**ORIG** etched below".
  - FAIL `doc.root_readme.pcb_variants`: README.md offers the PCB .uf2 for Pico W and Pico 2 W without "not supported".
- `python3 sim/systems/budgets.py`: `SUMMARY: 35 checks, 31 PASS, 4 FAIL`. The 4 FAILs are A3b and the three 100 kHz latency rows, unchanged from the baseline. New rows:
  - `PASS  C2 budget BOM = fabrication BOM ... bom-kicad.csv 8 lines / 21 parts, budget 21 parts; differences []; knob in README True`
  - `PASS  D1 ... 1.49 A vs 2.67 A (0.56x), 0.90 nC vs 400 nC; bounce 330 V / ~1 ns`
  - `PASS  D2 SDA coupling step <= 3 counts ... 2.09 counts (36.6 fF), touch threshold 12, margin 5.7x`
  - `PASS  D3 largest M3 screw force at a 30 N USB pull <= 100 N (ASSUMPTION limit, not sourced) :: 35.6 N`
- `python3 management/handoffs/systems-engineer/T-104/mutation_tests.py <scratch>`: `MUTATION SUMMARY: 85 proved, 0 not proved` (0 MUT-BAD lines). New proofs:
  - land-table mutations: A2, C1, R15;
  - keep-outs: TP7 keep-out removed, and a track through TP7;
  - A1 moved 1.0 mm in, and 0.2 mm out;
  - BOM flags: J1 included, R16 excluded;
  - README text: Pico variants (×2), alternative part, knob and SW1 notes (×2);
  - manual and root README made stale;
  - budgets: C2 ×3, D1 ×2 (one with the file missing), D2, D3;
  - the two checks that fail today, each proved to pass on a corrected copy.
- INTERFACES placement re-read against the board: `placement mismatches []`.
- No new non-ASCII characters outside the allowed set.
- ERC/DRC: NOT RUN by systems. T-103 reports "Found 0 DRC violations".

Numerical findings:
- Board geometry:
  - Pico anchor y 1.48 mm (MEASUREMENT); Pico end 0.11 mm inside the edge; USB face 1.19 mm beyond it (CALCULATION; limit 1.0 mm ASSUMPTION).
  - A2 lands 1.8 × 4.2 mm and 1.8 × 5.515 mm (MEASUREMENT), 1.73–1.775 mm beyond the module outline (MEASUREMENT, T-103).
  - Module underside 5.5 mm and board top 7.1 mm above the copper (CALCULATION on ASSUMPTIONS 2.5 / 3.0 / 1.6 mm).
  - Clearance minimum 0.680 mm, down from 0.720 mm (MEASUREMENT).
- Board-level items:
  - GND bounce 330 V for about 1 ns; 1.49 A and 0.90 nC per I²C line (CALCULATION on ASSUMPTIONS).
  - SDA coupling 36.6 fF, 2.09 counts against a threshold of 12 (CALCULATION).
  - USB pry: 35.6 N on the most loaded screw at a 30 N pull (CALCULATION on ASSUMPTIONS).
- Cost:
  - Core BOM 14.84–16.84 EUR ex VAT, ex shipping, unchanged (CALCULATION).
  - The R-016 alternative adds 3.78 EUR, giving 18.62–20.62 EUR (CALCULATION from SOURCE 0.424 EUR via T-103).

Requirement counts (draft-13): PASS 17, PARTIAL 18, FAIL 3 (REQ-018, REQ-036, REQ-040), NOT RUN 4, BLOCKED 0; total 42. No status changed.

Assumptions:
- D3 allowable 100 N per M3 nylon screw: not sourced, my ASSUMPTION.
- D2 criterion 3 counts: the REQ-038 proposal, half of RELEASE_THRESHOLD.
- D1 criterion: the RP2040 FT-pin HBM equivalent; the GP26/GP27 rating is NOT CONFIRMED.
- Cutting tolerance 1.0 mm.
- T-103 build assumptions, now in the REQ-029 first-build list: strip 2.5 mm, pin 3.0 mm, module board 1.6 mm, C1 body 3.4 × 1.8 mm, B3S body 6.1 mm.

Errors:
- The harness first failed with IndexError: the A1 keep-out zones are nested inside the footprint (two tabs). I fixed the regex; the run was not partial.
- One stray scratch file was written to /tmp during an interface_check run and deleted at once.

Open decisions for the manager:
1. Enter ADR-028 in management/DECISIONS.md. The draft is management/handoffs/systems-engineer/T-104/ADR-028_draft.md.
   - D-1 and D-2 are your rulings.
   - D-3 to D-7 restate the T-104 directions (Pico variants, BOM consistency, R-016 alternative, records, residual items) and need your confirmation.
   - Also correct the ADR-026 stock date, 2026-11-09 against 2026-11-11 (F3-009). That file is yours.
2. REQ-036 → PASS is not supported yet.
   - The manual repeats the "ORIG etched below" error that ADR-028 D-2 corrected in the README.
   - The root README lists PCB firmware for Pico W and Pico 2 W without the not-supported note.
   - The manual does not yet describe the T-103 module-pin and trimming steps.
   - All three are for documentation (T-105). Then re-run interface_check.
3. Freeze or reject the INTERFACES frozen-9 proposal.
4. D3 screw-force limit: ask electronics to source a nylon M3 axial or pull-through value. Until then, D3 PASS rests on an ASSUMPTION.
5. metrics.json entry `v1.3_plan_b_window` is labelled SIMULATION. It is an ASSUMPTION window (R-018) and needs relabelling; I did not edit it because I did not write that entry.

Next actions:
- Documentation T-105: correct the manual JP1 text and the T-103 assembly steps, and mark the root README PCB rows for Pico W and Pico 2 W as not supported.
- Systems: re-run interface_check after T-105 and set REQ-036.
- Electronics: open the CRCW25123K30FKEG datasheet.

# T-106 — systems-engineer (after documentation T-105)

Status: PASS for the three items. Nothing is committed.
- interface_check: `SUMMARY documentation: 31 checks, 31 PASS, 0 FAIL`, `SUMMARY: 121 checks, 121 PASS, 0 FAIL`.
- REQ-036 is now PASS (draft-14) in REQUIREMENTS.md and requirements.csv. Totals: PASS 18, PARTIAL 18, FAIL 2 (REQ-018, REQ-040), NOT RUN 4, BLOCKED 0, total 42.
- metrics.json: `v1.3_plan_b_window` relabelled from SIMULATION to ASSUMPTION (ADR-027 D-2).
- SDA coupling label: no change. The 36.6 fF and 2.09 counts come from sim/electronics/calc/calc_i2c_coupling.py, whose docstring and output header both say "CALCULATION" (method of moments). The metrics, budgets and this handoff already say CALCULATION. The electronics T-103 handoff (line 88) calls the result SIMULATION, so that handoff is mislabelled. Reported, not changed: it is not my file.
- budgets: `SUMMARY: 35 checks, 31 PASS, 4 FAIL` (unchanged baseline FAILs).
- Mutations (T-106 copy of the harness): `MUTATION SUMMARY: 86 proved, 0 not proved`. The two T-104 inverse proofs (each check passes on a corrected copy) became MUT-BAD once the documents were fixed. That is expected: those proofs only work while the document fails. They were replaced by forward mutations on stale copies, all proved. The T-104 record is unchanged.

# T-110 — systems-engineer (re-review T-108, ADR-029)

Status: PARTIAL. All four items are done. Three of the new documentation rules FAIL, as expected, until T-109 and the documentation update land. REQ-036 goes from PASS to FAIL on those rules. Nothing is committed. I did not edit hardware/README.md, analysis.md or check_smd (T-109 holds their locks).

Inputs: change/CR-003 at f0c016b (the board file is unchanged against f0c016b); reports/review/CR-003/findings-T-108.md; DECISIONS.md ADR-029. hardware/README.md was read while T-109 was editing it.

1. RISKS R-013: the mitigation now follows ADR-029 D-1.
   - Side beads go over pins 1–3 and 38–40.
   - No epoxy on the USB end face and none beyond the board edge.
   - The plug seat is re-checked after curing.
2. F4-007: geometry read from the design file is relabelled CALCULATION (design file). The counts of changed labels are:
   - REQUIREMENTS.md 5, requirements.csv 5, RISKS.md 6, INTERFACES.json 4;
   - metrics.json 20 entries. host_free_disk and report_pages stay MEASUREMENT because they are real measurements.
   - budgets.md and the systems .out files had none (`grep -c MEASUREMENT` = 0).
   - Requirements are now draft-15, because evidence text and one status changed.
3. New interface_check rules:
   - `doc.usb_epoxy_not_on_end_face` (F4-001): FAIL. Offending text:
     - root README line 16;
     - manual bullet "USB end: epoxy bead" and its table row "Epoxy bead at the USB end";
     - hardware README BOM row "epoxy at the Pico USB end", which is still stale in T-109's draft.
   - `doc.usb_epoxy_side_beads` (F4-001): FAIL. The hardware README passes (side beads present, re-check after curing present); the manual is not done yet.
   - `doc.hw_readme.continuity_37_38` (F4-002): PASS on the T-109 README in progress (the 37–38 checklist line is present and the wrong "39 and 40 lie 0.94 mm" text is gone).
   - `doc.jp1_before_module` (F4-003): FAIL. The hardware README passes (JP1 is step 7, the module is step 8, and it says ORIG is hidden); the manual assembly order still puts the module before JP1.
   - Proof (T-110/rule_proofs.py): `RULE PROOF SUMMARY: 12 proved, 0 not proved`.
     - On the corrected scratch copies all 4 rules PASS.
     - Each of 10 single mutations turns its own rule to FAIL.
     - On the HEAD documents that T-108 reviewed, the F4-001, F4-002 and F4-003 rules all FAIL, so these rules would have caught them.
   - The good set is built on the T-109 README as it stood during this run. If T-109 changes those passages, re-run the proof.
4. INTERFACES frozen-9 against the board at f0c016b (`git show f0c016b:hardware/frutamidi.kicad_pcb`): it matches.
   - `placement mismatches []`; R1 and R12 at x 33.35 and 89.23.
   - Land table, BOM exclusions (J1, J2, J3, JP1) and R1..R12 footprint all match.
   - pcb_rules_check on that file: `SUMMARY: 26 checks, 26 PASS, 0 FAIL`, `A1 at (4.50, 1.48); Pico end 0.11 mm inside the edge; face 1.19 mm beyond it`.
   - frozen-9 is ready to freeze, provided T-109 makes no copper change (ADR-029 says none).

Check results:
- interface_check: `SUMMARY hardware/firmware: 90 checks, 90 PASS, 0 FAIL`, `SUMMARY documentation: 35 checks, 32 PASS, 3 FAIL`, `SUMMARY: 125 checks, 122 PASS, 3 FAIL`
- pcb_rules_check: `SUMMARY: 26 checks, 26 PASS, 0 FAIL`
- budgets: `SUMMARY: 35 checks, 31 PASS, 4 FAIL` (the unchanged baseline)
- Full mutation harness (T-110 copy): `MUTATION SUMMARY: 86 proved, 0 not proved`

Requirement counts (draft-15): PASS 17, PARTIAL 18, FAIL 3 (REQ-018, REQ-036, REQ-040), NOT RUN 4, BLOCKED 0; total 42.

For the manager:
- REQ-036 returns to PASS once T-109 and the documentation update land and interface_check gives 125/125.
- Re-run rule_proofs.py and interface_check at that point.

# T-112 — systems-engineer (after T-109 and documentation T-111)

Status: PASS for the three items. Nothing is committed.

1. interface_check: `SUMMARY documentation: 35 checks, 35 PASS, 0 FAIL`, `SUMMARY: 125 checks, 125 PASS, 0 FAIL`. REQ-036 is now PASS (draft-16), with the same scope note as before (consistency only, nothing built).
2. Rule proofs: the T-110 script stopped with "text not found". It built its good set by patching stale text, and that text is now fixed. I wrote a T-112 copy whose good set is the current documents.
   - Its first run gave 11 of 12. The "manual loses the 38–40 bead" mutation survived because it removed only the first of two mentions in the manual. I corrected the mutation to remove every mention; the rule was not changed.
   - Final result: `RULE PROOF SUMMARY: 12 proved, 0 not proved` (T-112/rule_proofs.txt).
3. INTERFACES references: REQUIREMENTS.md now says "frozen-9 frozen by the manager (ADR-028 D-8)" in the header, the evidence-path list and the draft-16 note. The older draft notes stay as history. The frozen-9 state itself (`frozen` true, ADR-028 D-8) is the manager's.
4. Re-runs:
   - budgets: `SUMMARY: 35 checks, 31 PASS, 4 FAIL` (the unchanged baseline; C2 PASS);
   - pcb_rules_check: `SUMMARY: 26 checks, 26 PASS, 0 FAIL`;
   - mutations: `MUTATION SUMMARY: 86 proved, 0 not proved` (T-112/mutation_results.txt).

Requirement counts (draft-16): PASS 18, PARTIAL 18, FAIL 2 (REQ-018, REQ-040), NOT RUN 4, BLOCKED 0; total 42.
