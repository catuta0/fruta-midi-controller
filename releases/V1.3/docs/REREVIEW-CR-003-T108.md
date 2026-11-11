# CR-003 independent re-review (T-108): findings

Reviewer: independent-reviewer (did not see the work), 2026-11-11. Inputs: change/CR-003 at f0c016b. Recorded by the manager from the reviewer's hand-back; raw outputs in T-108/raw/ (scripts, clear.out, segs.out, dump.out, erc.rpt, drc.rpt).

Verdict: ready for the first build after fixes. No critical findings. The design files do not need to change; the findings are in the assembly instructions and labels. Status: PARTIAL (design-file review complete; everything physical NOT RUN [PHYSICAL]).

Reviewer's own checks: ERC 0, DRC 0 / 0 unconnected / 0 parity (kicad-cli 10.0.4 via pcgate chat2, on a git archive of f0c016b). Own parser: smallest net-to-net gap 0.680 mm, tracks 0.8/1.0/1.2 mm, no vias, edge 0.680 mm (0.605 mm to the etched outline line); A2 lands 1.730/1.775 mm beyond the outline; Pico end 0.11 mm inside, USB face 1.19 mm beyond; 12 Pico 2 underside features >= 2.14 mm from copper; spark gap 1.40 mm; R1-R12 termination gap >= 4.65 mm; transfer PDF 1:1 and mirrored; BOM matches README; nothing claims hardware validation (all CALCULATION from the design file unless stated).

| ID | Sev. | Location | Finding | Suggested fix |
| --- | --- | --- | --- | --- |
| F4-001 | major | hardware/README.md section 4 step 6; root README line 16; MANUAL.md line 44; RISKS R-013 | The epoxy bead "along the end of the Pico at the USB connector" has no board to bond to (Pico end 0.11 mm inside the edge, CALCULATION) and would hang into the 1.19 mm where the plug overmould seats. Step 6 also says "module" for the Pico (F3-013 recurred). | Bead on the two long sides at pins 1-3 and 38-40, off the end face; no epoxy beyond the board edge; re-check the plug seat after curing. Update R-013 and the manual. |
| F4-002 | minor | hardware/README.md section 6 line 188 | Says pads 39 and 40 are 0.94 mm from GND pad 38; only 39 is (40 is 3.48 mm, CALCULATION). Pad 37 (3V3_EN) to 38 (GND), 0.94 mm, is not checked; a bridge turns the regulator off. | Correct the sentence; add "37 to 38 must not beep" and a troubleshooting line. |
| F4-003 | minor | ORIG copper text; README section 5; MANUAL line 47 | About 98 % of the etched ORIG lies under the module outline (MEASUREMENT on a 300 dpi render of the transfer PDF; outline CALCULATION), and JP1 is bridged in step 8 after the module goes on in step 7. | Say ORIG is hidden once the module is fitted and rely on the pad position, or set JP1 before step 7; move the label at the next copper change. |
| F4-004 | minor | A2 S row; README step 7 | S-row pin centres are 2.54 mm inside the module outline (electrode row 1.27 mm, CALCULATION); the 7 S joints are reachable but only visible from a low angle. | Say so; add a continuity check from each S pad to its module-top pin. |
| F4-005 | minor | README BOM RV1; MANUAL | PTV09A-4015F has no bushing; "mount it in your enclosure" gives no method. | Describe a mounting method or name a bushed variant. |
| F4-006 | minor | root README line 15; hardware README "Rework" | "Soldered flat" is wrong for the module (underside about 5.5 mm up, ASSUMPTION). | "The module stands on its header pins." |
| F4-007 | info | check_smd.out header; report REQ-029 evidence; analysis 7.3/8.4; MANUAL line 194 | Geometry read from the design file is labelled MEASUREMENT. | Relabel CALCULATION (design file). |
| F4-008 | info | gen_pcb.py comment near line 372; analysis.md line 175 | Stale "module end y 0.63". | Update or mark as history. |
| F4-009 | info | README design-rule table | The 0.8 mm S2-S6 stubs lie inside the S-row lands and J3 pads; no 0.8 mm copper is exposed. | Optional note. |
| F4-010 | info | README A1 "The Pico 2 also fits" | USB overhang 1.30 mm is sourced for the Pico only. | Make the plug-seat check explicit for the Pico 2, or cite its drawing. |

Could not check: the S-row pin order and offsets of both module versions (Adafruit Eagle files not on disk); Pico 2 USB overhang; tenting of Pico/Pico 2 underside vias; Mouser stock (no network); a bushed PTV09A variant; regeneration (geometry identical in T-102); anything physical.

## Dispositions (manager)

All ten accepted; documentation and labels only, no copper change (ADR-029).

- F4-001: side beads at pins 1-3 and 38-40, nothing on the end face or beyond the edge, plug-seat re-check after curing (ADR-029 D-1).
- F4-003: JP1 is set before the module is fitted (step order changed); text relies on the pad position and says ORIG is hidden by the module; label move deferred to the next copper change (ADR-029 D-2).
- F4-005: describe a mounting method for the bushless pot (ADR-029 D-3).
- F4-002, F4-004, F4-006..F4-010: as suggested.
