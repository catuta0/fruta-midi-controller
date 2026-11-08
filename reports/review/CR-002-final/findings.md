# CR-002 final independent re-review (T-079): findings

Reviewer: independent-reviewer, inputs at be9d1f2 (branch change/CR-002). The harness refused the reviewer's write; the manager recorded the hand-back content without changing its substance. Raw outputs in this folder. Nothing here is a hardware measurement.

**Verdict: release-ready yes** (design-file release v1.2; no critical or major findings; F2-001…F2-004 minor, to fix or record before the tag).

Checks reproduced: ERC 0; DRC 0 / unconnected 0 / parity 0; generators reproduce the committed design (sch 0 diff lines, PCB 179/179 blocks, identical geometry); B.Cu gerber and drill match the PCB (133 holes); interface_check 85/85, pcb_rules_check 19/19, budgets 30/25/5 and 11 electronics calc scripts byte-identical; C1 RC recomputed: τ 0.380 ms, settle 2.89 ms vs POT_READ_MS 30 ms, margin 10.4× (CALCULATION); report PDF 39 pages sha256 e6686b04…f0db. Dispositions C2-001…C2-013 verified (C2-002 residual wording → F2-004).

| ID | Sev. | Finding | Suggested fix |
|---|---|---|---|
| F2-001 | minor | C1 lead D = 0.48–0.61 mm (SOURCE EE-S29 tolerance); 0.8 mm drill leaves 0.19 mm at max lead, below the 0.2 mm fit rule; calc_mechanical uses the nominal lead. | Drill 0.9 mm or record PARTIAL. |
| F2-002 | minor | RV1 frame (and a metal shaft) on AGND gives a knob/shaft discharge a direct path into Pico pin 33 / analog ground; no analysis, risk or test; shaft material not fixed in BOM. | Risk/analysis entry, knob/shaft strike in the REQ-023 test, specify insulated shaft or plastic knob. |
| F2-003 | minor | REQ-032 says the C1 cost is "not yet covered by an acceptance" while the ADR-021 addendum accepts it; report contradicts itself. | Update REQ-032 evidence; rebuild report. |
| F2-004 | minor | README says end caps "at least 4 mm apart"; at the allowed ±0.25 mm the worst is 3.61 mm (3.13 mm at ±0.5 mm). | Reword with check_gap (d). |
| F2-005 | info | C1 up to 6.6 mm tall, 7.8 mm from the shaft: knobs wider than ≈15.5 mm overhang C1; substitute body size unqualified. | Knob limit ≤ 15 mm; body limit for substitutes. |
| F2-006 | info | No pass/fail check enforces the 1.40 mm Ex↔GND spark gap (a flipped J2 offset gives 0.65 mm and still passes DRC). | Add a check. |
| F2-007 | info | analysis.md §6 typo "R16 moved above R16"; C1 3D model 5.00 mm pitch. | Cosmetic. |

Requirement cross-check: REQ-006 PARTIAL; REQ-023 PARTIAL; REQ-027/028/029 PASS; REQ-032 FAIL; REQ-036 PASS.
Not covered: hardware, ESD, peel-strength, knob fit; RK09K and current KEMET TA datasheets not opened.

## Dispositions (manager)
All F2 items are to be fixed before the tag (T-080 electronics: F2-001, F2-004, F2-005, F2-007; T-081 systems: F2-002 risk/test, F2-003, F2-006; documentation rebuild afterwards).
