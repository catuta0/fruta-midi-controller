# Firmware host-test coverage — FrutaMIDI

Tasks T-040, T-041 · firmware-engineer · base `firmware/FrutaMIDI/FrutaMIDI.ino` @ e4668d4 (uncommitted changes listed in `management/handoffs/firmware-engineer/T-040.md` and `T-041.md`).

Host route: `tests/firmware/logic/fm_probe.cpp` is built with `c++ -std=c++17 -Wall -Wextra -Werror` (Apple clang 21.0.0) against the production headers in `firmware/FrutaMIDI/fm_*.h`. pytest drives it through one long-lived process. The expected values are in the Python tests (hand tables or independent models), never computed by the code under test.

Latest run (T-041): eng-tools `run_pytest tests/firmware` → `267 passed in 1.79s` (MEASUREMENT, verbose log `reports/firmware/T-041/pytest_tests_firmware.log`; 263 logic tests + 4 smoke tests).
Mutation check: 27 of 27 hand-written mutants of the production headers make the suite fail, every file restored (MEASUREMENT, `reports/firmware/T-041/mutation/summary_all.txt`; M23 hung the probe for 17 min before failing, as an n = 0 run loops forever, but it was still killed).

## Logic → test → status

| Logic (header · function) | Used in sketch by | Test file | What is checked | Status |
|---|---|---|---|---|
| Scale table `fm_scales.h · SCALES` | `noteForPad`, `nextScale` | `test_scales.py` | All 6 entries (root, len, fixed, steps) against a hand table | PASS |
| Pad → note `note_for_pad` | `noteForPad` | `test_scales.py` | First octave of every scale (hand table); wrap at pad `len` and pad 23; octave −2..+2 = ±12 per step; fixed scale ignores the octave; clamp at 0 and 127 (exact 0, 1, 126, 127, 128→127, −12→0); real-table extremes 24 and 127 | PASS |
| Scale cycling `next_scale_index` | `nextScale` | `test_scales.py` | 0→1 … 5→0 | PASS |
| Pad debounce `fm_debounce.h · pad_change_allowed`, `pad_step` | `loop()` | `test_debounce.py`, `test_blink.py` | DEBOUNCE_MS (15, read from the .ino) −1 / exact / +1; no change when states match; boundary across the 2^32 ms wrap; chatter filtered in a 1 ms timeline; release inside the lockout applied at its end; `pad_step` records the timestamp only on a change | PASS |
| Touch bit `pad_touched` | `loop()` | `test_debounce.py` | bits 0, 10, 11, out-of-range high bits | PASS |
| Aftertouch scaling `fm_aftertouch.h · pressure_from_delta` | `sendPressure` | `test_aftertouch.py` | delta −50, 0, 11, 12, 13, 66, 119, AT_MAX_DELTA=120, 121, 1000, 32767 (hand values, Arduino `map()` truncation); monotonic, always 0..127 | PASS |
| Aftertouch change filter `pressure_should_send` | `sendPressure` | `test_aftertouch.py` | \|Δ\| = 0, 1, 2 both directions; 127 / 126 / 125; T-041: a fall to 0 is always sent once (1→0, 127→0) | PASS |
| Aftertouch reset on release `pressure_reset_on_release` (T-041) | `releasePad` (also `releaseAll` on recalibrate) | `test_aftertouch.py` | last 0 → no message; last 1/2/127 → AT 0. Pad harness (`padsim`): AT 0 is sent immediately before Note Off; no AT at all when the pressure stayed 0; a slow fall to the floor sends exactly one 0 while touched and none at release; 2 → 1 → 0 gives `[2, 0]`; the zero obeys the 15 ms rate limit | PASS |
| MPR121 burst plan `mpr121_next_run` (T-041) | `loop()` aftertouch pass | `test_mpr121.py` | Hand cases (0, 1 pad, adjacent, gap 1 merged, gap 2 split, extremes, all 12); all 4096 masks: runs cover every sounding pad, start/end on one, gaps ≥ 2, bytes ≤ 9 × pads (old path), equal to an independent DP optimum, worst 42 bytes | PASS |
| MPR121 config after `begin()` (T-041, ADR-008 F-1/F-2) | `configureSensor` | `test_mpr121.py` | AUTOCONFIG1 (0x7C) byte = 0x00, SCTS bit 7 cleared; bit packing; USL/TL/LSL = 201/180/130 @ 3300 mV, 198/178/128 @ 3100 mV, 156/140/101 @ 1800 mV; library source: AUTOCONFIG0 = 0b00001011 decoded (FFI 0, RETRY 0, BVA 2 = ECR CL, ARE 1, ACE 1), library never writes 0x7C, library limit 200; sketch writes in stop mode in the order ECR read, ECR = 0, 0x7C, 0x7D, 0x7F, 0x7E, ECR restore, after `begin()` | PASS |
| MPR121 burst decoding `fm_mpr121.h` (T-041) | `readSensorData` → `sendPressure` | `test_mpr121.py` | Register layout 0x04 / up to 24 bytes, 0x1E / up to 12 bytes against the linked Adafruit_MPR121 1.2.1 header; run offset decoding (index e − lo); hand-decoded vector (E0 677/676/−1, E1 768/800/32, E5 1023/1020/−3, E7 with reserved high bits set → 272/320/48, E11 500/560/60); no aliasing between electrodes; 50 random valid frames give the same delta as the old per-electrode library path; the loop uses no per-pad `filteredData`/`baselineData`; `setClock(400000)` unchanged | PASS |
| Aftertouch rate limit `fm_time.h · elapsed_at_least` with AT_INTERVAL_MS | `loop()` | `test_aftertouch.py` | interval −1 / exact; across the wrap; timeline at loop periods 1, 4, 7, 15, 20 ms: every gap is ≥ 15 ms and < 15 ms + loop period | PASS |
| Interval helpers `elapsed_at_least`, `elapsed_more_than` | button, pot, sensor retry, aftertouch, blink | `test_midi_time.py` | ≥ vs >, wrap-safety (catches `now >= since + interval`), SENSOR_RETRY_MS = 2000 strictly greater | PASS |
| Button `fm_button.h · ButtonClassifier` | `handleButton` | `test_button.py` | 10 ms sample gate boundary; long press at 800 ms → not long, 801 ms → long; release at 800 ms → short; release after a long press is silent and re-arms; sampled timeline: long fires at 1810 for a press at 1000; 50 random < 10 ms bounce patterns → exactly one short press | PASS |
| Pot → octave `fm_pot.h · octave_from_adc` | `handlePot` | `test_pot.py` | All 1024 ADC values × 5 current octaves against an independent integer model; hand thresholds (655/656, 369/368, 574/573, 860/861); end zones; large jumps; ±1/3/5/10 count noise at all 4 borders does not chatter; a slow ramp with ±3 noise switches exactly once per border | PASS |
| MIDI bytes `fm_midi.h · channel_status`, CIN constants | `midiSend` (ATmega32u4 only) | `test_midi_time.py` | ch 1 / 10 / 16 for 0x80, 0x90, 0xA0; CIN 0x08 / 0x09 / 0x0A | PASS |
| LED sequencer `fm_blink.h · Blinker` (new, finding DOC-1) | `setup`, `recalibrate`, `nextScale`, `loop()` | `test_blink.py` | Pattern constants unchanged (2×120, 3×60, N×90); 1/2/3/6 blinks × 60/90/120 ms at a 1 ms tick: exact edges and end time (6×90 → END at 1080 ms); 3/7/13 ms ticks: count kept and every half-period is ≥ 90 ms and < 90 ms + tick; zero blinks = inactive | PASS |
| Pads stay live during a blink (DOC-1) | `loop()` order | `test_blink.py` | Loop harness (button → pad 0 → LED, 1 ms tick): a touch at 1500–1699 ms during the 6-blink scale signal gives `1500:ON:48`, `1700:OFF:48`, and the LED still shows 12 edges at 90 ms steps. Blocking model of the old code: the same touch gives **no** note. A second button press during a blink is honoured and the blink restarts with the new count | PASS |
| English-only firmware (T-041, ADR-000/ADR-005) | all firmware files | `test_sketch_uses_headers.py`, `test_scales.py` | Every firmware file is pure ASCII and has none of the Portuguese words found in e4668d4 (the guard finds 72 hits and 14 non-ASCII characters in the e4668d4 sketch); scale names are the English hand table | PASS |
| Sketch uses the headers | — | `test_sketch_uses_headers.py` | Every `fm::` entry point appears in the .ino; the old inline formulas (`steps[pad % sc.len]`, `map(`, `fabsf(`, `now - downAt`) are gone; `blink()` is gone and the only `delay()` left is `delay(10)` in `midiBegin`; headers include only `<stdint.h>` / `fm_*.h`; headers compile standalone with `-std=c++11` and `-std=c++17` (`-Wall -Wextra -Werror -pedantic`) | PASS |

Compile-time guards in the .ino (`static_assert`): NUM_SENSORS 1..2, MIDI_CHANNEL 1..16, VELOCITY 1..127, RELEASE_THRESHOLD < TOUCH_THRESHOLD, AT_MAX_DELTA > TOUCH_THRESHOLD. They are checked on every target build (9 of 9 PASS).

## Documented semantics (kept by decision, T-041)

- **Pad debounce is a lockout, not a stability filter.** After an accepted press or release, further changes of that pad are ignored for DEBOUNCE_MS (15 ms). They are not queued, but the current state is re-evaluated on every loop, so a release that happens inside the window is applied at the window's end (`test_change_inside_lockout_is_applied_at_window_end`). A single spurious `touched` sample produces a note of at least 15 ms. The MPR121's own filtering and touch/release thresholds are the first line against noise.
- **Aftertouch ceiling**: the ±2 filter can leave the last sent value at 126 when the pressure reaches 127 in one step of 1. This is not covered by the T-041 floor rule (not requested).

## Limits of the host tests

- The loop harness in `fm_probe.cpp` (`loopsim`) is a copy of the call order in `loop()`, not the `.ino` itself. `test_sketch_uses_headers.py` guards that the sketch calls the same functions, but it does not check the order of the calls. I reviewed the order by hand.
- I did not write a test that runs the old and new binaries side by side. Equivalence of the refactor rests on three things: a line-by-line transcription (diff in `reports/firmware/T-040/FrutaMIDI.ino.diff`), hand-table tests and the flash deltas (−48 … +4 bytes before the DOC-1 change).
- On target, the timing granularity of the blinker and debounce depends on how long one `loop()` iteration takes. That time has not been measured (see below).

## Not testable on host → needs hardware

| Item | Why it cannot be tested on host | Hardware check proposed |
|---|---|---|
| MPR121 over I2C (`begin()` with AUTOCONFIG, `touched()`, 400 kHz bus, Wire vs Wire1 on GP4/5 or GP26/27) | Library + bus + chip registers | Logic analyser on SDA/SCL; serial debug of deltas with fruit and copper pads; check 0x5A/0x5B detection and hot-plug retry |
| MPR121 config (T-041): SCTS bit position (0x7C bit 7) and the effect of USL 201 vs 200 | Register layout confirmed against the MPR121 datasheet (SOURCES S-006, ADR-011): SCTS = D7 of 0x7C, USL/TL/LSL formula; the effect of the limits on the 3.3 kOhm electrodes still needs the chip | Read back 0x7B..0x7F and the CDC/CDT registers (0x5F..0x6B, 0x6C..0x72) after start-up with the 3.3 kΩ electrodes; check that no electrode reports out-of-range (0x02..0x03) |
| Burst read (T-041): runs of 2n bytes from 0x04 + 2·lo and n bytes from 0x1E + lo, with register auto-increment and repeated start | Needs the chip; multiple-byte reads with auto-increment are documented in the datasheet (SOURCES S-006 section 6.4); actual bus behaviour still needs the chip | Logic analyser: 2 transactions per sensor per due loop; compare burst deltas with `filteredData()`/`baselineData()` (still used by `debugPrint`) over 10 s with SERIAL_DEBUG; measure the aftertouch pass time with a GPIO toggle |
| Long-press block during `startSensors()` (kept by decision) | MPR121 reset + autoconfig time over I2C | GPIO toggle around `recalibrate()`; measure the duration per sensor |
| Touch / release thresholds 12 / 6 and the AT_MAX_DELTA = 120 scale | Depend on electrode capacitance (fruit, wire length) | Record the delta range per object with SERIAL_DEBUG; check that full pressure reaches about 127 |
| USB-MIDI enumeration and descriptor name (TinyUSB detach/attach, MIDIUSB) | USB stack and host OS | Enumerate on macOS/Windows/Linux; MIDI monitor shows note on/off/poly AT on channel 1 |
| Real loop period (sets debounce, aftertouch and blink granularity) | Depends on I2C transfer time and the USB task | Toggle a spare GPIO each loop and measure the period with a scope; expected well under 15 ms (ASSUMPTION) |
| Button contact bounce (< 10 ms assumed) and the 800 ms long press felt by the user | Mechanical | Scope the button pin; press tests |
| Pot ADC noise on the PCB (10-bit reading, hysteresis ≈ 41 counts) | Analogue noise, layout | Log `analogRead` at each border for 10 s; peak-to-peak noise must stay < 41 counts |
| LED visibility (Pico W / 2 W LED goes through CYW43) | Board-specific driver | Visual check of 1…6 blinks on every board |
