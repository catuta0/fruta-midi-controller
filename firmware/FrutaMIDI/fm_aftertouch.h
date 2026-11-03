// FrutaMIDI pure logic: polyphonic aftertouch scaling and change filter.
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

// Minimum change in pressure value (0..127) before a new aftertouch message is sent.
const uint8_t AT_MIN_CHANGE = 2;

// delta = baseline - filtered (electrode counts). Clamped to [touchThreshold, maxDelta]
// and mapped linearly (integer, truncating, same formula as Arduino map()) to 0..127.
// Requires maxDelta > touchThreshold.
inline uint8_t pressure_from_delta(int delta, int touchThreshold, int maxDelta) {
  long x = delta < touchThreshold ? touchThreshold : (delta > maxDelta ? maxDelta : delta);
  long p = (x - touchThreshold) * (127L - 0L) / ((long)maxDelta - touchThreshold) + 0L;
  return (uint8_t)p;
}

// True when the new pressure differs from the last sent value by at least AT_MIN_CHANGE,
// or when it reached the floor (0) and the last sent value was above 0, so the
// receiver always ends at exactly 0 (sent once: lastSent becomes 0).
inline bool pressure_should_send(uint8_t p, uint8_t lastSent) {
  if (p == 0) return lastSent > 0;
  int d = (int)p - (int)lastSent;
  if (d < 0) d = -d;
  return d >= AT_MIN_CHANGE;
}

// On release: true when an aftertouch 0 must be sent before Note Off
// (the last value sent for this note was above 0).
inline bool pressure_reset_on_release(uint8_t lastSent) {
  return lastSent > 0;
}

}  // namespace fm
