# FrutaMIDI V1.3 (v1.3.0)

Immutable release produced by change request CR-003 (docs/CR-003.md) on top of V1.2 (v1.2.0). Do not edit files in this folder; later work goes to a new release folder through the change process.

| File | Content |
|---|---|
| FrutaMIDI-report.pdf | Engineering report v1.3 (56 pages): requirements and verification status, architecture and decisions (ADR-023..029), interfaces (frozen-9), the SMD conversion (section 3), ESD analysis, review T-102 and re-review T-108 with dispositions, first-build measurement list, risks, change history |
| REQUIREMENT_STATUS.md | Status of all 42 requirements (draft-16) |
| FrutaMIDI-fabrication.zip | PCB v1.3: mirrored copper transfer PDF (1:1), negative, assembly map, schematic PDF, Gerbers, drill (4 M3 holes), BOM, renders |
| firmware/ | UF2 files for Pico, Pico W, Pico 2, Pico 2 W (breadboard), `pcb-` UF2 for Pico and Pico 2 only, Leonardo HEX, build log. Firmware source unchanged since V1.2; rebuilt for this release, same sizes |
| docs/ | User manual, assembly guide (hardware/README.md), README, CR-003, review findings T-102 and re-review T-108 with dispositions, purchase list (Mouser) |
| REPRODUCE.md | How to rebuild and re-check everything |
| SHA256SUMS | Checksums of every other file in this folder |

## What changed since V1.2 (summary; details in report section 3 and section 12)
- Board converted to surface mount for home chemical etching (toner transfer): one copper layer on the component side, no vias, tracks >= 1.0 mm (0.8 mm stubs inside pads only), clearance >= 0.6 mm (smallest 0.680 mm, CALCULATION, design file), 4 M3 holes instead of 133 drilled holes.
- Pico soldered flat by its castellated edge; Pico (SC0915) and Pico 2 supported on the PCB; Pico W and Pico 2 W are not (underside not checked).
- MPR121 module (Adafruit 1982) on its header pins with the plastic strip against the module; lands extend 1.73-1.78 mm outside the module outline for soldering from outside (CALCULATION, design file).
- R1-R12: YAGEO RC2512FK-073K3L 3k3 1 % 2512 on a 5.0 mm land gap; termination gap >= 4.65 mm against the 3.5 mm rule at 4 kV (CALCULATION). Pulse capability at 4 kV NOT PROVEN (ADR-026); plan B defined (ADR-027 D-2).
- Off-board potentiometer, wire pads for electrodes and configuration, all parts from Mouser: core BOM 14.84-16.84 EUR excluding VAT and shipping (CALCULATION from SOURCE prices, 2026-11-11).

## Status
Designed, analysed, reviewed and host-tested. **Not built or tested on real hardware.** ERC/DRC passing, analyses and host tests are not hardware validation.
- Checks at release (MEASUREMENT of the check outputs, macOS host): ERC 0; DRC 0 violations / 0 unconnected / 0 parity; check_smd 65/65; interface_check 125/125; pcb_rules_check 26/26; budgets 35 checks, 31 PASS, 4 FAIL (A3b VBUS on low-power ports; three latency rows at 100 kHz I2C); mutations 86 proved; firmware host tests 295 passed; host/sampler tests 102 passed; 9/9 firmware builds, 7 shipped.
- Requirements: 18 PASS, 18 PARTIAL, 2 FAIL, 4 NOT RUN. Open FAILs: REQ-018 (VBUS on USB low-power ports), REQ-040 (wrong JP1 position exceeds the module's absolute maximum; accepted risk).
- ESD scope +/-4 kV; 8 kV deferred. Open risks include R-010 (GND bounce 330 V for about 1 ns, GP26/GP27 rating NOT CONFIRMED), R-013 (USB held by solder joints and epoxy side beads), R-016 (R1-R12 stock: 13 at Mouser on 2026-11-11), R-018 (plan B trigger). First-build measurements: report section 3, FB-1..FB-12.
