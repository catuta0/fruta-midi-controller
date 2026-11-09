# Sources — electronics (T-050)

Accessed 2026-10-30. "Read" means the text was opened and the quoted value was found in it. "Search" means the
value comes from a search-engine extract of the document; it was not opened, so treat it as lower confidence.

| ID | Source | Values used | How |
|---|---|---|---|
| EE-S01 | NXP/Freescale MPR121 data sheet, https://www.nxp.com/docs/en/data-sheet/MPR121.pdf | VDD 2.0–3.6 V (Table 5); abs max VDD −0.3..+3.6 V, SDA/SCL/IRQ VSS−0.3..VDD+0.3 V (Table 3); ESD HBM ±2000 V, MM ±200 V, CDM ±500 V (Table 4); IDD 393 µA @ 1 ms, peak 1 mA; ELE leakage 0.025 µA; ELE self-capacitance 15 pF; SDA/SCL VIH 0.7·VDD, C 7 pF; fSCL 400 kHz, tR 20+0.1Cb..300 ns (Table 7); CDC 1–63 µA, CDT 0.5–32 µs; USL/TL/LSL Eqn 1–3; Cin = I·T/V Eqn 4; "sampled at the end of each charge cycle"; SCTS = 0 also searches CDT; 10 pF–2000 pF range; pull-up "typically 4.7 kΩ" | Read (PDF text extracted locally) |
| EE-S02 | Adafruit MPR121 breakout Eagle schematic (original, 1982), https://github.com/adafruit/Adafruit-MPR121-PCB `Adafruit MPR121 Breakout.sch` | U4 MIC5225-3.3, IN+EN = VIN, OUT = 3.3V = MPR121 VDD; Q1/Q2 BSS138, gate = 3.3V; 10k R2/R4 to VIN (host side), 10k R1/R3 to 3.3V (chip side); JP2: 1 VIN, 2 3.3V, 3 GND, 4 ADDR, 5 SDA, 6 SCL, 7 IRQ; ELEC nets go straight from MPR121 to JP1 (no series R); red LED + 1k on IRQ | Read (XML nets) |
| EE-S03 | Adafruit Eagle schematic STEMMA QT, same repo, `Adafruit MPR121Q QT.sch` | U2 AP2112K-3.3, IN+EN = VCC; OUT = 3.3V = MPR121 VDD; dual BSS138 Q3, gate = 3.3V; R8 4×10k pack (2 to VCC, 2 to 3.3V); JP2: 1 VCC, 2 3.3V, 3 GND, 4 SCL, 5 SDA, 6 INT, 7 ADDR; green LED D2 + 10k R9 on 3.3V | Read (XML nets) |
| EE-S04 | Adafruit learn guide, pinouts page, https://learn.adafruit.com/adafruit-mpr121-12-key-capacitive-touch-sensor-breakout-tutorial/pinouts | "give it the same power as the logic level of your microcontroller"; on-board ultra-low-dropout 3.3 V regulator; 3Vo up to 100 mA | Read |
| EE-S05 | Adafruit_MPR121 library, https://github.com/adafruit/Adafruit_MPR121 `Adafruit_MPR121.cpp` | CONFIG1 0x10 (16 µA, FFI 6), CONFIG2 0x20 (0.5 µs, ESI 1 ms); autoconfig AUTOCONFIG0 0x0B, USL 200, TL 180, LSL 130; AUTOCONFIG1 not written | Read |
| EE-S06 | Diodes Inc. AP2112 data sheet, https://www.diodes.com/assets/Datasheets/AP2112.pdf | AP2112-3.3: dropout 5 typ / 8 max mV at 10 mA, 125/200 mV at 300 mA; IQ 55/80 µA; VOUT ±1.5 % | Read |
| EE-S07 | Microchip MIC5225 data sheet DS20006683A (third-party copy, encrypted PDF) | dropout 50 mV typ at 100 µA; 230/300 mV at 50 mA; 310/450 mV at 150 mA | Search, not verified |
| EE-S08 | Raspberry Pi Pico pinout, https://pico.pinout.xyz/ and https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html | pin 29 GP22; 31 GP26 = I2C1 SDA / ADC0; 32 GP27 = I2C1 SCL / ADC1; 33 AGND; 34 GP28 = ADC2; 35 ADC_VREF; 36 3V3 out, "recommended to keep the load less than 300mA"; VSYS 2–5 V | Read (Pico datasheet PDF too large for the fetch tool; official wording not opened) |
| EE-S09 | onsemi BSS138 / BSS138K / BSS138L data | VGS(th) 0.8/1.3/1.5 V; BSS138K Coss 9.75 pF typ; BSS138L Coss 25 pF max (VDS 25 V) | Search, not verified |
| EE-S10 | TI TPD4E05U06 product page, https://www.ti.com/product/TPD4E05U06 | 4 ch, VRWM 5.5 V, 0.5 pF typ, 10 nA max leakage, IEC ±12 kV contact; USON/DFN 2.5×1 mm | Read |
| EE-S11 | Vishay 1N4148 data sheet, https://www.vishay.com/docs/81857/1n4148.pdf | IR 25 nA at VR 20 V; CD 4 pF at 0 V; VF 1 V at 10 mA | Read |
| EE-S12 | Phoenix Contact 1715721 MKDS 1,5/2-5,08 | pin 0.9 × 0.9 mm, hole 1.3 mm, pitch 5.08 mm | Search |
| EE-S13 | Alps RK09K1130A5R product page, https://tech.alpsalpine.com/e/products/detail/RK09K1130A5R/ | 10 kΩ ±20 %, 0.05 W | Read |
| EE-S14 | Yageo MFR leaded resistor data (MFR-12) | body 3.4 ± 0.3 × Ø1.9 ± 0.2 mm, lead Ø0.45–0.5 mm, 1/6 W, 200 V working / 400 V overload | Search |
| EE-S15 | IPC-2221B (generic standard for PCB design) | external-conductor current formula I = 0.048·ΔT^0.44·A^0.725; Table 6-1 B2 0–15 V: 0.1 mm | Standard, from memory: not opened in this session |
| EE-S16 | IEC 61000-4-2 | 150 pF / 330 Ω; contact levels 2/4/6/8 kV; first peak 3.75 A/kV | Standard, from memory: not opened in this session |
| EE-S14b | Yageo leaded resistors data sheet (MFR series table), https://pccomponents.com/datasheets/YAGEO-LEADED_RESISTORS.PDF | MFR-12: 1/6 W, L 3.4 ± 0.3, Ø1.9 ± 0.2, lead Ø0.5 ± 0.05 mm; max working 200 V, max overload 400 V, dielectric withstanding 300 V; short-time overload 2.5×RCWV 5 s; pulse overload 4×RCWV 10000 cycles (1 s on / 25 s off); no µs pulse / ESD rating | Read (T-053) |
| EE-S17 | Vishay Beyschlag MBA/SMA 0204, MBB/SMA 0207, MBE/SMA 0414 Professional, doc 28766 rev 11-Jul-2018, https://www.vishay.com/docs/28766/mbxsma.pdf | Umax AC/DC 200/350/500 V; Uins (1 min) 300/500/800 V; range 10 Ω–2.43 MΩ; 1.2/50 µs pulse rating per IEC 60115-1 4.27 (5 pulses, ΔR ≤ 0.5 % + 0.05 Ω) and single-pulse load given ONLY as charts (image), value at 3.3 kΩ not readable | Read (text); chart values not read |
| EE-S18 | Ohmite OX/OY ceramic composition data sheet | OX: 1 W, 3.3 Ω–100 kΩ, 50 J single impulse, 300 V working | Search, not verified (storage.sea.com.ua copy refused connection) |
| EE-S19 | Vishay VR25/VR37/VR68 product overview, https://www.vishay.com/docs/48446/_vr25_vr37_vr68_ppt_product-overview.pdf | range 100 kΩ–68 MΩ (does not include 2.7–3.3 kΩ); pulse 7 kV (VR25) / 10 kV (VR37), 1 nF discharge per IEC 60065 14.2 | Search |
| EE-S20 | Search extract of a Vishay listing: "MBA/SMA 0204: 2 kV, MBB/SMA 0207: 4 kV, MBE/SMA 0414: 6 kV" | not confirmed as the 1.2/50 µs value at 3.3 kΩ | Search, not verified |
| EE-S21 | Raspberry Pi Pico order code, Pimoroni wholesale https://wholesale.pimoroni.com/products/raspberry-pi-pico and DigiKey https://www.digikey.co.uk/en/products/detail/raspberry-pi/SC0915/13684020 | SC0915 = Raspberry Pi Pico (RP2040), no headers fitted | Search (distributor listings) |
| EE-S22 | Phoenix Contact 1729128 distributor listings (Farnell 3041440, RS 1930586, Octopart) | 1729128 is the MKDSN 1,5/2-5,08 (13.5 A, 250 V), not MKDS 1,5; MKDS 1,5/ 2-5,08 is 1715721 (EE-S12) | Search |
| EE-S23 | Omron B3F catalogue (mirrors: manualsdir, elcodis) | B3F-1000: 6×6 mm, 4.3 mm plunger height; PCB drawing 6.5 × 4.5 mm, four Ø1.0 holes (variant coverage not confirmed) | Search |
| EE-S17b | Same document as EE-S17, saved locally as `sim/systems/datasheets/vishay_mbxsma_28766.pdf` (git-ignored), sha256 201a7ea8e35843345975a100b4b98802df0b3a56cf57805e881ecd93b9973cff, URL https://www.vishay.com/docs/28766/mbxsma.pdf | Page 10 "1.2/50 Pulse" chart read from the PDF vector paths (axis grid 10 Ω = 156.04 pt, 49.09 pt/decade; 100 V = 603.42 pt, 40.07 pt/decade; legend 2 pt = 0414, 1 pt = 0207, 0.5 pt = 0204): Umax at 3.3 kΩ 0414 4.08 kV, 0207 1.74 kV, 0204 1.47 kV; ESD HBM (IEC 61340-3-1) 0204 2 kV, 0207 4 kV, 0414 6 kV; dimensions 0414 Ø4.2 × 11.9 mm, lead 0.8 mm, min pitch 15.0 mm | Read (T-060; supersedes "chart values not read" in EE-S17 and the unconfirmed EE-S20) |
| EE-S24 | Vishay BCcomponents LSR37 High Voltage Surge Resistor, doc. 28735 rev 21-Feb-08, mirror https://pdf2.datasheet.su/bc%20components%20vishay/lsr3700001001kr500.pdf, saved as `sim/systems/datasheets/lsr37_bc.pdf`, sha256 cd74dacdd3304934151d475ee1f2bb51ad5961b90744728402d545be4bd8f8ad | 1 k–10 kΩ E12, ±10 %/±20 %, 0.5 W; ESD contact discharge 12 kV, 100 pulses, ΔR ≤ ±20 % (typ. ±10 %); 10 kV 1 nF test for R > 3.3 k; Ø4.0, L1 9.0, L2 10.0, lead 0.7 mm; min pitch 15 mm (machine forming) | Read (T-060; third-party mirror of the Vishay PDF) |
| EE-S25 | IEC 60664-1 Table F.2 (clearance vs rated impulse voltage, up to 2000 m) | case A / B: 2.5 kV 1.5/0.6 mm, 4 kV 3.0/1.2 mm, 6 kV 5.5/2.0 mm, 8 kV 8.0/3.0 mm | Standard, from memory: not opened (T-060, to be checked) |
| EE-S26 | Distributor listings for sibling values MBE04140C3300FC100 (RS 607-662: £0.26 at 1–24) and MBE04140C3303FC100 (LCSC C1364355: $0.30 at 1+) | 3k3 price assumed equal: ≈0.30–0.66 € each at qty 12 | Search (T-060) |
| EE-S27 | Same document as EE-S17b (Vishay doc. 28766 rev 11-Jul-2018), page 7 "Description" and page 13 "Dimensions" table, text extracted from the PDF content streams (T-073) | MBE/SMA 0414 Dmax 4.2, Lmax 11.9, d 0.8, lmin 31.0, Mmin 15.0 mm, 700 mg; no cap length and no Lmin given; "Plated steel termination caps", resistor elements "covered by a light blue protective coating" | Read (T-073) |
| EE-S28 | Raspberry Pi RP2040 datasheet, ESD table (page 616), local extract `sim/systems/datasheets/rp2040-datasheet-gpio-dc.txt` | HBM 4 kV (JEDEC JS-001-2012), "Digital (FT) pins only"; CDM 500 V (JESD22-C101E); no separate HBM value found for the ADC-capable GPIO26–29 | Read (T-073, local extract) |
| EE-S29 | KEMET "Multilayer Ceramic Capacitors / Axial & Radial" catalogue (Golden Max conformally coated radial, older CA-suffix edition), mirror https://sy-dep-epc-lpc.web.cern.ch/components/datasheets/epc-lpc%20(converters)/C320%20CERAMIC%20CAPACITOR%20(KEMET).pdf, sha256 935cb3bf0b1fb26f904310cd0a6922dba2a582930437383a4b88c8b72e8fb8ba; text extracted from the PDF content streams, excerpt `reports/electronics/evidence/T-076/kemet_golden_max_extract.txt` (T-076) | Dimensions table: C320 L .200 (5.08) / H .260 (6.60) / T .125 (3.18) max, **LS .100 (2.54)**, lead .020 (0.51); **C322 same body, LS .200 (5.08 mm)**, lead 0.51 mm; note "Case Sizes C320/C322/C323 are identical electrically". 50 V X7R C32x range includes .1 µF = C32(2)C104(K)5R5 (X7R table). Code: K = ±10 %, 5 = 50 V, R = X7R (±15 % over −55…+125 °C). So the manager's example C320C104K5R5TA has 2.54 mm leads; the 5.08 mm part is **C322C104K5R5TA**. The current "TA" suffix (vs "CA" in this edition) is ASSUMED to be the lead-free version of the same part (distributor listings use TA) | Read (old edition; check current KEMET page before ordering) |
| EE-S30 | Distributor listings for C322C104K5R5TA (search extract, T-076): Cytech USD 0.372 at 1+, LCSC USD 0.382, RS UK GBP 0.212 at 50+, myMectronic USD 0.87–0.90 | ≈0.20–0.90 € per piece at quantity 1 | Search, not verified |

## SMD board sources (T-090, added to this list in T-092)

"Read" means the document was opened locally and the value found in it. PDFs and full sha256 values: `reports/electronics/evidence/T-090/datasheets/`; pages read through `evidence/T-090/chartread.py` and `pdfpages.swift`.

| ID | Source | Values used | How |
|---|---|---|---|
| T90-S1 | Raspberry Pi Pico datasheet RP-008307-DS-2, sha256 757ff485...aa89eb, `sim/systems/datasheets/pico-datasheet.pdf` | Figures 3, 5, 6: castellation land 16.18 / 22.58 mm, 1.6 mm pad, 2.54 mm pitch; TP positions; USB shell pads; module end to pin 1 column 1.37 mm | Read (pages 7, 10, 11 rendered) |
| T90-S2 | TT Electronics HPWC Series 09.23, sha256 1088aba0...eb1a, `evidence/T-090/datasheets/tt_hpwc_0923.pdf` | 2512: L 6.5 ±0.3, A 0.6 ±0.3, W 3.2 ±0.2, B min 4.4 mm; ±5 %; 1.2/50 µs chart: 4352-4472 V at 2850 Ω, 4472 V at 3000 Ω, 4596 V at 3150 Ω (raster chart, ±5 % reading ASSUMPTION, `evidence/T-090/charts/chartread_raw.txt`) | Read |
| T90-S3 | Vishay CMA 0204, CMB 0207, doc. 28956 rev. 29-Mar-2023, sha256 3bd3f934...8c61 | Dimensions, ESD, chart (rejected option) | Read |
| T90-S4 | Vishay MMU 0102, MMA 0204, MMB 0207, doc. 28963 rev. 02-Jun-2026, sha256 07bf424d...7969 | Chart, dimensions (rejected option) | Read |
| T90-S5 | Vishay MMA 0204 HV, MMB 0207 HV, doc. 28880, sha256 0f8dca2b...6519 | Range 340 kΩ-10 MΩ (excluded) | Read |
| T90-S6 | Vishay Recommended Solder Pad Dimensions, doc. 28950 rev. 12-Jul-2022, sha256 9e2b145c...144e | 1206 land G 1.75, Y 1.15, X 1.80 mm; 0207 lands | Read |
| T90-S7 | Vishay CMA/CMB product overview, doc. 48636, sha256 b6cc6a9f...c4 | Cross-check only | Read |
| T90-S8 | NXP MPR121 datasheet Rev 4, sha256 a02ff161...55c | QFN-20 pitch 0.40, terminal 0.20 mm (bare chip rejected) | Read (same document as EE-S01) |
| T90-S9 | Omron B3S catalogue, sha256 c6391ce5...289b | SW1 land 9.5 / 6.4 / 4.5 / 1.3 mm, height, force | Read |
| T90-S10 | Adafruit Eagle `Adafruit MPR121 Breakout.brd` | Board 33.02 × 19.05 mm, drills, no bottom-side parts, bottom copper and vias | Read through WebFetch (truncated, then read with offset). STEMMA QT board bottom side NOT opened |
| T90-S11 | Adafruit product page 1982 | Header included, 2021 revision | Read through WebFetch |

### Not opened (stated as ASSUMPTION wherever used)

| Item | Used for | Status |
|---|---|---|
| KEMET C1206C104K5RACTU (C1, 1206 X7R) | Tolerance ±10 %, X7R ±15 % in calc_pot_rc | **Datasheet NOT opened** (certificate error on the KEMET site, T-090); EIA class figures |
| Generic 1206 thick-film resistors R13-R16 | 1206 land only | **No datasheet opened**; land from T90-S6 |
| HPWC2512-3K0JT18 orderable MPN | BOM | Built from the T90-S2 pattern; **stock and price NOT confirmed** |
| FR-4 copper peel strength 0.8-1.05 N/mm | T-090 pry margins | **IPC-4101 NOT opened**, recalled; home-etched and heated copper may be lower |
| FR-4 modulus 22 GPa, Poisson 0.15 | calc_usb_pry | **No laminate datasheet opened**, typical values |
| ISO 7045 M3 pan head 5.6 mm, ISO 7089 M3 washer 7.0 mm, ISO 273 fine clearance 3.2 mm | Screw-head and washer clearance | **Standards NOT opened**, recalled |
| IEC 61000-4-2 (EE-S16), IEC 60664-1 F.2 (EE-S25), IPC-2221B (EE-S15) | ESD source, flashover rule, track rise | **Standards NOT opened**, recalled (as before) |
| Off-board potentiometer (ADR-023 D-2) | R-011, pot RC | No part chosen; Alps EE-S13 values carried over as ASSUMPTION |
