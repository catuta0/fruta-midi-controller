// FrutaMIDI pure logic: scale table and pad -> MIDI note mapping.
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

// A scale maps pad index -> note. "fixed" scales ignore the octave potentiometer
// (useful for drum racks).
struct Scale {
  const char* name;
  uint8_t root;        // MIDI note of pad 0 (36 = C1, 48 = C2 in Ableton / C3 elsewhere)
  uint8_t len;         // number of used entries in steps[], 1..12
  int8_t steps[12];    // semitone offsets from root within one octave
  bool fixed;
};

const Scale SCALES[] = {
  {"Drum Rack (notes 36-47)", 36, 12, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}, true},
  {"Major pentatonic",        48,  5, {0, 2, 4, 7, 9},                         false},
  {"Minor pentatonic",        48,  5, {0, 3, 5, 7, 10},                        false},
  {"Major",                   48,  7, {0, 2, 4, 5, 7, 9, 11},                  false},
  {"Natural minor",           48,  7, {0, 2, 3, 5, 7, 8, 10},                  false},
  {"Chromatic",               48, 12, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}, false},
};
const uint8_t NUM_SCALES = sizeof(SCALES) / sizeof(SCALES[0]);

const int MIDI_NOTE_MIN = 0;
const int MIDI_NOTE_MAX = 127;

inline int clamp_int(int v, int lo, int hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

// Note for a pad: root + octave shift (ignored for fixed scales) + scale step,
// wrapping into the next octave every `len` pads; clamped to 0..127.
inline uint8_t note_for_pad(const Scale& sc, int8_t octaveShift, uint8_t pad) {
  int oct  = sc.fixed ? 0 : octaveShift;
  int note = sc.root + 12 * oct + sc.steps[pad % sc.len] + 12 * (pad / sc.len);
  return (uint8_t)clamp_int(note, MIDI_NOTE_MIN, MIDI_NOTE_MAX);
}

// Index of the scale selected by a short button press (wraps to 0).
inline uint8_t next_scale_index(uint8_t idx, uint8_t count) {
  return (uint8_t)((idx + 1) % count);
}

}  // namespace fm
