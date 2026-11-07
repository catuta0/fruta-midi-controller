# Requirements

Owner: systems-engineer. Revision: draft-6 (T-070, 2026-11-07, CR-002 / FrutaMIDI v1.2), proposed and not yet baselined. It replaces draft-5 (T-013): REQ-023, REQ-028, REQ-029 and REQ-032 evidence updated for the pulse-rated DIN0414 R1–R12; no status changed.

Inputs are the working tree on top of be8d69d. The PCB, firmware and documentation snapshot checksums are in `management/handoffs/systems-engineer/T-010.md`. Targets follow ADR-007; the relaxations of REQ-014 and REQ-015 are flagged for user review.

Verification methods: **A** Analysis, **S** Simulation, **I** Inspection, **T** Test.

Status rules:
- Status covers only the verification that was actually performed: PASS, PARTIAL, FAIL, BLOCKED or NOT RUN.
- A requirement whose analysis or inspection passes, but whose test is still NOT RUN, is PARTIAL.
- Requirements marked **[PHYSICAL]** can only be closed by measurements on built hardware. Flashing and powering hardware are out of scope for this project.

Evidence paths:
- `sim/systems/budgets.out`: budgets and latency (revision 6, T-070)
- `sim/systems/interface_check.out`: pins, nets, jumper and documentation links
- `sim/systems/pcb_rules_check.out`: home-etch rules
- `reports/systems/budgets.md`
- `management/INTERFACES.json`

Sources are referenced as S-xx (see `requirements/SOURCES_SYSTEMS.md`). PD means `management/PROJECT_DEFINITION.md`. The machine-readable table is `requirements/requirements.csv`.

## Summary

| Status | Count |
| --- | --- |
| PASS | 17 |
| PARTIAL | 18 |
| FAIL | 3 |
| NOT RUN | 4 |
| BLOCKED | 0 |
| Total | 42 |

## 1. Function

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Each of the 12 electrode inputs E0–E11 (MPR121 ELE0–ELE11) shall send one MIDI Note On, on the configured channel (default 1) with the configured fixed velocity (default 100, range 1–127), when a touch is detected. It shall send a Note Off for the same note when the touch is released. | Core function | PD | I + T [PHYSICAL] | PARTIAL | I: PASS. The chain terminal → series resistor → module electrode is 1:1 (interface_check `pcb.A2.pin2..13`, `pcb.J2.*`). T: NOT RUN. |
| REQ-002 | The Note Off for a pad shall carry the note number sent in its Note On, even if the scale or octave changed in between. All sounding notes shall be released before a recalibration. | No stuck notes | Derived from REQ-001 | T (host unit test) + T [PHYSICAL] | PARTIAL | Host tests PASS (T-044 handoff, 295 host tests passed). Hardware test NOT RUN. |
| REQ-003 | The firmware shall support a second MPR121 at I2C address 0x5B (`NUM_SENSORS = 2`), mapping its electrodes to pads 12–23. This is a breadboard-only option; the PCB carries one module (ADR-007 D-3). | Expansion to 24 inputs | PD, ADR-007 | A + T [PHYSICAL] | PARTIAL | A: latency PASS at 400 kHz (12.35 ms ≤ 15 ms, jitter 8.35 ms), using the worst-case run-based burst plan (budgets.out §b). T: NOT RUN. |
| REQ-004 | While a pad is touched, the device shall send Polyphonic Key Pressure (0xAn) with a value 0–127. The value shall map linearly from delta = baseline − filtered, clamped to [12, 120]. It shall be evaluated every 15 ms and sent only when it changes by at least 2. | Expressive control | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS (T-044 handoff, 295 host tests passed). Aftertouch messages are sent after all Note On/Off of the same loop (ADR-010). Hardware NOT RUN. |
| REQ-042 | When two or more pads map to the same MIDI note, the note shall be sent once (Note On on the first pad), stay sounding while any of those pads is held, and get its Note Off only when the last of them is released (reference counting). Aftertouch for that note shall be the maximum of the holding pads' values, with a final pressure of 0 on the last release. | Melodic scales with 24 pads, and the octave clamp, can map pads to the same note; without counting, releasing one pad cuts a note that is still held (review F-004) | Review F-004, firmware T-044 | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS: `tests/firmware/logic/test_notes_health.py` (reviewer sequence, `releaseAll`), `firmware/FrutaMIDI/fm_notes.h` (T-044, 295 passed). Physical NOT RUN. |
| REQ-005 | The device shall provide 6 scales, selected cyclically: Drum Rack (36–47, octave ignored, the power-on default), major pentatonic, minor pentatonic, major, natural minor and chromatic (root 48). Notes shall be clamped to 0–127. | Musical use; sampler default mapping | PD, firmware | A + T (host) | PASS | A: notes 24–99 with 12 pads and 24–127 with 24 pads, never clamped (T-009 budgets §d). Host tests PASS (T-040 `test_scales.py`). |
| REQ-006 | The octave potentiometer shall shift melodic scales by −2..+2 octaves using 5 ADC zones, each V33/5 = 0.660 V wide. The octave shall change only when the reading is more than 0.7 zone from the current zone centre, i.e. 0.2 zone (0.132 V) beyond the border, which is the dead band. The combined ADC noise, DNL, quantisation and supply ripple shall stay below the dead band. A static ADC offset shifts every threshold together and does not consume the dead band. The pot shall have no effect on Drum Rack and shall be enabled by default on the PCB build. | Live octave control | PD | A + T (host) + T [PHYSICAL] | PARTIAL | A: PASS. Error budget 0.0364 V < dead band 0.132 V, margin 0.096 V (budgets A5). Inputs: noise from ENOB 8.7 (SOURCE S-17 Table 627); DNL peak 10 LSB12 (ASSUMPTION; S-17 §4.9.4 and erratum RP2040-E11 give peaks at codes 512/1536/2560/3584, height only in a figure); 10-bit step; ripple 10 mV (ASSUMPTION). The nearest DNL-peak code is 0.049 V from a switch point. The static offset of about 30 mV (S-01 §4.3) is reported, not budgeted (review F-003). Host tests PASS (T-043). Hardware NOT RUN. |
| REQ-007 | A short press of the button (released within 800 ms, sampled every 10 ms) shall select the next scale, and the LED shall blink N times for scale N. | User control | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS (T-044 handoff, 295 host tests passed). Hardware NOT RUN. |
| REQ-008 | A press of more than 800 ms shall release all notes and recalibrate all sensors; the LED then blinks 3 times. | Recalibration after moving objects | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS (T-044 handoff, 295 host tests passed). Recalibration blocks for 16.8–22.1 ms per sensor at 400 kHz (CALCULATION); this is user-requested and allowed by REQ-016. Hardware NOT RUN. |
| REQ-009 | If no MPR121 answers at start, the device shall send no MIDI from it and retry. During play, a sensor shall be marked lost after 3 consecutive failed I2C transactions, or at once when its ECR read-back (every 250 ms) differs from the value read after start-up (a chip that reset itself). On loss the firmware shall release that sensor's notes, show the fast error blink and stop reading it. It shall retry start-up when more than 2 s have passed since the last start attempt (this also covers a second sensor missing at boot). The other sensor shall keep playing. | Diagnosable fault state | Firmware; review T-060; firmware T-044 | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS: `tests/firmware/logic/test_notes_health.py` (15 tests), within `295 passed` (T-044 handoff). Implementation: `fm_notes.h`/health logic, `startSensor()` = begin → setClock(400000) → configure → ECR read. A self-reset chip releases its notes through the normal touch path before the ECR check, so only one Note Off is sent. Physical NOT RUN (it needs the sensor unplugged or reset during play). |
| REQ-010 | The LED shall give 2 slow blinks at start when a sensor is found, and shall be lit while any pad is touched. On Pico W and Pico 2 W the LED is driven through the CYW43 (WL_GPIO0). | User feedback | Firmware, S-02 | T [PHYSICAL] | NOT RUN | |

## 2. USB and host

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-011 | The device shall enumerate as a USB MIDI 1.0 class device (MIDIStreaming, bulk endpoints). It shall work without vendor drivers on Windows 10, Windows 11 and macOS 12 or later. | Non-technical end user | PD, ADR-007 D-6, S-14 | T [PHYSICAL] | NOT RUN | |
| REQ-012 | The USB product string and the MIDI port name shall be "FrutaMIDI". | Recognisable in DAWs and in the sampler | Firmware | I + T [PHYSICAL] | PARTIAL | I: `DEVICE_NAME = "FrutaMIDI"` is passed to `setProductDescriptor` and `setStringDescriptor`. T: NOT RUN. |
| REQ-013 | The device shall send only Note On (0x9n, CIN 0x9), Note Off (0x8n, velocity 0, CIN 0x8) and Polyphonic Key Pressure (0xAn, CIN 0xA), on one channel n = MIDI_CHANNEL − 1. Incoming MIDI shall be read and discarded. | Interface definition | S-14, S-15 | I | PASS | `fm_midi.h` constants match S-14 Table 4-1. |
| REQ-014 | Device latency from the first touch after a pad has been idle for at least 15 ms (DEBOUNCE_MS) to the USB-MIDI packet being available to the host shall be ≤ 15 ms worst case, for electrode capacitance ≤ 100 pF, with mitigation M1 (one burst read per sensor per aftertouch pass). A re-touch of the same pad within the 15 ms lockout is outside this requirement and is reported separately. | Playability; ADR-007 D-1 relaxation from the earlier unsourced 10 ms | ADR-007 | A + T [PHYSICAL] | PARTIAL | A: PASS. 1 sensor 10.72 ms, 2 sensors 12.35 ms at 400 kHz, including the T-044 ECR poll (≈ 0.14 ms per sensor) (CALCULATION, budgets.out §b). Separate term: a re-touch inside the lockout adds up to 15 ms, giving 25.72 ms worst case (review F-011). Design limit C ≤ 210 pF. T: NOT RUN (plan item P-2). Flagged for user review (ADR-007). |
| REQ-015 | Latency jitter (worst minus best) shall be ≤ 10 ms for electrode capacitance ≤ 100 pF. | ADR-007 D-1; the MPR121 sets a 4 ms floor (ADR-006) | ADR-007 | A + T [PHYSICAL] | PARTIAL | A: PASS. 6.72 ms (1 sensor) and 8.35 ms (2 sensors) at 400 kHz, including the ECR poll (CALCULATION). T: NOT RUN. |
| REQ-016 | During play, no firmware action other than a user-requested recalibration or the automatic restart of a lost sensor shall block touch processing for more than 10 ms. | Avoid delayed or stuck notes | Derived | I + A | PASS | I: the only `delay()` is `delay(10)` in `midiBegin()` (setup). LED feedback is non-blocking (`fm_blink.h`). A: worst loop ≈1.72 ms for 1 sensor at 400 kHz (aftertouch pass 1235–1585 µs + ECR poll 108–138 µs, sim/systems/budgets.out; CALCULATION). Exception (review N-001, ADR-018): a lost-sensor restart runs begin()+configure (16.8–22.1 ms per sensor, CALCULATION) and pauses the other sensor once per retry (≥2 s apart); fault-recovery only. |

## 3. Power and supply

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-017 | The device shall be powered only from USB VBUS through the Pico's micro-USB connector. No other power input shall exist. | Hard constraint | PD | I | PASS | Pico pins 39 and 40 are unconnected (`pcb.A1.no_other_nets`). |
| REQ-018 | The device shall operate with VBUS from 4.40 V to 5.50 V at its connector. | Full USB 2.0 VBUS range | S-10 | A + T [PHYSICAL] | FAIL | A: VSYS 3.95–5.25 V, inside the 1.8–5.5 V range (S-01 §2.1): PASS. However, the 4.40 V low-power-port minimum (S-10) is below the Pico's recommended VBUS of 5 V ± 10 % = 4.50 V (S-01 §2.3): budgets check A3b FAIL, so the requirement as stated FAILs (review F-010). Electrically the Pico still runs (VSYS margin 2.15 V). Options: restrict the statement to 4.50–5.50 V, or accept as a documented deviation. T: NOT RUN. |
| REQ-019 | VBUS current shall be ≤ 100 mA (the declared bMaxPower, S-11) for every supported Pico board. | One unit load; declared value | S-10, S-11 | A + T [PHYSICAL] | PARTIAL | A: worst case 55.6 / 70.6 / 60.6 / 75.6 mA for Pico / Pico W / Pico 2 / Pico 2 W. Lower bounds are SOURCE (S-01 Table 3, S-16 Table 2); RP2040 pull-ups 50–80 kΩ are SOURCE S-17. The upper bounds are ASSUMPTIONs. T: NOT RUN (plan item P-3). |
| REQ-020 | The external load on the Pico 3V3(OUT) shall be ≤ 300 mA with at least 50 % margin. | Regulator recommendation | S-01 §2.1 | A | PASS | 10.15 mA worst case with 2 sensors and PCB pull-ups: 96.6 % margin. |
| REQ-021 | The MPR121 VDD, fed from the Pico 3V3 through the module LDO, shall be within 2.0–3.6 V. | Sensor operating range | S-04, S-06, S-07 | A | PASS | 3.10–3.40 V (CALCULATION; dropout and rail tolerance are ASSUMPTIONs). |

## 4. User safety and robustness

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-022 | Every user-touchable conductor shall be at ≤ 3.6 V relative to GND and shall be supplied only from the USB SELV source. | Users touch electrodes directly | PD | A | PASS | Electrodes are charged from MPR121 VDD ≤ 3.6 V (S-04), and REQ-017 holds. |
| REQ-023 | Each user-touched electrode terminal shall survive ±4 kV contact discharge without permanent damage. The ±4 kV target is an ASSUMPTION, following IEC 61000-4-2 level 2 (the standard was not read). | Bare human touch on sensor pins | Derived; S-04; ADR-007 D-2 | I + A + T [PHYSICAL] | PARTIAL | Estimate on ASSUMPTIONs, not a PASS (review F-002). Current: with 3.3 kΩ (R1–R12) plus the IEC 330 Ω source, the peak at 4 kV is 4 kV / 3.63 kΩ = 1.10 A, below the 1.33 A pin limit inferred from the HBM ±2 kV rating (the limit is itself an ASSUMPTION); IEC 4 kV through 3.63 kΩ gives τ = 545 ns and Q = 600 nC against 150 ns / 200 nC for HBM 2 kV (CALCULATION). Voltage across R: 3.64 kV at 4 kV, 7.27 kV at 8 kV (CALCULATION). Pulse rating (CR-002, ADR-019 D-1): R1–R12 are now Vishay MBE04140C3301FC100 (DIN0414, 3k3 1 %), 4.08 kV 1.2/50 µs at 3.3 kΩ (SOURCE EE-S17b chart; ±5 % reading ASSUMPTION), margin 1.12 at 4 kV (1.07 at −5 %) (CALCULATION); the former Yageo MFR-12 was rated 400 V. Flashover around R: gap rule ≥ 3.5 mm for 4 kV (CALCULATION, breakdown sweep on ASSUMPTION models; IEC 60664-1 F.2 values recalled, EE-S25); the design file has (a) ELEx–Ex 13.04 mm on all 12 channels and (b) Ex to any other ELE/MPR121/Pico net 10.92 mm (MEASUREMENT on the design file, sim/electronics/calc/check_gap.out; old layout 0.94 / 1.99 mm FAIL). 8 kV: gaps also meet the 7.5 mm rule but the resistor fails (4.08 < 7.27 kV): risk R-006. Evidence: reports/electronics/analysis.md §5. T: NOT RUN [PHYSICAL] (ESD-gun test, ±4 kV contact on each terminal). |
| REQ-024 | A misplaced SDA or SCL hand wire (including one on a supply hole S1/S2/S6/S7) shall not drive an RP2040 pad beyond its IO current limits. | Hand wiring by a non-expert builder | Derived | I + A | PASS | I: 220 Ω series resistors are present between the Pico pads and the bus: pad 31 SDA_PICO → R16 → SDA, pad 32 SCL_PICO → R15 → SCL (interface_check `fw.pcb.PIN_SDA/SCL_vs_pcb`). A: fault current 15.5 mA per line at 3.4 V, 30.9 mA for both lines, ≤ IIOVDD_MAX 50 mA (SOURCE S-17 Table 625). Low-level margins: Pico→MPR121 0.138 V, MPR121→Pico 0.235 V (budgets B5/B6, CALCULATION). Statement reworded after ADR-009 D-9: a wire on a supply hole is still physically possible, but it is now current-limited. |
| REQ-025 | One PCB shall accept both Adafruit 1982 revisions. JP1 bridges ORIG (+3V3 → S1 = VIN) or QT (+3V3 → S7 = VCC). The SDA/SCL wires from J1 go to S5/S6 (original) or S3/S4 (STEMMA QT). | The bought-in part exists in two pinouts | PD, S-05..S-07, ADR-007 D-4 | I + T [PHYSICAL] | PARTIAL | I: PASS. JP1 selector S1/+3V3/S7 with silkscreen legend 'ORIG = no white connectors' and 'QT = 2 white connectors' (`pcb.JP1_legend`). J1 1 = SCL, 2 = SDA. hardware/README.md table (JP1, SDA, SCL) = ORIG/S5/S6 and QT/S3/S4, which matches the Eagle-derived S-row (`doc.hw_readme.jp1_and_wires.*`). T: NOT RUN. |
| REQ-026 | The PCB-build I2C bus shall meet the rise time for its clock: ≤ 300 ns at 400 kHz (≤ 1000 ns at 100 kHz), with the module at 0x5A. | Sensor interface within spec | S-04, S-13 | A + T [PHYSICAL] | PARTIAL | A: PASS. R13/R14 4.7 kΩ: t_r 156 ns at 60 pF, C_b limit 115.2 pF (systems, with RPU 80 kΩ from S-17); electronics gives 103 ns at 38 pF. The 220 Ω series resistors add 2.2 ns (ASSUMPTION of 10 pF pad capacitance). IO levels with 220 Ω: B5–B8 PASS, minimum margin 0.138 V (S-17 Table 625, S-04 Table 5). T: NOT RUN (plan item P-4). |
| REQ-039 | No position of the JP1 3V3 selector (ORIG, QT, open) shall connect +3V3 to GND. | ADR-007 D-4: removes the T-008 wrong-hole short | ADR-007 | I | PASS | S1 and S7 are never GND in either revision (`pcb.JP1_no_gnd_reachable`). |
| REQ-040 | A wrong JP1 position (ORIG on a STEMMA QT module, or QT on an original module), or both sides bridged, shall not apply a voltage outside the MPR121 absolute maximum ratings (inputs ≤ VDD + 0.3 V, S-04 Table 3), and shall not short +3V3 through a module output. | Builder error tolerance | Derived from ADR-007 D-4 | A | FAIL | A: still FAIL as stated. The ORIG bridge on a QT module puts +3V3 on ADDR, and the QT bridge on an original module puts it on IRQ, both above VDD + 0.3 V on an unpowered module. Both sides bridged on an original module ties +3V3 to the IRQ open drain. Mitigation per ADR-009 D-10: silkscreen legend present (`pcb.JP1_legend` PASS), manual warning, and the firmware 'sensor not found' LED pattern. Residual risk R-007 accepted by the manager. |
| REQ-041 | The breadboard-build I2C bus, with the two 4.7 kΩ pull-ups required by ADR-009 D-11, shall meet the rise time for 400 kHz. | Same as REQ-026, for the breadboard build | S-13 | A + T [PHYSICAL] | PARTIAL | A: PASS. t_r 156 ns at 60 pF with 4.7 kΩ (CALCULATION). Without them, 452 ns: FAIL above 39.8 pF. I: README.md lists the two 4.7 kΩ pull-ups in its BOM and wiring table. T: NOT RUN (plan item P-4). |

## 5. PCB (home-etch)

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-027 | The PCB shall be single-sided: copper on B.Cu only, through-hole parts only, no vias, no copper pour, and no wire bridges apart from the 2 I2C configuration wires and the JP1 solder bridge. | Home etching | PD, ADR-007 | I | PASS | pcb_rules_check: all segments on B.Cu; 0 vias, 0 zones, 0 SMD pads. |
| REQ-028 | The board outline shall be 100 × 70 mm. | Hard constraint | PD | I | PASS | Outline 100.000 × 70.000 mm (pcb_rules_check on the CR-002 PCB). Board label: ADR-019 D-2 sets 'FrutaMIDI v1.2'; `pcb.label_v1.2` FAIL on 3a3684b (PCB still reads 'FrutaMIDI v1.1') until the generator text is changed. The label is not part of this requirement's statement, so the status stays PASS. |
| REQ-029 | Home-etch rules: signal tracks ≥ 1.0 mm (≥ 0.8 mm for short stubs), power tracks ≥ 1.2 mm, clearance ≥ 0.6 mm (DRC hard minimum 0.5 mm), annular ring ≥ 0.4 mm, drills ≥ 0.8 mm. | Undercut and drill wander | gen_pcb.py, hardware/README.md | I + A (DRC) | PASS | pcb_rules_check `SUMMARY: 16 checks, 16 PASS, 0 FAIL` on the CR-002 PCB (3a3684b; new R_Axial_DIN0414_P15.24mm_Horizontal_HomeEtch: drill 1.0 mm, ring 0.60 mm); minimum annular ring 0.40 mm. Clearance relies on the electronics DRC (hardware/build/drc.rpt, T-060: 0 violations), which systems did not re-run. |
| REQ-030 | The PCB shall provide 14 screw terminals at 5.08 mm pitch: GND, E0..E11, GND. Terminal k (k = 2..13) shall reach MPR121 electrode k − 2 through its series resistor. | Hard constraint | PD | I | PASS | interface_check J2.T1..T14 and A2.pin2..13. |
| REQ-031 | The firmware PCB pin map (I2C1 SDA GP26 / SCL GP27, button GP22, pot GP28/ADC2) shall match the PCB nets. The breadboard map (I2C0 GP4/GP5, button GP15, pot GP26) shall match README.md. | No dead board | Firmware, gen_pcb.py | I | PASS | interface_check: 0 pin mismatches. |

## 6. Cost

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-032 | The core BOM (assembled board, excluding tools, consumables and USB cable) shall cost ≤ 30 EUR. | Affordable kit | PD, ADR-007 D-7 | A | FAIL | 23.78–37.72 EUR (CALCULATION, sim/systems/budgets.out revision 6, T-070). R1–R12 pulse-rated Vishay MBE04140C3301FC100: 12 × 0.30–0.66 = 3.60–7.92 EUR (SOURCE EE-S26 sibling-value listings; equal 3k3 price ASSUMPTION), replacing 0.24–0.60 EUR. The upper bound exceeds the target by 7.72 EUR (was 0.40 EUR); the lower bound meets it. The increase is accepted for ESD safety (ADR-019 D-3); the status stays FAIL. Most other prices are ASSUMPTIONs; quoted prices from one supplier would narrow the range. |

## 7. Firmware variants and host software

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-033 | The firmware shall build without errors for Pico, Pico W, Pico 2 and Pico 2 W, each for the breadboard and PCB variants (FQBN `rp2040:rp2040:<board>:usbstack=tinyusb`, plus `-DFRUTAMIDI_PCB` for PCB), and for `arduino:avr:leonardo` (optional). | Supported boards | PD | T (compile) | PASS | `reports/firmware/T-044/build/*.log`: 9 of 9 logs (Pico, Pico W, Pico 2, Pico 2 W × std/PCB, plus Leonardo) contain 'Sketch uses'. A clean compile is not a hardware validation. |
| REQ-034 | The browser sampler `docs/index.html` shall work in Chrome and Edge (Web MIDI) on Windows and macOS. It shall map its 12 pads to notes 36–47 by default, treat Note On with velocity 0 as Note Off, send unmapped notes to the synthesiser, apply aftertouch (0xA0) to the filter, and offer a keyboard fallback and dropped-file samples. | Included sound source | PD | T | PARTIAL | Automated browser tests with a stubbed Web MIDI PASS (T-020, T-021 handoffs). A real browser, a real device and audible output are NOT RUN. |

## 8. Documentation

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-035 | All project files, code, comments, reports, generated PCB text, fabrication file names and user-visible strings shall be in English. | Project language rule | PD, ADR-004, ADR-005 | I | PASS | I: 0 Portuguese-word matches in firmware (`.ino`, `fm_*.h`), gen_*.py, docs/index.html, README.md, hardware/README.md and docs/manual/MANUAL.md. Silkscreen is English (SCALE, OCTAVE, ORIG, QT, legend, 'copper: bottom side'); fabrication file names are English; no broken relative links (`doc.links.*` PASS). |
| REQ-036 | The user and assembly manual shall match the current PCB. It shall cover both module revisions, the JP1 selector and data wires, flashing, first start, a valid pre-power continuity checklist and troubleshooting. | Non-technical end user | PD | I | PASS | I: hardware/README.md (assembly) matches the current PCB: JP1 and two wires, R15/R16 220 Ω, JP1 legend, a continuity test that accounts for the 3.3 kΩ resistors, English silkscreen names, valid links (interface_check documentation `17 checks, 17 PASS, 0 FAIL`). README.md documents the breadboard 4.7 kΩ pull-ups. docs/manual/MANUAL.md (user manual) refers to JP1 and covers BOOTSEL/UF2 and troubleshooting. The inspection covered consistency with the design, not readability. |

## 9. Physical validation only

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-037 | [PHYSICAL] Touch detection shall work on objects from a bare pad (about 20 pF) to large fruit or a glass of water (up to about 500 pF, ASSUMPTION), with leads of 20–50 cm, after recalibration. | Product promise | PD | T [PHYSICAL] | NOT RUN | A: the MPR121 can charge up to about 1203 pF (CALCULATION). Latency targets hold up to 210 pF at 400 kHz. AUTOCONFIG limits USL/TL/LSL = 200/180/130 at design VDD 3.2 V and SCTS = 0 (0x7C D7) are now SOURCE (ADR-010/011, MPR121 datasheet S-006 in management/SOURCES.md). T: NOT RUN. |
| REQ-038 | [PHYSICAL] There shall be no false Note On in 10 min idle with all 12 electrodes connected to objects, and no crosstalk when touching a neighbouring electrode. | Reliability on stage | Derived | T [PHYSICAL] | NOT RUN | |

## Open decisions

The full text is in `management/handoffs/systems-engineer/T-010.md`.

- D-5, D-9, D-10 and D-11 are closed by ADR-008, ADR-009 and ADR-012.
- No new open decisions in draft-3.
- draft-6 (T-070): ADR-019 D-1..D-4 applied; no new open decisions. REQ-032 FAIL is accepted by ADR-019 D-3, not waived.
