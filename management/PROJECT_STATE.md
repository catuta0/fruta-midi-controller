# Project state

| Field | Value |
| --- | --- |
| Current gate | Pre-G1 (setup) |
| Baseline under work | `main` @ d85b330 (v1.1 content; GitHub release v1.0.0 published; v1.1.0 release NOT published) |
| Phase | B — workspace and specialist setup done; restart required to load agents |
| Last update | 2026-10-30 |

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
