# Project state

| Field | Value |
| --- | --- |
| Current gate | G5 done — V1_BASELINE released (tag v1.1.0 = 048023c; GitHub release v1.1.0 published 2026-11-04 with user approval) |
| Baseline under work | `main` @ b1e4bf5: two post-release hardware commits (21a4919 schematic readability, b1e4bf5 J4–J7 socket symbols removed) made outside a change request; NOT independently reviewed, NOT released |
| Phase | B complete; next work only through /engineering-change (candidate CR-001) |
| Last update | 2026-11-07 (state reconstructed from the repository after the original session was lost) |

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
