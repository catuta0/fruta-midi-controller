// FrutaMIDI pure logic: non-blocking LED blink sequencer, ticked from loop().
// Replaces the delay()-based blink() so pads, button and USB keep being serviced
// while the LED signals (finding DOC-1, T-040).
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>
#include "fm_time.h"

namespace fm {

// Patterns (values unchanged from the original blocking blink() calls @ e4668d4).
const uint8_t  BLINK_READY_TIMES = 2;    // sensors found at power-up
const uint16_t BLINK_READY_MS    = 120;
const uint8_t  BLINK_RECAL_TIMES = 3;    // after recalibration
const uint16_t BLINK_RECAL_MS    = 60;
const uint16_t BLINK_SCALE_MS    = 90;   // scale N -> N blinks

// `times` blinks of `ms` on then `ms` off, starting ON at start(). Each half-period
// lasts at least `ms` and ends on the first tick at or after it (so at most one
// loop period longer). start() while active restarts with the new pattern.
struct Blinker {
  uint16_t phasesLeft = 0;   // remaining half-periods including the current one
  uint16_t halfMs     = 0;
  uint32_t phaseStart = 0;

  void start(uint32_t now, uint8_t times, uint16_t ms) {
    phasesLeft = (uint16_t)(2u * times);
    halfMs     = ms;
    phaseStart = now;
  }

  bool active() const { return phasesLeft > 0; }

  // Advance at most one half-period; true = LED on. Even phasesLeft = ON phase.
  bool tick(uint32_t now) {
    if (phasesLeft > 0 && elapsed_at_least(now, phaseStart, halfMs)) {
      phasesLeft--;
      phaseStart = now;
    }
    return phasesLeft > 0 && (phasesLeft % 2u) == 0;
  }

  // LED level for this loop: the blink pattern while active, otherwise `idle`.
  bool level_or(uint32_t now, bool idle) {
    bool on = tick(now);
    return active() ? on : idle;
  }
};

}  // namespace fm
