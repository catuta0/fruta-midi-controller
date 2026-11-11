# T-101 — documentation-engineer
Status: PASS (documentation consistency only; no hardware result exists or is claimed)

Requirements addressed: REQ-036 (manual and root README match the v1.3 PCB, evidence for systems to update the status); REQ-031 (firmware, flashing and pin-map content kept unchanged); REQ-023 (ESD status described in plain words, no status change).

Inputs (path @ revision 9505245, branch change/CR-003, working tree dirty only in .claude/ and CLAUDE.md before this task):
- changes/CR-003.md; management/DECISIONS.md ADR-020, ADR-023 to ADR-027
- hardware/README.md (v1.3 assembly guide, read-only); hardware/fabrication/bom-kicad.csv (via interface_check `fab.bom_matches_board`); hardware/scripts/gen_pcb.py (board label)
- management/REQUIREMENTS.md draft-12 (REQ-023, REQ-031, REQ-036); management/RISKS.md R-011, R-016, R-018; management/metrics.json (`ex_gnd_spark_gap`, `jp1_pad_gap`); management/INTERFACES.json frozen-8 (frozen)
- sim/systems/budgets.out (13.84 EUR line); reports/electronics/analysis.md §7.3; handoffs electronics-engineer-T-096, systems-engineer-T-099
- firmware/FrutaMIDI/*.ino, fm_*.h (sha256 re-checked)

Outputs (uncommitted):
- docs/manual/MANUAL.md: header now v1.3 (CR-003, ADR-023..027, 9505245, REQ-031 unchanged); section "PCB v1.2" replaced by "PCB v1.3: what to know before you build" (SMD single layer, 4 M3 holes, Mouser cost, R1-R12 RC2512FK-073K3L, assembly order with tests before the Pico/module, surface-soldered Pico and module with no sockets and harder rework, flash first, epoxy bead at the USB end and strain-relieved cable, H4, J2 solder-wire pads with hot-melt and the open spark gap, off-board RV1 PTV09A with insulated shaft and plastic knob, knob bore fit NOT CONFIRMED, JP1 SMD solder bridge, J1 wire links table, optional neutral-cure silicone never acetic-cure, ESD status: 4 kV pulse capability NOT PROVEN (ADR-026), plan B clamp diodes + 1 kOhm if the physical test shows damage (ADR-027 D-2), pre-power checklist link); a short History paragraph for V1.2 and earlier; contents, Setup and Troubleshooting links/wording updated (S holes -> S pads, terminal -> J2 electrode pad); traceability rows for v1.2 parts replaced by 21 v1.3 rows with labels and evidence. Playing, Scales, Octave, Recalibration, LED and firmware traceability unchanged.
- README.md: PCB bullet rewritten for v1.3 (SMD, one layer, 4 optional holes, 13.84 EUR, no sockets, epoxy/cable, hot-melt wires, off-board insulated-shaft pot, JP1 bridge and J1 links, ESD NOT PROVEN); BOM row for the 3.3 kOhm resistors points to RC2512FK-073K3L; Safety paragraph rewritten (target is an ASSUMPTION, survival NOT PROVEN, plan B, nothing tested, no 8 kV, insulated pot shaft). Breadboard, firmware, flashing, sampler and pin tables unchanged.
- management/handoffs/documentation-engineer/T-101/interface_check.out (raw output), link_check.out (raw output).

Checks performed:
- `python3 sim/systems/interface_check.py` · Python 3.9.6 · exit 0 · `SUMMARY: 115 checks, 115 PASS, 0 FAIL`; `SUMMARY documentation: 26 checks, 26 PASS, 0 FAIL`; `PASS  doc.manual.matches_v1.3 :: docs/manual/MANUAL.md: 'version 1.2' present: False; stale v1.2 terms: []`; `PASS  doc.root_readme.matches_v1.3 :: README.md stale PCB terms: []`. Run read-only: `git status --porcelain sim/` identical before and after (the script writes no file; output saved by redirect into my handoff folder).
- First run: `FAIL  doc.manual.matches_v1.3 ... stale v1.2 terms: ['screw terminals']` from my negative sentence "no screw terminals". Rephrased to "no terminal blocks" (same meaning). The check was not edited.
- Relative links and GitHub anchors of MANUAL.md and README.md (own script, Python 3.9.6): `LINKS: 63 relative links, 0 broken` (interface_check does not check the manual's links).
- `shasum -a 256 firmware/FrutaMIDI/FrutaMIDI.ino fm_*.h`: the 9 hashes listed in the manual still match; `git log -- firmware/FrutaMIDI` last commit a208a30.
- Non-ASCII characters in the two files: only § ± ² · × Ω – — … € → ↔ − ⌊ ⌋.

Numerical findings (all cited, none new):
- One-board parts cost 13.84 EUR, Mouser Portugal 2026-11-11, ex shipping and tax: CALCULATION (sim/systems/budgets.out, T-096).
- R1-R12 3.3 kOhm ±1 %, 2512: SOURCE (BOM, ADR-026). Continuity window 3267–3333 Ohm: CALCULATION (hardware/README.md section 6).
- ESD target ±4 kV: ASSUMPTION (REQ-023). Pulse capability: NOT PROVEN (ADR-026). ESD test: NOT RUN.
- Plan-B trigger 3234–3366 Ohm: ASSUMPTION window (ADR-027 D-2, R-018).
- Spark gap 1.40 mm: MEASUREMENT on the design file (metrics `ex_gnd_spark_gap`); cited in traceability only.
- JP1 3.81 mm pitch, 1.87 mm gap: MEASUREMENT on the design file (metrics `jp1_pad_gap`).
- Configuration wires about 25–35 mm: SOURCE hardware/README.md section 5 (CALCULATION from layout, T-060).
- R1-R12 stock 13 for 12: SOURCE Mouser listing (R-016).

Assumptions: none new. The readability of the steps is not verified; no step was tried on hardware.

Errors: one interface_check FAIL on the first run (above), fixed by rewording.

Open decisions for the manager:
1. The stale-term checks are plain substring tests and also catch negations ("no screw terminals"). I reworded rather than weaken; the check may deserve a negation exception like `doc.hw_readme.no_sockets` (systems owns it).
2. management/metrics.json has no v1.3 entries (13.84 EUR, 14.84–16.84 EUR core, RC2512 gaps, plan-B window). The numbers I used come from cited reports and handoffs; systems may want to record them in metrics.json before the LaTeX report.
3. REQ-036 can move from FAIL to PASS on inspection (systems' call), still without hardware validation.
4. Root README intro still says the breadboard build "costs about 25 €" and the breadboard BOM 23–31 €; unchanged (breadboard, not part of CR-003).

Next actions: systems re-runs interface_check and updates REQ-036; independent review of the changed docs; LaTeX report in a later task.
