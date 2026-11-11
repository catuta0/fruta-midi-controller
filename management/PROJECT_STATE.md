# Project state

| Field | Value |
| --- | --- |
| Current gate | G5 (v1.3) waiting for the user — releases/V1.3, tag v1.3.0; GitHub release v1.3.0 not published |
| Baseline under work | `main` (CR-003 merged); releases V1_BASELINE (v1.1.0-baseline), V1.2 (v1.2.0), V1.3 (v1.3.0) |
| Phase | CR-003 complete (SMD board for home etching); only the physical first build remains (out of scope) |
| Last update | 2026-11-11 |

## Mapping of the generic structure to this repository
| Generic | Here | Reason |
| --- | --- | --- |
| design/electronics | `hardware/` | Existing work, linked from release v1.0.0 and README |
| code/firmware | `firmware/` | Existing work |
| code/host | `docs/index.html` (sampler), `scripts/` | GitHub Pages serves `docs/` |
| sim/, tests/, reports/, releases/, changes/ | as named | New |

## Status of existing work (not yet re-verified in this project)
| Item | Status | Evidence |
| --- | --- | --- |
| Firmware compiles (Pico, Pico W, Pico 2, Pico 2 W, Leonardo; std + PCB) | NOT RUN in this project (PASS in earlier session, logs not kept) | — |
| Schematic ERC | NOT RUN in this project (0 violations in earlier session) | — |
| PCB DRC + schematic parity | NOT RUN in this project (0 violations in earlier session) | — |
| Sampler behaviour | NOT RUN in this project (simulated-MIDI check in earlier session) | — |
| Any hardware test | NOT RUN (out of scope) | — |

## V1.2 (CR-002) status at release, 2026-11-08
| Item | Status | Evidence |
| --- | --- | --- |
| ERC / DRC with parity | PASS (0 / 0 / 0 / 0) — design files only | reports/electronics/evidence/T-080/ |
| interface_check / pcb_rules_check / budgets | 85/85 PASS; 20/20 PASS; 25 PASS 5 FAIL | sim/systems/*.out |
| Firmware builds / host tests | 9/9 builds; 295 passed; host/sampler 102 passed | releases/V1.2/firmware/build.log |
| Independent review | T-071 re-review and T-079 final re-review: release-ready; all findings dispositioned (ADR-020, ADR-022) | reports/review/CR-002*, |
| Requirements | 17 PASS, 18 PARTIAL, 3 FAIL (REQ-018, 032, 040), 4 NOT RUN | releases/V1.2/REQUIREMENT_STATUS.md |
| Hardware | NOT RUN (out of scope) | report §10 V-01…V-29 |
