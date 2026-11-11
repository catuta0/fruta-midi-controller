# T-099 — systems-engineer

Status: PARTIAL. The checks, budgets, requirements, risks and the frozen-8 proposal are updated to the T-098 board (5c92ca3, YAGEO RC2512FK-073K3L 3k3 on R_2512_HomeEtch_G5.0mm, Mouser BOM, PTV09A pot). Every changed check is mutation-proved. Two documentation checks FAIL, as expected (docs/manual/MANUAL.md and the root README.md still describe V1.2). REQ-032 is PARTIAL until the manager rules the cost basis. Nothing is raised to PASS on hardware grounds. Nothing is committed.

Requirements addressed: REQ-006, REQ-023, REQ-032, REQ-036 (evidence), REQ-038 (evidence); risks R-003, R-006, R-009, R-011, R-016, R-017, plus R-018 (new).

Inputs (path @ revision 5c92ca3, branch change/CR-003): management/DECISIONS.md ADR-024/025/026; handoffs electronics-engineer-T-094..T-098; reports/electronics/SOURCES_EE.md (T96-S0..S5); hardware/frutamidi.kicad_pcb, hardware/README.md, hardware/fabrication BOM (read-only); sim/electronics/calc outputs as quoted in the EE handoffs (not re-run by systems).

Outputs (uncommitted):
- sim/systems/interface_check.py and .out: footprint, MPN and Mouser triplets per part; new checks `pcb.R1_R12_Mouser`, `doc.hw_readme.mouser_numbers`; BOM needs a Mouser column; RV1 PTV09A insulated-shaft text; HPWC added to the stale-term lists.
- sim/systems/pcb_rules_check.py and .out: new check `ADR-026 R1-R12 on footprint R_2512_HomeEtch_G5.0mm`.
- sim/systems/budgets.py (revision 9) and .out; reports/systems/budgets.md (generated).
- management/REQUIREMENTS.md draft-11; requirements/requirements.csv (42 rows; the MD and CSV statuses match, asserted by the patch script).
- management/RISKS.md: R-003, R-006, R-009, R-011, R-016, R-017 updated; R-018 is new (plan-B trigger).
- management/INTERFACES.json: frozen-8 proposal revised, `frozen` false, `frozen_on` "frozen-8 pending manager freeze".
- requirements/SOURCES_SYSTEMS.md: S-40..S-47 marked HISTORICAL; S-48..S-50 added (second-hand SOURCE via T-096/T-097).
- management/handoffs/systems-engineer/T-099/mutation_tests.py, mutation_results.txt. The T-093 copy was left unchanged (restored to HEAD).

Checks performed (Python 3.9.6):
- `python3 sim/systems/pcb_rules_check.py`: `SUMMARY: 25 checks, 25 PASS, 0 FAIL`
- `python3 sim/systems/interface_check.py` (exit 1 because of the doc FAILs): `SUMMARY hardware/firmware: 89 checks, 89 PASS, 0 FAIL`, `SUMMARY documentation: 26 checks, 24 PASS, 2 FAIL`, `SUMMARY: 115 checks, 113 PASS, 2 FAIL`. The two FAILs are `doc.manual.matches_v1.3` and `doc.root_readme.matches_v1.3`.
- `python3 sim/systems/budgets.py`: `SUMMARY: 31 checks, 27 PASS, 4 FAIL`. The 4 FAILs are A3b and the three 100 kHz latency rows, the same as the baseline. `PASS  C1 core BOM upper bound <= 30 EUR (ex VAT, ex shipping) :: core 14.84 .. 16.84 EUR` (it was FAIL at 20.10–53.55).
- Mutations: `MUTATION SUMMARY: 61 proved, 0 not proved` (T-093: 54; scratch copies only). The new or changed mutations are:
  - R5 footprint
  - R7 MPN
  - R8 Mouser
  - R9 value 3k0
  - RV1 MPN
  - A1 Mouser removed
  - C1 MPN
  - R15 MPN
  - README part, Mouser numbers, RV1 insulated text, continuity 3.0 kΩ
  - BOM MPN, BOM C1 Mouser
  - R3 on the old footprint name
- pcb_rules_check INFO line: `3.30 mm between track#99 (94.46,70.90)-(138.81,70.90) w1.00 [/SDA] and A2.10 [/ELE8]`. Minimum clearance: `minimum 0.720 mm`.
- Placement re-read from the board: all anchors match INTERFACES except R15, which is now at (85.00, 18.90) (was 21.05, T-094 re-route). Updated.
- `git status --short hardware/ sim/electronics/ reports/report/`: 0 lines (untouched).
- New text contains no non-ASCII characters outside §±²µ×Ωτ–→↔−≈≤≥. The °·… in SOURCES_SYSTEMS.md were already there.
- ERC/DRC and the pcbnew parser cross-check: NOT RUN in T-099. The parser is unchanged apart from the new footprint-name check.

Numerical findings:
- Mouser lines 13.84 EUR (CALCULATION from T-096 SOURCE prices, ex VAT, ex shipping). It matches T-096.
- Core BOM 14.84–16.84 EUR (CALCULATION; copper clad 1.0–3.0 EUR ASSUMPTION), margin 13.16 EUR against the 30 EUR target.
- With VAT at 23 % (ASSUMPTION rate) the core is 18.25–20.71 EUR. Shipping is NOT CONFIRMED.
- Plan B (T-097) adds 6.18 EUR, giving 21.02–23.02 EUR (CALCULATION).
- Series 3k3 +1 % (3333 Ω): τ 0.33 µs at 100 pF against CDT 4 µs (ratio 0.08); IR 0.210 V at 63 µA (CALCULATION).
- C1 settling 2.89 ms against the 30 ms read period, margin 10.4× (CALCULATION). Pot ±20 % is now SOURCE (Bourns PTV09, T96-S3).
- REQ-023 figures (cited from the EE outputs, not re-run):
  - 1.10 A (1.11 A at −1 %) against 1.33 A (ASSUMPTION), margin 1.20–1.22.
  - 3636 / 7273 V across R.
  - Gaps 5.00 / 5.29 mm; terminations 4.65 / 4.54 / 4.08 mm.
  - Bypass 8.40 mm; spark gap 1.40 mm.
  - Sensitivity 0.904 against 0.90 (SIMULATION).
  - Pulse capability NOT PROVEN.

Requirement counts (draft-11): PASS 16, PARTIAL 19, FAIL 3 (REQ-018, REQ-036, REQ-040), NOT RUN 4, BLOCKED 0; total 42. Change: REQ-032 FAIL to PARTIAL.

Assumptions:
- Plan-B trigger window 3234–3366 Ω (±2 %), based on the 0.901 sensitivity at 3366 Ω (SIMULATION, T-094).
- VAT 23 %.
- Copper clad 1.0–3.0 EUR.
- C1 X7R ±15 % over temperature (Samsung datasheet not opened).
- Knob material ABS, taken from hardware/README.md (no knob datasheet opened).

Errors:
- The first harness patch was refused on a wrong anchor ("pad 1" where the file has "pad 2"). It was re-applied with the correct anchor, and nothing partial was written.
- The harness edits first landed in the T-093 folder as well. That copy was reverted to HEAD, and the updated harness lives in T-099/.

Open decisions for the manager:
1. REQ-032 cost basis. ADR-007 D-7 does not say whether VAT and shipping are in. Ruling the basis ex VAT and ex shipping (as in every earlier revision) makes REQ-032 PASS. With 23 % VAT it is still ≤ 30 EUR. Shipping is unknown.
2. Accept the R-018 plan-B trigger (the ±2 % window is an ASSUMPTION) and its place in REQ-023 test steps (1) and (3).
3. R-016: Mouser PT stock of RC2512FK-073K3L was 13 for the 12 needed (next delivery 2027-05-18). This leaves no spare.
4. Freeze or reject the revised frozen-8 INTERFACES proposal.
5. Still open from T-093: the PD amendment; REQ-036 (the manual and root README are a documentation task); REQ-040 JP1 legend; R-010 GP26/GP27 rating; the REQ-038 3-count criterion. Knob bore fit NOT CONFIRMED.

Next actions: documentation updates docs/manual/MANUAL.md and README.md to v1.3 (this clears the two doc FAILs and REQ-036). After the manager rules on items 1–4, systems updates the REQ-032 status and freezes the INTERFACES text as directed.

# T-100 — systems-engineer (ADR-027 applied)

Status: PARTIAL. All five ADR-027 rulings are recorded: D-1 to D-3 and D-5 in the requirements and risks, and D-4 in INTERFACES.json, which the manager froze. The two documentation FAILs remain because docs/manual/MANUAL.md and README.md are still being edited by documentation in parallel. Nothing was raised to PASS on hardware grounds. Nothing is committed.

Requirements addressed: REQ-032 (PARTIAL → PASS, ADR-027 D-1), REQ-023 (plan-B trigger accepted, D-2; status PARTIAL unchanged), REQ-040 (FAIL kept as an accepted risk, D-5). Risks: R-007 (legend text, D-5), R-016 (OPEN → ACCEPTED, D-3), R-018 (trigger accepted, D-2; stays OPEN until the physical test).

Inputs: branch change/CR-003 at 9505245 (clean apart from .claude/ and CLAUDE.md); management/DECISIONS.md ADR-027.

Outputs (uncommitted): management/REQUIREMENTS.md draft-12, requirements/requirements.csv, management/RISKS.md. management/INTERFACES.json was NOT edited, because it is frozen by the manager (`frozen` true, `frozen_on` "2026-11-11 (frozen-8, manager freeze, ADR-027 D-4)").

Checks performed (Python 3.9.6):
- `python3 sim/systems/budgets.py`: `SUMMARY: 31 checks, 27 PASS, 4 FAIL` (A3b and three 100 kHz latency rows; C1 cost PASS)
- `python3 sim/systems/interface_check.py`: `SUMMARY hardware/firmware: 89 checks, 89 PASS, 0 FAIL`, `SUMMARY documentation: 26 checks, 24 PASS, 2 FAIL`, `SUMMARY: 115 checks, 113 PASS, 2 FAIL` (doc.manual.matches_v1.3, doc.root_readme.matches_v1.3; exit 1)
- `python3 sim/systems/pcb_rules_check.py`: `SUMMARY: 25 checks, 25 PASS, 0 FAIL`
- The three .out files are byte-identical to the T-099 versions committed in 9505245 (git shows no change).
- The patch script asserts that MD and CSV status counts are equal and that the evidence text of the patched rows is equal in both files. No non-ASCII characters outside the allowed set.
- Mutation harness: not re-run, because no check code changed (T-099: `MUTATION SUMMARY: 61 proved, 0 not proved`).

Requirement counts (draft-12): PASS 17, PARTIAL 18, FAIL 3 (REQ-018, REQ-036, REQ-040), NOT RUN 4, BLOCKED 0; total 42.

Numerical findings (unchanged from T-099): core 14.84–16.84 EUR ex VAT (CALCULATION), 18.25–20.71 EUR with 23 % VAT (ASSUMPTION rate), shipping NOT CONFIRMED; plan B 21.02–23.02 EUR (CALCULATION).

Errors: none.

Open items for the manager:
1. INTERFACES.json is frozen, but two of its text fields still read as a proposal: `revision` says "frozen-8 proposal ... freeze by the manager" and `frozen_by` says "manager (pending)". These are the manager's fields, so I did not edit them.
2. ADR-027 D-3 says the purchase list names a standard 3k3 ±1 % 2512 alternative. I did not find one in hardware/README.md on 2026-11-11. R-016 records this.
3. Still open: REQ-036 (documentation in progress); after it lands, interface_check must be re-run to clear the two doc FAILs. Also R-010, the REQ-038 3-count criterion, the knob bore fit, and the shipping cost.

Next actions: re-run interface_check when documentation finishes MANUAL.md and README.md, and then update REQ-036.
