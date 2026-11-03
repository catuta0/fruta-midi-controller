// FrutaMIDI pure logic: button sampling and short / long press classification.
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

const uint16_t BUTTON_SAMPLE_MS = 10;   // sample period; sampling slower than bounce = debounce
const uint16_t BUTTON_LONG_MS   = 800;  // held strictly longer than this = long press

enum class ButtonEvent : uint8_t { None, ShortPress, LongPress };

struct ButtonClassifier {
  uint32_t lastSample = 0;
  uint32_t downAt     = 0;
  bool     wasDown    = false;
  bool     longDone   = false;

  // True (and records the sample time) when a new sample is due.
  bool sample_due(uint32_t now) {
    if (now - lastSample < BUTTON_SAMPLE_MS) return false;
    lastSample = now;
    return true;
  }

  // Feed one sample. LongPress fires once, while still held, on the first sample
  // more than BUTTON_LONG_MS after press; ShortPress fires on release if no long
  // press fired during that hold.
  ButtonEvent update(uint32_t now, bool down) {
    ButtonEvent ev = ButtonEvent::None;
    if (down && !wasDown) { downAt = now; longDone = false; }
    if (down && !longDone && now - downAt > BUTTON_LONG_MS) { longDone = true; ev = ButtonEvent::LongPress; }
    if (!down && wasDown && !longDone) ev = ButtonEvent::ShortPress;
    wasDown = down;
    return ev;
  }
};

}  // namespace fm
