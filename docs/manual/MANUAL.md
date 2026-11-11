# FrutaMIDI user manual

> **Draft — not yet validated on hardware.**

This manual describes the firmware after task T-044 (commit `a208a30`) (`firmware/FrutaMIDI/FrutaMIDI.ino` and its `fm_*.h` headers) and the PCB at version 1.3 (change request CR-003: single copper layer on the component side, all parts surface-mounted, for home chemical etching; decisions ADR-023 to ADR-028; branch `change/CR-003` at `f6693c9`, the board after the review fixes of task T-103). The firmware and the PCB pin map did not change in v1.3 (REQ-031). Every behaviour below is traced to that source, to the [PCB guide](../../hardware/README.md) or to the project README; see [Traceability](#traceability) at the end. The complete build has not been tested on hardware, so this manual describes what the firmware is written to do and how the board is designed, not measured behaviour.

## Contents

- [What FrutaMIDI does](#what-frutamidi-does)
- [Setup](#setup)
- [PCB v1.3: what to know before you build](#pcb-v13-what-to-know-before-you-build)
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

1. **Build the hardware.** Follow the [breadboard wiring](../../README.md#wiring) or the [PCB guide](../../hardware/README.md). For the PCB, read [PCB v1.3: what to know before you build](#pcb-v13-what-to-know-before-you-build) first.
2. **Load the firmware.** Download the `.uf2` file for your board and build from the [Releases](https://github.com/catuta0/fruta-midi-controller/releases/latest) page. The breadboard and the PCB need different files. Hold **BOOTSEL** while you plug in the USB cable, then drag the `.uf2` onto the drive that appears. Details: [Quick start](../../README.md#quick-start-no-programming).
3. **Connect the objects first.** Clip the leads onto the fruit before you plug in the USB, and do not touch anything while it starts. At startup the sensor measures each pad at rest; that reading is the reference for detecting touches.
4. **Wait for the LED.** Two slow blinks mean the sensor was found and FrutaMIDI is ready. See [LED signals](#led-signals) for the other patterns.
5. **Open a sound program.** Open the [online sampler](https://catuta0.github.io/fruta-midi-controller/) in Edge or Chrome, or a music program, and select FrutaMIDI as the MIDI input.

## PCB v1.3: what to know before you build

The [PCB guide](../../hardware/README.md) is the full assembly procedure. This section lists what you need to know about version 1.3 of the board (etched text "FrutaMIDI v1.3"), which replaces the earlier through-hole board.

- **One copper layer, on the component side, everything surface-mounted.** The board is made for chemical etching at home. The only holes are the 4 M3 mounting holes (3.2 mm bit), and they are optional. There are no sockets, no terminal blocks and no through-hole parts ([PCB guide, design rules and section 3](../../hardware/README.md#3-drill)).
- **Parts.** All parts are sold by Mouser. One board costs about 13.84 EUR at Mouser Portugal prices of 2026-11-11, excluding shipping and tax; this is a calculation from list prices, not an invoice ([PCB guide, bill of materials](../../hardware/README.md#bill-of-materials)). The electrode resistors R1–R12 are 3.3 kΩ ±1 % chip resistors in the 2512 size, YAGEO **RC2512FK-073K3L**. Mouser stock of this part was tight on 2026-11-11; the guide says which substitutes fit the same pads.
- **Assembly order.** Low parts first: R13–R16 and C1 (1206), then R1–R12 (2512), then the button SW1. Then **run the continuity tests** ([PCB guide, section 6](../../hardware/README.md#6-test-before-soldering-the-pico-and-the-module)), because you cannot reach under the Pico and the module afterwards. Then flash and solder the Pico, add the epoxy bead, solder the module, then JP1 and the two configuration wires, and last the potentiometer wires and the electrode wires ([PCB guide, section 4](../../hardware/README.md#4-solder)). Clean the flux from around R1–R12 with isopropyl alcohol.
- **Which Pico.** The PCB supports only the Raspberry Pi **Pico (SC0915)**, recommended, and the **Pico 2**, both without headers fitted. **Pico W and Pico 2 W are not supported on the PCB** until their undersides have been checked against the keep-outs under the Pico ([PCB guide, bill of materials, A1](../../hardware/README.md#bill-of-materials)). On the breadboard all four boards work.
- **The Pico and the module are soldered flat, with no sockets.** The Pico is soldered on its castellated edge pads. The module stands on its own male header pins, cut short and soldered onto surface pads. **Flash the firmware before you solder the Pico.** Replacing a failed Pico or module later means desoldering it from the surface, which is harder than pulling it out of a socket.
- **Trim the board at the USB end with care.** Cut the blank oversize, etch it, then trim to the **outside** of the thin etched outline line and file the edges. The Pico's USB end lies on the top edge: the end of the Pico is about 0.1 mm inside the board edge and the USB connector sticks out about 1.2 mm beyond it, so do not cut inside the line there ([PCB guide, section 2](../../hardware/README.md#2-transfer-and-etch)).
- **Before soldering the Pico: plug seat and rocking check.** With the Pico held in place on its pads, **plug the USB cable in**: the plug must go fully home without touching the board edge; if it does not, file the edge back to the etched outline. Then press the Pico down at each corner: it must **not rock**. Solder left on the USB connector pins on the Pico's underside can hold it up; remove it with braid first. Only then tack two opposite corners, check the alignment and solder all 40 pads from the outer edge of each castellation ([PCB guide, section 4 step 5](../../hardware/README.md#4-solder)).
- **Module mounting.** Fit the supplied male header from below, with the plastic strip pushed **up against the underside of the module**, and solder the pins on the top of the module. Cut the long pins below the strip to **3.0 mm**, all 20 the same length. Stand the module on its 20 pads (13-pin row towards J2): each pad runs about 1.7 mm out beyond the module edge, so solder each pin **from outside the module**, with the iron on the outer part of the pad, and check that a **fillet climbs the pin**. Tack one pin at each end of each row first so the module sits level. The top of the module board ends up about **7 mm** above the copper (about 5.5 mm to its underside); these heights are estimates from assumed pin, strip and board thicknesses, not measured ([PCB guide, section 4 step 7](../../hardware/README.md#4-solder)).
- **USB end: epoxy bead and a strain-relieved cable.** The USB connector is held only by the solder joints and a small bead of 2-part epoxy at the USB end of the Pico, applied after a first USB check and kept out of the USB opening. Use a data cable that is strain-relieved or supported, and do not lever on the plug: a sharp pull can peel the end pads. If you fit mounting screws, fit H4, the one nearest the USB end ([PCB guide, section 4](../../hardware/README.md#4-solder)).
- **Electrode wires on solder pads.** Each electrode (and GND) wire is soldered onto its J2 pad, on the half away from the board edge, and then held with a bead of hot-melt glue so the joint does not carry the pull. **Keep the glue and solder out of the small gap between each electrode pad and the GND track along the bottom edge:** it is an intentional spark gap and must stay open air.
- **Octave knob: off-board potentiometer, insulated shaft, plastic knob.** RV1 is a Bourns **PTV09A-4015F-B103** with an insulated shaft, mounted in your enclosure and connected by 3 wires (strain-relieved with hot-melt). Keep the insulated shaft and use a plastic knob, such as the Same Sky **SPK-016A** listed in the guide. **Whether that knob's bore grips the flatted shaft is not confirmed:** check the fit, or use any plastic knob for a 6 mm flatted shaft. A metal shaft or knob is not protected against a finger's static discharge. If the octave goes down when you turn clockwise, swap the two outer wires.
- **JP1 is a surface solder bridge.** JP1 has 3 surface pads, upright to the right of the module, with 3V3 on the centre pad. **QT** is etched above the top pad (pad 3, where the S7 track comes in). **ORIG** is etched to the left of JP1, beside the gap between the centre pad and the bottom pad; it means the bottom pad (pad 1, where the S1 track comes in from the left). Bridge the middle pad to **one** side only, preferably with a short tinned wire off-cut soldered flat across the two pads (or with generous solder). The pads are 3.81 mm apart, with 1.87 mm of bare board between them. ORIG is for the original module (no white connectors), QT for the STEMMA QT module (two small white connectors). A wrong position can damage the sensor; check it before you power the board ([PCB guide, section 5](../../hardware/README.md#5-module-configuration-jp1-and-two-wires)).
- **J1: two wire links.** J1, to the right of JP1, has two surface pads: SCL on the left, SDA on the right. Link them with short insulated solid wires (about 25–35 mm) to the S pads above the module's 7-pin row. Solder each end flat on its pad and add a dab of hot-melt:

  | Module | JP1 | J1 SDA → | J1 SCL → |
  | --- | --- | --- | --- |
  | Original (no white connectors) | ORIG | S5 | S6 |
  | STEMMA QT (two white connectors) | QT | S3 | S4 |

- **Optional silicone over R1–R12.** It is not needed. If you want an extra cover against dust and moisture, apply it only after cleaning and after the tests, as one continuous bead without bubbles over each resistor and its two pads. Use only a **neutral-cure, electronics-grade** silicone. **Never** use an acetic-cure silicone (the kind that smells of vinegar, often sold for bathrooms): it corrodes copper and solder. No particular product has been checked for this board.
- **Static electricity (ESD): what is and is not known.** Each electrode has a 3.3 kΩ resistor between the pad you touch and the sensor, and the electrode pads sit next to a spark gap to GND. The project's protection target is a ±4 kV contact discharge. It is **not proven** that the chosen standard chip resistors survive a 4 kV discharge: their maker publishes no surge rating, and the project accepted this to keep the board cheap (decision ADR-026). If the planned physical ESD test shows damage (a resistor whose value has shifted, a channel that stops detecting touch, or a spark across a resistor), the fallback is a board revision with clamp diodes to GND and 1 kΩ resistors (plan B, decision ADR-027). Nothing about ESD has been tested yet. Never connect the electrodes to anything plugged into mains power ([PCB guide, Electrical safety](../../hardware/README.md#electrical-safety)).
- **Test before powering.** Follow the checklist in [section 6 of the PCB guide](../../hardware/README.md#6-test-before-soldering-the-pico-and-the-module): each J2 electrode pad should read about 3.3 kΩ to its module pin pad, and after JP1 is bridged its centre pad must reach only the S pad for your module (S1 for ORIG, S7 for QT). After the Pico and the module are soldered, with the USB unplugged: Pico pads **36** (3V3), **39** (VSYS) and **40** (VBUS) must **not** beep to GND (a meter may show a resistance or a diode drop through the Pico's own circuit, but not a short), and the button's BTN pad next to the Pico must **not** beep to Pico pad **30** (RUN).

The board has not been made, soldered or tested. Hand-soldering the Pico and the module joints has not been tried. These steps describe the design, not a verified build.

**History.** Boards up to V1.2 (tag v1.2.0) were through-hole designs: they had drilled holes for every part, sockets for the Pico and the module, terminal blocks for the electrodes, large axial pulse-rated resistors and a potentiometer on the board. None of that applies to v1.3 (change request CR-003).

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
| LED blinks fast and does not stop | The sensor is not answering. Unplug the USB, then check the sensor wiring: 3V3, GND, SDA, SCL. On the PCB (v1.3), check that JP1 is bridged to the right side for your module (QT: centre pad to the top pad; ORIG: centre pad to the bottom pad) and that the 2 configuration wires go to the right S pads (see [PCB v1.3](#pcb-v13-what-to-know-before-you-build) and [section 5 of the PCB guide](../../hardware/README.md#5-module-configuration-jp1-and-two-wires)). Also check that you loaded the right `.uf2`: breadboard or PCB. |
| A pad is always on | Recalibrate without touching anything. If it persists, the object may be too large: use a smaller piece. |
| Notes trigger without touching | Recalibrate. Keep cables apart. See [Design notes](../../README.md#design-notes) for threshold settings. |
| A pad does not react | Check the clip connection (use a nail or needle pushed into the fruit). Recalibrate. On the PCB, check the electrode wire joint and its hot-melt, then measure about 3.3 kΩ from the J2 electrode pad to the module pin; if not, resolder that resistor (R1–R12). |
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
| Board version, construction | v1.3: one copper layer on the component side, SMD only, 4 M3 holes (3.2 mm) | SOURCE | changes/CR-003.md; management/DECISIONS.md ADR-023 D-4; hardware/README.md (title, design rules, section 3) |
| Board label | "FrutaMIDI v1.3" | SOURCE | hardware/scripts/gen_pcb.py (`bd.text("FrutaMIDI v1.3", ...)`); hardware/README.md section 1 |
| One-board parts cost | 13.84 EUR, Mouser Portugal prices of 2026-11-11, excluding shipping and tax | CALCULATION (from SOURCE list prices) | hardware/README.md BOM; sim/systems/budgets.out (`Mouser lines only 13.84 .. 13.84 EUR`); management/handoffs/electronics-engineer-T-096.md |
| R1–R12 part | YAGEO RC2512FK-073K3L, 3.3 kΩ ±1 %, 1 W, 2512 (Mouser 603-RC2512FK-073K3L) | SOURCE | hardware/README.md BOM; hardware/fabrication/bom-kicad.csv; ADR-026; management/INTERFACES.json frozen-8 |
| R1–R12 stock tight | 13 in stock for 12 needed, 2026-11-11 | SOURCE (Mouser listing) | hardware/README.md BOM; management/RISKS.md R-016; ADR-027 D-3 |
| Assembly order | 1206 parts, R1–R12, SW1, tests, Pico, epoxy, module, JP1 and J1 wires, RV1 wires, electrode wires | SOURCE | hardware/README.md section 4 steps 1–10 |
| Pico and module surface-soldered, no sockets; rework by desoldering | — | SOURCE | hardware/README.md BOM (A1, A2), section 4 steps 5 and 7, "Rework"; ADR-023 (manager items) |
| Flash before soldering the Pico | — | SOURCE | hardware/README.md section 4 step 5 and section 7 step 1 |
| Supported boards on the PCB | Pico (SC0915) and Pico 2 only; Pico W and Pico 2 W not supported | SOURCE (decision) | management/DECISIONS.md ADR-028 D-3; hardware/README.md BOM (A1); sim/systems/interface_check.py `doc.hw_readme.pico_variants` |
| Pico end inside the board edge; USB connector beyond it | about 0.1 mm inside; about 1.2 mm beyond (0.11 mm and 1.19 mm in the design file) | CALCULATION (design file, from SOURCE 1.30 mm receptacle overhang) | hardware/README.md sections 2 and 4 step 5; management/DECISIONS.md ADR-028 D-1; management/handoffs/electronics-engineer-T-103.md (F3-002) |
| Plug-seat check and rocking check before soldering the Pico | — | SOURCE | hardware/README.md section 4 step 5; review findings F3-002, F3-012 |
| Module pins cut length; land beyond the module edge | 3.0 mm; about 1.7 mm (1.73–1.775 mm in the design file) | ASSUMPTION (pin length, to be measured at first build); MEASUREMENT (design file) | hardware/README.md section 4 step 7; management/handoffs/electronics-engineer-T-103.md (F3-001) |
| Module height above the copper | underside about 5.5 mm, board top about 7 mm (7.1 mm) | CALCULATION on ASSUMPTIONS (pin 3.0 mm, strip 2.5 mm, module board 1.6 mm), not measured | hardware/README.md section 4 step 7; management/handoffs/electronics-engineer-T-103.md |
| Post-solder checks: pads 36/39/40 not to GND; BTN not to pad 30 | — | SOURCE | hardware/README.md section 6 (final checks); review finding F3-007 |
| Epoxy bead at the USB end; strain-relieved cable; H4 nearest the USB end | — | SOURCE | hardware/README.md section 4 step 6 and "Mounting (M3)"; BOM (USB cable) |
| Electrode wires on J2 solder pads with hot-melt; keep the spark gap clear | — | SOURCE | hardware/README.md section 4 step 10; ADR-023 D-3; ADR-020 (spark gap) |
| Spark gap, electrode pad to GND edge track | 1.40 mm (not quoted in this manual's text) | MEASUREMENT (design file) | management/metrics.json `ex_gnd_spark_gap`; reports/electronics/analysis.md §7.3 (1.401 mm on the SMD board) |
| RV1 off-board, insulated shaft, plastic knob; knob bore fit | Bourns PTV09A-4015F-B103; Same Sky SPK-016A; bore fit NOT CONFIRMED | SOURCE; NOT CONFIRMED | hardware/README.md BOM (RV1, knob) and Electrical safety; ADR-023 D-2; management/RISKS.md R-011 |
| JP1 surface solder bridge; QT etched above pad 3, ORIG etched left of JP1 beside the pad 2–1 gap (meaning pad 1); wire off-cut preferred | 3.81 mm pitch, 1.87 mm gap | SOURCE (layout, decision); MEASUREMENT (design file) for the gap | hardware/README.md section 5 and design rules; management/DECISIONS.md ADR-028 D-2; management/metrics.json `jp1_pad_gap`; sim/systems/interface_check.py `doc.hw_readme.JP1_smd`, `doc.manual.JP1_label_position` |
| J1 SCL left / SDA right; S pads per module | S5/S6 original, S3/S4 STEMMA QT | SOURCE | hardware/README.md section 5 table; management/INTERFACES.json IF-MPR121-MODULE |
| Configuration wire length | about 25–35 mm | SOURCE (hardware/README.md section 5); CALCULATION (layout, T-060) | hardware/README.md section 5; management/RISKS.md R-008 |
| Optional silicone over R1–R12: neutral-cure only, never acetic-cure | — | SOURCE | hardware/README.md section 4 ("Optional: silicone over R1–R12"); ADR-025 (last item), ADR-026 (silicone stays optional) |
| ESD target and status | ±4 kV contact (target is an ASSUMPTION); R1–R12 pulse capability NOT PROVEN; ESD test NOT RUN | ASSUMPTION; SOURCE (decision) | management/DECISIONS.md ADR-026; management/REQUIREMENTS.md REQ-023 (PARTIAL); hardware/README.md Electrical safety |
| Plan B if the ESD test shows damage | clamp diodes to GND, R1–R12 at 1 kΩ; trigger: any R1–R12 outside 3234–3366 Ω, a dead channel, or an arc across a resistor | SOURCE (decision); trigger window is an ASSUMPTION | management/DECISIONS.md ADR-027 D-2; management/RISKS.md R-018 |
| Continuity check through each electrode resistor | about 3.3 kΩ (3267–3333 Ω, plus meter error) | CALCULATION (3.3 kΩ ±1 %) | hardware/README.md section 6 |
| Firmware and pin map unchanged in v1.3 | SDA GP26, SCL GP27, button GP22, pot GP28 | SOURCE | management/REQUIREMENTS.md REQ-031 (PASS, interface_check); hardware/README.md section 7; firmware sha256 above, re-checked in T-101 |
| Earlier boards (V1.2 and before) through-hole | history only | SOURCE | changes/CR-003.md (133 drilled holes in V1.2, MEASUREMENT); tag v1.2.0 |
