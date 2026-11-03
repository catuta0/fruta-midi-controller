// FrutaMIDI pure logic: decoding of MPR121 burst reads (filtered and baseline data).
// Header-only, no Arduino dependency (host-testable). C++11 compatible (avr-gcc).
//
// Register addresses as used by the linked Adafruit_MPR121 1.2.1 library
// (Adafruit_MPR121.h: MPR121_FILTDATA_0L = 0x04, MPR121_BASELINE_0 = 0x1E):
//   0x04..0x1B  filtered data E0..E11, 2 bytes each, LSB first, 10 bits (24 bytes)
//   0x1C..0x1D  filtered data ELEPROX (not read)
//   0x1E..0x29  baseline E0..E11, 1 byte each = upper 8 of 10 bits (12 bytes)
// Multiple-byte reads with register auto-increment: MPR121 datasheet S-006 section 6.4.
// The two blocks are read as two transactions so each fits the 32-byte AVR Wire buffer,
// and only over runs of sounding electrodes (see mpr121_next_run).
#pragma once
#include <stdint.h>

namespace fm {

const uint8_t MPR121_ELECTRODES     = 12;
const uint8_t MPR121_REG_FILTDATA_0 = 0x04;
const uint8_t MPR121_REG_BASELINE_0 = 0x1E;
const uint8_t MPR121_FILT_BYTES     = 2 * MPR121_ELECTRODES;   // 24
const uint8_t MPR121_BASE_BYTES     = MPR121_ELECTRODES;       // 12

// Burst plan for aftertouch: the sounding electrodes (bit e of `mask`) are read in runs.
// A run of n electrodes costs (3 + 2n) + (3 + n) = 6 + 3n bytes on the bus (address,
// register, repeated-start address, data; two transactions). Bridging a gap of g silent
// electrodes adds 3g bytes and saves 6, so runs are merged across gaps <= MPR121_MERGE_GAP.
// Result: never more bytes than the old 9 bytes per sounding pad, at most 42 for 12 pads.
const uint8_t MPR121_MERGE_GAP = 1;

// Next run at or after electrode `from`: [lo, lo + n). Returns false when none is left.
inline bool mpr121_next_run(uint16_t mask, uint8_t from, uint8_t& lo, uint8_t& n) {
  lo = 0; n = 0;
  uint8_t e = from;
  while (e < MPR121_ELECTRODES && !(mask & (1u << e))) e++;
  if (e >= MPR121_ELECTRODES) return false;
  lo = e;
  uint8_t hi = e, gap = 0;
  for (e = (uint8_t)(e + 1); e < MPR121_ELECTRODES; e++) {
    if (mask & (1u << e)) { hi = e; gap = 0; }
    else if (++gap > MPR121_MERGE_GAP) break;
  }
  n = (uint8_t)(hi - lo + 1);
  return true;
}

// Values below index a block that starts at electrode `lo`; pass (e - lo) as the index.
// 10-bit filtered value of electrode e from the 24-byte filtered block.
// Bits 7..2 of the high byte are not part of the value and are masked off.
inline uint16_t mpr121_filtered(const uint8_t* filt, uint8_t e) {
  return (uint16_t)(filt[2 * e] | ((uint16_t)(filt[2 * e + 1] & 0x03u) << 8));
}

// Baseline of electrode e on the same 10-bit scale (register holds bits 9..2).
inline uint16_t mpr121_baseline(const uint8_t* base, uint8_t e) {
  return (uint16_t)((uint16_t)base[e] << 2);
}

// delta = baseline - filtered, as in the original per-electrode code.
inline int mpr121_delta(const uint8_t* filt, const uint8_t* base, uint8_t e) {
  return (int)mpr121_baseline(base, e) - (int)mpr121_filtered(filt, e);
}

// ---- Configuration written after Adafruit_MPR121::begin() (T-041, ADR-008 F-1/F-2) ----
// begin() (library 1.2.1) writes AUTOCONFIG0 (0x7B) = 0x0B (FFI 6 samples, RETRY 0, BVA = CL,
// ARE = 1, ACE = 1) and fixed limits USL/TL/LSL = 200/180/130; it never writes AUTOCONFIG1.
const uint8_t MPR121_REG_ECR         = 0x5E;
const uint8_t MPR121_REG_AUTOCONFIG0 = 0x7B;
const uint8_t MPR121_REG_AUTOCONFIG1 = 0x7C;
const uint8_t MPR121_REG_UPLIMIT     = 0x7D;
const uint8_t MPR121_REG_LOWLIMIT    = 0x7E;
const uint8_t MPR121_REG_TARGETLIMIT = 0x7F;

// AUTOCONFIG1 (0x7C, datasheet S-006): bit 7 (D7) SCTS (skip charge time search), bit 2 OORIE, bit 1 ARFIE,
// bit 0 ACFIE (interrupt enables, IRQ pin unused here). Bits 6..3 reserved = 0.
inline uint8_t mpr121_autoconfig1(bool scts, bool oorie, bool arfie, bool acfie) {
  return (uint8_t)((scts ? 0x80u : 0u) | (oorie ? 0x04u : 0u) | (arfie ? 0x02u : 0u) | (acfie ? 0x01u : 0u));
}
// SCTS = 0: AUTOCONFIG searches both charge current and charge time (needed with 3.3 kOhm
// in series with each electrode, ADR-008). Interrupts off. Equals the reset value.
const uint8_t MPR121_AUTOCONFIG1_VALUE = 0x00;

// Auto-configuration limits from the supply voltage (datasheet S-006 formula, integer truncation):
// USL = (VDD - 0.7) / VDD * 256, TL = 0.9 * USL, LSL = 0.65 * USL.
// Design VDD 3.2 V (ADR-010): between the 3.3 V nominal rail and the lower measured-case
// estimate (3.10 V, reports/electronics/analysis.md). Gives exactly 200/180/130, the values
// AN3889 lists for 3.3 V-class supplies and the Adafruit library uses; written explicitly.
const uint16_t MPR121_VDD_MV = 3200;
inline uint8_t mpr121_usl(uint16_t vddMv) {
  return (uint8_t)(((uint32_t)(vddMv - 700u) * 256u) / vddMv);
}
inline uint8_t mpr121_tl(uint8_t usl)  { return (uint8_t)((uint16_t)usl * 9u / 10u); }
inline uint8_t mpr121_lsl(uint8_t usl) { return (uint8_t)((uint16_t)usl * 65u / 100u); }

}  // namespace fm
