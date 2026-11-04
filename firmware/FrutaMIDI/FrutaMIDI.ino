/*
  FrutaMIDI - capacitive USB MIDI controller (Playtron style)

  Supported boards:
    - Raspberry Pi Pico / Pico 2 (Earle Philhower "Raspberry Pi Pico/RP2040/RP2350" core)
      -> Tools > USB Stack > "Adafruit TinyUSB"   (required!)
    - Arduino Pro Micro / Leonardo (ATmega32u4)

  Sensors: 1 or 2 x MPR121 (I2C), 12 pads each.

  Libraries (Library Manager):
    - Adafruit MPR121   (also installs Adafruit BusIO)
    - MIDI Library      (FortySevenEffects)  -> Pico only
    - MIDIUSB           (Arduino)            -> Pro Micro / Leonardo only

  Controls:
    - Button, short press : next scale (the LED blinks N times = scale N)
    - Button, held > 0.8 s: recalibrate the sensors (take your hands off the fruit!)
    - Potentiometer       : octave -2 .. +2 (optional, see USE_POT)

  Assembly:
    - Breadboard (README guide): default pins, I2C on GP4/GP5.
    - FrutaMIDI v1.0 PCB (hardware/ folder): uncomment the line below or build with -DFRUTAMIDI_PCB.
*/

// #define FRUTAMIDI_PCB

#include <Wire.h>
#include <Adafruit_MPR121.h>

// Pure decision logic (header-only, no Arduino dependency) is unit-tested on host:
// see tests/firmware/ and reports/firmware/coverage.md.
#include "fm_time.h"
#include "fm_scales.h"
#include "fm_debounce.h"
#include "fm_aftertouch.h"
#include "fm_button.h"
#include "fm_pot.h"
#include "fm_midi.h"
#include "fm_blink.h"
#include "fm_mpr121.h"
#include "fm_notes.h"
#include "fm_sensor_health.h"

// ============================ CONFIGURATION ============================

const char*    DEVICE_NAME       = "FrutaMIDI";     // name shown in the DAW (Pico only)
const uint8_t  NUM_SENSORS       = 1;               // 1 = 12 pads, 2 = 24 pads
const uint8_t  SENSOR_ADDR[2]    = {0x5A, 0x5B};    // ADDR->GND = 0x5A, ADDR->3V3 = 0x5B
const uint8_t  MIDI_CHANNEL      = 1;               // 1-16
const uint8_t  VELOCITY          = 100;             // fixed note velocity (1-127)
const uint8_t  TOUCH_THRESHOLD   = 12;              // higher = less sensitive
const uint8_t  RELEASE_THRESHOLD = 6;               // must be lower than TOUCH_THRESHOLD
const bool     AUTOCONFIG        = true;            // tunes the charge current to each object's size (essential for fruit)
const uint16_t DEBOUNCE_MS       = 15;              // ignores changes faster than this
const bool     SEND_AFTERTOUCH   = true;            // "pressure" -> Polyphonic Aftertouch
const uint16_t AT_MAX_DELTA      = 120;             // delta that maps to aftertouch 127
const uint16_t AT_INTERVAL_MS    = 15;              // minimum interval between aftertouch messages
const bool     USE_BUTTON        = true;            // scale / recalibration button
#ifdef FRUTAMIDI_PCB
const bool     USE_POT           = true;            // the PCB always has the octave potentiometer
#else
const bool     USE_POT           = false;           // true if you wire the octave potentiometer
#endif
const bool     SERIAL_DEBUG      = false;           // true = print deltas on the Serial Monitor (115200)

#if defined(ARDUINO_ARCH_RP2040) && defined(FRUTAMIDI_PCB)
#define I2C_BUS Wire1                               // PCB: all signals on the inner row of the Pico
const int PIN_SDA = 26, PIN_SCL = 27;               // GP26 / GP27 = I2C1 (physical pins 31 and 32)
const int PIN_BUTTON = 22;                          // GP22 (physical pin 29)
const int PIN_POT = 28;                             // GP28 / ADC2 (physical pin 34)
#elif defined(ARDUINO_ARCH_RP2040)
#define I2C_BUS Wire
const int PIN_SDA = 4, PIN_SCL = 5;                 // GP4 / GP5 (physical pins 6 and 7)
const int PIN_BUTTON = 15;                          // GP15 (physical pin 20)
const int PIN_POT = 26;                             // GP26 / ADC0 (physical pin 31)
#else
#define I2C_BUS Wire
const int PIN_BUTTON = 7;                           // Pro Micro: SDA=2 and SCL=3 are fixed
const int PIN_POT = A0;
#endif

// Scales (table, "fixed" flag and note mapping) live in fm_scales.h.
using fm::Scale;
using fm::SCALES;
using fm::NUM_SCALES;

// Compile-time guards for the configuration above (no runtime effect).
static_assert(NUM_SENSORS >= 1 && NUM_SENSORS <= 2, "NUM_SENSORS must be 1 or 2");
static_assert(MIDI_CHANNEL >= 1 && MIDI_CHANNEL <= 16, "MIDI_CHANNEL must be 1..16");
static_assert(VELOCITY >= 1 && VELOCITY <= 127, "VELOCITY must be 1..127");
static_assert(RELEASE_THRESHOLD < TOUCH_THRESHOLD, "RELEASE_THRESHOLD must be below TOUCH_THRESHOLD");
static_assert(AT_MAX_DELTA > TOUCH_THRESHOLD, "AT_MAX_DELTA must be above TOUCH_THRESHOLD");

// =========================== USB MIDI LAYER ===========================

#if defined(ARDUINO_ARCH_RP2040)
  #include <Adafruit_TinyUSB.h>
  #include <MIDI.h>

  Adafruit_USBD_MIDI usbMidi;
  MIDI_CREATE_INSTANCE(Adafruit_USBD_MIDI, usbMidi, MIDI);

  void midiBegin() {
    if (!TinyUSBDevice.isInitialized()) TinyUSBDevice.begin(0);
    TinyUSBDevice.setProductDescriptor(DEVICE_NAME);
    usbMidi.setStringDescriptor(DEVICE_NAME);
    MIDI.begin(MIDI_CHANNEL_OMNI);
    MIDI.turnThruOff();
    // The core already enumerated USB before setup(): force the host to re-read the descriptor.
    if (TinyUSBDevice.mounted()) {
      TinyUSBDevice.detach();
      delay(10);
      TinyUSBDevice.attach();
    }
  }
  void midiNoteOn(uint8_t note, uint8_t vel) { MIDI.sendNoteOn(note, vel, MIDI_CHANNEL); }
  void midiNoteOff(uint8_t note)             { MIDI.sendNoteOff(note, 0, MIDI_CHANNEL); }
  void midiPolyPressure(uint8_t note, uint8_t p) { MIDI.sendAfterTouch(note, p, MIDI_CHANNEL); }
  void midiTask()                            { MIDI.read(); }  // drain whatever the host sends

#elif defined(__AVR_ATmega32U4__)
  #include <MIDIUSB.h>

  void midiSend(uint8_t cin, uint8_t status, uint8_t d1, uint8_t d2) {
    midiEventPacket_t p = {cin, fm::channel_status(status, MIDI_CHANNEL), d1, d2};
    MidiUSB.sendMIDI(p);
    MidiUSB.flush();
  }
  void midiBegin() {}
  void midiNoteOn(uint8_t note, uint8_t vel) { midiSend(fm::CIN_NOTE_ON, fm::STATUS_NOTE_ON, note, vel); }
  void midiNoteOff(uint8_t note)             { midiSend(fm::CIN_NOTE_OFF, fm::STATUS_NOTE_OFF, note, 0); }
  void midiPolyPressure(uint8_t note, uint8_t p) { midiSend(fm::CIN_POLY_PRESSURE, fm::STATUS_POLY_PRESSURE, note, p); }
  void midiTask() {
    midiEventPacket_t rx;
    do { rx = MidiUSB.read(); } while (rx.header != 0);
  }

#else
  #error "Unsupported board: use a Raspberry Pi Pico (RP2040/RP2350) or an ATmega32u4 (Pro Micro / Leonardo)."
#endif

// ================================ STATE ================================

const uint8_t MAX_PADS = 24;
const uint8_t NUM_PADS = NUM_SENSORS * 12;

Adafruit_MPR121 sensors[2];
fm::SensorHealth health[2];              // presence monitoring and retry per sensor (fm_sensor_health.h)
fm::PadNotes<MAX_PADS> pads;             // note held by each pad, shared-note counting (fm_notes.h)
uint32_t lastChangeMs[MAX_PADS];
uint32_t lastPressureMs        = 0;
uint8_t  scaleIdx              = 0;
int8_t   octaveShift           = 0;
fm::Blinker led;                         // non-blocking LED signalling, ticked from loop()

// MIDI output used by the pad bookkeeping.
struct MidiOut {
  void noteOn(uint8_t note)                 { midiNoteOn(note, VELOCITY); }
  void noteOff(uint8_t note)                { midiNoteOff(note); }
  void pressure(uint8_t note, uint8_t p)    { midiPolyPressure(note, p); }
};
MidiOut midiOut;

// =============================== HELPERS ===============================

bool anySensorOk() {
  for (uint8_t s = 0; s < NUM_SENSORS; s++) if (health[s].ok) return true;
  return false;
}

bool anySensorLost() {
  for (uint8_t s = 0; s < NUM_SENSORS; s++) if (!health[s].ok) return true;
  return false;
}

uint8_t noteForPad(uint8_t pad) {
  return fm::note_for_pad(SCALES[scaleIdx], octaveShift, pad);
}

void pressPad(uint8_t pad) {
  pads.press(pad, noteForPad(pad), midiOut);   // Note On only if no other pad holds the note
}

void releasePad(uint8_t pad) {
  // Always the note that was turned on, even if the scale changed; Note Off only when the
  // last pad holding that note releases it (aftertouch 0 first if needed).
  pads.release(pad, midiOut);
}

void releaseAll() {
  for (uint8_t p = 0; p < NUM_PADS; p++) releasePad(p);
}

// After begin(): SCTS = 0 written explicitly and USL/TL/LSL derived from VDD (fm_mpr121.h).
// All writes happen in stop mode (ECR = 0), so the chip runs auto-configuration once, with
// these limits, when ECR is restored to the value begin() set.
void configureSensor(uint8_t s) {
  Adafruit_MPR121& m = sensors[s];
  uint8_t ecr = m.readRegister8(fm::MPR121_REG_ECR);
  uint8_t usl = fm::mpr121_usl(fm::MPR121_VDD_MV);
  m.writeRegister(fm::MPR121_REG_ECR, 0x00);
  m.writeRegister(fm::MPR121_REG_AUTOCONFIG1, fm::MPR121_AUTOCONFIG1_VALUE);
  m.writeRegister(fm::MPR121_REG_UPLIMIT, usl);
  m.writeRegister(fm::MPR121_REG_TARGETLIMIT, fm::mpr121_tl(usl));
  m.writeRegister(fm::MPR121_REG_LOWLIMIT, fm::mpr121_lsl(usl));
  m.writeRegister(fm::MPR121_REG_ECR, ecr);
}

bool readRegisters(uint8_t addr, uint8_t reg, uint8_t* buf, uint8_t n);

void startSensor(uint8_t s) {
  // begin() resets the chip; with AUTOCONFIG the MPR121 measures each electrode's capacitance
  // and picks the right charge current (a watermelon needs far more than a copper pad).
  bool ok = sensors[s].begin(SENSOR_ADDR[s], &I2C_BUS, TOUCH_THRESHOLD, RELEASE_THRESHOLD, AUTOCONFIG);
  // begin() calls Wire.begin(); on AVR that re-runs twi_init() = 100 kHz (review F-006).
  I2C_BUS.setClock(400000);
  if (ok && AUTOCONFIG) configureSensor(s);
  uint8_t ecr = 0;
  ok = ok && readRegisters(SENSOR_ADDR[s], fm::MPR121_REG_ECR, &ecr, 1);
  health[s].started(ok, millis(), ecr);
  if (SERIAL_DEBUG && Serial) {
    Serial.print("MPR121 0x"); Serial.print(SENSOR_ADDR[s], HEX);
    Serial.println(ok ? " OK" : " NOT FOUND");
  }
}

void startSensors() {
  for (uint8_t s = 0; s < NUM_SENSORS; s++) startSensor(s);
}

// A sensor stopped answering (or reset itself): release its notes; it is retried every 2 s.
void sensorLost(uint8_t s) {
  for (uint8_t e = 0; e < 12; e++) releasePad(s * 12 + e);
  if (SERIAL_DEBUG && Serial) { Serial.print("MPR121 0x"); Serial.print(SENSOR_ADDR[s], HEX); Serial.println(" LOST"); }
}

void recalibrate() {
  releaseAll();
  startSensors();
  led.start(millis(), fm::BLINK_RECAL_TIMES, fm::BLINK_RECAL_MS);
}

void nextScale() {
  scaleIdx = fm::next_scale_index(scaleIdx, NUM_SCALES);
  if (SERIAL_DEBUG && Serial) { Serial.print("Scale: "); Serial.println(SCALES[scaleIdx].name); }
  led.start(millis(), scaleIdx + 1, fm::BLINK_SCALE_MS);   // N blinks = scale N, pads stay live
}

// ================================ INPUTS ================================

void handleButton() {
  if (!USE_BUTTON) return;
  static fm::ButtonClassifier button;     // 10 ms sampling = debounce; > 800 ms = long press
  uint32_t now = millis();
  if (!button.sample_due(now)) return;

  bool down = digitalRead(PIN_BUTTON) == LOW;
  fm::ButtonEvent ev = button.update(now, down);
  if (ev == fm::ButtonEvent::LongPress) recalibrate();
  else if (ev == fm::ButtonEvent::ShortPress) nextScale();
}

void handlePot() {
  if (!USE_POT) return;
  static uint32_t lastRead = 0;
  if (!fm::elapsed_at_least(millis(), lastRead, fm::POT_READ_MS)) return;
  lastRead = millis();

  // 5 zones (-2 .. +2) with hysteresis so the octave does not flicker at a border.
  int8_t next = fm::octave_from_adc(analogRead(PIN_POT), octaveShift);
  if (next != octaveShift) {
    octaveShift = next;
    if (SERIAL_DEBUG && Serial) { Serial.print("Octave: "); Serial.println(octaveShift); }
  }
}

// Burst read of `n` consecutive MPR121 registers starting at `reg` (auto-increment,
// repeated start). Returns false if the sensor did not acknowledge or returned fewer bytes.
bool readRegisters(uint8_t addr, uint8_t reg, uint8_t* buf, uint8_t n) {
  I2C_BUS.beginTransmission(addr);
  I2C_BUS.write(reg);
  if (I2C_BUS.endTransmission(false) != 0) return false;
  if (I2C_BUS.requestFrom(addr, n) != n) return false;
  for (uint8_t i = 0; i < n; i++) buf[i] = (uint8_t)I2C_BUS.read();
  return true;
}

// Filtered + baseline data of electrodes lo .. lo+n-1 of sensor s: 2 burst transactions
// instead of 2 transactions per sounding pad.
bool readSensorData(uint8_t s, uint8_t lo, uint8_t n, uint8_t* filt, uint8_t* base) {
  return readRegisters(SENSOR_ADDR[s], fm::MPR121_REG_FILTDATA_0 + 2 * lo, filt, 2 * n) &&
         readRegisters(SENSOR_ADDR[s], fm::MPR121_REG_BASELINE_0 + lo, base, n);
}

// delta = how far the capacitance rose above the baseline (closer hand / more skin = larger)
void sendPressure(uint8_t pad, int delta) {
  pads.update_pressure(pad, fm::pressure_from_delta(delta, TOUCH_THRESHOLD, AT_MAX_DELTA), midiOut);
}

void debugPrint() {
  static uint32_t last = 0;
  if (!SERIAL_DEBUG || !Serial || millis() - last < 250) return;
  last = millis();
  Serial.print("delta:");
  for (uint8_t s = 0; s < NUM_SENSORS; s++) {
    if (!health[s].ok) continue;
    for (uint8_t e = 0; e < 12; e++) {
      Serial.print(' ');
      Serial.print((int)sensors[s].baselineData(e) - (int)sensors[s].filteredData(e));
    }
  }
  Serial.println();
}

// ============================ SETUP / LOOP ============================

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  if (USE_BUTTON) pinMode(PIN_BUTTON, INPUT_PULLUP);

  midiBegin();
  if (SERIAL_DEBUG) Serial.begin(115200);

#if defined(ARDUINO_ARCH_RP2040)
  I2C_BUS.setSDA(PIN_SDA);
  I2C_BUS.setSCL(PIN_SCL);
#endif
  I2C_BUS.begin();
  I2C_BUS.setClock(400000);

  pads.reset();
  for (uint8_t p = 0; p < MAX_PADS; p++) lastChangeMs[p] = 0;

  startSensors();
  if (anySensorOk()) led.start(millis(), fm::BLINK_READY_TIMES, fm::BLINK_READY_MS);   // 2 slow blinks = ready
}

void loop() {
  midiTask();

  // Lost or missing sensors are retried every 2 s (the MPR121 can be connected while running).
  for (uint8_t s = 0; s < NUM_SENSORS; s++) if (health[s].retry_due(millis())) startSensor(s);

  // No sensor: blink fast.
  if (!anySensorOk()) {
    digitalWrite(LED_BUILTIN, led.level_or(millis(), (millis() / 100) % 2));
    return;
  }

  handleButton();
  handlePot();

  uint32_t now = millis();
  bool pressureDue = SEND_AFTERTOUCH && fm::elapsed_at_least(now, lastPressureMs, AT_INTERVAL_MS);
  if (pressureDue) lastPressureMs = now;
  bool anyTouched = false;

  for (uint8_t s = 0; s < NUM_SENSORS; s++) {
    if (!health[s].ok) continue;

    // Touch status read with the transaction result (a NACK must not look like 12 touches).
    uint8_t st[2];
    bool readOk = readRegisters(SENSOR_ADDR[s], fm::MPR121_REG_TOUCHSTATUS, st, 2);
    if (health[s].report(readOk)) { sensorLost(s); continue; }
    if (!readOk) continue;                   // keep the pads as they are for this loop
    if (health[s].check_due(now)) {
      uint8_t ecr = 0;
      bool ecrOk = readRegisters(SENSOR_ADDR[s], fm::MPR121_REG_ECR, &ecr, 1);
      if (health[s].report_check(ecrOk, ecr)) { sensorLost(s); continue; }
    }
    uint16_t bits = fm::mpr121_touch_bits(st);
    uint16_t sounding = 0;                   // bit e = pad of electrode e has a note on

    for (uint8_t e = 0; e < 12; e++) {
      uint8_t pad = s * 12 + e;
      bool touched = fm::pad_touched(bits, e);
      bool active  = pads.sounding(pad);

      fm::PadAction action = fm::pad_step(touched, active, now, lastChangeMs[pad], DEBOUNCE_MS);
      if (action == fm::PadAction::Press) pressPad(pad);
      else if (action == fm::PadAction::Release) releasePad(pad);
      if (touched) anyTouched = true;
      if (pads.sounding(pad)) sounding |= (uint16_t)(1u << e);
    }

    // Aftertouch: burst reads over runs of sounding pads (one run when they are adjacent,
    // all 12 pads = 2 transactions) instead of 2 transactions per sounding pad.
    uint8_t lo, n;
    for (uint8_t from = 0; pressureDue && fm::mpr121_next_run(sounding, from, lo, n); from = lo + n) {
      uint8_t filt[fm::MPR121_FILT_BYTES], base[fm::MPR121_BASE_BYTES];
      bool dataOk = readSensorData(s, lo, n, filt, base);
      if (health[s].report(dataOk)) { sensorLost(s); break; }
      if (!dataOk) continue;
      for (uint8_t e = lo; e < lo + n; e++) {
        if (sounding & (1u << e)) sendPressure(s * 12 + e, fm::mpr121_delta(filt, base, e - lo));
      }
    }
  }

  // A lost sensor (or a missing second one) shows the fast error blink instead of touch.
  bool idle = anySensorLost() ? ((millis() / 100) % 2) != 0 : anyTouched;
  digitalWrite(LED_BUILTIN, led.level_or(millis(), idle));
  debugPrint();
}
