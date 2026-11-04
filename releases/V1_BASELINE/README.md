# FrutaMIDI V1_BASELINE (v1.1.0-baseline)

Immutable engineering baseline. Do not edit files in this folder; later work goes to a new release folder via the change process (`.claude/skills/engineering-change`).

| File | Content |
|---|---|
| FrutaMIDI-report.pdf | Engineering report: requirements and verification status, architecture and decisions, interfaces, analyses, review findings, limitations, physical validation plan |
| REQUIREMENT_STATUS.md | Status of all 42 requirements |
| firmware/ | UF2 files for Pico, Pico W, Pico 2, Pico 2 W (breadboard and `pcb-` variants), Leonardo HEX, build log |
| FrutaMIDI-fabrication.zip | PCB v1.1: copper transfer PDFs (1:1), assembly map, schematic PDF, Gerbers, drill, BOM, renders |
| docs/ | User manual, assembly guide, README, review and re-review findings |
| REPRODUCE.md | How to rebuild and re-check everything |
| SHA256SUMS | Checksums of every file in this folder |

Status: designed, analysed, reviewed and host-tested. **Not built or tested on real hardware.** Analyses, design-rule checks and host tests are not hardware validation. Open FAILs: REQ-018 (VBUS on USB low-power ports), REQ-032 (BOM upper bound 30.40 EUR vs 30 EUR, assumed prices), REQ-040 (wrong JP1 position exceeds the module's absolute maximum; accepted risk).
