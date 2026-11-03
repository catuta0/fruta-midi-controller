// FrutaMIDI pure logic: wrap-safe millisecond interval checks.
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

// True when at least `interval` ms have passed since `since`.
// Unsigned subtraction keeps this correct across the 2^32 ms millis() wrap.
inline bool elapsed_at_least(uint32_t now, uint32_t since, uint32_t interval) {
  return (uint32_t)(now - since) >= interval;
}

// True when strictly more than `interval` ms have passed since `since`.
inline bool elapsed_more_than(uint32_t now, uint32_t since, uint32_t interval) {
  return (uint32_t)(now - since) > interval;
}

}  // namespace fm
