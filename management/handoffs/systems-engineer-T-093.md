# T-093 — systems-engineer

Status: PARTIAL. The requirements, checks, budgets, risks and frozen-8 proposal are done on the final v1.3 board (76027e9). Two doc checks FAIL because docs/manual/MANUAL.md and README.md still describe V1.2 (REQ-036 FAIL). Nothing was built or tested. Design-file checks are not hardware validation.

Requirements addressed: REQ-006, REQ-023, REQ-024 (wording), REQ-025, REQ-027, REQ-028, REQ-029, REQ-030, REQ-032, REQ-035 (wording), REQ-036, REQ-038 (note), REQ-040 (note).

Inputs (path @ revision): changes/CR-003.md, DECISIONS.md ADR-023, handoffs electronics-engineer-T-090/T-091/T-092, reports/electronics/smd_feasibility.md, sim/electronics/calc/*.out, hardware/ @ 76027e9. Board sha256 3071ad1d780678cc2284c49bc02d97b2adbc7a557593368262c46af076d7b671. Drill sha256 7970d7f811d1cf62a63ceffd83ba3b5ccffd7ecaf06f6abf5bde531972b916ff.

Outputs (uncommitted):
- management/REQUIREMENTS.md draft-10, requirements/requirements.csv (42 rows, status matches the MD on all rows)
- management/RISKS.md (R-003, R-006, R-008 to R-011 updated; R-012 to R-017 new)
- management/INTERFACES.json frozen-8 proposal, `frozen` false, `frozen_on` "frozen-8 pending manager freeze"
- sim/systems/pcb_rules_check.py and .out (rewritten), interface_check.py and .out (rewritten for SMD), budgets.py and .out (revision 8)
- reports/systems/budgets.md (generated), requirements/SOURCES_SYSTEMS.md (S-40 to S-47)
- management/handoffs/systems-engineer/T-093/mutation_tests.py, mutation_results.txt

Checks performed (Python 3.9.6):
- `python3 sim/systems/pcb_rules_check.py`: `SUMMARY: 24 checks, 24 PASS, 0 FAIL`
- `python3 sim/systems/interface_check.py`: `SUMMARY hardware/firmware: 88 checks, 88 PASS, 0 FAIL`, `SUMMARY documentation: 25 checks, 23 PASS, 2 FAIL`, `SUMMARY: 113 checks, 111 PASS, 2 FAIL`
- The 2 FAILs: `doc.manual.matches_v1.3`, `doc.root_readme.matches_v1.3`
- `python3 sim/systems/budgets.py`: `SUMMARY: 31 checks, 26 PASS, 5 FAIL` (A3b, three 100 kHz latency rows, C1 BOM; A8 new PASS)
- Mutations: `MUTATION SUMMARY: 54 proved, 0 not proved` (scratch copies only)
- Parser cross-check with pcbnew 10.0.4: `pad compare 131 mismatch 0`
- 0 U+222B in REQUIREMENTS.md, requirements.csv, RISKS.md; no new non-ASCII characters
- ERC/DRC NOT RUN by systems (T-092 reports `Found 0 DRC violations`).

Numerical findings:
- Core BOM 20.10–53.55 EUR CALCULATION (target 30 EUR, REQ-032 FAIL)
- R1–R12 4.26–27.13 EUR for 12: ASSUMPTION on sibling values, USD at ASSUMED 0.85–0.95 EUR/USD
- Sensitivity with listed TME sibling prices: core 19.47–37.36 EUR CALCULATION
- HPWC2512-3K0JT18: no distributor offer found 2026-11-09 SOURCE S-40. Sibling MOQ scenario 145–162 EUR CALCULATION (outside the core range)
- Clearance minimum 0.650 mm (A2.1 GND to SDA track, and SDA to A2.10 ELE8) MEASUREMENT vs rule 0.6 mm: PASS
- Spark gap 1.400 mm on E0–E11 MEASUREMENT vs 1.40 ± 0.05 mm: PASS
- Holes 4, drill 3.2 mm, drill file hits equal the board MEASUREMENT
- A8 pot wires 25 pF on C1, 26.8 uV IR drop CALCULATION on ASSUMPTIONS

Assumptions: EUR/USD rate range; sibling HPWC price for 3k0; 0.5 m pot wires, 50 pF/m, 0.13 ohm/m; short stub ≤ 6 mm (from check_smd). Pot-wire hum not analysed.

Errors: board text with parentheses in descriptions broke the pad parser, fixed by ignoring quoted strings; the R5 land-gap mutation first moved the wrong pad, fixed. T-092 committed during this task: checks and mutations re-run on the final board. Handoff path follows the task, not the agent default folder. management/metrics.json is not updated (outside my paths).

Open decisions for manager:
1. Freeze or reject INTERFACES frozen-8 (I set `frozen` false until you do).
2. REQ-032: new upper bound 53.55 EUR is not covered by ADR-019 D-3 or the ADR-021 addendum. Get a real HPWC quote or pick another 3k0 pulse-rated 2512 (R-016).
3. Amend PROJECT_DEFINITION.md, which still says through-hole, socketed, screw terminals (ADR-023 reverses these).
4. Documentation task for MANUAL.md and README.md (closes REQ-036 FAIL).
5. JP1 legend is on the assembly map only, not on the board (R-007, REQ-040): accept or etch it.
6. New R-017: SDA passes 0.65 mm from A2 electrode pads (V1.2 about 3.2 mm), passes the rules, coupling not analysed: ask electronics or leave for REQ-038 test.
7. Is `frozen` false right for a proposal? Earlier frozen-7 left it true.

Next actions: documentation updates, independent review, report rebuild from the new CSV, manager commit.
