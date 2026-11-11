# T-097 — clamp diode per electrode: study

Study only. No hardware/ change and no KiCad job. Date 2026-11-11; Mouser data was read on 2026-11-09. Inputs: branch change/CR-003 @ 04edcc9 plus the uncommitted T-096 tree.

## Summary

| Item | Status | Evidence |
|---|---|---|
| Candidates with an opened datasheet | 3 found (SOD323) | `evidence/T-097/datasheets/`, `evidence/T-097/text/` |
| Sensing against the 0.90 worst-case limit, R 3k3 | FAIL for every candidate | `sim/electronics/calc/sim_tvs_clamp.out` |
| Sensing with R lowered to 330 Ω | PASS only for C_d ≤ 2 pF (Bourns 1.0 pF typ); NOT CONFIRMED (no max C_d published) | same |
| Resistor stress with a clamp | V_R about 50-100 V instead of 3.6-7.3 kV (CALCULATION, ASSUMPTION clamp overshoot) | below |
| Layout | Feasible by estimate: SOD323 across the 1.40 mm gap, no wire bridge | below |
| Recommendation | Do not add clamps now; decide after an ESD test, or accept a sensing deviation | below |

## 1. Candidates (Mouser Portugal, cheapest first)

| Part | Mouser No. | Stock | 12 pcs | V_RWM | C_d | I_leak max | IEC 61000-4-2 contact | Clamping | Datasheet |
|---|---|---|---|---|---|---|---|---|---|
| Nexperia PESD5V0S1BA (bidir, SOD323) | 771-PESD5V0S1BAF | 2,451 | 1.86 EUR (0.155 at 10+) | 5 V | 35 typ / 45 max pF at 0 V | 100 nA at 5 V | 30 kV (10 pulses) | ≤ 10 V at 1 A, ≤ 14 V at 12 A, 8/20 µs | NXP Rev. 04, 20 Aug 2009 (copy from szlcsc.com) |
| Nexperia PESD5V0U1BA (bidir, SOD323) | 771-PESD5V0U1BA115 | 2,268 | 1.96 EUR (0.163) | 5 V | 2.9 typ / 3.5 max pF at 0 V; 1.9 pF typ at 5 V | 100 nA at 5 V (5 nA typ) | 10 kV (10 pulses) | No numeric value, only oscilloscope figures | NXP Rev. 01, 25 Apr 2007 (copy from chipsmall.com) |
| Bourns CDSOD323-T05LC (bidir, SOD323) | 652-CDSOD323-T05LC | 31,164 | 6.18 EUR (0.515) | 5 V | 1.0 pF typ at 0 V (no max) | 5 µA at 5 V | ±8 kV min, ±30 kV max | ≤ 9.8 V at 1 A; 18.3 V typ at 15 A, 8/20 µs | bourns.com, CDSOD323-TxxLC |

All values in the table are SOURCE. The datasheets are old revisions from distributor copies, because nexperia.com refused the download (403). The electrical values must be re-checked against the current revision before use.

- **Working voltage:** 5 V ≥ the 3.3 V MPR121 electrode swing (CALCULATION; VDD 3.29 V, sim_electrode.py).
- **Packages:**
  - SOD323 (lead span 2.5-2.7 mm; NXP reflow land pitch about 2.1 mm, lands 0.5-0.6 mm) is hand-solderable. A land gap ≥ 0.95 mm meets the 0.6 mm rule (SOURCE NXP footprint, CALCULATION).
  - SOD123 and SOT-23-3 would also pass on clearance; no cheaper low-capacitance single-line part was checked in them.
  - SOD523, SOD882, SOD923 and DFN1006 fail: land gaps 0.3-0.5 mm are below 0.6 mm, and they are too small for toner transfer (ASSUMPTION from typical land patterns, not opened).

## 2. Effect on sensing (SIMULATION, sim_tvs_clamp.py with the sim_electrode.py model)

The clamp sits on node E, so its capacitance adds to the electrode capacitance. The ratio is the worst-case sensitivity with R and the clamp, divided by the worst case with R = 0 and no clamp, at the same C_ext. The limit is ADR-019's 0.90. C_d is taken at 0 V, the worst case; it falls with bias.

| Clamp (C_d, I_leak) | R 100 | R 330 | R 1000 | R 3300 |
|---|---|---|---|---|
| none | 0.981 | 0.977 | 0.962 | 0.904 PASS |
| Bourns T05LC (1.0 pF, 5 µA) | 0.950 PASS | 0.947 PASS | 0.938 PASS | 0.897 FAIL |
| PESD5V0U1BA (3.5 pF, 100 nA) | 0.882 FAIL | 0.866 FAIL | 0.857 FAIL | 0.827 FAIL |
| PESD5V0S1BA (45 pF, 100 nA) | 0.380 FAIL | 0.373 FAIL | 0.370 FAIL | 0.341 FAIL |

- **Capacitance:** the worst case is always the smallest electrode (C_ext 10 pF). Above 100 pF, all but the 45 pF part stay at ≥ 0.89.
  - At R 3300 Ω, the largest C_d that keeps 0.90 is 0 pF (1 pF gives 0.889).
  - At R 330 Ω, the largest is 2 pF (0.921); 3.5 pF gives 0.868.
  - This is the same effect as making the electrode wire longer: 1 pF is about 2-3 cm of wire at 30-50 pF/m (ASSUMPTION). The 0.90 limit is strict at 10 pF.
  - **A Zener or a general TVS of 35-45 pF and more is unusable:** ratio 0.34-0.38 at 10 pF (SIMULATION).
- **Leakage:**
  - As a constant offset, it changes the ratio by ≤ 0.006 up to 5 µA. This is the noise of the discrete autoconfig choice, so it does not limit the ratio.
  - As an offset in counts at the nominal CDC/CDT pair (model, C_ext 10 pF): 0.1 counts at 5 nA, 2.3 at 100 nA, 23 at 1 µA, 116 at 5 µA, against the 12-count touch threshold.
  - The baseline filter absorbs a slow offset. A leakage that changes faster, for example a finger warming the diode, could cause false touches.
  - Maximum acceptable leakage (CALCULATION on the model): about 100 nA, which gives an offset of 2.3 counts, a fifth of the threshold.
  - The Bourns part is specified only at 5 µA max (at 5 V); its leakage at ≤ 3.3 V is NOT CONFIRMED.

## 3. What R sees with a clamp (CALCULATION, IEC 150 pF / 330 Ω, first peak 3.75 A/kV SOURCE)

- **Clamp current:** the first peak is 15 A at 4 kV and 30 A at 8 kV.
- **Clamp voltage:** at 8/20 µs the clamp holds about 15 V at 15 A and 20 V at 30 A. This is a PESD5V0S1BA extrapolation with r_dyn (14 - 10) / 11 A = 0.36 Ω (ASSUMPTION).
- **Inductive overshoot:** with 2 nH of lead and track inductance (ASSUMPTION), the overshoot at about 19 A/ns is about 38 V. So Ex peaks at about 50-60 V at 4 kV and 80-100 V at 8 kV (ASSUMPTION; the U1BA datasheet gives only waveforms).
- **Across R:** V_R ≈ V_Ex - 3.8 V, which is about 50-100 V instead of 3.6-7.3 kV.
  - Pin current: 18-30 mA at R 3300 Ω, 0.15-0.29 A at 330 Ω, 0.5-1.0 A at 100 Ω, against I_lim 1.33 A (ASSUMPTION).
  - Energy into R: < 1 µJ.
- **What still matters, if the clamp works:**
  - The 3.5 mm flashover rule across R and R's pulse rating no longer matter: 100 V against R's 200 V working voltage.
  - Both matter again if the clamp fails open. An overstressed TVS usually fails short (ASSUMPTION), but open cannot be excluded.
  - A clamp that fails short kills that electrode (a stuck channel) but leaves the MPR121 safe.
  - The 1.40 mm Ex-to-GND spark gap: keep it. It costs nothing and it diverts air discharges before they reach the clamp. With a clamp it is no longer the only defence.
  - The clamp current returns through the same GND edge track as the arc (calc_gnd_bounce.out). That ground bounce stays unproven.
- **Can R be smaller or cheaper?** For sensing, the smaller the better: R 330 Ω gives ratio 0.977 without a clamp.
  - With a clamp, the pin current stays below I_lim down to about 100 Ω (CALCULATION, ASSUMPTION clamp overshoot).
  - Cost: no saving. The present 2512 3k3 costs 0.109 EUR each, the same as any 2512 at Mouser. A 1206 would need a new land.
  - Best value with a clamp: 330 Ω-1 kΩ, which balances sensing (≥ 0.94 with a 1 pF clamp) against a residual pin current (≤ 0.3 A). Keeping 3k3 gives fail-open defence but costs sensing (0.897 with 1 pF).

## 4. Layout on the single layer (estimate only)

Each J2 pad is 3.0 x 4.5 mm with its lower edge 1.40 mm above the GND edge track; the pad pitch is 5.08 mm, so pads are 2.08 mm apart (SOURCE gen_pcb.py).

- **Placement:** one SOD323 per pad, standing vertically across the 1.40 mm gap.
  - Lands: 0.8 x 1.0 mm (hand-solder size, ASSUMPTION) at 2.2-2.4 mm pitch.
  - One land merges into the lower part of the J2 pad; the other merges into the GND track.
  - Clearance to the next channel: about 2 mm. No track crosses, so no wire bridge is needed.
- **Interaction with the spark gap:** the diode body covers about 1.25 mm of the 3.0 mm gap width. The rest of the gap stays as open air. Keep the spark gap.
- **Assembly:** the electrode wire stays on the upper half of the pad, as now. The hot-melt must keep off the diode.
- **Effort:** a gen_pcb.py footprint and placement, about 12 parts. DRC and check_gap would need an update for a new net-to-GND part.

## 5. Cost and recommendation

| Option | Added cost | One board (now 13.84 EUR) |
|---|---|---|
| PESD5V0S1BAF x12 | +1.86 EUR | 15.70 EUR (sensing FAIL, 0.34) |
| PESD5V0U1BA x12 | +1.96 EUR | 15.80 EUR (sensing FAIL at any R, 0.83-0.88) |
| CDSOD323-T05LC x12, R kept | +6.18 EUR | 20.02 EUR (0.897 at 3k3 FAIL; 0.947 at 330 Ω PASS, typ C_d only) |

CALCULATION from SOURCE prices (Mouser 2026-11-09), excluding shipping and tax.

**Recommendation:** do not add clamps in this revision.

- Under the agreed 0.90 sensing limit, only the Bourns 1 pF part passes, and only if R is lowered to about 330 Ω-1 kΩ.
- Its capacitance is only typical, and its 5 µA leakage bound is high enough to risk false touches.
- First, test the present board with an ESD gun at 4 kV contact on each electrode: check for resistance shift in R1-R12, MPR121 function, and Pico resets.
- If the resistors drift or fail, the next revision should use the Bourns CDSOD323-T05LC with R1-R12 at 1 kΩ (ratio 0.938, SIMULATION). The manager should accept that as a recorded decision, after confirming the Bourns maximum capacitance and the leakage at 3.3 V.

**Unproven until a physical test:**
- The clamp voltage at the IEC first peak, including inductance.
- The real C_d and leakage at 0-3.3 V and over temperature.
- False touches caused by leakage drift.
- The clamp's survival over repeated strikes, and whether it fails open or short.
- Ground bounce in the GND edge track.
- The sensing model itself (SIMULATION, not measured).
