// Smoke-test helper for the FrutaMIDI host test route (T-006-FW).
// Pure logic, no Arduino dependencies, so it compiles on host and target.
#pragma once
#include <stdint.h>

// Returns root + 12 * octave, clamped to the MIDI note range 0..127.
inline uint8_t midi_note(uint8_t root, int8_t octave) {
  int value = static_cast<int>(root) + 12 * static_cast<int>(octave);
  if (value < 0) return 0;
  if (value > 127) return 127;
  return static_cast<uint8_t>(value);
}
