# Requirements

Owner: systems-engineer. Revision: draft-2 (T-010, 2026-10-30), proposed and not yet baselined. The previous revision, draft-1 (T-008), is replaced.

Inputs are the working tree on top of a63257d. The PCB, firmware and documentation snapshot checksums are in `management/handoffs/systems-engineer/T-010.md`. Targets follow ADR-007; the relaxations of REQ-014 and REQ-015 are flagged for user review.

Verification methods: **A** Analysis, **S** Simulation, **I** Inspection, **T** Test.

Status rules:
- Status covers only the verification that was actually performed: PASS, PARTIAL, FAIL, BLOCKED or NOT RUN.
- A requirement whose analysis or inspection passes, but whose test is still NOT RUN, is PARTIAL.
- Requirements marked **[PHYSICAL]** can only be closed by measurements on built hardware. Flashing and powering hardware are out of scope for this project.

Evidence paths:
- `sim/systems/budgets.out`: budgets and latency (revision 2)
- `sim/systems/interface_check.out`: pins, nets, jumper and documentation links
- `sim/systems/pcb_rules_check.out`: home-etch rules
- `reports/systems/budgets.md`
- `management/INTERFACES.json`

Sources are referenced as S-xx (see `requirements/SOURCES_SYSTEMS.md`). PD means `management/PROJECT_DEFINITION.md`. The machine-readable table is `requirements/requirements.csv`.

## Summary

| Status | Count |
| --- | --- |
| PASS | 14 |
| PARTIAL | 17 |
| FAIL | 5 |
| NOT RUN | 5 |
| BLOCKED | 0 |
| Total | 41 |

## 1. Function

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Each of the 12 electrode inputs E0–E11 (MPR121 ELE0–ELE11) shall send one MIDI Note On, on the configured channel (default 1) with the configured fixed velocity (default 100, range 1–127), when a touch is detected. It shall send a Note Off for the same note when the touch is released. | Core function | PD | I + T [PHYSICAL] | PARTIAL | I: PASS. The chain terminal → series resistor → module electrode is 1:1 (interface_check `pcb.A2.pin2..13`, `pcb.J2.*`). T: NOT RUN. |
| REQ-002 | The Note Off for a pad shall carry the note number sent in its Note On, even if the scale or octave changed in between. All sounding notes shall be released before a recalibration. | No stuck notes | Derived from REQ-001 | T (host unit test) + T [PHYSICAL] | PARTIAL | Host tests PASS: `reports/firmware/T-040/pytest_tests_firmware.log` ("213 passed"). Hardware test NOT RUN. |
| REQ-003 | The firmware shall support a second MPR121 at I2C address 0x5B (`NUM_SENSORS = 2`), mapping its electrodes to pads 12–23. This is a breadboard-only option; the PCB carries one module (ADR-007 D-3). | Expansion to 24 inputs | PD, ADR-007 | A + T [PHYSICAL] | PARTIAL | A: PASS for latency at 400 kHz (11.50 ms ≤ 15 ms). A: FAIL at 100 kHz (17.98 ms) (budgets.out §b). T: NOT RUN. |
| REQ-004 | While a pad is touched, the device shall send Polyphonic Key Pressure (0xAn) with a value 0–127. The value shall map linearly from delta = baseline − filtered, clamped to [12, 120]. It shall be evaluated every 15 ms and sent only when it changes by at least 2. | Expressive control | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS (T-040, `test_aftertouch.py`). Hardware NOT RUN. |
| REQ-005 | The device shall provide 6 scales, selected cyclically: Drum Rack (36–47, octave ignored, the power-on default), major pentatonic, minor pentatonic, major, natural minor and chromatic (root 48). Notes shall be clamped to 0–127. | Musical use; sampler default mapping | PD, firmware | A + T (host) | PASS | A: notes 24–99 with 12 pads and 24–127 with 24 pads, never clamped (T-009 budgets §d). Host tests PASS (T-040 `test_scales.py`). |
| REQ-006 | The octave potentiometer shall shift melodic scales by −2..+2 octaves using 5 ADC zones with a hysteresis of 0.7 zone. It shall have no effect on Drum Rack, and shall be enabled by default on the PCB build. | Live octave control | PD | A + T (host) + T [PHYSICAL] | PARTIAL | A: the ADC offset of 30 mV (SOURCE S-01 §4.3) is 6.5 % of the 0.462 V hysteresis (CALCULATION). Host tests PASS (`test_pot.py`). Hardware NOT RUN. |
| REQ-007 | A short press of the button (released within 800 ms, sampled every 10 ms) shall select the next scale, and the LED shall blink N times for scale N. | User control | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS (`test_button.py`, `test_blink.py`). Hardware NOT RUN. |
| REQ-008 | A press of more than 800 ms shall release all notes and recalibrate all sensors; the LED then blinks 3 times. | Recalibration after moving objects | PD | T (host) + T [PHYSICAL] | PARTIAL | Host tests PASS. Recalibration blocks for 16.8–22.1 ms per sensor at 400 kHz (CALCULATION); this is user-requested and allowed by REQ-016. Hardware NOT RUN. |
| REQ-009 | If no MPR121 answers, the device shall send no MIDI, blink the LED at 5 Hz and retry every 2 s. | Diagnosable fault state | Firmware | T [PHYSICAL] | NOT RUN | |
| REQ-010 | The LED shall give 2 slow blinks at start when a sensor is found, and shall be lit while any pad is touched. On Pico W and Pico 2 W the LED is driven through the CYW43 (WL_GPIO0). | User feedback | Firmware, S-02 | T [PHYSICAL] | NOT RUN | |

## 2. USB and host

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-011 | The device shall enumerate as a USB MIDI 1.0 class device (MIDIStreaming, bulk endpoints). It shall work without vendor drivers on Windows 10, Windows 11 and macOS 12 or later. | Non-technical end user | PD, ADR-007 D-6, S-14 | T [PHYSICAL] | NOT RUN | |
| REQ-012 | The USB product string and the MIDI port name shall be "FrutaMIDI". | Recognisable in DAWs and in the sampler | Firmware | I + T [PHYSICAL] | PARTIAL | I: `DEVICE_NAME = "FrutaMIDI"` is passed to `setProductDescriptor` and `setStringDescriptor`. T: NOT RUN. |
| REQ-013 | The device shall send only Note On (0x9n, CIN 0x9), Note Off (0x8n, velocity 0, CIN 0x8) and Polyphonic Key Pressure (0xAn, CIN 0xA), on one channel n = MIDI_CHANNEL − 1. Incoming MIDI shall be read and discarded. | Interface definition | S-14, S-15 | I | PASS | `fm_midi.h` constants match S-14 Table 4-1. |
| REQ-014 | Device latency from touch to the USB-MIDI packet being available to the host shall be ≤ 15 ms worst case, for electrode capacitance ≤ 100 pF, with mitigation M1 (one burst read per sensor per aftertouch pass). | Playability; ADR-007 D-1 relaxation from the earlier unsourced 10 ms | ADR-007 | A + T [PHYSICAL] | PARTIAL | A: PASS. 1 sensor 10.30 ms, 2 sensors 11.50 ms at 400 kHz (the clock retained by ADR-008); 100 kHz would give 13.54 ms. Design limit C ≤ 210 pF (CALCULATION, budgets.out §b). Based on the firmware's actual transactions: `touched()` (2 B) plus burst reads of 24 B and 12 B (M1, already in FrutaMIDI.ino sha256 b3f25158). Depends on firmware T-041. T: NOT RUN (plan item P-2). Flagged for user review. |
| REQ-015 | Latency jitter (worst minus best) shall be ≤ 10 ms for electrode capacitance ≤ 100 pF. | ADR-007 D-1; the MPR121 sets a 4 ms floor (ADR-006) | ADR-007 | A + T [PHYSICAL] | PARTIAL | A: PASS. 6.30 ms at 400 kHz, 9.54 ms at 100 kHz (0.46 ms margin). T: NOT RUN. |
| REQ-016 | During play, no firmware action other than a user-requested recalibration shall block touch processing for more than 10 ms. | Avoid delayed or stuck notes | Derived | I + A | PASS | I: the only `delay()` is `delay(10)` in `midiBegin()` (setup); LED feedback uses the non-blocking `fm_blink.h` (T-040). A: worst loop 1.30 ms at 400 kHz. Depends on firmware T-041, which is still being finished; re-check after it lands. |

## 3. Power and supply

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-017 | The device shall be powered only from USB VBUS through the Pico's micro-USB connector. No other power input shall exist. | Hard constraint | PD | I | PASS | Pico pins 39 and 40 are unconnected (`pcb.A1.no_other_nets`). |
| REQ-018 | The device shall operate with VBUS from 4.40 V to 5.50 V at its connector. | Full USB 2.0 VBUS range | S-10 | A + T [PHYSICAL] | PARTIAL | A: VSYS 3.95–5.25 V, inside the SOURCE S-01 range of 1.8–5.5 V: PASS. However, the 4.40 V low-power-port minimum is below the Pico's recommended VBUS of 5 V ± 10 % (4.50 V; S-01 §2.3): budgets check A3b FAIL. The diode drop is an ASSUMPTION. T: NOT RUN. |
| REQ-019 | VBUS current shall be ≤ 100 mA (the declared bMaxPower, S-11) for every supported Pico board. | One unit load; declared value | S-10, S-11 | A + T [PHYSICAL] | PARTIAL | A: worst case 55.6 / 70.6 / 60.6 / 75.6 mA for Pico / Pico W / Pico 2 / Pico 2 W. The lower bounds are SOURCE (S-01 Table 3 9.9 mA, S-16 Table 2 12.74 mA). The upper bounds are ASSUMPTIONs because neither datasheet covers a busy USB-MIDI loop at 200 MHz. T: NOT RUN (plan item P-3). |
| REQ-020 | The external load on the Pico 3V3(OUT) shall be ≤ 300 mA with at least 50 % margin. | Regulator recommendation | S-01 §2.1 | A | PASS | 10.15 mA worst case with 2 sensors and PCB pull-ups: 96.6 % margin. |
| REQ-021 | The MPR121 VDD, fed from the Pico 3V3 through the module LDO, shall be within 2.0–3.6 V. | Sensor operating range | S-04, S-06, S-07 | A | PASS | 3.10–3.40 V (CALCULATION; dropout and rail tolerance are ASSUMPTIONs). |

## 4. User safety and robustness

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-022 | Every user-touchable conductor shall be at ≤ 3.6 V relative to GND and shall be supplied only from the USB SELV source. | Users touch electrodes directly | PD | A | PASS | Electrodes are charged from MPR121 VDD ≤ 3.6 V (S-04), and REQ-017 holds. |
| REQ-023 | Each user-touched electrode terminal shall survive ±4 kV contact discharge without permanent damage. The ±4 kV target is an ASSUMPTION, following IEC 61000-4-2 level 2 (the standard was not read). | Bare human touch on sensor pins | Derived; S-04; ADR-007 D-2 | I + A + T [PHYSICAL] | PARTIAL | A: PASS at ±4 kV. With 3.3 kΩ series per electrode (R1–R12), the peak current is 1.10 A, against a 1.33 A pin limit inferred from the HBM ±2 kV rating (ASSUMPTION) (`reports/electronics/analysis.md`, ADR-008). My own check gives the same 1.10 A (CALCULATION). At 8 kV the peak is 2.20 A (1.65× over): PARTIAL, accepted as documented risk R-006. The resistor pulse rating is not checked. Sensing impact: sensitivity factor 0.904 (EE); τ/CDT ≤ 0.10; I·R offset 0.208 V (CALCULATION). T: NOT RUN [PHYSICAL]; it needs an ESD generator. |
| REQ-024 | A misplaced SDA or SCL hand wire shall not connect an I2C line to a supply hole. | Hand wiring by a non-expert builder | Derived | I + A | FAIL | I (interface_check, current PCB): the SDA/SCL hand wires from J1 (1 = SCL, 2 = SDA) can reach S1/S7 (+3V3 when JP1 is bridged) and S2/S6 (module 3.3 V output). An I2C low then drives the RP2040 pad against a supply; the current is limited only by the pad driver (ASSUMPTION). T-052 did not change this. Mitigation option: 220 Ω series resistors in SDA/SCL, limiting the fault current to ≤ 15 mA (CALCULATION). Open decision D-9. |
| REQ-025 | One PCB shall accept both Adafruit 1982 revisions. JP1 bridges ORIG (+3V3 → S1 = VIN) or QT (+3V3 → S7 = VCC). The SDA/SCL wires from J1 go to S5/S6 (original) or S3/S4 (STEMMA QT). | The bought-in part exists in two pinouts | PD, S-05..S-07, ADR-007 D-4 | I + T [PHYSICAL] | PARTIAL | I: PASS (`pcb.JP1_selector`, `pcb.JP1_targets`, the S-row labels, `pcb.J1`). T: NOT RUN. |
| REQ-026 | The PCB-build I2C bus shall meet the rise time for its clock: ≤ 300 ns at 400 kHz (≤ 1000 ns at 100 kHz), with the module at 0x5A. | Sensor interface within spec | S-04, S-13 | A + T [PHYSICAL] | PARTIAL | A: PASS. R13/R14 4.7 kΩ: electronics gives 103 ns at 38 pF and 135 ns at 50 pF (`reports/electronics/analysis.md`). My check, which also includes the module 10 kΩ and a 50 kΩ internal pull-up, gives 153 ns at 60 pF, with a C_b limit of 117.8 pF at 400 kHz; sink current 1.43 mA ≤ 3 mA (CALCULATION). The clock stays at 400 kHz (ADR-008, D-5 closed). T: NOT RUN (plan item P-4). |
| REQ-039 | No position of the JP1 3V3 selector (ORIG, QT, open) shall connect +3V3 to GND. | ADR-007 D-4: removes the T-008 wrong-hole short | ADR-007 | I | PASS | S1 and S7 are never GND in either revision (`pcb.JP1_no_gnd_reachable`). |
| REQ-040 | A wrong JP1 position (ORIG on a STEMMA QT module, or QT on an original module), or both sides bridged, shall not apply a voltage outside the MPR121 absolute maximum ratings (inputs ≤ VDD + 0.3 V, S-04 Table 3), and shall not short +3V3 through a module output. | Builder error tolerance | Derived from ADR-007 D-4 | A | FAIL | The ORIG bridge on a QT module puts +3V3 on ADDR while the module is unpowered. The QT bridge on an original module puts +3V3 on IRQ while the module is unpowered. Both exceed VDD + 0.3 V, back-powering the module through its input clamp. Bridging both sides on an original module ties +3V3 to the open-drain IRQ output, which shorts through the MPR121 when IRQ asserts. Expected outcome: sensor not found; the damage risk is low but unquantified (ASSUMPTION; S-04 latch-up rating ±100 mA). Open decision D-10. |
| REQ-041 | The breadboard-build I2C bus (no PCB pull-ups) shall meet the rise time for its clock. | Same as REQ-026, for the breadboard build | S-13 | A + T [PHYSICAL] | FAIL | A: on the breadboard (no R13/R14), R_eff 8.33 kΩ gives t_r 424 ns at 60 pF, which fails the 300 ns limit at 400 kHz (C_b limit 42.5 pF). ADR-008 keeps 400 kHz, so the breadboard build needs the 4.7 kΩ pull-ups documented in the README, or a measurement (P-4). Open decision D-11. |

## 5. PCB (home-etch)

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-027 | The PCB shall be single-sided: copper on B.Cu only, through-hole parts only, no vias, no copper pour, and no wire bridges apart from the 2 I2C configuration wires and the JP1 solder bridge. | Home etching | PD, ADR-007 | I | PASS | pcb_rules_check: all segments on B.Cu; 0 vias, 0 zones, 0 SMD pads. |
| REQ-028 | The board outline shall be 100 × 70 mm. | Hard constraint | PD | I | PASS | Outline 100.000 × 70.000 mm. Separate finding: the PCB silkscreen still reads 'FrutaMIDI v1.0' where ADR-008 requires v1.1 (interface_check `pcb.label_v1.1` FAIL). |
| REQ-029 | Home-etch rules: signal tracks ≥ 1.0 mm (≥ 0.8 mm for short stubs), power tracks ≥ 1.2 mm, clearance ≥ 0.6 mm (DRC hard minimum 0.5 mm), annular ring ≥ 0.4 mm, drills ≥ 0.8 mm. | Undercut and drill wander | gen_pcb.py, hardware/README.md | I + A (DRC) | PASS | pcb_rules_check `SUMMARY: 14 checks, 14 PASS, 0 FAIL`; minimum annular ring 0.40 mm. Clearance relies on the electronics DRC (ERC 0, DRC 0, unconnected 0, parity 0; manager re-run, `reports/electronics/analysis.md`), which systems did not re-run. |
| REQ-030 | The PCB shall provide 14 screw terminals at 5.08 mm pitch: GND, E0..E11, GND. Terminal k (k = 2..13) shall reach MPR121 electrode k − 2 through its series resistor. | Hard constraint | PD | I | PASS | interface_check J2.T1..T14 and A2.pin2..13. |
| REQ-031 | The firmware PCB pin map (I2C1 SDA GP26 / SCL GP27, button GP22, pot GP28/ADC2) shall match the PCB nets. The breadboard map (I2C0 GP4/GP5, button GP15, pot GP26) shall match README.md. | No dead board | Firmware, gen_pcb.py | I | PASS | interface_check: 0 pin mismatches. |

## 6. Cost

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-032 | The core BOM (assembled board, excluding tools, consumables and USB cable) shall cost ≤ 30 EUR. | Affordable kit | PD, ADR-007 D-7 | A | FAIL | 20.38–30.30 EUR (CALCULATION). Nearly all prices are ASSUMPTIONs; the upper bound exceeds the target by 0.30 EUR. Quoted prices from one supplier would close this. |

## 7. Firmware variants and host software

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-033 | The firmware shall build without errors for Pico, Pico W, Pico 2 and Pico 2 W, each for the breadboard and PCB variants (FQBN `rp2040:rp2040:<board>:usbstack=tinyusb`, plus `-DFRUTAMIDI_PCB` for PCB), and for `arduino:avr:leonardo` (optional). | Supported boards | PD | T (compile) | PASS | `reports/firmware/T-041/build/*.log`: 9 of 9 logs contain "Sketch uses …". A clean compile is not a hardware validation. |
| REQ-034 | The browser sampler `docs/index.html` shall work in Chrome and Edge (Web MIDI) on Windows and macOS. It shall map its 12 pads to notes 36–47 by default, treat Note On with velocity 0 as Note Off, send unmapped notes to the synthesiser, apply aftertouch (0xA0) to the filter, and offer a keyboard fallback and dropped-file samples. | Included sound source | PD | T | PARTIAL | Automated browser tests with a stubbed Web MIDI PASS (T-020, T-021 handoffs). A real browser, a real device and audible output are NOT RUN. |

## 8. Documentation

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-035 | All project files, code, comments, reports, generated PCB text, fabrication file names and user-visible strings shall be in English. | Project language rule | PD, ADR-004, ADR-005 | I | PARTIAL | Now English: firmware (`.ino`, `fm_*.h`), gen_*.py, PCB silkscreen ("SCALE", "OCTAVE", "ORIG", "QT", "copper: bottom side"), `hardware/fabrication/` file names, docs/index.html (0 Portuguese matches in a scan). Remaining: README.md and hardware/README.md link to the old Portuguese paths `fabrico/…` (broken links, `doc.links.*` FAIL) and quote the silkscreen as "ESCALA"/"OITAVA". |
| REQ-036 | The user and assembly manual shall match the current PCB. It shall cover both module revisions, the JP1 selector and data wires, flashing, first start, a valid pre-power continuity checklist and troubleshooting. | Non-technical end user | PD | I | FAIL | As of this snapshot, hardware/README.md still describes the J1 3V3 wire (no JP1). Its continuity test expects a beep from terminal to module, which now passes through 3.3 kΩ. Its links are broken (interface_check `doc.hw_readme.*`, 7 FAIL). This may be work in progress by the documentation engineer. |

## 9. Physical validation only

| ID | Statement | Rationale | Source | Method | Status | Evidence / notes |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-037 | [PHYSICAL] Touch detection shall work on objects from a bare pad (about 20 pF) to large fruit or a glass of water (up to about 500 pF, ASSUMPTION), with leads of 20–50 cm, after recalibration. | Product promise | PD | T [PHYSICAL] | NOT RUN | A: the MPR121 can charge up to about 1203 pF (CALCULATION). The latency targets hold up to 210 pF at 400 kHz. |
| REQ-038 | [PHYSICAL] There shall be no false Note On in 10 min idle with all 12 electrodes connected to objects, and no crosstalk when touching a neighbouring electrode. | Reliability on stage | Derived | T [PHYSICAL] | NOT RUN | |

## Open decisions

The full text is in `management/handoffs/systems-engineer/T-010.md`.

- **D-5:** closed by ADR-008 (400 kHz).
- **D-11:** breadboard I2C pull-ups (REQ-041).
- **D-9:** protection of the I2C data wires (REQ-024).
- **D-10:** wrong JP1 position (REQ-040).
