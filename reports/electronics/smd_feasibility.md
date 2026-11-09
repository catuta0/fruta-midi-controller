# SMD conversion feasibility and part selection (T-090, CR-003)

Author: electronics-engineer. Date: 2026-11-09. Scope: feasibility and part selection only. `hardware/` and the generators were not changed and no layout was run. Input revision: `8e5f595-dirty` (the dirty files are `.claude/` and `CLAUDE.md`, none used here).

Status: **PARTIAL.** Every point was analysed against datasheets, but nothing here is measured on hardware, and the routing conclusion is an estimate until a layout exists.

Numbers carry one label: SOURCE (datasheet opened, section 9), CALCULATION (`sim/electronics/calc/calc_smd_feasibility.py`, output `.out`), ASSUMPTION, MEASUREMENT.

## 1. Result in one page

| Item | Recommendation | Status |
| --- | --- | --- |
| R1-R12 | **TT Electronics HPWC2512, 3k0 ±5 %, one part per electrode.** Fall-back for more ESD margin: two 1k6 in series | PASS at 4 kV (analysis); FAIL at 8 kV, as in V1.2 |
| A1 Pico | Surface-solder with the datasheet land, pads lengthened outward 1.0 mm; keep bare copper out of the rectangle in section 3 | Feasible, hand-solder not tested |
| A2 module | Header pins butted on pads, plastic strip as 2.5 mm stand-off | Feasible, weaker than a socket |
| Bare MPR121 | Rejected | FAIL: 0.40 mm pitch |
| J2 | 14 solder-wire pads, hot-melt strain relief, spark gap kept | Peel risk, mitigated |
| RV1 | Off-board pot on 3 wire pads; alternative keep 5 THT holes | User decision |
| SW1 | Omron B3S-1000 | Feasible |
| R13-R16 | 1206 thick film | Feasible |
| C1 | 1206 100 nF X7R 50 V | Feasible, datasheet not opened |
| Holes | 133 to **4** (M3 mounting only) | CALCULATION |
| Single layer, no new wire bridges | Plausible | Estimate, NOT RUN |

SMD does match the 4 kV rule, and the part-level numbers are better than V1.2 at 4 kV. What is lost is the 13 mm copper gap: 8 kV copper margin goes away, although V1.2 already failed 8 kV at the resistor body and end caps.

## 2. R1-R12

### Requirement

Across each resistor at 4 kV: 3636 V for 3k3, 3604 V for 3k0 (CALCULATION). Flashover rule ≥ 3.5 mm at 4 kV, derived in `calc_flashover.py` from the worst of two models, both ASSUMPTION (M4 eta = 0.3; IEC 60664-1 F.2 case A, recalled).

Note on the V1.2 baseline. The 13.04 mm is copper only. The real conductor gap in V1.2 is end cap to end cap of the DIN0414 body: 3.61 mm worst with ±0.25 mm placement, 3.13 mm at ±0.5 mm, with an assumed cap length (`check_gap.out` section (d), accepted as PARTIAL in ADR-020). V1.2 was never a 13 mm conductor gap.

### Comparison

The conductor gap below is the part's own smallest metal-to-metal distance (SOURCE). No land pattern can make it larger: copper can be pulled apart, but the terminations stay where they are.

Rating is read from each datasheet's 1.2/50 µs chart at the resistor value (SOURCE, chart reading; ±5 % reading uncertainty, ASSUMPTION; raw values `reports/electronics/evidence/T-090/charts/chartread_raw.txt`). Margin = rating / voltage across the part; gap margin = gap / required gap, both CALCULATION. A value of 1.00 or more meets the criterion.

| Rank | Option | Land copper gap (mm) | Conductor gap per part (mm) | Rating per part (V) | Rating margin 4 kV | Gap margin 4 kV | Rating margin 8 kV | Gap margin 8 kV | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | V1.2 MBE0414 3k3 1 % | 13.04 | 3.61 (worst, cap length ASSUMPTION) | 4083 | 1.12 | 1.08 | 0.56 | 0.48 | V1.2 |
| 1 | **HPWC2512 3k0 5 %** | 5.0 | 4.4 | 4472 | **1.24** | **1.34** | 0.62 | 0.60 | **PASS 4 kV**, FAIL 8 kV |
| 2 | 2 × HPWC2512 1k6 5 % | 5.0 × 2 | 4.4 × 2 | 3547 | 1.96 | 3.10 | 0.98 | 1.33 | PASS 4 kV, 8 kV rating FAIL within reading error |
| 3 | 2 × CMB 0207 1k65 1 % | 3.6 × 2 | 3.2 × 2 | 3689 | 2.03 | 2.25 | 1.01 | 0.96 | PASS 4 kV, 8 kV marginal, MELF rolls |
| 4 | CMB 0207 3k3 1 % | 3.6 | 3.2 | 5175 | 1.42 | 0.96 | 0.71 | 0.43 | Rating PASS, conductor gap 0.13 mm short at 4 kV |
| 5 | HPWC2010 3k3 5 % | 3.3 (ASSUMPTION) | 3.0 | 3797 | 1.04 | 0.90 | 0.52 | 0.40 | Gap FAIL |
| 6 | 3 × MMB 0207 1k1 1 % | 3.2 × 3 | 3.2 × 3 | 1008 | 0.83 | 3.80 | 0.42 | 1.57 | Rating FAIL |
| 7 | 3 × HPWC1206 1k1 5 % | 1.75 × 3 | 1.7 × 3 | 1025 | 0.85 | 2.02 | 0.42 | 0.83 | Rating FAIL |
| 8 | MMB 0207 3k3 1 % | 3.6 | 3.2 | 1736 | 0.48 | 0.96 | 0.24 | 0.43 | FAIL |
| 9 | HPWC1206 3k3 5 % | 1.75 | 1.7 | 1722 | 0.47 | 0.51 | 0.24 | 0.23 | FAIL |

MMB 0207 is the part CR-003 suggested and it does not work: its 1.2/50 µs value at 3k3 is 1.74 kV, so the part fails at 4 kV even before flashover is considered. The carbon-film CMB 0207 is the pulse-rated MELF in the same size. The high-voltage MMB 0207 HV is unusable here, since its range starts at 340 kΩ (SOURCE).

The CMB 0207 single part has the best rating of any single option, and the datasheet states up to 15 kV IEC 61000-4-2 contact and 16 kV HBM. The IEC figure has a note saying a special test setup is needed to avoid flashovers on small parts, which is the flashover issue here. The same datasheet's test table gives 16 kV HBM across the CMB 0207 range (3 pos + 3 neg, ΔR ≤ 0.5 % R + 0.05 Ω).

### Why HPWC2512 first

1. It meets both criteria with one part per channel and a SOURCE gap, not an assumed one.
2. It is flat, so it stays where placed and solders by hand far more easily than a MELF.
3. 4.4 mm is the part's own minimum (B min), with no lead-forming or placement error in it, unlike V1.2 at 3.13-3.61 mm.
4. It frees roughly 9 mm of lane length: Z 8.8 mm against the V1.2 15.24 mm pitch plus pads.

### Resistance value

The tightest HPWC tolerance is ±5 % (SOURCE). 3k3 ±5 % reaches 3465 Ω, sensitivity about 0.902 by interpolation (CALCULATION) and about 0.899 on the worst-choice column, against the 0.90 limit in ADR-019. So **3k0 ±5 %** (2850-3150 Ω, inside the 2.7-3.3 kΩ design rule). The cost is ESD peak current: 1.20 A at 3k0 versus 1.10 A at 3k3 (CALCULATION), against a 1.33 A inferred pin limit (ASSUMPTION, analysis.md). Worst at 2850 Ω: 1.26 A, margin 1.06 (CALCULATION), against 1.2 at the V1.2 value. Part number by the datasheet pattern would be `HPWC2512-3K0JT18`; stock and price are **not confirmed**.

### Does series really solve flashover?

Yes under static sharing, with one caveat.

- With two equal resistors each gap sees half the voltage, and the intermediate pad is held at the midpoint by the divider. Breakdown then needs half the voltage to exceed one gap, so V_bd total ≈ 2 × V_bd(d). There is no cascade while both gaps are below threshold. CALCULATION.
- Below a few ns the capacitive divider takes over. With mid-node stray capacitance about 0.5 pF (ASSUMPTION) and 1.6 kΩ, the time constant is 0.8 ns, comparable to the IEC 0.8 ns rise (recalled, EE-S16, not opened). In that interval the first part can see most of the voltage. Air breakdown also has a formative lag, so the effect is unquantified. Physical test only.

### Land pattern

- 2512 hand-solder: pad 1.9 × 3.35 mm, copper gap G = 5.0 mm, overall Z = 8.8 mm (CALCULATION). The KiCad IPC land has G = 4.7 mm (SOURCE, library). G must stay at least 4.4 mm (body gap). Pads at G = 5.0 keep every termination on its pad at all tolerances (CALCULATION).
- Lane pitch 5.08 mm: pad-to-pad gap across lanes 1.73 mm, rule (b) diagonal Ex to ELEy 5.29 mm (CALCULATION).
- Keep every other net out from under R1-R12. A track under the body bridges the rule.
- Keep the Ex to GND edge spark gap at 1.40 mm (ADR-020 / F2-006).

Two pads in a series option: total Z = 16.8 mm.

### What is lost at 4 kV

| Quantity | V1.2 | SMD (option 1) |
| --- | --- | --- |
| Copper gap | 13.04 mm | 5.0 mm (lost) |
| Conductor gap (real) | 3.61 mm worst, assumed cap | 4.4 mm SOURCE (gain) |
| Rating margin | 1.12 | 1.24 (gain) |
| Peak current | 1.10 A | 1.20 A (loss) |
| Tolerance | 1 % | 5 % (loss, no sensitivity effect at 3k0) |

At 8 kV: V1.2 copper met the 7.5 mm rule but caps did not; SMD meets neither. Both fail the 8 kV rating. R-006 stays open in either case.

## 3. Pico SC0915

Sourced from the datasheet RP-008307-DS-2, section 2, Figures 3, 5, 6 (rendered and read in this task).

| Item | Value | Label |
| --- | --- | --- |
| Module | 51 × 21 × 1 mm | SOURCE |
| Pad pitch, row spacing | 2.54 mm, 17.78 mm | SOURCE |
| Land size | 1.6 mm wide (R0.8), 3.2 mm long ((22.58 - 16.18)/2) | SOURCE, CALCULATION |
| Inner / outer pad width across | 16.18 / 22.58 mm | SOURCE |
| Overhang beyond module edge | 0.79 mm | SOURCE |
| Three end debug pads across | 6.68 mm | SOURCE |
| Test points TP1-6 | 1.5 × 1.5 mm, 0.3 mm radius | SOURCE |
| TP centres (origin bottom left) | (8,43) (8,40.5) (8,38) (9.5,49.8) (11.5,49.8) (10.5,46.5) | SOURCE |
| TP names mapped to the centres | KiCad RaspberryPi_Pico_SMD footprint | SOURCE (library) |
| USB shell pads | A (7.775,49.5), B (13.225,49.5) 1.1 × 1.8; C (8.075,46.47), D (12.925,46.47) 1.05 × 1.45 | SOURCE |
| USB overhang beyond module end | 1.3 mm typ | SOURCE |

The figure labels the second pad-geometry block "B, C"; it must mean C and D (ASSUMPTION, geometry matches).

The datasheet recommends this footprint "for reflow"; hand soldering is not addressed. Its statement that unused test points may have the copper voided applies directly.

### Recommended land

Per pad 1.6 × 4.2 mm, inner edge at the datasheet 16.18 mm width, outer edge 1.79 mm beyond the module. Pad gap at 2.54 mm pitch: **0.94 mm, PASS** against 0.6 mm (CALCULATION). Outer edge to board edge at the V1.2 position: 1.10 mm. Etch all 40 pads as mechanical anchors although only 7 carry signals (pins 3, 29, 31, 32, 33, 34, 36, from `gen_schematic.py`).

### Bare-copper keep-out

Exposed underside features would short to bare carrier tracks. In V1.2 board coordinates, the union keep-out with 0.6 mm clearance is **x 9.52-17.27, y 0.48-14.98 mm** (7.75 × 14.50 mm, CALCULATION). TP6 is BOOTSEL: a short means a Pico that always boots to mass storage, so this is not cosmetic.

Do not etch pads A-D: iron soldering can't reach them, and the datasheet warns that existing solder pools there can stop the module sitting flat. Voiding gives a little relief.

### Tracks under the Pico

Allowed outside the keep-out, on the protection of the Pico's own solder mask. Interior width 16.18 mm minus clearances fits up to 9 tracks of 1.0 mm (CALCULATION); channels beside the keep-out are 3.61 mm each, two tracks. No track can pass between adjacent castellated pads: 0.94 mm available, 2.2 mm needed (CALCULATION). Optional insulation: a strip of polyimide tape on the carrier, not required by the rules.

### USB and strength

The USB shell front ends 0.67 mm beyond the board edge at the V1.2 position, so the plug cannot foul the carrier (CALCULATION).

Pry on the plug end, rigid-module model: at 10 N, 0.75 N on the first pad versus 1.28-1.68 N peel capacity (margin 1.7-2.2); at 30 N, margin 0.6-0.75 (CALCULATION; peel 0.8-1.05 N/mm is ASSUMPTION, not opened, home-etched and heated copper may be lower). So an awkward pull on a cable can start peeling. Recommend an epoxy bead at the USB-end pads after solder and a strain-relieved cable. Two M2 holes through the Pico's own 2.1 mm mounting holes are possible but add drilling. Sockets are lost: a failed Pico needs castellation desoldering (CR-003).

## 4. Adafruit 1982 module

Facts: original board 33.02 × 19.05 mm, 1.0 mm drills on 2.54 mm pitch, 1.68 mm pads, no bottom-side components, but bottom copper traces, a GND pour and vias (SOURCE, S-003 Eagle file, read in this task). The STEMMA QT board was **not** opened for its bottom side (ASSUMPTION same). The header ships with the module (SOURCE, Adafruit page; loose or soldered not stated).

| Option | Result |
| --- | --- |
| Straight pins butted, strip as stand-off | **Recommended.** About 2.5 mm clearance (ASSUMPTION), tracks under the module are safe, reworkable row by row |
| Bent pins (gull-wing feet) | Stronger per joint, but 20 hand-formed pins to ±0.2 mm coplanarity is unreliable |
| SMD 2.54 mm vertical headers | Good strength, alternating feet; adds a footprint, no datasheet opened |
| Flat on the board, solder through plated holes | Simplest, no rework, and the underside traces and vias sit against bare carrier copper |

Pry at 5 N on the module end: about 0.59 N per joint against 1.44-1.89 N peel (margin 2.5-3.2, CALCULATION on ASSUMPTION inputs). The module carries no connector force. Butt joint gross area 8.2 mm² over 20 pins, plus side fillet (CALCULATION). Keep pad size 1.8 × 2.4 mm.

Both revisions stay on one footprint, since their pin rows do not change (REQ-025).

- **JP1**: SMD 3-pad solder bridge, 3.81 mm pitch kept (gap 1.87 mm, ADR-021). No component.
- **J1 wires**: S3-S6 interleave SDA and SCL, so one selector cannot be planar. Keep two short insulated wire links, soldered flat to surface pads (allowed by REQ-027). A 0 Ω 1206 cannot span a track (gap 1.75 mm against 2.2 mm needed); 0 Ω 2512 could, but needs 4 footprints for no gain.
- Q-row wire holes become surface pads.

**Bare MPR121**: 3 × 3 mm QFN, pitch 0.40 mm, terminal width 0.20 mm (SOURCE, NXP datasheet Rev 4, case 2059, 98ASA00021D). Terminal gap 0.20 mm is one third of the 0.6 mm clearance, and the pitch itself is below that clearance. FAIL against REQ-029. It also needs its own regulator, level-shift and passives (SOURCE, S-003 schematics). DigiKey lists it discontinued (search result, not verified).

## 5. J2, RV1, SW1, holes

| Item | Proposal | Peel risk |
| --- | --- | --- |
| J2 | Solder-wire pads 3.0 × 4.5 mm or larger, 5.08 mm pitch, spark gap 1.40 mm retained, hot-melt bead per wire. Electrode wires become soldered, not screw-swapped | Moderate: wire tug loads the pad. Hot-melt mandatory |
| J2 alternative | WAGO 2060-452/998-404 push-button SMD terminals (4.0 mm pitch), datasheet not opened | Low force on wire insertion; needs a 4 mm pitch fan-out |
| J2 rejected | Surface-mounted screw terminals | Screw torque peels two small pads |
| RV1 | Off-board 10 k pot (RK09K or panel) on 3 wire pads, C1 at the pads | Low on the board; pot needs its own fixing. **Tab and shaft ESD path changes (R-011)**: the AGND frame link must be re-derived |
| RV1 alternative | Keep the THT pot: 5 holes (3 pins + 2 tabs), force carried by drilled pins | None new |
| RV1 rejected | SMD trimmer | Screwdriver, not a musician's control |
| SW1 | Omron B3S-1000: gull-wing, 4 pads 1.55 × 1.3 mm, pads 6.4 mm apart inside, rows 4.5 mm, height 4.3 mm, 1.57 N max operate (SOURCE). Hand-solderable. Finger load is compression, so peel risk is low; lateral force is small | Low |

No enclosure is defined in the project documents searched, so an off-board pot needs somewhere to live. That is the user's call.

**Holes:** 133 (MEASUREMENT, CR-003) to **4** M3 mounting holes (CALCULATION, 97 % fewer), or 9 if the THT pot stays, or 0 with adhesive feet. Every hole left is justified by mounting force. The mounting metal check (floating-metal bypass, ADR-020) must be redone against the new R positions.

## 6. R13-R16 and C1

- **R13-R16**: 1206. Land G 1.75, Y 1.15, X 1.80, Z 4.05 mm (SOURCE, Vishay 28950, IPC-7351 reflow; suitable for hand). Pad gap 1.75 mm PASS. 1.0 mm tracks fit the 1.80 mm pad. 0805 is possible but offers no benefit by hand. Parts: generic 1 % thick film 4k7 and 220 Ω; datasheets not opened, values are as V1.2.
- **C1**: 100 nF X7R 50 V 1206, e.g. KEMET C1206C104K5RACTU, datasheet **not opened** (certificate error on the KEMET site). 3.3 V on 50 V is 6.6 % of rating (CALCULATION). X7R ±15 % over temperature is a standard EIA figure (ASSUMPTION). No derating problem; C0G is unnecessary. τ stays under 0.4 ms against the 30 ms read interval (CALCULATION, analysis.md).

## 7. Copper-side assembly

- **Layer and mirroring**: copper moves to the component side (KiCad F.Cu, proposed). F.Cu needs the plot mirror on; B.Cu did not, so the fabrication script changes. The user check stays valid: board text must read reversed on the paper. Rule changes: REQ-027 rewrite (systems); drill and ring rules apply to the 4 holes only.
- **Silkscreen**: no longer practical on the copper side, because toner on the bare laminate is poor and sits on the solder areas. Use etched copper text in free areas (stroke ≥ 0.5 mm, clearance ≥ 0.6 mm), and the assembly-map PDF. JP1 legend ORIG/QT must be in copper, since it prevents the wrong power pin (R-007).
- **Exposed copper under parts**: every bare track under a module counts in the rules; the Pico keep-out above is the example. Clean flux under R1-R12: residue on bare FR-4 reduces the 4.4 mm path, ASSUMPTION.

### Routing estimate (reasoned estimate, NOT RUN)

V1.2 is single-layer, all planar except the two configuration wires and JP1 (REQ-027, PASS). The topology does not change: 12 ordered electrode lanes, 7 connected Pico pins all but one on the right column, module S row. Changes that help: 2512 lanes are about 9 mm shorter, and tracks can run under the Pico interior. Changes that hurt: tracks previously ran on the opposite side under THT bodies; now SMD pads are on the same layer, and under-R1-R12 is forbidden. The pinch points are GND and 3V3 getting past the electrode lanes and the J1/JP1 corner.

Estimate: single-layer with the same two wire links is plausible on 100 × 70 mm, likely with no new bridges. It is not proven until the layout passes ERC, DRC and parity. If a third wire appears, flag it rather than relax a rule.

## 8. Assumptions, gaps and open risks

- Standards not opened: IEC 61000-4-2, IEC 60664-1 F.2 (recalled, EE-S16/S25), IPC-4101 peel.
- HPWC chart is a raster image (±5 % reading). It is a 1.2/50 µs rating, not an IEC ESD rating, same basis as ADR-019.
- HPWC cost and stock not checked; REQ-032 impact not recalculated.
- Not opened: WAGO 2060, KEMET C1206, Yageo chip data, STEMMA QT module bottom side, SMD header data, any PWC (1 %) datasheet.
- No ESD test, no hand-solder trial, no etch test.

## 9. Sources opened in this task

| ID | Document | Used for | Access |
| --- | --- | --- | --- |
| T90-S1 | Raspberry Pi Pico datasheet RP-008307-DS-2, sha256 757ff485...aa89eb, `sim/systems/datasheets/pico-datasheet.pdf` | Figures 3, 5, 6; TP names; section 2 | Local, rendered pages 7, 10, 11 |
| T90-S2 | TT Electronics HPWC Series (09.23), sha256 1088aba0...eb1a, `.../datasheets/tt_hpwc_0923.pdf` | Dimensions, tolerance, 1.2/50 µs chart | Downloaded by WebFetch |
| T90-S3 | Vishay CMA 0204, CMB 0207, doc. 28956 rev. 29-Mar-2023, sha256 3bd3f934...8c61 | Dimensions, ESD, chart | Same |
| T90-S4 | Vishay MMU 0102, MMA 0204, MMB 0207, doc. 28963 rev. 02-Jun-2026, sha256 07bf424d...7969 | Chart, dimensions | Same |
| T90-S5 | Vishay MMA 0204 HV, MMB 0207 HV, doc. 28880, sha256 0f8dca2b...6519 | Range 340 kΩ-10 MΩ | Same |
| T90-S6 | Vishay Recommended Solder Pad Dimensions, doc. 28950 rev. 12-Jul-2022, sha256 9e2b145c...144e | 0207 and 1206 lands | Same |
| T90-S7 | Vishay CMA/CMB product overview doc. 48636, sha256 b6cc6a9f...c4 | Cross-check only | Same |
| T90-S8 | NXP MPR121 datasheet Rev 4, sha256 a02ff161...55c | Package pitch and width | Same (matches S-006) |
| T90-S9 | Omron B3S catalogue, sha256 c6391ce5...289b | SW1 dimensions, force, pads | Same |
| T90-S10 | Adafruit Eagle `Adafruit MPR121 Breakout.brd` (S-003) | Board size, drills, no bottom parts | Read via WebFetch, truncated then read with offset |
| T90-S11 | Adafruit product page 1982 | Header included, 2021 revision | Read via WebFetch |

Full sha256 values and PDFs: `reports/electronics/evidence/T-090/datasheets/`. Chart method: `evidence/T-090/chartread.py`, pages rendered with `evidence/T-090/pdfpages.swift`. Calculation: `sim/electronics/calc/calc_smd_feasibility.py` and `.out`.
