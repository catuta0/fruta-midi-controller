# FrutaMIDI user manual

> **Draft — not yet validated on hardware.**

This manual describes the firmware after task T-044 (commit `a208a30`) (`firmware/FrutaMIDI/FrutaMIDI.ino` and its `fm_*.h` headers) and the PCB at version 1.2 (change request CR-002; the firmware did not change in v1.2). Every behaviour below is traced to that source or to the project README; see [Traceability](#traceability) at the end. The complete build has not been tested on hardware, so this manual describes what the firmware is written to do, not measured behaviour.

## Contents

- [What FrutaMIDI does](#what-frutamidi-does)
- [Setup](#setup)
- [PCB v1.2: what to know before you build](#pcb-v12-what-to-know-before-you-build)
- [Playing](#playing)
- [Scales](#scales)
- [Octave](#octave)
- [Recalibration](#recalibration)
- [LED signals](#led-signals)
- [Troubleshooting](#troubleshooting)
- [Traceability](#traceability)

## What FrutaMIDI does

FrutaMIDI is a USB MIDI device. Each of its 12 pads (24 with a second sensor) sends a MIDI note when you touch the object connected to it. FrutaMIDI makes no sound itself: a program on the computer (the online sampler or a music program) turns the notes into sound.

## Setup

1. **Build the hardware.** Follow the [breadboard wiring](../../README.md#wiring) or the [PCB guide](../../hardware/README.md). For the PCB, read [PCB v1.2: what to know before you build](#pcb-v12-what-to-know-before-you-build) first.
2. **Load the firmware.** Download the `.uf2` file for your board and build from the [Releases](https://github.com/catuta0/fruta-midi-controller/releases/latest) page. The breadboard and the PCB need different files. Hold **BOOTSEL** while you plug in the USB cable, then drag the `.uf2` onto the drive that appears. Details: [Quick start](../../README.md#quick-start-no-programming).
3. **Connect the objects first.** Clip the leads onto the fruit before you plug in the USB, and do not touch anything while it starts. At startup the sensor measures each pad at rest; that reading is the reference for detecting touches.
4. **Wait for the LED.** Two slow blinks mean the sensor was found and FrutaMIDI is ready. See [LED signals](#led-signals) for the other patterns.
5. **Open a sound program.** Open the [online sampler](https://catuta0.github.io/fruta-midi-controller/) in Edge or Chrome, or a music program, and select FrutaMIDI as the MIDI input.

## PCB v1.2: what to know before you build

The [PCB guide](../../hardware/README.md) is the full assembly procedure. These are the points that changed in version 1.2 of the board (silkscreen "FrutaMIDI v1.2"):

- **Electrode resistors R1–R12.** Use 12 × 3.3 kΩ 1 % pulse-rated resistors, Vishay **MBE04140C3301FC100** (DIN0414 size, the large body). Do not use small DIN0204/0207 resistors: they are not rated for the voltage of an electrostatic spark ([PCB guide, Electrical safety](../../hardware/README.md#electrical-safety)).
- **They lie flat.** All 12 sit in one row between the module and the screw terminals, leads 15.24 mm apart. Bend each lead at least 1.5 mm from the body so the body is centred between its two holes, press it onto the board and solder. Do not stand them up: lying flat keeps the two ends of each resistor about 13 mm apart, which a spark cannot jump.
- **Assembly order.** Solder from the lowest part to the tallest: R1–R12 first, then R13–R14 (4.7 kΩ) and R15–R16 (220 Ω), the button, the Pico headers, the module headers, the potentiometer, the screw terminals, and last JP1 and the two configuration wires ([PCB guide, section 4](../../hardware/README.md#4-solder)).
- **JP1 stands upright** to the right of the module: **QT** at the top, **ORIG** at the bottom, 3V3 in the middle. Bridge the middle pad to **one** side only: ORIG for the original module (no white connectors), QT for the STEMMA QT module (two small white connectors). A wrong position can damage the sensor; check it before you insert the module ([PCB guide, section 5](../../hardware/README.md#5-module-configuration-jp1-and-two-wires)).
- **Two configuration wires.** J1, to the right of JP1, has two holes: SCL on the left, SDA on the right. Wire them to the S holes above the module's 7-pin row:

  | Module | JP1 | J1 SDA → | J1 SCL → |
  | --- | --- | --- | --- |
  | Original (no white connectors) | ORIG | S5 | S6 |
  | STEMMA QT (two white connectors) | QT | S3 | S4 |

  In v1.2 the wires are longer than before (about 25–35 mm). Use insulated solid wire, keep each wire flat against the board and no longer than needed, so it cannot be pushed onto the wrong hole or strain its joint.
- **Test before powering.** Follow the checklist in [section 6 of the PCB guide](../../hardware/README.md#6-test-before-powering): each terminal should read about 3.3 kΩ to its module pin, and the JP1 centre pad must reach only the S hole for your module (S1 for ORIG, S7 for QT).

The board has not been built or tested. These steps describe the design, not a verified build.

## Playing

- **Touch** an object: FrutaMIDI sends a Note On for that pad, with a fixed velocity of 100, on MIDI channel 1. Both values can be changed in the firmware.
- **Let go:** FrutaMIDI sends a Note Off for the same note. This holds even if you changed scale or octave while touching, so notes do not get stuck.
- **Press harder / touch more:** while you touch, FrutaMIDI sends Polyphonic Aftertouch from 0 to 127. A larger change in the sensor reading gives a higher value. If the value falls back to the bottom of the range while you are still touching, FrutaMIDI sends 0. When you let go, it sends aftertouch 0 just before the Note Off, so a program never keeps a leftover pressure value. Programs that use aftertouch respond to it; according to the README, the sampler opens a filter with it.
- **The LED** stays on while any pad is touched, except while a blink pattern is running (see [LED signals](#led-signals)).
- **Several pads at once** work. Normally each pad has its own note, but after an octave change two pads can play the same note. That note then keeps sounding until the last pad holding it is released, and its aftertouch is the stronger of the pads' values.
- **If the sensor stops answering during play**, FrutaMIDI releases that sensor's notes, the LED blinks fast, and it tries to restart the sensor about every 2 s. When the sensor answers again, the pads play again.

## Scales

FrutaMIDI has 6 scales. It always starts in scale 1, Drum Rack.

**To change scale:** briefly press the button and release it. FrutaMIDI moves to the next scale, and after the last scale it returns to scale 1. The LED then blinks the number of the new scale (1 to 6 blinks).

The pads keep playing while the LED blinks. If you press the button again before the blinks finish, FrutaMIDI moves to the next scale and the blinking starts over with the new number.

| # | Scale | Notes sent by pads 0–11 (MIDI note numbers, octave 0) | Octave knob |
| --- | --- | --- | --- |
| 1 | Drum Rack | 36 37 38 39 40 41 42 43 44 45 46 47 | Ignored |
| 2 | Major pentatonic | 48 50 52 55 57 60 62 64 67 69 72 74 | Applies |
| 3 | Minor pentatonic | 48 51 53 55 58 60 63 65 67 70 72 75 | Applies |
| 4 | Major | 48 50 52 53 55 57 59 60 62 64 65 67 | Applies |
| 5 | Natural minor | 48 50 51 53 55 56 58 60 62 63 65 67 | Applies |
| 6 | Chromatic | 48 49 50 51 52 53 54 55 56 57 58 59 | Applies |

The Drum Rack notes 36–47 match the 12 pads of the online sampler. In the melodic scales, once a pad runs past the last step of the scale, the next pad starts the same pattern one octave (12 notes) higher. With a second sensor, pads 12–23 continue the same pattern.

To change the scales, edit the scale table in the firmware source: `firmware/FrutaMIDI/fm_scales.h`.

## Octave

The octave knob (potentiometer) shifts every note of the melodic scales by whole octaves. It has 5 positions: −2, −1, 0, +1, +2. Each step moves all notes by 12. The knob has a small dead band at each boundary, so the octave does not flicker when the knob sits between two positions. In Drum Rack (scale 1) the knob has no effect.

The knob only works when the firmware has it enabled:
- **PCB build:** always enabled.
- **Breadboard build:** disabled by default. To use it, set `USE_POT = true` and compile the firmware yourself ([Firmware](../../README.md#firmware)).

## Recalibration

Recalibrate after you swap, move or add objects, or when a pad stays on by itself.

1. Take your hands off all objects.
2. **Hold the button for 0.8 s.** Recalibration starts while you are still holding; releasing the button afterwards does not change the scale.
3. FrutaMIDI first releases every sounding note (aftertouch 0 where needed, then Note Off), then restarts the sensor, which measures each pad at rest again. The LED gives 3 quick blinks.

While the sensor restarts, FrutaMIDI does not read the pads or the button. Wait for the 3 blinks before playing.

Unplugging and replugging the USB has the same effect, and also resets the scale to Drum Rack and the octave to 0.

## LED signals

| LED | Meaning |
| --- | --- |
| 2 slow blinks after power-up | Sensor found, ready |
| Blinking fast, continuously | Sensor not found, or lost during play. FrutaMIDI tries again about every 2 s |
| On | A pad is being touched |
| 1–6 blinks after a short button press | Number of the scale just selected |
| 3 quick blinks after a long button press | Recalibration done |

While one of the blink patterns is running, the LED shows the pattern rather than touches. The pads still work and still send notes.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| LED blinks fast and does not stop | The sensor is not answering. Unplug the USB, then check the sensor wiring: 3V3, GND, SDA, SCL. On the PCB (v1.2), check that JP1 is bridged to the right side for your module (QT at the top, ORIG at the bottom) and that the 2 configuration wires go to the right S holes (see [PCB v1.2](#pcb-v12-what-to-know-before-you-build) and [section 5 of the PCB guide](../../hardware/README.md#5-module-configuration-jp1-and-two-wires)). Also check that you loaded the right `.uf2`: breadboard or PCB. |
| A pad is always on | Recalibrate without touching anything. If it persists, the object may be too large: use a smaller piece. |
| Notes trigger without touching | Recalibrate. Keep cables apart. See [Design notes](../../README.md#design-notes) for threshold settings. |
| A pad does not react | Check the clip connection (use a nail or needle pushed into the fruit). Recalibrate. On the PCB, measure about 3.3 kΩ from the terminal to the module header pin; if not, resolder that resistor (R1–R12). |
| The octave knob does nothing | You are in Drum Rack (scale 1), or the breadboard firmware has the knob disabled (see [Octave](#octave)). |
| A note keeps sounding after I let go of a pad | Another pad may hold the same note (possible after an octave change); release that pad too. |
| A note is stuck in the program | Touch and release the same pad again: the Note Off releases it. |
| The LED does not light when I touch a pad | A blink pattern may still be running; the pads still play. Wait for it to finish. |
| The computer does not see FrutaMIDI | See [Troubleshooting](../../README.md#troubleshooting) in the main README (cable, USB stack, program settings). |

## Traceability

The firmware source is commit `a208a30` (T-044). sha256 values:
- `FrutaMIDI.ino` 84f798203a116f1f2d21835a6e04dee9715d28a97cb695bf7abc08eb8c77e73c
- `fm_aftertouch.h` 1068ecd62b38f8b40ee8f1a4c8ac4aaceab83d0039b19784a1f9566f4c9a1297
- `fm_blink.h` f181d70f7dcd74b7cddf15f14b2e9c2fa67ee1e3a9b1387170e3f853692b675a
- `fm_button.h` 32bd40cd9bb316e67d0a67fb2025085fdd57f1fcdfd2cce132bbc3024d62de63
- `fm_mpr121.h` 98c28d469b62d0892c08331c5f9d538ec7ff8466a905140c0db73b7ecda3993b
- `fm_notes.h` 8038e2ee0c870766e925ec3d94053bb39a47fd96f0c5d11279e2fef516f04041
- `fm_pot.h` 99d889881f53c227530add5c31cdff377cb85fe0a04b3a44fc2792eb7596c7db
- `fm_scales.h` 3ca6dca471699192abfad0872c77b67c08822ccb67e37351022ea9db710e7150
- `fm_sensor_health.h` 10924a7bf487723505ffba81886887ce3be98f8ed337e8d1e3220de3ae5b2ffe

| Claim | Value | Label | Evidence |
| --- | --- | --- | --- |
| Fixed velocity, channel | 100, 1 | SOURCE | `VELOCITY`, `MIDI_CHANNEL` (FrutaMIDI.ino) |
| Note Off of the stored note | — | SOURCE | `fm_notes.h` `PadNotes`: each pad stores its note; Note Off is sent for that note |
| Shared note: one Note On, Note Off on the last release, aftertouch = max | — | SOURCE | `fm_notes.h`: reference count per note, Note On on 0 → 1, Note Off on 1 → 0 (after AT 0), shared aftertouch = max of holders (ADR-017) |
| Sensor lost during play: release, fast blink, retry | 3 failed transactions or ECR changed; retry > 2000 ms | SOURCE | `fm_sensor_health.h`: `SENSOR_FAIL_LIMIT = 3`, `SENSOR_CHECK_MS = 250`, `SENSOR_RETRY_MS = 2000`; `sensorLost()` releases the sensor's pads (ADR-017) |
| Aftertouch range | 0–127 | SOURCE | `fm::pressure_from_delta()` with `TOUCH_THRESHOLD = 12`, `AT_MAX_DELTA = 120` |
| Aftertouch 0 on a fall to the floor and before Note Off | — | SOURCE | `pressure_should_send()`: `if (p == 0) return lastSent > 0;` and `releasePad()`: `pressure_reset_on_release()` then `midiPolyPressure(note, 0)` |
| LED on while touched, pattern has priority | — | SOURCE | `digitalWrite(LED_BUILTIN, led.level_or(millis(), anyTouched))`; `Blinker::level_or()` returns the pattern while it is active |
| Blinking does not stop the pads | — | SOURCE | `fm_blink.h`: a non-blocking `Blinker` ticked from `loop()`; no `delay()` |
| A new press during a blink restarts it | — | SOURCE | `Blinker::start()`: "start() while active restarts with the new pattern"; `nextScale()` calls `led.start()` |
| 6 scales, start in Drum Rack, wrap-around | — | SOURCE | `SCALES[]` in fm_scales.h (English names), `scaleIdx = 0`, `fm::next_scale_index()` |
| Pad-to-note table | see Scales table | CALCULATION | `fm::note_for_pad()`: root + 12·octave + steps[pad mod len] + 12·⌊pad / len⌋, clamped 0–127. Roots 36 / 48. Same formula and values as in e4668d4, so the table from T-031 is unchanged. Range at octave −2…+2: 24 to 99. |
| Drum Rack ignores the octave | — | SOURCE | `fixed = true`; `int oct = sc.fixed ? 0 : octaveShift` |
| Octave positions and dead band | −2…+2, 5 zones, 0.7 zone | SOURCE | `fm_pot.h`: `octave_from_adc()`, `POT_HYSTERESIS = 0.7f` |
| Knob enabled on PCB / disabled on breadboard | true / false | SOURCE | `USE_POT` under `#ifdef FRUTAMIDI_PCB` |
| Long press | > 800 ms, fires while held | SOURCE | `fm_button.h`: `BUTTON_LONG_MS = 800`; LongPress "fires once, while still held"; ShortPress only if no long press fired |
| Recalibration sequence | release all, restart, 3 blinks | SOURCE | `recalibrate()`: `releaseAll(); startSensors(); led.start(…, BLINK_RECAL_TIMES, BLINK_RECAL_MS)`; 3 × 60 ms |
| Pads and button not read during the sensor restart | — | SOURCE | `startSensors()` runs inside `recalibrate()` before `loop()` continues; reports/firmware/coverage.md lists the long-press block during `startSensors()` for hardware test |
| Startup ready signal | 2 blinks of 120 ms | SOURCE | `BLINK_READY_TIMES = 2`, `BLINK_READY_MS = 120`, started in `setup()` when a sensor is found |
| Sensor-missing signal and retry | toggles every 100 ms, retry every 2000 ms | SOURCE | `loop()`: `(millis() / 100) % 2`, `SENSOR_RETRY_MS = 2000` |
| Scale blinks | N × 90 ms | SOURCE | `BLINK_SCALE_MS = 90` |
| Power cycle resets scale and octave | 0 / 0 | SOURCE | initial values of `scaleIdx` and `octaveShift` |
| Startup reference measurement | — | SOURCE | `startSensors()` calls `begin()` with `AUTOCONFIG`, then `configureSensor()` |
| Sampler pads on notes 36–47; aftertouch opens filter | — | README | README "Sound"; not traced to `docs/index.html` |
| Flashing procedure, BOOTSEL, `.uf2` names | — | README | README "Quick start" |
| R1–R12 part, size, lying flat | Vishay MBE04140C3301FC100, 3.3 kΩ 1 %, DIN0414, 15.24 mm lead pitch | SOURCE | hardware/README.md (BOM, section 4 step 1); management/INTERFACES.json frozen-4 `board.resistors`; ADR-019 D-1 |
| Distance between the two ends of each resistor | about 13 mm (13.04 mm copper gap) | MEASUREMENT (design file) | sim/electronics/calc/check_gap.out; reports/electronics/analysis.md §5 |
| Assembly order | lowest to tallest, R1–R12 first, JP1 and wires last | SOURCE | hardware/README.md section 4 |
| JP1 upright, QT top / ORIG bottom | — | SOURCE | hardware/README.md section 5; INTERFACES.json frozen-4 `board.placement_mm.JP1` (rotation 90°); ADR-019 D-4 |
| J1 SCL left / SDA right; S holes per module | S5/S6 original, S3/S4 STEMMA QT | SOURCE | hardware/README.md section 5 table; INTERFACES.json IF-MPR121-MODULE |
| Configuration wire length in v1.2 | about 25–35 mm | CALCULATION (T-060, layout) | management/handoffs/electronics-engineer/T-060.md; management/RISKS.md R-008 |
| Board label | "FrutaMIDI v1.2" | SOURCE | hardware/scripts/gen_pcb.py; ADR-019 D-2 |
