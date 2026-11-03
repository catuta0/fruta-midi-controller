# FrutaMIDI architecture options (input for the manager's ADR)

Author: systems-engineer · T-008 · 2026-10-30. Status: proposal; the manager writes the ADR.

All three options use the same host side: USB MIDI 1.0 class-compliant, with the browser sampler or a DAW. They differ in how touch is sensed and which microcontroller is used. Unless a value cites budgets.out or a source, it is an ASSUMPTION.

## Options

**A. Pico + Adafruit MPR121 breakout (1982). This is the current design.**
- A socketed Pico talks over I2C to a socketed MPR121 module.
- The MPR121 does the sensing in hardware: it sets the charge current and time for each electrode automatically, tracks the baseline, and filters in two stages.
- Status: firmware exists, and the PCB exists with DRC 0 violations (report not re-run here).

**B. Pico with native capacitive sensing (no MPR121).**
- Each electrode connects to a Pico GPIO through a high-value resistor, for example 1 MΩ (ASSUMPTION).
- A PIO program times the RC charge or discharge for all 12 pins in parallel.
- Baseline tracking, filtering and auto-calibration are written in firmware.

**C. ATmega32u4 Pro Micro + Adafruit MPR121.**
- The sensing chain is the same as A, with the Pico replaced by a Pro Micro or Leonardo-class board.
- USB MIDI comes from the MIDIUSB library.
- The current firmware already has this branch (`__AVR_ATmega32U4__`).

## Comparison (same criteria for each option)

| Criterion | A: Pico + MPR121 | B: Pico native sensing | C: Pro Micro + MPR121 |
| --- | --- | --- | --- |
| Core BOM cost | 23.60–34.60 EUR (CALCULATION, budgets.out) | 14.20–22.20 EUR. A minus the module (9–12 EUR) and its two headers (0.90 EUR), plus 12 resistors (about 0.50 EUR) (CALCULATION from ASSUMPTION prices) | 22.60–34.60 EUR. A with a clone Pro Micro at 4–8 EUR in place of the Pico (ASSUMPTION); a genuine board costs much more |
| Part count (populated) | 2 modules + 4 sockets + 7 terminal blocks + SW + RV = 15, plus 3 wires | 1 module + 2 sockets + 12 R + 7 terminal blocks + SW + RV = 24, no wires | Same as A, with a different MCU socket (2×12) |
| Sensitivity and robustness with fruit or water | Good. Autoconfiguration charges up to about 1.2 nF (CALCULATION). The baseline filter is in hardware. Latency rises above about 109 pF (design rule) | Unproven. With 1 MΩ and 100–1000 pF, τ = 0.1–1 ms. Mains hum and humidity drift must be filtered in firmware. Pico 2 (RP2350 A2) has a known GPIO input-leakage erratum (E9) affecting high-impedance inputs. That is an ASSUMPTION from prior knowledge, not read here, and must be checked | Same as A |
| Latency floor | 4 ms (SFI × ESI) at the sensor. Worst case 9.56–12.83 ms for C ≤ 100 pF (CALCULATION) | Potentially below 1 ms per parallel PIO scan, plus firmware filtering (ASSUMPTION). This is the only option that could meet a 1 ms jitter target | Same as A. A 16 MHz AVR adds slightly more I2C overhead (ASSUMPTION) |
| Home-etch feasibility | Good. All THT, large pads, 3 configuration wires. The annular ring is 0.30 mm on oval pads (REQ-029 FAIL, fixable) | Good. 12 more THT resistors, but no module-revision wiring. All 12 GPIO traces become sensor lines and need spacing | Good. The Pro Micro footprint is small; module wiring is as in A |
| Firmware effort | Low. Exists. Mitigations M1 (burst read) and non-blocking LED are small | High. A PIO timing program, per-pad calibration, drift tracking, a touch-intensity metric for aftertouch, and noise rejection, all of which need tuning on real objects | Low. A branch exists. There is no UF2 drag-and-drop: flashing needs the IDE or avrdude and the Caterina bootloader |
| End-user flashing | UF2 drag-and-drop (BOOTSEL) | UF2 drag-and-drop | Worse for a non-technical user |
| Constraint compliance | Uses the fixed bought-in parts (Pico family, Adafruit 1982) | Drops the Adafruit 1982, which PD lists as a part not to redesign. That needs a definition change | Drops the Pico family, which PD lists as fixed. That needs a definition change |
| Main risks | ESD on bare electrodes (REQ-023); I2C rise time at 400 kHz (REQ-026); latency and jitter targets (REQ-014/015); wiring the wrong configuration hole (REQ-024); module price and availability | Sensing performance unknown until measured; RP2350 erratum; ESD straight into RP2040/RP2350 GPIO; schedule | Clone quality; 5 V and 3.3 V Pro Micro variants confuse builders; the definition conflict |
| Risk level (qualitative) | Low–medium | High | Medium |

## Recommendation

**Keep option A** (Pico + Adafruit MPR121) as the baseline. It is the only option that meets the fixed-part constraints in PD without changing the definition. It also has existing firmware and PCB, and the lowest technical risk with fruit and water.

Attach these actions to the ADR:
1. **Firmware:** read aftertouch data with one burst read (M1). Make the LED feedback non-blocking (REQ-016).
2. **Decision D-5:** choose the I2C clock. Either keep 400 kHz and measure the rise time (P-4), or drop to 100 kHz. The 100 kHz route costs loop time but is in spec for C_b ≤ 142 pF.
3. **Decisions D-2 and D-4:** for the electronics engineer.
   - D-2: add a series resistor per electrode (and optionally a TVS array) between each terminal and the module row. The value must be chosen against the MPR121 charge time (R·C ≪ CDT), so it needs analysis before it is adopted.
   - D-4: re-arrange J1 and the S-row so that no single misplaced wire can short 3V3 to GND.
4. **Decision D-1:** relax REQ-015 (jitter), or accept that it fails. Option A cannot reach 1 ms of jitter.

Keep **option B** as a research spike, valid only if the manager or the user wants a sub-module cost or below-1 ms jitter. It would need a definition change and physical tests, which this project cannot run.

**Reject option C.** It conflicts with the fixed Pico family and makes flashing worse for end users. Its only advantage, an existing firmware branch, does not need the hardware to change.
