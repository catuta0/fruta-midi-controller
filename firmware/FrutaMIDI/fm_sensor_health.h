// FrutaMIDI pure logic: MPR121 presence monitoring and retry (review finding F-005).
// Every loop the sketch reads the touch status itself and reports whether the I2C
// transaction succeeded (Adafruit touched() cannot report it: on a NACK BusIO read()
// returns -1 and touched() returns 0x0FFF = all 12 pads touched). Every SENSOR_CHECK_MS
// the ECR register is read back: a different value means the chip reset itself (it then
// sits in stop mode and still ACKs). A lost or missing sensor is retried every
// SENSOR_RETRY_MS. Header-only, no Arduino dependency (host-testable). C++11 compatible.
#pragma once
#include <stdint.h>
#include "fm_time.h"

namespace fm {

const uint8_t  SENSOR_FAIL_LIMIT = 3;     // consecutive failed transactions -> lost
const uint16_t SENSOR_CHECK_MS   = 250;   // ECR read-back period while running
const uint16_t SENSOR_RETRY_MS   = 2000;  // retry period for a lost or missing sensor (strictly >)

struct SensorHealth {
  bool     ok          = false;
  uint8_t  fails       = 0;
  uint8_t  expectedEcr = 0;
  uint32_t lastCheck   = 0;
  uint32_t lastRetry   = 0;

  // Result of a begin() attempt (initial, retry or recalibration).
  void started(bool success, uint32_t now, uint8_t ecr) {
    ok = success; fails = 0; expectedEcr = ecr; lastCheck = now; lastRetry = now;
  }

  // Result of one I2C transaction. True when the sensor has just been declared lost.
  bool report(bool success) {
    if (!ok) return false;
    if (success) { fails = 0; return false; }
    if (++fails >= SENSOR_FAIL_LIMIT) { ok = false; fails = 0; return true; }
    return false;
  }

  bool check_due(uint32_t now) {
    if (!ok || !elapsed_at_least(now, lastCheck, SENSOR_CHECK_MS)) return false;
    lastCheck = now;
    return true;
  }

  // Result of the periodic ECR read-back. A wrong value = chip reset = lost at once.
  bool report_check(bool success, uint8_t ecr) {
    if (!ok) return false;
    if (success && ecr != expectedEcr) { ok = false; fails = 0; return true; }
    return report(success);
  }

  bool retry_due(uint32_t now) {
    if (ok || !elapsed_more_than(now, lastRetry, SENSOR_RETRY_MS)) return false;
    lastRetry = now;
    return true;
  }
};

}  // namespace fm
