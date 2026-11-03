// FrutaMIDI pure logic: per-pad touch debounce (lockout after each accepted change).
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>
#include "fm_time.h"

namespace fm {

// A pad changes state (note on / note off) only when the sensor state differs from
// the current note state AND at least debounceMs have passed since the last accepted
// change of that pad. Changes inside the lockout window are ignored, not queued.
inline bool pad_change_allowed(bool touched, bool active, uint32_t now,
                               uint32_t lastChangeMs, uint16_t debounceMs) {
  return touched != active && elapsed_at_least(now, lastChangeMs, debounceMs);
}

enum class PadAction : uint8_t { None, Press, Release };

// One loop iteration for one pad: decides press / release and records the change time.
inline PadAction pad_step(bool touched, bool active, uint32_t now,
                          uint32_t& lastChangeMs, uint16_t debounceMs) {
  if (!pad_change_allowed(touched, active, now, lastChangeMs, debounceMs)) return PadAction::None;
  lastChangeMs = now;
  return touched ? PadAction::Press : PadAction::Release;
}

// Bit e of the MPR121 touch status word.
inline bool pad_touched(uint16_t bits, uint8_t electrode) {
  return (bits & (1u << electrode)) != 0;
}

}  // namespace fm
