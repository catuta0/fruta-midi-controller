# T-095 — electronics-engineer

Status: PARTIAL. Both quotes compared. All-LCSC cannot be completed today (FAIL for that option). Mouser complete, with one R1-R12 trade-off left to the user. Shipping NOT CONFIRMED for both shops. No hardware or generator changed; no KiCad job run.

Requirements addressed: R-016 (R1-R12 sourcing, still open).

Inputs: T-094 evidence; reports/electronics/smd_feasibility.md; repository at 82067c2-dirty.

Outputs: reports/electronics/evidence/T-095/comparison.md (table), distributor_pages.txt (raw data), compute_quote.py and compute_quote.out.

Checks performed: `python3 -I compute_quote.py`, output in compute_quote.out: "R1-R12 HPWC2512-3K3JT1 15.00 EUR; total 27.53 EUR"; "R1-R12 CRGP2512F3K3 4.031 USD = 3.60 EUR; with common lines 6.92 EUR". PASS for the arithmetic only. ERC, DRC and sim: NOT RUN (nothing changed).

Numerical findings (2026-11-09; prices SOURCE, totals CALCULATION, 1 EUR = 1.1193 USD SOURCE ECB):
- Mouser complete board 27.53 EUR with HPWC2512-3K3JT1; 17.60 EUR with CMB02070X3301GB200.
- LCSC orderable lines 6.92 EUR with CRGP2512F3K3 (pulse unproven), without A1, A2 and knob.
- LCSC with CMB 13.74 EUR; with Pico 2 (not confirmed drop-in) 15.30 EUR; still no A2 or knob.
- LCSC hypothetical with the module listed at 19.37 EUR: 34.67 EUR, no knob.
- Highest LCSC voltage attribute at 2.7-3.3 kΩ: 1 kV (SOURCE); 9 parts at 600 V or above, stock 0.
- CMB02070X3301GB200: 5175 V 1.2/50 µs chart reading at 3k3, about ±5 % (SOURCE T-090), margin 1.42 CALCULATION; gap 3.2 mm SOURCE against 3.5 mm rule, FAIL; 3366 Ω worst 0.901 SIMULATION.

Assumptions: chart readings about ±5 %; SC0915 and 1982 Mouser figures as given by the coordinator from the user's check, not opened by me.

Errors: the Same Sky datasheet link on Mouser answered as a file download and a save dialog appeared to the user; I did not retry. The dialog should be dismissed if it is still open.

Not opened or not confirmed: Same Sky SPK-016 datasheet, so bore fit on the flatted shaft is not confirmed; RC1206, CL31, PTV09 datasheets (Mouser rows only); Ta-I, Viking, Ralec, Walsin not searched by brand; shipping to Portugal for both shops.

Open decisions for manager / user:
1. R1-R12: HPWC2512-3K3JT1 (15.00 EUR, fits the land, accept 0.885 vs 0.90 at +5 %); CMB 0207 3k3 (5.06 EUR at Mouser, accept 3.2 mm vs 3.5 mm and a new MELF land); or CRGP2512F3K3 (pulse unproven).
2. If Mouser is chosen, the BOM needs Mouser numbers: RV1 and R13-R16 differ from the LCSC parts now in the generators.

Next actions: manager takes decision 1. Nothing committed.
