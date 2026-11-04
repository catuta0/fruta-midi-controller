# Independent review of 72f67f0 (T-060)

Reviewer: independent-reviewer (inputs: REQUIREMENTS.md, INTERFACES.json frozen-1, released outputs; no handoffs). Written to file by the manager verbatim in substance because the reviewer's harness refused report writes. Checks run by the reviewer: kicad_erc "Found 0 violations"; kicad_drc 0/0/0; run_pytest tests/firmware "268 passed"; firmware_compile rpipico PCB "Sketch uses 90700 bytes (4%)". External SOURCE: Adafruit Eagle files (github.com/adafruit/Adafruit-MPR121-PCB), read via WebFetch.

Summary: 16 findings — 0 critical, 3 major, 9 minor, 4 info.

| ID | Sev | Finding (evidence) | Disposition | Owner / task |
|---|---|---|---|---|
| F-001 | major | hardware/README.md:176 says a wrong JP1 position is harmless; REQ-040 FAIL: +3V3 on ADDR (QT) / IRQ (orig) of an unpowered chip exceeds VDD+0.3 V abs. max; back-feed through module 10k pull-ups. | FIX: README §5 states abs-max violation and back-feed; §6 adds "check JP1 continuity to S1 or S7 before inserting the module". | documentation T-038 |
| F-002 | major | ±4 kV "A: PASS" compares peak current only; IEC 4 kV through 3.63 kΩ: τ 545 ns, Q 600 nC vs HBM 2 kV τ 150 ns, Q 200 nC; pin limit is ASSUMPTION; resistor not pulse-rated. | FIX: REQ-023 analysis relabelled "estimate on ASSUMPTIONs, not PASS"; charge/energy comparison added; closure only by ESD-gun test with a pulse-rated resistor (CR-001). | systems T-012, docs T-038 |
| F-010 | major | REQ-018 PARTIAL although budgets A3b FAIL (VBUS 4.40 V < 4.50 V recommended). | FIX: REQ-018 → FAIL; counts updated. | systems T-012 |
| F-003 | minor | Pot hysteresis defined two ways; dead band 0.132 V; 30 mV offset is 22.7 % of it, not 6.5 %; static offset does not consume hysteresis. | FIX: restate REQ-006; replace A5 with noise/DNL criterion. | systems T-012 |
| F-004 | minor | Two held pads can share a note (octave change); releasing one sends Note Off while the other is held. | FIX: per-note reference counting in firmware + host test; manual corrected. | firmware T-044, docs T-038 |
| F-005 | minor | Sensor lost during play not detected; missing 2nd sensor never retried. | FIX: periodic presence check, mark sensor lost, release its notes, retry; host test with failing-bus stub; REQ-009 behaviour specified. | firmware T-044, systems T-012 |
| F-006 | minor | Leonardo may run I2C at 100 kHz (setClock before begin; AVR twi_init may reset). | FIX: inspect AVR Wire; call setClock after sensor begin on all cores. | firmware T-044 |
| F-007 | minor | REQ-033 evidence (T-041 build logs) not in the commit. | FIX: commit logs; check every evidence path exists in git. | manager |
| F-008 | minor | budgets.md stale vs budgets.out/REQUIREMENTS (latency, rise time, BOM); coverage.md "USL 201". | FIX: regenerate budgets.md from budgets.out; reconcile coverage.md. | systems T-012, firmware T-044 |
| F-009 | minor | README.md:151 names an "aprender" button; sampler uses "learn". | FIX. | documentation T-038 |
| F-011 | minor | Latency model omits the 15 ms firmware pad lockout (re-touch can add up to 15 ms). | FIX: REQ-014 scoped to first touch after idle; lockout shown separately in the model. | systems T-012 |
| F-014 | minor | Terminal 0.9 mm square pin diagonal 1.27 mm in 1.3 mm hole (0.03 mm); pot slots 2.1×1.8 drilled with a 1.8 mm bit; pin sizes unsourced. | FIX: terminal drill 1.4 mm (ring stays ≥0.4 mm); slot instructions in README; source pin sizes if available. | electronics T-056, docs T-038 |
| F-012 | info | Latency worst case rests on an assumed MPR121 status-update model. | ACCEPTED as ASSUMPTION; measured by plan V/P-2. | — |
| F-013 | info | ERC ignores single-pin labels globally. | FIX at root: replace S-row single-pin labels on unused pins with no-connect flags and remove the global ignore if ERC stays clean. | electronics T-056 |
| F-015 | info | BOM lacks MPNs for A1, A2, J2, RV1, SW1 and the headers; README "3 strips of 1×40" (2 suffice). | FIX: add maker/MPN fields where a real part is named; README strip count. | electronics T-056, docs T-038 |
| F-016 | info | AGND only on A1 pin 33 and RV1 pin 3; relies on the Pico's internal tie. | FIX: cite Pico datasheet statement. | systems T-012 |

Verified OK (reviewer): module socket geometry and S1–S7 mapping for both Adafruit revisions vs Eagle files; electrode row order; JP1 never reaches GND; Pico socket numbering; PCB nets vs firmware pins (PCB and breadboard); R13–R16, J1, JP1 nets; MIDI status bytes and USB-MIDI CIN; bMaxPower 100 mA; AUTOCONFIG limits and write sequence; millis wrap safety; max note 127 without clamp; drill file 131 holes / 7 sizes; Gerber job single-sided, 0 vias.
Not covered: INTERFACES.json field by field; visual check of copper PDFs and mirroring; sampler beyond the MIDI handler; 8 of 9 firmware targets; MPR121 power-on-reset timing.
