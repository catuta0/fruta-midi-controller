/*
  FrutaMIDI — controlador MIDI USB capacitivo (estilo Playtron)

  Placas suportadas:
    - Raspberry Pi Pico / Pico 2 (core "Raspberry Pi Pico/RP2040/RP2350" de Earle Philhower)
      -> Ferramentas > USB Stack > "Adafruit TinyUSB"   (obrigatório!)
    - Arduino Pro Micro / Leonardo (ATmega32u4)

  Sensores: 1 ou 2 × MPR121 (I2C), 12 pads cada.

  Bibliotecas (Gestor de Bibliotecas):
    - Adafruit MPR121   (instala também a Adafruit BusIO)
    - MIDI Library      (FortySevenEffects)  -> só para o Pico
    - MIDIUSB           (Arduino)            -> só para o Pro Micro / Leonardo

  Controlos:
    - Botão, toque curto  : próxima escala (o LED pisca N vezes = escala N)
    - Botão, 1 s premido  : recalibrar os sensores (tira as mãos das frutas!)
    - Potenciómetro       : oitava -2 … +2 (opcional, ver USE_POT)
*/

#include <Wire.h>
#include <Adafruit_MPR121.h>

// ============================ CONFIGURAÇÃO ============================

const char*    DEVICE_NAME       = "FrutaMIDI";     // nome que aparece no DAW (só Pico)
const uint8_t  NUM_SENSORS       = 1;               // 1 = 12 pads, 2 = 24 pads
const uint8_t  SENSOR_ADDR[2]    = {0x5A, 0x5B};    // ADDR->GND = 0x5A, ADDR->3V3 = 0x5B
const uint8_t  MIDI_CHANNEL      = 1;               // 1–16
const uint8_t  VELOCITY          = 100;             // velocidade fixa das notas (1–127)
const uint8_t  TOUCH_THRESHOLD   = 12;              // mais alto = menos sensível
const uint8_t  RELEASE_THRESHOLD = 6;               // tem de ser menor que TOUCH_THRESHOLD
const bool     AUTOCONFIG        = true;            // ajusta a corrente de carga ao tamanho de cada objeto (essencial p/ fruta)
const uint16_t DEBOUNCE_MS       = 15;              // ignora mudanças mais rápidas que isto
const bool     SEND_AFTERTOUCH   = true;            // "pressão" -> Polyphonic Aftertouch
const uint16_t AT_MAX_DELTA      = 120;             // delta que corresponde a aftertouch 127
const uint16_t AT_INTERVAL_MS    = 15;              // intervalo mínimo entre mensagens de aftertouch
const bool     USE_BUTTON        = true;            // botão de escala / recalibração
const bool     USE_POT           = false;           // true se ligares o potenciómetro de oitava
const bool     SERIAL_DEBUG      = false;           // true = imprime deltas no Monitor Série (115200)

#if defined(ARDUINO_ARCH_RP2040)
const int PIN_SDA = 4, PIN_SCL = 5;                 // GP4 / GP5 (pinos físicos 6 e 7)
const int PIN_BUTTON = 15;                          // GP15 (pino físico 20)
const int PIN_POT = 26;                             // GP26 / ADC0 (pino físico 31)
#else
const int PIN_BUTTON = 7;                           // Pro Micro: SDA=2 e SCL=3 são fixos
const int PIN_POT = A0;
#endif

// Escalas. "fixed" = ignora o potenciómetro de oitava (útil para Drum Racks).
struct Scale {
  const char* name;
  uint8_t root;        // nota MIDI do pad 0 (36 = C1, 48 = C2 no Ableton / C3 noutros)
  uint8_t len;
  int8_t steps[12];
  bool fixed;
};

const Scale SCALES[] = {
  {"Drum Rack (notas 36-47)", 36, 12, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}, true},
  {"Pentatonica maior",       48,  5, {0, 2, 4, 7, 9},                         false},
  {"Pentatonica menor",       48,  5, {0, 3, 5, 7, 10},                        false},
  {"Maior",                   48,  7, {0, 2, 4, 5, 7, 9, 11},                  false},
  {"Menor natural",           48,  7, {0, 2, 3, 5, 7, 8, 10},                  false},
  {"Cromatica",               48, 12, {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}, false},
};
const uint8_t NUM_SCALES = sizeof(SCALES) / sizeof(SCALES[0]);

// =========================== CAMADA MIDI USB ===========================

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
    // O core já enumerou o USB antes do setup(): força o computador a voltar a ler o descritor.
    if (TinyUSBDevice.mounted()) {
      TinyUSBDevice.detach();
      delay(10);
      TinyUSBDevice.attach();
    }
  }
  void midiNoteOn(uint8_t note, uint8_t vel) { MIDI.sendNoteOn(note, vel, MIDI_CHANNEL); }
  void midiNoteOff(uint8_t note)             { MIDI.sendNoteOff(note, 0, MIDI_CHANNEL); }
  void midiPolyPressure(uint8_t note, uint8_t p) { MIDI.sendAfterTouch(note, p, MIDI_CHANNEL); }
  void midiTask()                            { MIDI.read(); }  // esvazia o que o computador mandar

#elif defined(__AVR_ATmega32U4__)
  #include <MIDIUSB.h>

  void midiSend(uint8_t cin, uint8_t status, uint8_t d1, uint8_t d2) {
    midiEventPacket_t p = {cin, (uint8_t)(status | (MIDI_CHANNEL - 1)), d1, d2};
    MidiUSB.sendMIDI(p);
    MidiUSB.flush();
  }
  void midiBegin() {}
  void midiNoteOn(uint8_t note, uint8_t vel) { midiSend(0x09, 0x90, note, vel); }
  void midiNoteOff(uint8_t note)             { midiSend(0x08, 0x80, note, 0); }
  void midiPolyPressure(uint8_t note, uint8_t p) { midiSend(0x0A, 0xA0, note, p); }
  void midiTask() {
    midiEventPacket_t rx;
    do { rx = MidiUSB.read(); } while (rx.header != 0);
  }

#else
  #error "Placa nao suportada: usa um Raspberry Pi Pico (RP2040/RP2350) ou um ATmega32u4 (Pro Micro / Leonardo)."
#endif

// ================================ ESTADO ================================

const uint8_t NONE = 255;
const uint8_t MAX_PADS = 24;
const uint8_t NUM_PADS = NUM_SENSORS * 12;

Adafruit_MPR121 sensors[2];
bool     sensorOk[2]           = {false, false};
uint8_t  activeNote[MAX_PADS];          // nota enviada por cada pad (NONE = solto)
uint8_t  lastPressure[MAX_PADS];
uint32_t lastChangeMs[MAX_PADS];
uint32_t lastPressureMs        = 0;
uint8_t  scaleIdx              = 0;
int8_t   octaveShift           = 0;

// =============================== AJUDANTES ===============================

void blink(uint8_t times, uint16_t ms) {
  for (uint8_t i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH); delay(ms);
    digitalWrite(LED_BUILTIN, LOW);  delay(ms);
  }
}

bool anySensorOk() {
  for (uint8_t s = 0; s < NUM_SENSORS; s++) if (sensorOk[s]) return true;
  return false;
}

uint8_t noteForPad(uint8_t pad) {
  const Scale& sc = SCALES[scaleIdx];
  int oct  = sc.fixed ? 0 : octaveShift;
  int note = sc.root + 12 * oct + sc.steps[pad % sc.len] + 12 * (pad / sc.len);
  return (uint8_t)constrain(note, 0, 127);
}

void pressPad(uint8_t pad) {
  uint8_t note = noteForPad(pad);
  activeNote[pad]   = note;
  lastPressure[pad] = 0;
  midiNoteOn(note, VELOCITY);
}

void releasePad(uint8_t pad) {
  if (activeNote[pad] == NONE) return;
  midiNoteOff(activeNote[pad]);      // desliga sempre a nota que foi ligada, mesmo que a escala tenha mudado
  activeNote[pad] = NONE;
}

void releaseAll() {
  for (uint8_t p = 0; p < NUM_PADS; p++) releasePad(p);
}

void startSensors() {
  for (uint8_t s = 0; s < NUM_SENSORS; s++) {
    // begin() faz reset ao chip; com AUTOCONFIG o MPR121 mede a capacidade de cada elétrodo
    // e escolhe a corrente de carga certa (uma melancia precisa de muito mais que um pad de cobre).
    sensorOk[s] = sensors[s].begin(SENSOR_ADDR[s], &Wire, TOUCH_THRESHOLD, RELEASE_THRESHOLD, AUTOCONFIG);
    if (SERIAL_DEBUG && Serial) {
      Serial.print("MPR121 0x"); Serial.print(SENSOR_ADDR[s], HEX);
      Serial.println(sensorOk[s] ? " OK" : " NAO ENCONTRADO");
    }
  }
}

void recalibrate() {
  releaseAll();
  startSensors();
  blink(3, 60);
}

void nextScale() {
  scaleIdx = (scaleIdx + 1) % NUM_SCALES;
  if (SERIAL_DEBUG && Serial) { Serial.print("Escala: "); Serial.println(SCALES[scaleIdx].name); }
  blink(scaleIdx + 1, 90);
}

// ================================ ENTRADAS ================================

void handleButton() {
  if (!USE_BUTTON) return;
  static uint32_t lastSample = 0, downAt = 0;
  static bool wasDown = false, longDone = false;
  uint32_t now = millis();
  if (now - lastSample < 10) return;   // amostra a cada 10 ms = debounce
  lastSample = now;

  bool down = digitalRead(PIN_BUTTON) == LOW;
  if (down && !wasDown) { downAt = now; longDone = false; }
  if (down && !longDone && now - downAt > 800) { longDone = true; recalibrate(); }
  if (!down && wasDown && !longDone) nextScale();
  wasDown = down;
}

void handlePot() {
  if (!USE_POT) return;
  static uint32_t lastRead = 0;
  if (millis() - lastRead < 30) return;
  lastRead = millis();

  // 5 zonas (-2 … +2) com histerese para não saltar entre oitavas na fronteira.
  float pos = analogRead(PIN_POT) * 5.0f / 1024.0f;   // 0.0 … 5.0
  float centre = (octaveShift + 2) + 0.5f;
  if (fabsf(pos - centre) > 0.7f) {
    octaveShift = constrain((int)pos, 0, 4) - 2;
    if (SERIAL_DEBUG && Serial) { Serial.print("Oitava: "); Serial.println(octaveShift); }
  }
}

void sendPressure(uint8_t s, uint8_t e, uint8_t pad) {
  // delta = quanto a capacidade subiu em relação à linha de base (mão mais perto / mais pele = maior)
  int delta = (int)sensors[s].baselineData(e) - (int)sensors[s].filteredData(e);
  long p = map(constrain(delta, TOUCH_THRESHOLD, AT_MAX_DELTA), TOUCH_THRESHOLD, AT_MAX_DELTA, 0, 127);
  if (abs((int)p - (int)lastPressure[pad]) >= 2) {
    lastPressure[pad] = (uint8_t)p;
    midiPolyPressure(activeNote[pad], (uint8_t)p);
  }
}

void debugPrint() {
  static uint32_t last = 0;
  if (!SERIAL_DEBUG || !Serial || millis() - last < 250) return;
  last = millis();
  Serial.print("delta:");
  for (uint8_t s = 0; s < NUM_SENSORS; s++) {
    if (!sensorOk[s]) continue;
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
  Wire.setSDA(PIN_SDA);
  Wire.setSCL(PIN_SCL);
#endif
  Wire.begin();
  Wire.setClock(400000);

  for (uint8_t p = 0; p < MAX_PADS; p++) {
    activeNote[p] = NONE;
    lastPressure[p] = 0;
    lastChangeMs[p] = 0;
  }

  startSensors();
  if (anySensorOk()) blink(2, 120);   // 2 piscadelas lentas = pronto
}

void loop() {
  midiTask();

  // Sem sensor: pisca depressa e tenta de novo a cada 2 s (podes ligar o MPR121 com tudo a correr).
  if (!anySensorOk()) {
    static uint32_t lastTry = 0;
    digitalWrite(LED_BUILTIN, (millis() / 100) % 2);
    if (millis() - lastTry > 2000) { lastTry = millis(); startSensors(); }
    return;
  }

  handleButton();
  handlePot();

  uint32_t now = millis();
  bool pressureDue = SEND_AFTERTOUCH && now - lastPressureMs >= AT_INTERVAL_MS;
  if (pressureDue) lastPressureMs = now;
  bool anyTouched = false;

  for (uint8_t s = 0; s < NUM_SENSORS; s++) {
    if (!sensorOk[s]) continue;
    uint16_t bits = sensors[s].touched();

    for (uint8_t e = 0; e < 12; e++) {
      uint8_t pad = s * 12 + e;
      bool touched = bits & (1 << e);
      bool active  = activeNote[pad] != NONE;

      if (touched != active && now - lastChangeMs[pad] >= DEBOUNCE_MS) {
        lastChangeMs[pad] = now;
        if (touched) pressPad(pad); else releasePad(pad);
      }
      if (touched) anyTouched = true;
      if (pressureDue && activeNote[pad] != NONE) sendPressure(s, e, pad);
    }
  }

  digitalWrite(LED_BUILTIN, anyTouched);
  debugPrint();
}
