# FrutaMIDI V1.2 (v1.2.0)

Immutable release produced by change request CR-002 (docs/CR-002.md) on top of V1_BASELINE (v1.1.0-baseline). Do not edit files in this folder; later work goes to a new release folder through the change process.

| File | Content |
|---|---|
| FrutaMIDI-report.pdf | Engineering report v1.2 (42 pages): requirements and verification status, architecture and decisions, interfaces (frozen-7), analyses (ESD flashover, pulse rating, C1/AGND), review findings (CR-002 re-review T-071, manager PCB review, final re-review T-079), risks, physical validation plan V-01…V-29, change history |
| REQUIREMENT_STATUS.md | Status of all 42 requirements |
| FrutaMIDI-fabrication.zip | PCB v1.2: copper transfer PDFs (1:1), assembly map, schematic PDF, Gerbers, drill (133 holes), BOM, renders |
| firmware/ | UF2 files for Pico, Pico W, Pico 2, Pico 2 W (breadboard and `pcb-` variants), Leonardo HEX, build log. Firmware source unchanged since V1_BASELINE; rebuilt for this release, same sizes |
| docs/ | User manual, assembly guide (hardware/README.md), README, CR-002, re-review findings T-071 and T-079 with dispositions |
| REPRODUCE.md | How to rebuild and re-check everything |
| SHA256SUMS | Checksums of every other file in this folder |

## What changed since V1_BASELINE (summary; details in report §12)
- Electrode resistors R1–R12: Vishay MBE04140C3301FC100 (DIN0414, 3k3 1 %, pulse rating 4.08 kV at 3k3, SOURCE EE-S17b), lying flat at 15.24 mm pitch; copper gap across each resistor 13.04 mm (MEASUREMENT on design file) against the 3.5 mm rule at 4 kV (CALCULATION). Fixes the v1.1 flashover across R (0.94 mm pad gap).
- JP1 pitch 3.81 mm; J2 oval pads 3.0 × 4.5 mm; RV1 tabs on AGND; C1 100 nF wiper filter (drill 0.9 mm); H3 moved; Ex ↔ GND 1.40 mm spark gap enforced by a check; silkscreen and schematic relaid (A3); sockets as part fields; board label "FrutaMIDI v1.2".

## Status
Designed, analysed, reviewed and host-tested. **Not built or tested on real hardware.** ERC/DRC passing, analyses and host tests are not hardware validation.
- Checks at release: ERC 0; DRC 0 violations / 0 unconnected / 0 parity; interface_check 85/85; pcb_rules_check 20/20; budgets 30 checks, 25 PASS, 5 FAIL; firmware host tests 295 passed; host/sampler tests 102 passed; 9/9 firmware builds (MEASUREMENT, macOS host).
- Requirements: 17 PASS, 18 PARTIAL, 3 FAIL, 4 NOT RUN. Open FAILs: REQ-018 (VBUS on USB low-power ports), REQ-032 (core BOM 23.98–38.62 EUR vs 30 EUR, cost increase accepted in ADR-019 D-3 and ADR-021), REQ-040 (wrong JP1 position exceeds the module's absolute maximum; accepted risk).
- ESD scope ±4 kV (ADR-019 D-1); 8 kV deferred (R-006). End caps 4 kV PARTIAL (≥ 3.6 mm only with leads formed within ±0.25 mm). Open risks include R-009 (end caps), R-010 (GND spark gap / GP26–27 rating), R-011 (knob/shaft path into AGND: use a plastic knob ≤ 15 mm on an insulated shaft).
