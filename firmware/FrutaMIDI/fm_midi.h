// FrutaMIDI pure logic: raw MIDI byte helpers (used by the ATmega32u4 MIDIUSB path).
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>

namespace fm {

// USB-MIDI code index numbers (USB MIDI 1.0, table 4-1).
const uint8_t CIN_NOTE_OFF      = 0x08;
const uint8_t CIN_NOTE_ON       = 0x09;
const uint8_t CIN_POLY_PRESSURE = 0x0A;

const uint8_t STATUS_NOTE_OFF      = 0x80;
const uint8_t STATUS_NOTE_ON       = 0x90;
const uint8_t STATUS_POLY_PRESSURE = 0xA0;

// Status byte for a channel message; channel is 1..16.
inline uint8_t channel_status(uint8_t status, uint8_t channel) {
  return (uint8_t)(status | (channel - 1));
}

}  // namespace fm
