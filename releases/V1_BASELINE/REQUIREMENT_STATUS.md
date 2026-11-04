# Requirement status matrix — V1_BASELINE

Source: requirements/requirements.csv (REQUIREMENTS.md draft-5). Status words: PASS, PARTIAL (analysis/host tests pass, physical test NOT RUN), FAIL, NOT RUN. No requirement has been verified on hardware.

| ID | Title | Verification | Status |
|---|---|---|---|
| REQ-001 | Note On/Off per electrode | I + T [PHYSICAL] | PARTIAL |
| REQ-002 | Note Off integrity | T (host unit test) + T [PHYSICAL] | PARTIAL |
| REQ-003 | Second sensor (24 pads) | A + T [PHYSICAL] | PARTIAL |
| REQ-004 | Polyphonic aftertouch | T (host) + T [PHYSICAL] | PARTIAL |
| REQ-005 | Six scales | A + T (host) | PASS |
| REQ-006 | Octave potentiometer | A + T (host) + T [PHYSICAL] | PARTIAL |
| REQ-007 | Button short press | T (host) + T [PHYSICAL] | PARTIAL |
| REQ-008 | Button long press recalibration | T (host) + T [PHYSICAL] | PARTIAL |
| REQ-009 | Sensor absent or lost | T (host) + T [PHYSICAL] | PARTIAL |
| REQ-010 | Status LED | T [PHYSICAL] | NOT RUN |
| REQ-011 | USB MIDI class compliance | T [PHYSICAL] | NOT RUN |
| REQ-012 | Device name | I + T [PHYSICAL] | PARTIAL |
| REQ-013 | MIDI message set | I | PASS |
| REQ-014 | Touch-to-MIDI latency | A + T [PHYSICAL] | PARTIAL |
| REQ-015 | Latency jitter | A + T [PHYSICAL] | PARTIAL |
| REQ-016 | No blocking during play | I + A | PASS |
| REQ-017 | USB bus power only | I | PASS |
| REQ-018 | VBUS range | A + T [PHYSICAL] | FAIL |
| REQ-019 | VBUS current | A + T [PHYSICAL] | PARTIAL |
| REQ-020 | 3V3 rail load | A | PASS |
| REQ-021 | MPR121 supply voltage | A | PASS |
| REQ-022 | Touchable voltage (SELV) | A | PASS |
| REQ-023 | Electrode ESD robustness | I + A + T [PHYSICAL] | PARTIAL |
| REQ-024 | I2C hand-wire fault current | I + A | PASS |
| REQ-025 | Both module revisions | I + T [PHYSICAL] | PARTIAL |
| REQ-026 | I2C rise time (PCB) | A + T [PHYSICAL] | PARTIAL |
| REQ-027 | Single-sided PCB | I | PASS |
| REQ-028 | Board outline | I | PASS |
| REQ-029 | Home-etch rules | I + A (DRC) | PASS |
| REQ-030 | Screw-terminal map | I | PASS |
| REQ-031 | Pin map consistency | I | PASS |
| REQ-032 | Core BOM cost | A | FAIL |
| REQ-033 | Firmware build matrix | T (compile) | PASS |
| REQ-034 | Browser sampler | T | PARTIAL |
| REQ-035 | English language | I | PASS |
| REQ-036 | User and assembly manual | I | PASS |
| REQ-037 | Sensing range (physical) | T [PHYSICAL] | NOT RUN |
| REQ-038 | False triggers and crosstalk (physical) | T [PHYSICAL] | NOT RUN |
| REQ-039 | JP1 cannot short 3V3 | I | PASS |
| REQ-040 | JP1 wrong-position tolerance | A | FAIL |
| REQ-041 | I2C rise time (breadboard, with pull-ups) | A + T [PHYSICAL] | PARTIAL |
| REQ-042 | Shared-note reference counting | T (host) + T [PHYSICAL] | PARTIAL |

Totals: 42 requirements — FAIL 3, NOT RUN 4, PARTIAL 18, PASS 17
