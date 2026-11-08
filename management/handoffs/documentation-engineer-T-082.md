# T-082 — documentation-engineer
Status: PASS (documents and report build only; nothing here is a hardware measurement)

## Requirements / findings addressed
REQ-036 (manual matches the PCB), report coverage of final re-review T-079 (F2-001..F2-007, ADR-022), REQ-023 step 2b, REQ-032/REQ-029 text (via the regenerated table), risk R-011, INTERFACES frozen-7.

## Inputs (path @ revision)
All at a51dfff (branch change/CR-002, clean at start):
- reports/review/CR-002-final/findings.md; management/DECISIONS.md (ADR-022)
- management/handoffs/electronics-engineer-T-080.md, management/handoffs/systems-engineer-T-081.md
- requirements/requirements.csv (sha256 5d08d5ff6b2789b380312c1d52a7e2c097655a30b4b3289c973146a4297b6c83), management/REQUIREMENTS.md draft-9, management/RISKS.md (R-011), management/INTERFACES.json frozen-7
- sim/systems/pcb_rules_check.out, interface_check.out, budgets.out; sim/electronics/calc/calc_mechanical.out, check_gap.out
- hardware/README.md; hardware/fabrication/gerbers/frutamidi.drl (sha256 6469f1ef…44a6); hardware/fabrication/images/*.png

## Outputs (uncommitted)
- reports/report/frutamidi_report.tex: date line frozen-7 / draft-9 / 2026-11-08; abstract sentence on T-079 and ADR-022.
- reports/report/sections/02_requirements.tex: draft-9 description.
- reports/report/sections/03_architecture.tex: ADR-022 row.
- reports/report/sections/04_interfaces.tex: frozen-7 (C1 drill/ring, spark-gap rule, AGND ESD note); knob in IF-CONTROLS.
- reports/report/sections/05_electronics.tex: checks at a51dfff (pcb_rules_check 20/20 incl. spark gap, mutation tests); new paragraphs "C1 holes" (0.9 mm, fit 0.29 mm, ring 0.55 mm, substitute limits, drill counts, 133 holes) and "Knob clearance over C1"; end-cap wording (≈4.0 / ≥3.6 / ≈3.1 mm, lead-forming gauge); spark gap now enforced by check; new paragraph "Knob and shaft discharge into AGND" (R-011); BOM knob spec; status and safety statement.
- reports/report/sections/08_review.tex: the three "not re-reviewed independently" statements (T-073 fixes, re-review coverage, ADR-021 changes) replaced by references to T-079; new subsection "CR-002 final independent re-review (T-079)" with summary, findings/dispositions table F2-001..F2-007 and re-checks after T-080/T-081.
- reports/report/sections/09_limitations.tex: open risks, RV1 assumptions, process limitations (draft-9, T-079 review, a51dfff outputs 85/85, 20/20, 25/5 of 30); R-010 mitigation mentions the check; R-011 row.
- reports/report/sections/10_validation_plan.tex: V-28 now 0.9 mm holes and knob clearance; new V-29 (REQ-023 step 2b knob/shaft strike).
- reports/report/sections/11_reproducibility.tex, 12_change_history.tex: be9d1f2, e9309d8, a51dfff and (T-082) rows; a216c1b row annotated (C1 then at 0.8 mm); current state a51dfff, frozen-7, draft-9.
- reports/report/scripts/csv_to_table.py: evidence longer than 900 characters is split at sentence ends into full-width continuation rows (≤ 1800 characters each) so longtable can break between them; colon added as a break point in code spans. Verified lossless: joined chunks equal the CSV evidence for all 42 rows ("mismatches 0").
- reports/report/generated/requirements_table.tex (regenerated, REQ-023/REQ-029/REQ-032/REQ-006 text and CSV hash updated).
- reports/report/frutamidi_report.pdf, .aux, .log, .out, .toc (rebuilt).
- reports/figures/board-top-v1.2.png, board-copper-v1.2.png, board-3d-v1.2.png: refreshed from hardware/fabrication/images at a51dfff (C1 model scale changed in T-080); captions say "Render at a51dfff".
- README.md: knob note in the PCB v1.2 C1/pot bullet (plastic knob ≤ 15 mm covering the shaft, insulated shaft preferred, why).
- docs/manual/MANUAL.md: header cites a51dfff; C1 0.9 mm holes and substitute limits; new "Octave knob: plastic, at most 15 mm" bullet; two traceability rows (C1 drill, knob); frozen-6 → frozen-7 references.
- management/handoffs/documentation-engineer/T-082/: frutamidi_report.log, interface_check_T082.out.

## Checks performed (command · version · result line)
- `sh reports/report/build.sh` · pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026), TinyTeX-1 · "Wrote …requirements_table.tex with 42 rows; status counts: PASS 17, PARTIAL 18, FAIL 3, NOT RUN 4"; "Output written on frutamidi_report.pdf (42 pages, 764696 bytes)."; "LaTeX error lines: 0".
- Log (/usr/bin/grep -c): `^! ` 0; "undefined" 0; "Rerun to get" 0; "LaTeX Warning" 0; "Overfull" 0 (was 2 at HEAD, including "Overfull \vbox (720.14507pt too high)" from the REQ-023 row running off the page; first build of this task gave 1072 pt before the generator fix).
- PDF sha256 8600c8477109ffe7b1a0cda4a507075e658ace3e6c146e03aad9ecde65bc1bc6 (MEASUREMENT, shasum -a 256).
- Drill file count (awk over hardware/fabrication/gerbers/frutamidi.drl): T1 0.8 mm 11, T2 0.9 mm 11, T3 1.0 63, T4 1.1 28, T5 1.4 14, T6 1.8 2, T7 3.2 4 = 133 (MEASUREMENT of the export).
- `python3 sim/systems/interface_check.py` (Python 3.9.6, output to handoff folder, sim/ untouched): "SUMMARY documentation: 17 checks, 17 PASS, 0 FAIL", "SUMMARY: 85 checks, 85 PASS, 0 FAIL".
- Figures: sha256 of reports/figures/*-v1.2.png equal to hardware/fabrication/images at a51dfff: top 27c0f3f1…0205, copper 666f0a51…9e, 3d 1a5c6b85…b3b2.
- PDF pages not inspected visually (pdftoppm/pdftotext not installed); layout judged from the log only.

## Numerical findings (all copied from cited files)
- C1 drill 0.9 mm; fit 0.9 − 0.61 = 0.29 mm; ring (2.0 − 0.9)/2 = 0.55 mm; pad gap 3.08 mm (CALCULATION, calc_mechanical.out, T-080). C1 lead 0.48–0.61 mm (SOURCE EE-S29).
- Holes: 133 total; 0.8 mm 11, 0.9 mm 11 (MEASUREMENT of drill export).
- End caps: 4.00 mm centred, 3.61 mm at ±0.25 mm, 3.13 mm at ±0.5 mm vs 3.5 mm rule (CALCULATION on ASSUMPTIONs, check_gap.out (d)).
- Spark gap 1.400 mm on 12/12 pads, rule 1.40 ± 0.05 mm (MEASUREMENT, design file, pcb_rules_check.out); mutations 0.650 / −0.100 mm FAIL.
- Knob ≤ 15 mm; shaft to C1 7.77 mm; plan clearance 0.27 mm (CALCULATION from design file, T-080; sufficiency ASSUMPTION).
- Report 42 pages (MEASUREMENT, build log).

## Assumptions
- T-079 covered the T-073/T-074 fixes and the ADR-021 changes: based on findings.md (inputs at be9d1f2, "Dispositions C2-001…C2-013 verified", F2-001/F2-002 on ADR-021 items) and the task statement.
- The T-080/T-081 fixes are stated as reproduced by the manager, not independently re-reviewed (ADR-022 wording).

## Errors
- None blocking. Pre-existing layout defect found and fixed: the REQ-023 table row was taller than a page (Overfull \vbox 720 pt at HEAD), so part of its evidence ran off the page in the 39-page v1.2 PDF; fixed in csv_to_table.py.

## Open decisions for manager
1. metrics.json has no entries for c1_drill (0.9 mm), c1_fit (0.29 mm), drill_holes_total (133), spark_gap_check (1.400 mm) or knob_max_diameter (15 mm); the report cites calc_mechanical.out, pcb_rules_check.out, the drill export and T-080 instead. Add them if wanted (not in my write paths).
2. The generator change alters the requirements table layout (continuation rows for REQ-006, REQ-023, REQ-029, REQ-036). Accept or ask for another layout.
3. The PDF has not been checked by eye; a quick visual check of pages with the requirements table and Section 8.4 is advisable before the tag.

## Next actions
- Manager: review diff and commit; record the PDF sha256 in the V1.2 SHA256SUMS at release.
- No hardware claims added; REQ-023 (incl. V-29) and all V-rows remain NOT RUN.
