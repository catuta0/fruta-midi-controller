// FrutaMIDI pure logic: pad -> note bookkeeping with shared notes (review finding F-004).
// Two held pads can map to the same MIDI note (e.g. after an octave change). The note's
// reference count is the number of pads holding it: Note On only on 0 -> 1, Note Off only
// on 1 -> 0. Polyphonic aftertouch of a shared note is the maximum of its holders'
// pressures; the final 0 is sent only when the last holder releases (or pressure falls).
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
#pragma once
#include <stdint.h>
#include "fm_aftertouch.h"

namespace fm {

const uint8_t NOTE_NONE = 255;

// Sink must provide noteOn(note), noteOff(note) and pressure(note, value).
template <uint8_t N>
struct PadNotes {
  uint8_t note[N];       // note held by each pad (NOTE_NONE = released)
  uint8_t pressure[N];   // latest pressure measured for each holder (0..127)
  uint8_t sent[N];       // last aftertouch value sent for the pad's note (same for all holders)

  void reset() {
    for (uint8_t p = 0; p < N; p++) { note[p] = NOTE_NONE; pressure[p] = 0; sent[p] = 0; }
  }

  bool sounding(uint8_t p) const { return note[p] != NOTE_NONE; }

  // Number of pads holding note n (its reference count).
  uint8_t holders(uint8_t n) const {
    uint8_t c = 0;
    for (uint8_t p = 0; p < N; p++) if (note[p] == n) c++;
    return c;
  }

  uint8_t max_pressure(uint8_t n) const {
    uint8_t m = 0;
    for (uint8_t p = 0; p < N; p++) if (note[p] == n && pressure[p] > m) m = pressure[p];
    return m;
  }

  void set_sent(uint8_t n, uint8_t v) {
    for (uint8_t p = 0; p < N; p++) if (note[p] == n) sent[p] = v;
  }

  template <class Sink> void press(uint8_t p, uint8_t n, Sink& out) {
    if (sounding(p) || n == NOTE_NONE) return;
    uint8_t s0 = 0;
    for (uint8_t q = 0; q < N; q++) if (note[q] == n) { s0 = sent[q]; break; }
    bool first = holders(n) == 0;
    note[p] = n; pressure[p] = 0; sent[p] = s0;
    if (first) out.noteOn(n);
  }

  template <class Sink> void release(uint8_t p, Sink& out) {
    if (!sounding(p)) return;
    uint8_t n = note[p], s0 = sent[p];
    note[p] = NOTE_NONE; pressure[p] = 0; sent[p] = 0;
    if (holders(n) == 0) {
      // Return pressure to 0 before Note Off so no DAW keeps a stuck aftertouch value.
      if (pressure_reset_on_release(s0)) out.pressure(n, 0);
      out.noteOff(n);
    } else {
      uint8_t m = max_pressure(n);
      if (pressure_should_send(m, s0)) { set_sent(n, m); out.pressure(n, m); }
    }
  }

  template <class Sink> void update_pressure(uint8_t p, uint8_t v, Sink& out) {
    if (!sounding(p)) return;
    pressure[p] = v;
    uint8_t n = note[p], m = max_pressure(n);
    if (pressure_should_send(m, sent[p])) { set_sent(n, m); out.pressure(n, m); }
  }
};

}  // namespace fm
