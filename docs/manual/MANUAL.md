# FrutaMIDI user manual

> **Draft — not yet validated on hardware.**

It describes the firmware at git revision `e4668d4` (`firmware/FrutaMIDI/FrutaMIDI.ino`). Every behaviour below is traced to that file or to the project README; see [Traceability](#traceability) at the end. The hardware has not been tested as a complete build, so this manual describes what the firmware is written to do, not measured behaviour.

## Contents

- [What FrutaMIDI does](#what-frutamidi-does)
- [Setup](#setup)
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

1. **Build the hardware.** Follow the [breadboard wiring](../../README.md#wiring) or the [PCB guide](../../hardware/README.md).
2. **Load the firmware.** Download the `.uf2` file for your board and build from the [Releases](https://github.com/catuta0/fruta-midi-controller/releases/latest) page. The breadboard and the PCB need different files. Hold **BOOTSEL** while you plug in the USB cable, then drag the `.uf2` onto the drive that appears. Details: [Quick start](../../README.md#quick-start-no-programming).
3. **Connect the objects first.** Clip the leads onto the fruit before you plug in the USB, and do not touch anything while it starts. At startup the sensor measures each pad at rest; that reading is the reference for detecting touches.
4. **Wait for the LED.** Two slow blinks mean the sensor was found and FrutaMIDI is ready. See [LED signals](#led-signals) for the other patterns.
5. **Open a sound program.** Open the [online sampler](https://catuta0.github.io/fruta-midi-controller/) in Edge or Chrome, or a music program, and select FrutaMIDI as the MIDI input.

## Playing

- **Touch** an object: FrutaMIDI sends a Note On for that pad, with a fixed velocity of 100, on MIDI channel 1. Both values can be changed in the firmware.
- **Let go:** FrutaMIDI sends a Note Off for the same note. This holds even if you changed scale or octave while touching, so notes do not get stuck.
- **Press harder / touch more:** while you touch, FrutaMIDI sends Polyphonic Aftertouch from 0 to 127. A larger change in the sensor reading gives a higher value. Programs that use aftertouch respond to it; according to the README, the sampler opens a filter with it.
- **The LED** stays on while any pad is touched.
- **Several pads at once** work: each pad has its own note.

## Scales

FrutaMIDI has 6 scales. It always starts in scale 1, Drum Rack.

**To change scale:** briefly press the button and release it. FrutaMIDI moves to the next scale, and after the last scale it returns to scale 1. The LED then blinks the number of the new scale (1 to 6 blinks).

While the LED is blinking, FrutaMIDI does not read the pads. Wait for the blinks to finish before playing.

| # | Scale | Notes sent by pads 0–11 (MIDI note numbers, octave 0) | Octave knob |
| --- | --- | --- | --- |
| 1 | Drum Rack | 36 37 38 39 40 41 42 43 44 45 46 47 | Ignored |
| 2 | Major pentatonic | 48 50 52 55 57 60 62 64 67 69 72 74 | Applies |
| 3 | Minor pentatonic | 48 51 53 55 58 60 63 65 67 70 72 75 | Applies |
| 4 | Major | 48 50 52 53 55 57 59 60 62 64 65 67 | Applies |
| 5 | Natural minor | 48 50 51 53 55 56 58 60 62 63 65 67 | Applies |
| 6 | Chromatic | 48 49 50 51 52 53 54 55 56 57 58 59 | Applies |

The Drum Rack notes 36–47 match the 12 pads of the online sampler. In the melodic scales, once a pad runs past the last step of the scale, the next pad starts the same pattern one octave (12 notes) higher. With a second sensor, pads 12–23 continue the same pattern.

## Octave

The octave knob (potentiometer) shifts every note of the melodic scales by whole octaves. It has 5 positions: −2, −1, 0, +1, +2. Each step moves all notes by 12. The knob has a small dead band at each boundary, so the octave does not flicker when the knob sits between two positions. In Drum Rack (scale 1) the knob has no effect.

The knob only works when the firmware has it enabled:
- **PCB build:** always enabled.
- **Breadboard build:** disabled by default. To use it, set `USE_POT = true` and compile the firmware yourself ([Firmware](../../README.md#firmware)).

## Recalibration

Recalibrate after you swap, move or add objects, or when a pad stays on by itself.

1. Take your hands off all objects.
2. **Hold the button for 0.8 s.** Recalibration starts while you are still holding; releasing the button afterwards does not change the scale.
3. FrutaMIDI first sends Note Off for every sounding note, then restarts the sensor, which measures each pad at rest again. The LED gives 3 quick blinks.

Unplugging and replugging the USB has the same effect, and also resets the scale to Drum Rack and the octave to 0.

## LED signals

| LED | Meaning |
| --- | --- |
| 2 slow blinks after power-up | Sensor found, ready |
| Blinking fast, continuously | Sensor not found. FrutaMIDI tries again every 2 s |
| On | A pad is being touched |
| 1–6 blinks after a short button press | Number of the scale just selected |
| 3 quick blinks after a long button press | Recalibration done |

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| LED blinks fast and does not stop | The sensor is not answering. Unplug the USB, then check the sensor wiring: 3V3, GND, SDA, SCL (PCB: the 3 configuration wires). Also check that you loaded the right `.uf2`: breadboard or PCB. |
| A pad is always on | Recalibrate without touching anything. If it persists, the object may be too large: use a smaller piece. |
| Notes trigger without touching | Recalibrate. Keep cables apart. See [Design notes](../../README.md#design-notes) for threshold settings. |
| A pad does not react | Check the clip connection (use a nail or needle pushed into the fruit). Recalibrate. |
| The octave knob does nothing | You are in Drum Rack (scale 1), or the breadboard firmware has the knob disabled (see [Octave](#octave)). |
| A note is stuck in the program | Touch and release the same pad again: the Note Off releases it. |
| Touches are ignored right after a button press | The LED is still blinking the scale number; wait for it to finish. |
| The computer does not see FrutaMIDI | See [Troubleshooting](../../README.md#troubleshooting) in the main README (cable, USB stack, program settings). |

## Traceability

Each claim below is traced to the source at `e4668d4`. Firmware line numbers refer to `git show e4668d4:firmware/FrutaMIDI/FrutaMIDI.ino`.

| Claim | Value | Label | Evidence |
| --- | --- | --- | --- |
| Fixed velocity, channel | 100, 1 | SOURCE | `VELOCITY`, `MIDI_CHANNEL` |
| Note Off of the stored note | — | SOURCE | `releasePad()` uses `activeNote[pad]` |
| Aftertouch range and mapping | 0–127, delta 12…120 | SOURCE | `sendPressure()`, `AT_MAX_DELTA = 120`, `TOUCH_THRESHOLD = 12` |
| LED on while touched | — | SOURCE | `digitalWrite(LED_BUILTIN, anyTouched)` |
| 6 scales, start in Drum Rack, wrap-around | — | SOURCE | `SCALES[]`, `scaleIdx = 0`, `nextScale()` |
| Pad-to-note table | see Scales table | CALCULATION | `noteForPad()`: root + 12·octave + steps[pad mod len] + 12·⌊pad / len⌋, clamped 0–127. Roots 36 / 48. No value reaches the clamp at octave −2…+2: lowest 24, highest 99. |
| Drum Rack ignores the octave | — | SOURCE | `fixed = true`, `int oct = sc.fixed ? 0 : octaveShift` |
| Scale blinks block pad reading | 90 ms on / 90 ms off per blink | SOURCE | `blink(scaleIdx + 1, 90)` uses `delay()` |
| Octave positions and dead band | −2…+2, 5 zones, ±0.7 zone | SOURCE | `handlePot()` |
| Knob enabled on PCB / disabled on breadboard | true / false | SOURCE | `USE_POT` under `#ifdef FRUTAMIDI_PCB` |
| Long press | > 800 ms, fires while held | SOURCE | `handleButton()`: `now - downAt > 800`, `longDone` suppresses the short press |
| Recalibration sequence | Note Off all, restart, 3 blinks | SOURCE | `recalibrate()`: `releaseAll(); startSensors(); blink(3, 60);` |
| Startup ready signal | 2 blinks of 120 ms | SOURCE | `if (anySensorOk()) blink(2, 120);` |
| Sensor-missing signal and retry | toggles every 100 ms, retry every 2000 ms | SOURCE | `loop()`: `(millis() / 100) % 2`, `millis() - lastTry > 2000` |
| Power cycle resets scale and octave | 0 / 0 | SOURCE | initial values of `scaleIdx` and `octaveShift` |
| Startup reference measurement | — | SOURCE | `startSensors()` calls `begin()` with `AUTOCONFIG` |
| Sampler pads on notes 36–47; aftertouch opens filter | — | README | README "Sound"; not traced to `docs/index.html` |
| Flashing procedure, BOOTSEL, `.uf2` names | — | README | README "Quick start" |
