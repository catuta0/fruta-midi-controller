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

## ADR-008 — Electrode protection, I2C speed, board revision (from T-050/T-052) (label superseded by ADR-019 D-2: "FrutaMIDI v1.2")
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

## ADR-014 — Review fix batch before baseline
- All 16 findings of reports/review/72f67f0/findings.md dispositioned there (13 FIX, 1 ACCEPTED, 2 info FIX). The baseline is not yet released, so fixes are made on main before V1_BASELINE; none changes a frozen interface (MIDI message formats, pins and nets unchanged). A re-review of the changed outputs follows.

## ADR-015 — BOM part numbers (T-056)
- J2 = Phoenix Contact 1715721 (MKDS 1,5/2-5,08, ×7), matching the footprint basis; 1729128 (MKDSN) rejected. RV1 named by series (RK09K, 10k linear, vertical) — exact order code not sourced (PARTIAL, accepted). Female headers generic. SW1 Omron B3F-1000 drawing match to be confirmed against the official PDF (follow-up, info).

## ADR-016 — T-012 decisions
- REQ-018 stays FAIL with a documented deviation: on a USB low-power port (4.40 V min) VBUS is below the Pico's recommended 4.50 V; the user guide recommends a standard (high-power) port or powered hub. Not relabelled.
- INTERFACES change request from systems (AGND citations; pot zone 0.660 V, dead band 0.132 V, error budget 0.0364 V) is documentation-only and is applied by the manager as frozen-2 together with any firmware T-044 interface notes.

## ADR-017 — Firmware review fixes (T-044)
- Accepted: per-note reference counting (F-004), sensor health with loss detection and retry (F-005), setClock after every sensor begin (F-006). Retry timing measured from the last start attempt (an old loss is retried on the next loop, then every > 2 s) — accepted.
- Notable defect found while fixing F-005: on an I2C NACK the Adafruit library's touched() returned 0x0FFF (all 12 pads touched) — a lost sensor would have played 12 notes. The sketch now reads the status registers itself and checks the transaction result.

## ADR-018 — Re-review (T-061) dispositions
- F-007 NOT CLOSED → fixed: `.gitignore` exception `!reports/**/build/`; firmware build logs T-040/T-041/T-044 committed.
- N-001 (minor): accepted as a specified exception in REQ-016 — automatic restart of a lost sensor (16.8–22.1 ms, once per ≥2 s retry, fault path only). Splitting the restart across loops is left for a later revision.
- N-002 (minor): REQ-016 evidence refreshed (function reference, worst loop ≈1.72 ms).
- N-003 (info): INTERFACES frozen-3 adds IF-PCB-AUX (J3 wire holes, J4–J7 BOM-only headers); documentation-only.
- N-004, N-005 (info): accepted; behaviour matches REQ-009/REQ-042 and the manual.
- Manager edited REQUIREMENTS.md, requirements.csv and INTERFACES.json under locks for these items.

- N-004 (2026-11-05, user request): the BOM-only socket symbols J4–J7 (unconnected headers drawn only to appear in the BOM) are removed. Sockets are a "Socket" field of A1/A2, exported as a BOM column. Netlist otherwise unchanged; PCB copper identical (91 tracks, 131 pads compared). Schematic relaid out on A3 in framed blocks (commit 21a4919).

## ADR-019 — CR-002 decisions (T-060 open items), 2026-11-07
- D-1 ESD scope stays ±4 kV (REQ-023 as written). Vishay MBE04140C3301FC100 (DIN0414, 3k3 1 %) is selected: 4.08 kV rating at 3k3 from the datasheet chart, margin 1.12 at 4 kV (CALCULATION). 8 kV remains risk R-006; the LSR37 alternative (12 kV rated, same footprint) is rejected for now because its ±10 % tolerance and up to ±20 % drift after strikes bring touch sensitivity to the 0.90 limit. Recorded as a later option.
- D-2 Board label becomes "FrutaMIDI v1.2": the layout changed beyond the resistor row. Systems updates ADR-008 / interface_check; the generator text is changed after that.
- D-3 Cost: the +3.4…+7.3 € for R1–R12 is accepted for safety (ESD protection that cannot be bypassed outweighs the 30 € target); systems re-runs budgets.py and records the cost requirement status honestly (it may move from FAIL by 0.40 € to a larger FAIL).
- D-4 Layout escalation accepted: A2 15.1 mm up / 2.54 mm right; J1, JP1 (upright, QT top / ORIG bottom), R13–R15 right of the module; H4 to (88.5, 30.5). Nets and pinout unchanged; no firmware change.

## ADR-020 — CR-002 re-review dispositions, 2026-11-07
- See reports/review/CR-002/findings.md "Dispositions". Key choices: end-cap gap risk (C2-002) controlled by forming leads on a gauge (±0.25 mm) and a caliper check in the physical plan, not by relayout; the E-pad ↔ GND edge track stays as an intentional spark gap (C2-005); H3 moved to (96, 38).

## ADR-021 — Manager PCB design review follow-up (T-076), 2026-11-07
- Fixed: JP1 pitch 3.81 mm (pad gap 0.60 → 1.87 mm) against an accidental three-pad solder bridge; J2 pads 3.0 × 4.5 mm oval extended towards the block back (copper 7.1 → 11.6 mm² per pad, spark gap to the GND edge track kept at 1.40 mm); RV1 mounting tabs on AGND; C1 100 nF (KEMET C322C104K5R5TA) wiper to AGND, τ ≤ 0.38 ms vs 30 ms read interval (CALCULATION); silkscreen overlaps removed.
- Rejected: C2 1 µF at the module. No single-layer route without passing 3V3 close to H2 hardware and running GND 1.1 mm from all electrode pins; both module versions have their own regulator and capacitors. Recorded as not needed.
- D-ADR-021 addendum: C1 cost (+0.20–0.90 EUR) accepted (REQ-032 stays FAIL, upper bound 38.62 EUR); INTERFACES frozen-6 frozen by manager.

## ADR-022 — Final re-review (T-079) dispositions, 2026-11-08
- F2-001 fixed: C1 drill 0.8 → 0.9 mm (fit 0.29 mm at max lead 0.61 mm, ring 0.55 mm; CALCULATION, T-080).
- F2-002 accepted risk R-011 (OPEN, owner electronics): RV1 frame stays on AGND; plastic knob ≤ 15 mm on an insulated shaft specified; knob/shaft strike added to the REQ-023 physical test (step 2b). Fallbacks (tabs unconnected or on GND) only if that test fails.
- F2-003 fixed: REQ-032 evidence cites ADR-019 D-3 and the ADR-021 addendum; status FAIL against 30 EUR.
- F2-004, F2-005, F2-007 fixed in hardware/README.md and reports/electronics/analysis.md (T-080).
- F2-006 fixed: pcb_rules_check enforces the Ex ↔ GND spark gap 1.40 ± 0.05 mm (12/12 at 1.400 mm, MEASUREMENT on design file; mutation tests fail at 0.650 and −0.100 mm).
- INTERFACES frozen-7 frozen by manager (documentation-only change: C1 drill/ring, spark-gap rule note, AGND ESD note).
- No further independent re-review: changes are a drill size, wording and a new check, all reproduced by the manager (ERC 0, DRC 0/0/0, checks 85/85, 20/20, budgets 25/5).

## ADR-023 — SMD conversion for home chemical etching (CR-003), 2026-11-09
User decisions from the T-090 feasibility study (reports/electronics/smd_feasibility.md):
- D-1 R1-R12: one TT Electronics HPWC2512 3k0 ±5 % per channel. 4 kV rating margin 1.24 and conductor gap margin 1.34 (CALCULATION from SOURCE chart and dimensions); 8 kV stays FAIL (R-006). 3k3 rejected: at +5 % the worst-choice sensitivity is 0.899, below the 0.90 limit of ADR-019 (CALCULATION). MPN, stock and price not confirmed.
- D-2 RV1: off-board potentiometer on 3 wire pads. R-011 must be re-derived.
- D-3 J2: solder-wire pads with hot-melt strain relief. WAGO 2060 rejected.
- D-4 Holes: 4 M3 mounting holes stay; every other hole goes (133 to 4, MEASUREMENT for 133, design intent for 4).
- Manager: A1 surface-soldered on castellations with an etched bare-copper keep-out; A2 pins butted on surface pads; SW1 Omron B3S-1000; R13-R16 and C1 in 1206; JP1 SMD 3-pad bridge; J1 stays as two insulated wire links on surface pads. Bare MPR121 rejected (0.40 mm pitch against the 0.6 mm clearance rule, SOURCE and REQ-029). Loss of socket rework accepted as a consequence of the user's request.
- Single layer without new wire bridges is an estimate only until layout (T-091).

## ADR-024 — R1-R12 changed to CMB 0207 3k3; BOM moved to Mouser (CR-003), 2026-11-09
User decision after the T-095 quote comparison ("CMB, mudas a placa pronto"), replacing ADR-023 D-1:
- R1-R12: Vishay CMB02070X3301GB200 (MELF 0207, 3k3 ±2 %). HPWC2512-3K0JT18 has no small-quantity offer (T-093); HPWC2512-3K3JT1 rejected by the user.
- 1.2/50 us chart 5175 V at 3k3 (SOURCE, reading about ±5 %) against about 3636 V across R at 4 kV: margin 1.42 (CALCULATION). Worst-choice sensitivity at 3366 ohm 0.901 against the 0.90 limit (SIMULATION).
- Accepted deviation, by the user: the conductor gap of the part is 3.2 mm (SOURCE) against the 3.5 mm flashover rule at 4 kV. A layout cannot change it. The check must report this as a deviation and must not be relaxed. REQ-023 stays PARTIAL; 8 kV FAIL (R-006).
- All parts move to Mouser: the only shop able to supply the whole board on 2026-11-09 (T-095). One-board quote about 17.6 EUR, excluding shipping and taxes (CALCULATION from SOURCE prices).
- Consequences: new MELF land pattern, re-layout of the R row, a hand-soldering procedure for a rolling part.

## ADR-025 — R1-R12 HPWC2512 3k3 at Mouser (CR-003), 2026-11-09
User decision ("ok pronto fica HPWC"), replacing ADR-024 on R1-R12 and ADR-023 D-1. ADR-024 stays valid only for moving the BOM to Mouser.
- R1-R12: TT Electronics HPWC2512-3K3JT1, 3k3 ±5 %, existing 2512 land (G 5.0 mm). 12 for 15.00 EUR, stock 2381 (SOURCE, Mouser Portugal, 2026-11-09). One-board quote about 27.5 EUR, excluding shipping and taxes (CALCULATION).
- 1.2/50 us chart reading about 4596 V against about 3636 V across R at 4 kV: margin about 1.26 (CALCULATION, chart reading). Conductor gap 4.4 mm (SOURCE) against the 3.5 mm rule: PASS at 4 kV. 8 kV FAIL (R-006).
- Accepted deviation, by the user: at +5 % (3465 ohm) the worst-choice sensitivity is 0.885 against the 0.90 limit (SIMULATION). Mitigation: each resistor is measured before soldering and only those within the selection limit are used. The limit of 0.90 is not changed.
- The ADR-024 MELF land and the accepted 3.2 mm gap no longer apply. Silicone over R1-R12 is optional only: neutral-cure electronics grade, never acetic-cure.

## ADR-026 — R1-R12 standard 2512 3k3 1 % (CR-003), 2026-11-09
User decision after discussing cost against the 4 kV target (user: pulse-proven parts are excessive for a hand-built instrument; "ok ok"). Supersedes ADR-025 on R1-R12.
- R1-R12: Yageo RC2512FK-073K3L, 3k3 ±1 %, 1 W, 200 V rated. Mouser 603-RC2512FK-073K3L: 12 for 1.31 EUR at 0.109 EUR, stock 13, next delivery 2027-05-18 (SOURCE, Mouser Portugal, 2026-11-09). One-board quote about 13.8 EUR excluding shipping and taxes (CALCULATION).
- Accepted by the user: no sourced pulse capability, so survival of a 4 kV strike is NOT PROVEN. The ±4 kV target of REQ-023 was itself an ASSUMPTION (IEC 61000-4-2 level 2, standard not read). Possible effects: resistance drift or a dead channel; in the worst case an arc reaches the module. Energy of a 4 kV IEC-style strike into R is about 1 mJ against 182 mJ behind the earlier 1.2/50 us chart criterion (CALCULATION, T-060/T-090).
- REQ-023 stays PARTIAL at best; the physical ESD test decides. Selection by multimeter (ADR-025) no longer applies. Silicone stays optional.

## ADR-027 — CR-003 rulings after T-099, 2026-11-11
- D-1 REQ-032 basis: core BOM excluding shipping, consumables and tools, as in every earlier revision. VAT does not change the verdict: 14.84–16.84 EUR ex VAT, 18.25–20.71 EUR with 23 % VAT (ASSUMPTION), both under 30 EUR (CALCULATION, budgets.out revision 9). REQ-032: PASS on this basis; shipping stays NOT CONFIRMED and is reported beside it.
- D-2 Plan B (R-018) accepted: if after the physical ESD series any R1-R12 reads outside 3234–3366 ohm, a channel stops detecting touch, or an arc crosses a resistor, move to the T-097 clamp (Bourns CDSOD323-T05LC) with R1-R12 at 1 kohm, after confirming its maximum capacitance and leakage.
- D-3 R-016 accepted: Mouser stock 13 for 12 needed (one spare). The purchase list names a standard 3k3 ±1 % 2512 alternative on the same land.
- D-4 INTERFACES frozen-8 frozen by the manager.
- D-5 JP1 legend: etched ORIG/QT plus the assembly map is accepted (R-007, REQ-040 stays FAIL as an accepted risk). Project definition amendment was made in 410933d.
