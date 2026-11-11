# T-095: one-board quote, LCSC against Mouser Portugal

Date of all prices: 2026-11-09 (SOURCE, `distributor_pages.txt`). EUR amounts for LCSC and every total: CALCULATION (`compute_quote.out`), 1 EUR = 1.1193 USD (SOURCE, ECB reference rate, 9 November 2026). Ex shipping and tax. Amounts count minimums and multiples.

| Line | Needed | LCSC part | LCSC qty paid, price | LCSC EUR | Mouser part | Mouser qty, price | Mouser EUR |
|---|---|---|---|---|---|---|---|
| A1 Pico SC0915 | 1 | **Cannot supply** ("No results") | - | - | 358-SC0915 | 1 at 3.44 EUR | 3.44 |
| A2 Adafruit 1982 | 1 | **Cannot supply today**: C17523394 stock 0 | - | - | 485-1982 | 1 at 6.84 EUR | 6.84 |
| R1-R12 | 12 | C2082816 CRGP2512F3K3: fits the land, pulse **unproven** | 12 at 0.3359 USD | 3.60 | HPWC2512-3K3JT1: pulse proven, +5 % corner 0.885 vs 0.90 | 12 at 1.25 EUR | 15.00 |
| R13-R14 4k7 | 2 | C2907387 | 100 at 0.0040 USD | 0.36 | 603-RC1206FR-074K7L | 2 at 0.086 EUR | 0.17 |
| R15-R16 220R | 2 | C2933642 | 100 at 0.0046 USD | 0.41 | 603-RC1206FR-07220RL | 2 at 0.086 EUR | 0.17 |
| C1 100 nF | 1 | C24497 | 20 at 0.0143 USD | 0.26 | 187-CL31B104KBCNNNC | 1 at 0.12 EUR | 0.12 |
| SW1 B3S-1000 | 1 | C2733655 | 5 at 0.365 USD | 1.63 | 653-B3S-1000 | 1 at 0.697 EUR | 0.70 |
| RV1 10k linear, insulated shaft | 1 | C361173 RK09D1130C2P | 1 at 0.7417 USD | 0.66 | 652-PTV09A-4015F-B103 | 1 at 0.765 EUR | 0.77 |
| Knob | 1 | **None in stock** | - | - | 179-SPK-016A, 11 mm, ABS | 1 at 0.327 EUR | 0.33 |
| Header strip | 0 | Not needed, supplied with module | - | - | Not needed | - | - |
| **Total** | | **Incomplete** | | **6.92** | **Complete** | | **27.53** |
| Shipping to Portugal | | NOT CONFIRMED | | | NOT CONFIRMED | | |

Separate lines, not in the totals above:

| Alternative | LCSC | Mouser |
|---|---|---|
| R1-R12 as CMB02070X3301GB200 (MELF, pulse proven, gap 3.2 mm fails 3.5 mm, new land) | C2079554, stock 33, 12 at 0.9719 USD = 10.42 EUR; LCSC total 13.74 EUR | 12 at 0.422 EUR = 5.06 EUR; Mouser total 17.60 EUR |
| A1 as Pico 2, RP2350, **not confirmed as drop-in** | C41407547, stock 356, 8.38 EUR; LCSC total 15.30 EUR, still no A2 and no knob | - |
| A2 if LCSC had stock | Listed at 19.37 EUR; with CRGP and Pico 2 = 34.67 EUR, no knob, hypothetical | - |

**All-LCSC cannot be completed today**: A1 is not listed, A2 has zero stock, no knob is in stock, and no LCSC resistor passes all R1-R12 criteria.

## R1-R12 at LCSC

Criteria unchanged from T-094: pulse about 3.6 kV for 1.2/50 µs or a stated equivalent; conductor gap at least 3.5 mm; resistance window.

| Part | Stock, cost of 12 | Highest sourced voltage figure | Pulse | Gap | Result |
|---|---|---|---|---|---|
| C2079554 CMB02070X3301GB200, 3k3 ±2 % | 33, 11.66 USD | 5175 V, 1.2/50 µs chart at 3k3, about ±5 % reading (Vishay doc. 28956, T-090); margin 1.42 CALCULATION | PASS | 3.2 mm SOURCE | **FAIL, gap**; only pulse-proven part at LCSC; 3366 Ω worst 0.901 PASS (SIMULATION); MELF, new land |
| C2082816 CRGP2512F3K3, 3k3 ±1 % | 130, 4.03 USD | 1000 V overload (SOURCE); about 2000 W rectangular impulses gives 2.57 kV CALCULATION, not a rating | **Not proven** | 4.55 mm CALCULATION | FAIL, no 1.2/50 evidence |
| C2082813 CRGP2512F2K7 | 5, not enough | as above | Not proven | as above | FAIL |
| C4327785 MMB02070C3301FB200 | 100 | 1.74 kV chart at 3k3 (T-090) | FAIL, margin 0.48 | 3.2 mm | FAIL |
| C2532497 RPC2512JT3K30, 500 V | 0 | 500 V working (LCSC attribute) | no datasheet read, no stock | not read | Not available |
| ERJ-UP8 1206, 1 kV (four 3k-window parts listed) | 0 | 1 kV attribute | no stock, 1206 too short for the gap | below 3.5 mm | FAIL |

In plain terms: LCSC lists 16,351 chip resistors from 2.7 to 3.3 kΩ. Its highest voltage attribute in that range is 1 kV, and only 9 parts are at 600 V or above, all with zero stock. The kV-class chip families (HVC, CHV, CRHV, RCV, HV73) are listed there only at 100 kΩ and above: voltage ratings in the kV range come with high resistance, because the part must not dissipate V²/R. A plain 3k3 2512 has a datasheet working voltage of 200-500 V and no 1.2/50 µs figure. The only one with that evidence in stock is the CMB MELF, and it misses the gap rule.

Limit: LCSC's voltage attribute is a working voltage and is blank on some rows. Ta-I, Viking, Ralec and Walsin were not searched by brand; none appears among manufacturers at 400 V and above.

Not confirmed: SPK-016A bore style against the flatted shaft (datasheet not opened).
