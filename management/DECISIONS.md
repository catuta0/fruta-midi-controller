# Decisions (ADR style)

## ADR-000 — Project setup
- Date: 2026-10-30. Status: accepted (user, Phase A).
- Context: project continues the FrutaMIDI repository (v1.0.0 released, v1.1 on main).
- Decision: project folder `/Users/rod/fruta-midi-controller`; all project files in English (user choice, includes converting the existing Portuguese README/guide); existing paths `hardware/`, `firmware/`, `docs/` kept to avoid breaking released links; commits without Co-Authored-By lines (skill rule, supersedes earlier commits).
- Consequences: the existing Portuguese user documentation must be translated before the next release.

## ADR-001 — End-to-end run without stopping at intermediate gates
- Date: 2026-10-30. Status: accepted (user, chat: "sim, faz tudo, do inicio ao fim").
- Decision: the manager runs G1–G4 without waiting; each gate summary is written to `management/gates/G<n>.md` at the moment it is passed. Publishing a GitHub release (G5 public step) still requires an explicit user "yes" at that moment (CLAUDE.md rule). Pushing commits to `origin/main` is authorized.
- Consequences: user decisions normally taken at gates are taken by the manager and recorded as ADRs, flagged for later user review.

## ADR-002 — Documentation follows firmware for long-press time
- Date: 2026-10-30. Status: accepted (manager, ADR-001 authority; flagged for user review).
- Context: docs said "hold 1 s" to recalibrate; firmware uses `now - downAt > 800` (800 ms). Evidence: T-030 handoff.
- Decision: firmware is the source of truth; docs state 0.8 s. No firmware change.

## ADR-003 — Safety statement on touchable electrodes
- Status: accepted. The README must not claim "safe to touch" without evidence. Wording waits for the electronics analysis T-050 (ESD/current limiting); until then it is qualified as an ASSUMPTION.

## ADR-004 — English file and folder names
- Status: accepted. `hardware/fabrico/` → `hardware/fabrication/`, `imagens/` → `images/`, Portuguese PDF names → English, done by electronics in build_all.sh after T-050 (task T-051), docs links updated afterwards by documentation.

## ADR-005 — Sampler fixes and language
- Status: accepted (manager under ADR-001; flagged for user review). Evidence: T-020 handoff.
- FINDING-SW-2: learning a note already used by another pad SWAPS the two pads' notes (both stay reachable; no silent shadowing).
- FINDING-SW-1: before audio is enabled, incoming notes still flash pads and the page shows a visible "click to enable sound" hint.
- MIDI channels: the sampler stays omni (accepts all 16 channels); the firmware channel is configurable, so filtering would add a failure mode for no benefit.
- Language: ADR-000 (all English) extends to user-visible strings: sampler UI text and PCB silkscreen ("ESCALA"→"SCALE", "OITAVA"→"OCTAVE", T-051).

## ADR-006 — Architecture: option A (Pico + Adafruit MPR121 breakout)
- Status: accepted (manager, ADR-001). Options compared in reports/systems/architecture_options.md: A Pico+MPR121 (chosen), B Pico native RC/PIO sensing (cheaper 14.20–22.20 EUR CALCULATION on ASSUMPTION prices, sensing unproven, conflicts with bought-in parts), C Pro Micro+MPR121 (conflicts with fixed Pico family, harder flashing). Consequence: MPR121 sets a ≥4 ms sensing floor (REQ-015).

## ADR-007 — Responses to systems open decisions D-1…D-8 (T-008)
- D-1 latency/jitter: targets were unsourced ASSUMPTIONs. New targets with rationale: worst-case touch-to-MIDI ≤ 15 ms, jitter ≤ 10 ms; mitigation M1 (one burst read per loop for aftertouch) mandated. Recorded as a relaxation, flagged for user review.
- D-2 ESD: decided by electronics variant study T-050.
- D-3 24 pads: breadboard/firmware only; PCB carries one module.
- D-4 configuration wiring hazard: the 3V3 free wire is replaced by a 3-pad solder jumper (centre 3V3, sides S1/S7) so 3V3 can only reach VIN/VCC of either revision; a wrong choice lands on ADDR or IRQ (no short). SDA/SCL stay wires (a misplaced data wire cannot short the rail). Implementation: electronics T-052.
- D-5 I2C: move to 100 kHz if the latency budget with M1 still meets D-1 (systems recomputes, firmware implements); otherwise keep 400 kHz and list rise-time measurement P-4.
- D-6 hosts: Windows 10/11 and macOS 12 or later.
- D-7 BOM: target stays ≤ 30 EUR for the core BOM (assembled board, excluding tools, consumables and USB cable); prices remain ASSUMPTION unless sourced; status reported honestly.
- D-8 language: English (ADR-005).
- Tooling: pypdf may be installed into .venv to read datasheets.

## ADR-008 — Electrode protection, I2C speed, board revision (from T-050/T-052)
- Status: accepted (manager, ADR-001). Evidence: reports/electronics/analysis.md.
- Electrode protection: variant b (3.3 kΩ series per electrode). PASS vs the ±4 kV target (REQ-023), PARTIAL at 8 kV accepted as a documented risk (R-006); clamps rejected (SMD breaks THT-only; diode variant needs 12 jumpers).
- I2C: keep 400 kHz; rise-time FAIL fixed at the root cause by 4.7 kΩ pull-ups R13/R14 (D-5 closed).
- Firmware impacts F-1..F-4 passed to firmware (cross-discipline iteration #1: electronics → firmware).
- Board label becomes "FrutaMIDI v1.1".

## ADR-009 — Responses to T-010 open decisions
- Status: accepted (manager, ADR-001).
- Requirement status policy: analysis PASS + physical test NOT RUN = PARTIAL (systems' convention kept; honest).
- D-9 (REQ-024): add 220 Ω series resistors in SDA and SCL at J1 (fault current ≤ 15 mA CALCULATION by systems); electronics to verify VOL and rise time (T-055).
- D-10 (REQ-040): wrong JP1 position is mitigated by silkscreen ("ORIG = no STEMMA connectors / QT = two white connectors"), manual warning and the existing firmware "sensor not found" LED pattern; residual risk R-007 accepted.
- D-11 (REQ-041): breadboard docs add two 4.7 kΩ pull-ups (SDA, SCL to 3V3); one firmware configuration (400 kHz) for both builds.
- Pico datasheet PDFs are git-ignored (size); their sha256 is in requirements/SOURCES_SYSTEMS.md.

## ADR-010 — Firmware T-041 decisions
- Status: accepted (manager, ADR-001).
- M1 implemented as run-based burst reads (never more bytes than the per-pad path; 12 pads 945 µs vs 2430 µs CALCULATION) — accepted.
- AUTOCONFIG limits: design VDD = 3.2 V (between module regulator worst case 3.10 V and typical 3.25–3.295 V, reports/electronics/analysis.md) → USL/TL/LSL = 200/180/130, i.e. the library values; written explicitly together with AUTOCONFIG1 (0x7C) SCTS = 0, pending datasheet confirmation of the bit layout (T-042).
- Aftertouch messages after all Note On/Off of the same loop — accepted.
- MPR121 datasheet download approved (into a new folder under sim/, PDFs git-ignored).

## ADR-011 — MPR121 register facts confirmed (closes T-042 BLOCKED items)
- The manager read the datasheet (S-006): SCTS is D7 of 0x7C (firmware assumption correct); USL/TL/LSL formula matches; multiple-byte read format in §6.4 supports the burst reads; §6.1 recommends 4.7 kΩ pull-ups (consistent with R13/R14). The three firmware ASSUMPTIONs become SOURCE.
- Downloading the datasheet to the repo was not needed; the file read lives outside the repo, identified by sha256.

## ADR-012 — Electrode resistor voltage rating (T-054) and I2C series resistors (T-055)
- Status: accepted (manager, ADR-001).
- No 2.7–3.3 kΩ THT resistor with a datasheet-confirmed ≥3.64 kV pulse rating was found within the time box. MFR-12 3k3 kept; REQ-023 stays PARTIAL (pin current 1.10 A < 1.33 A at 4 kV, but the resistor may flash over: not rated). Vishay MBB 0207 (pulse chart unreadable, search extract "4 kV" unverified) is recorded as change candidate CR-001 for a later revision. Risk R-006 updated.
- 220 Ω series resistors R15/R16 on the Pico side of SDA/SCL accepted (fault current ≤ 15.5 mA; levels and rise time PASS by CALCULATION). Net names SDA_PICO/SCL_PICO at the Pico pins.

## ADR-013 — Interfaces frozen (frozen-1)
- Date 2026-11-03. INTERFACES.json draft-3 frozen as "frozen-1". Changes from now on go through /engineering-change.
- REQ-040 stays FAIL with accepted residual risk R-007 (not relabelled).
