# Risks

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-001 | Two Adafruit 1982 revisions with different power-row pin order; wrong wiring shorts 3V3 to GND | Medium | High | Configuration wires + inspection table; review in G4 | electronics | OPEN |
| R-002 | Capacitive sensing with large conductive objects (fruit) may exceed MPR121 range or be unstable | Medium | Medium | AUTOCONFIG; threshold sweep; physical validation plan | firmware | OPEN |
| R-003 | Home-etch defects (bridges between 2.54 mm pads) | Medium | Medium | 0.6 mm clearance rule, continuity checklist | electronics | OPEN |
| R-004 | Nothing has been tested on real hardware (out of scope) | Certain | High | Physical validation plan in report; no readiness claims | manager | OPEN |
| R-005 | Disk space on host is limited (8.4 GiB free at start) | Medium | Medium | Install only what is needed; no full MacTeX | manager | OPEN |
| R-006 | ESD at 8 kV contact exceeds the inferred pin limit by 1.65× even with 3.3 kΩ series R | Low | Medium | Accepted (ADR-008); IEC test listed in physical validation plan | electronics | ACCEPTED |
| R-007 | Wrong JP1 position puts +3V3 on ADDR (QT) or IRQ (original) of an unpowered module | Low | Low–Medium | Silkscreen, manual warning, firmware LED error pattern (ADR-009) | electronics/docs | ACCEPTED |
