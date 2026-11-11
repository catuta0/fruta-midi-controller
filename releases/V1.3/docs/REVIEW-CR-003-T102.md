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
Fixes: T-103 electronics, T-104 systems, T-105 documentation; decisions ADR-028. Commit f6693c9 plus the T-105 documentation.

| ID | Disposition | Evidence |
| --- | --- | --- |
| F3-001 | FIXED (design files): option (a) on all 20 pins, header strip against the module, lands 1.73-1.78 mm beyond the module outline (CALCULATION); strip and pin lengths are ASSUMPTION, first-build measurement. | check_smd "land beyond body" PASS, mutation M1 FAIL as expected |
| F3-002 | PARTIAL, accepted (ADR-028 D-1): Pico end 0.11 mm short of flush, USB face 1.19 mm beyond the edge; flush would put VBUS 0.495 mm from the outline. Cut oversize and trim; plug-seat check. | check_smd USB face PASS (1.0 mm tolerance ASSUMPTION), mutation M2 |
| F3-003 | FIXED: TP7 and all 11 Pico 2 underside features kept out (worst 2.14 mm); PCB scoped to Pico SC0915 and Pico 2; Pico W / Pico 2 W not supported (ADR-028 D-3). | check_smd, mutation M3; interface_check doc.root_readme.pcb_variants PASS |
| F3-004 | FIXED: analysis.md section 8 for RC2512FK-073K3L (pulse NOT PROVEN); 7.1/7.2 superseded; README link fixed. | analysis.md |
| F3-005 | FIXED: charge 3.0x and duration 3.6x stated beside the margin (README, analysis 8.3, REQ-023). | |
| F3-006 | FIXED in text (ADR-028 D-2): README and manual describe the real ORIG position; copper unchanged (0.49 mm room below pad 1). | interface_check doc.manual.JP1_label_position PASS |
| F3-007 | FIXED: post-solder continuity checks in README and manual. | |
| F3-008 | FIXED: pin-1 mark level with pin 1, square in pad 1 on the assembly map. | render/ |
| F3-009 | FIXED: records reconciled (REQ-027/029/030, INTERFACES status note, ADR-028 D-6 for the stock date); INTERFACES frozen-9 freeze after re-review (D-8). | interface_check 121/121 |
| F3-010 | FIXED: J1-J3, JP1 copper-only, excluded; knob in README only; SW1 genuine (ARATAS, formerly Omron Components). | budgets C2 PASS |
| F3-011..F3-013 | FIXED: README text. | |
| F3-014 | FIXED: 1206 lands >= 1.05 mm beyond the body (CALCULATION, C1 body ASSUMPTION). | check_smd, mutation M4 |
| F3-015 | ACCEPTED, no action. | |

Side effects accepted for the first build (ADR-028 D-7): GND bounce 330 V for about 1 ns, SDA coupling 2.09 counts, 35.6 N screw load; all on ASSUMPTION inputs, NOT RUN [PHYSICAL].
