// FrutaMIDI pure logic: potentiometer -> octave shift (-2..+2) with hysteresis.
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

const uint16_t POT_READ_MS    = 30;    // pot sample period
const float    POT_HYSTERESIS = 0.7f;  // distance from zone centre (zone units) to switch

// adc: 10-bit reading 0..1023. The range is split into 5 equal zones (-2..+2).
// The octave only changes when the position is more than POT_HYSTERESIS zone widths
// from the centre of the current zone, i.e. 0.2 zone (~41 counts) past the border.
inline int8_t octave_from_adc(int adc, int8_t current) {
  float pos    = adc * 5.0f / 1024.0f;    // 0.0 .. 5.0
  float centre = (current + 2) + 0.5f;
  float d      = pos - centre;
  if (d > POT_HYSTERESIS || d < -POT_HYSTERESIS) {
    int zone = (int)pos;
    zone = zone < 0 ? 0 : (zone > 4 ? 4 : zone);
    return (int8_t)(zone - 2);
  }
  return current;
}

}  // namespace fm
