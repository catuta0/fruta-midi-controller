# T-105 — documentation-engineer

Status: PASS for the documentation checks and the report build (interface_check 121/121; LaTeX 0 errors, 0 undefined references, 0 overfull boxes). None of this is hardware validation: nothing was built, soldered or measured. Nothing committed.

Requirements addressed: REQ-036 (manual and root README match the T-103 board; the status change FAIL -> PASS is for the systems engineer); report content for REQ-023, REQ-025, REQ-027..REQ-032, REQ-040. Review findings F3-003, F3-006 (documentation part). ADR-028 D-2, D-3.

Inputs (path @ revision): branch change/CR-003 at f6693c9 (clean apart from .claude/ and CLAUDE.md, which I did not touch); hardware/README.md, management/handoffs/electronics-engineer-T-103.md, management/handoffs/systems-engineer-T-104.md, management/DECISIONS.md (ADR-023..ADR-028), reports/review/CR-003/findings.md, reports/electronics/analysis.md section 8, sim/systems/budgets.out, requirements/requirements.csv (draft-13), management/metrics.json, hardware/fabrication/images/board-top.png (sha256 1166150b...4bb54d21) and board-3d.png (sha256 489fc302...0aa3a5c).

Outputs:
- docs/manual/MANUAL.md:
  - header now names ADR-028 and f6693c9;
  - JP1 text: QT etched above pad 3; ORIG etched left of JP1 beside the pad 2-1 gap, meaning pad 1;
  - new bullets: supported boards (Pico SC0915 and Pico 2 only on the PCB); board trimming at the USB end; plug-seat and rocking checks before soldering the Pico; module mounting (strip against the module, pins cut to 3.0 mm, solder from outside with a fillet, top about 7 mm, ASSUMPTION);
  - post-solder checks (pads 36/39/40 not to GND; BTN not to pad 30);
  - troubleshooting JP1 wording; six new traceability rows.
- README.md: PCB rows for Pico W and Pico 2 W say "not supported on the v1.3 PCB"; a note under the table; the PCB summary bullet names the supported boards. Breadboard use unchanged.
- reports/report/sections/02b_pcb_v13_smd.tex (new Section 3, "PCB v1.3: single-sided SMD board (CR-003)"). It covers:
  - reasons; figures;
  - geometry table; check summary lines;
  - Mouser BOM and cost; supply and the R-016 alternative; resistor decision history;
  - the ESD table with labels, NOT PROVEN statements, plan B and its trigger, and the D1-D3 residual items;
  - the T-102 findings and dispositions table; the first-build list FB-1..FB-12;
  - draft-13 requirement table.
- Other report files:
  - frutamidi_report.tex: title/date v1.3, abstract, \input of the new section;
  - 01_introduction (v1.3 label, a reading note);
  - 02_requirements: draft-13 summary; the FAIL list is now REQ-018/036/040;
  - 03_architecture: v1.3 note, cost sentence, ADR-023..ADR-028 rows;
  - v1.3 notes in 04, 05, 08, 09 (and "draft-13"), 10;
  - 12_change_history: CR-003 rows and status paragraph.
- Regenerated: generated/requirements_table.tex (42 rows), PDF, aux/log/out/toc.
- reports/figures/board-top-v1.3.png and board-3d-v1.3.png, copies of hardware/fabrication/images.
- Evidence: management/handoffs/documentation-engineer/T-105/interface_check.out, latex_build.out, frutamidi_report.log.

Checks performed:
- `python3 sim/systems/interface_check.py` (Python 3.9.6), before the edits: `SUMMARY: 121 checks, 119 PASS, 2 FAIL`. The two FAILs were doc.manual.JP1_label_position and doc.root_readme.pcb_variants.
- The same check after the edits (exit 0):
  - `PASS  doc.manual.JP1_label_position`
  - `PASS  doc.root_readme.pcb_variants`
  - `SUMMARY hardware/firmware: 90 checks, 90 PASS, 0 FAIL`
  - `SUMMARY documentation: 31 checks, 31 PASS, 0 FAIL`
  - `SUMMARY: 121 checks, 121 PASS, 0 FAIL`
  - No regression.
- `"$HOME/bin/pcgate" chat2 sh -c 'sh reports/report/build.sh ...'` (TinyTeX pdfTeX 3.141592653-2.6-1.40.29, TeX Live 2026, three passes):
  - `Output written on frutamidi_report.pdf (54 pages, 945414 bytes).`
  - `LaTeX error lines: 0`
- Log scan: Overfull 0, Underfull 17, "undefined" 0, "LaTeX Warning" 0. The committed v1.2 baseline log had Overfull 0 and Underfull 17 (42 pages), so there is no regression.
- PDF sha256 54974288dbafb1d1730e4c8b57920dc451f2b60d07fe161c3122770316d96724.
- Pages 1, 17-26 rendered with PDFKit (scratch) and read. The new chapter is on pp. 17-24: figures, tables and labels are legible, and there are no clipped columns.

Numerical findings: none new. Every number is copied with its label from metrics.json, budgets.out, analysis.md section 8, requirements.csv, ADR-023..028 or the T-103/T-104 handoffs.

Assumptions: none of mine. The report repeats the project ASSUMPTIONS with their labels: header strip 2.5 mm, pin 3.0 mm, module board 1.6 mm, cut tolerance 1.0 mm, ±4 kV target, 1.33 A pin limit, 100 N screw limit, VAT 23 %, and the 3234-3366 ohm window.

Errors:
- One interface_check run at the start wrote its output to /tmp. I deleted the file at once; later runs used the scratchpad and the handoff folder.
- The first build left the figures and the 3.2 heading badly placed, and the sources paragraph gave 3 new underfull boxes. I fixed both: one two-panel figure, and the sources as a list.

Open decisions for the manager:
1. REQ-036: both failing checks now PASS. Systems should re-run interface_check and set the status (the report shows draft-13 FAIL with this note).
2. Label inconsistencies, which I reported and did not edit:
   - metrics.json `v1.3_plan_b_window` is labelled SIMULATION. REQ-023 and ADR-027 call it an ASSUMPTION window; the report uses ASSUMPTION.
   - SDA coupling 2.09 counts / 36.6 fF is SIMULATION in analysis.md section 8.5 and the T-103 handoff, but CALCULATION in metrics.json and T-104; the report uses SIMULATION, citing analysis.md.
3. hardware/README.md says "One board costs about 13.84 EUR" (Mouser lines only). The core BOM is 14.84-16.84 EUR (copper clad included). Both are correct but differently scoped; the report shows both.
4. reports/review/CR-003/findings.md "Dispositions (manager)" is still "To be filled". The report takes its dispositions from ADR-028 and the handoffs (F3-002 and F3-009 PARTIAL).

Next actions: systems re-runs interface_check and updates REQ-036; the CR-003 re-review (ADR-028 D-8), then the frozen-9 freeze; the manager commits.

Locks: management/locks/{root-readme,manual,report}-t105.lock taken and released.
