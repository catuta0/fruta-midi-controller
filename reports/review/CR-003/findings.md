# CR-003 independent review (T-102): findings

Reviewer: independent-reviewer, inputs at 9505245 read through git archive. The harness refused the reviewer's write; the manager recorded the hand-back content without changing its substance. Raw outputs: reports/review/CR-003/raw/. Nothing here is a hardware measurement.

**Verdict: not ready for the first home-etched build.** F3-001 blocks; F3-002 and F3-003 must be fixed or scoped first. A copper-only trial etch can go ahead now (module pad gaps 0.74 mm, Pico pad gaps 0.94 mm, spark gap 1.40 mm).

Reproduced on the archived copy (KiCad 10.0.4, via pcgate chat2): ERC 0; DRC 0 violations / 0 unconnected / 0 parity / 0 footprint errors; pcb_rules_check 25/25, interface_check 115 checks 113 PASS 2 FAIL, budgets 31/27/4 (all identical to committed); electronics run_all 18 of 19 outputs identical (check_smd.out differs only in print order). Transfer PDF mirrored and 100.00 x 70.00 mm at 1:1; assembly map not mirrored (both correct). Pico land and keep-outs re-derived from RP-008307 Figure 5; B3S-1000 land checked against Omron. Regeneration is geometrically identical (311 lines, 0 differences).

| ID | Sev. | Finding | Suggested fix |
|---|---|---|---|
| F3-001 | critical | A2 lands lie entirely under the header strip and the module outline (0.00 mm outside both, CALCULATION, raw/review_geometry.out); the README joint "with a fillet around the pin" cannot be reached or inspected; 20 joints carry GND, VIN/VCC, SDA, SCL and all electrodes. | Lengthen lands >= 1.5-2 mm outside the module outline with longer pins; or a documented pre-tin and reflow method with continuity checks; or another mounting. |
| F3-002 | major | USB receptacle face only 0.67 mm beyond the board edge (SOURCE RP-008307 via T-090, CALCULATION); hand cutting and transfer alignment about ±0.5 mm each (ASSUMPTION) can consume it. | Cut oversize, etch, trim to the outline; plug-seat check before soldering; optionally move A1 0.63 mm so the Pico edge is flush. |
| F3-003 | major | Keep-outs come from the Pico datasheet only; Pico 2 TP7 (1V1) at (11.5, 30.5) mm is outside both keep-outs (clear by 3.66 mm today, not DRC-protected); Pico W / Pico 2 W never checked, yet the README says they fit. | Add all variants' underside features to the keep-outs, or scope the README to Pico and Pico 2 and recommend SC0915. |
| F3-004 | major | reports/electronics/analysis.md section 7, linked from the README safety text, still describes HPWC2512 3k0 with "Pulse rating PASS 4 kV"; RC2512 appears 0 times. | Add an RC2512FK-073K3L section; mark 7.2 superseded; fix the link. |
| F3-005 | minor | Pin-current margin 1.20-1.22 compares peak current only: 600 nC vs 200 nC HBM (3.0x) and 0.54 us vs 0.15 us (CALCULATION). | State charge and duration ratios beside the margin. |
| F3-006 | minor | Etched ORIG label is left of JP1 between pads 2 and 1 (y 12.30-14.10 mm), not "below" as the README says. | Fix text or move the label below pad 1. |
| F3-007 | minor | SW1 BTN pad 1.07 mm from unused A1 pin 30 (RUN); VSYS/VBUS lands 0.94 mm from pin 38 GND on bare copper; no post-solder short checks. | Continuity checks: pins 36, 39, 40 not to GND; BTN not to pin 30. |
| F3-008 | minor | Pin-1 mark on the assembly map is level with pin 2; the promised square marking is not implemented. | Fix the mark. |
| F3-009 | minor | Records disagree: REQ-032 PARTIAL vs ADR-027 PASS; REQ-027/029 cite 24 checks and 0.650 mm (now 25 and 0.720 mm); REQ-030 says the definition amendment is open (done); INTERFACES frozen_by "pending" and status_note frozen-6; stock date 2026-11-09 in ADR-026 vs 2026-11-11 elsewhere. | Reconcile. |
| F3-010 | minor | J1 is a BOM line without MPN while J2, J3, JP1 are excluded; knob in budget but not in KiCad BOM; SW1 maker shown as "Aratas" on the Mouser listing. | Make consistent; confirm the SW1 maker. |
| F3-011 | info | README does not say which way electrode wires leave J2 or how much to strip; a wire towards the edge crosses the spark gap. | Add. |
| F3-012 | info | Solder pooled at the Pico USB shell pins can stop it sitting flat. | Check for rocking before tacking. |
| F3-013 | info | README lines 204 and 223 say "module" for the Pico. | Fix. |
| F3-014 | info | 1206 lands extend only 0.43 mm beyond the body (CALCULATION); tight for an iron. | Lengthen if room. |
| F3-015 | info | Regeneration not byte-identical (random UUIDs); geometry identical. | None. |

Proposed new checks: every hand-soldered land has >= 1.0 mm of copper outside the body and strip outline; the USB receptacle face clears the board edge by at least the stated cutting tolerance.

Requirement cross-check: REQ-023 PARTIAL (agree); REQ-025 PARTIAL with reservation (F3-001); REQ-027 PASS on design file (stale text); REQ-028 PASS; REQ-029 PASS for stated rules (not solder access or edge tolerance); REQ-030 PASS; REQ-031 PASS; REQ-032 reconcile; REQ-036 FAIL at 9505245 (agree); REQ-039/040 agree; REQ-024 PASS.
Not run: mutation tests (result seen, not re-run); Eagle files and Pico W / Pico 2 W data (offline); YAGEO RC2512 PDF; anything physical.

## Dispositions (manager)
To be filled after the fixes (T-103 electronics, T-104 systems, T-105 documentation).
