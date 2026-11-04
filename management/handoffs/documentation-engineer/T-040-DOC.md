# T-040-DOC — documentation-engineer
Status: PASS. The report is re-synced to requirements draft-5, budgets revision 5, interfaces frozen-2, ADR-013..017, the BOM part numbers and the T-044 firmware results. It builds with 0 errors.

## Inputs (@ 05a06a3)
- **Requirements:** management/REQUIREMENTS.md draft-5 (T-013) and requirements/requirements.csv (42 rows).
- **Budgets:** reports/systems/budgets.md revision 5, which says "24 PASS, 5 FAIL".
- **Interfaces:** management/INTERFACES.json, revision "frozen-2 (documentation-only CR from T-012, ADR-016)", frozen_on 2026-11-04.
- **Decisions:** management/DECISIONS.md, ADR-013..017.
- **BOM:** hardware/fabrication/bom-kicad.csv.
- **Review:** reports/review/72f67f0/findings.md. 16 finding rows, counted by script: 3 major, 9 minor, 4 info, 0 critical.
- **Firmware:** management/handoffs/firmware-engineer/T-044.md.

## Changes (reports/report/sections/)
- **03_architecture (sha256 5bc605db…a97):**
  - Decision table extended with ADR-014 (review dispositions), ADR-015 (BOM part numbers), ADR-016 (REQ-018 deviation, frozen-2) and ADR-017 (firmware review fixes).
  - Range stated as ADR-000 to ADR-017.
- **04_interfaces (592bd729…f812):**
  - Revision is now frozen-2 (frozen-1 + ADR-016 change, 2026-11-04).
  - IF-CONTROLS: pot zone 0.66 V, dead band 0.132 V, error budget 0.0364 V (CALCULATION).
  - IF-PICO-PINS: AGND note (SOURCE S-01 §2.1).
- **05_electronics (8af07889…b8e2):**
  - New BOM subsection with the part numbers from bom-kicad.csv and ADR-015, and the core BOM 20.42–30.40 EUR, FAIL (REQ-032).
  - Variant table columns are now wrapping columns; this fixes 87.6 pt overflow caused by the longer F-002 verdict.
- **06_firmware (3c26388a…0b53):**
  - New latency-budget subsection, from budgets revision 5 (CALCULATION, C ≤ 100 pF, 400 kHz):
    - worst case 10.72 ms (1 sensor) and 12.35 ms (2 sensors)
    - jitter 6.72 ms and 8.35 ms
    - PASS against 15 ms / 10 ms
  - A re-touch within the 15 ms lockout reaches up to 25.72 ms, noted against the REQ-014 idle-pad condition.
  - The 100 kHz failures are noted.
  - The T-044 row (295 tests, 10/10 mutants, 9/9 builds) is moved to the end of the test table.
- **08_review (71bd0480…efd):** "Review of 72f67f0 (task T-060): 16 findings (0 critical, 3 major, 9 minor, 4 info). Dispositions in reports/review/72f67f0/findings.md; ADR-014 records 13 FIX, 1 ACCEPTED and 2 info FIX. Re-review pending." A `\tbf` placeholder remains for the per-finding table.
- **09_limitations (232361f8…f50):** requirements are draft-5; REQ-018 is noted as a documented deviation (ADR-016).
- **10_validation_plan (993ae81f…dc4):**
  - V-18 now covers a sensor lost during play (REQ-009 draft-5).
  - New V-22 for shared notes (REQ-042).
- **02_requirements:** already at draft-5 since T-039. Unchanged.

## Checks
- `sh reports/report/build.sh` (3 passes):
  - "Wrote …/requirements_table.tex with 42 rows; status counts: PASS 17, PARTIAL 18, FAIL 3, NOT RUN 4"
  - **"Output written on frutamidi_report.pdf (20 pages, 480274 bytes)."**
  - "LaTeX error lines: 0"
- Log counts: "Rerun to get" 0; undefined 0; overfull 1 (the known 13.7 pt code token in the generated table).
- PDF sha256 0c219337dff317e3ae8e5f664c08e102ed361d75c1fce276670e1a07aba9bf00
- Stale-value grep over sections/: no remaining matches for draft-3, "frozen-1 (", the old latency figures (10.59, 6.59, 12.07, 8.07, 10.30, 6.30, 11.50), "PARTIAL 17", "41 req" or "FAIL 2".
- Log: management/handoffs/documentation-engineer/T-040-DOC_build.out

## Numbers
- No new numbers. Every value is copied from the inputs above, with its label.

## Errors
- The variant-table overflow appeared after the first build and was fixed. No other errors.

## Open decisions for manager
- None. §8 still needs the per-finding table and the re-review result when available.

## Next actions
- Fill §8 after the re-review.
- Add the release checksums in §11 once releases/V1_BASELINE/ exists.
