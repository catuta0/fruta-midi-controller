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
