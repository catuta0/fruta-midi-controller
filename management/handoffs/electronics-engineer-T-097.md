# T-097 — electronics-engineer

Status: PASS for the study as scoped (questions 1-5 answered). Every clamp option is FAIL against the 0.90 sensing limit at R 3k3. The clamp benefit is NOT PROVEN until an ESD test.

## Requirements addressed
The user's proposal of one TVS/ESD clamp per electrode (Ex to the GND edge track), questions 1-5.

## Inputs
- change/CR-003 @ 04edcc9 plus the uncommitted T-096 tree.
- Datasheets in `reports/electronics/evidence/T-097/datasheets/` (git-ignored), text in `.../T-097/text/`:
  - Bourns CDSOD323-TxxLC, sha256 6d0c7007...ee30
  - NXP PESD5V0U1BA Rev. 01 2007, sha256 2b488364...27e0
  - NXP PESD5V0S1BA Rev. 04 2009, sha256 2c146d0d...515a
- Mouser Portugal pages, 2026-11-09.

## Outputs
- `reports/electronics/tvs_clamp_study.md`
- `sim/electronics/calc/sim_tvs_clamp.py` and `sim_tvs_clamp.out` (not added to run_all.sh)

## Checks performed
`"$HOME/bin/pcgate" chat2 sh -c 'cd sim/electronics/calc && python3 -I sim_tvs_clamp.py > sim_tvs_clamp.out'` · "sim exit 0". Output lines:
- "Bourns CDSOD323-T05LC (1.0 pF typ, 5 uA max) 3300 ... 0.897 FAIL"
- "... 330 ... 0.947 PASS"
- "R 3300 C_d 1.0 pF: min ratio 0.889 FAIL"
- "R 330 C_d 2.0 pF: min ratio 0.921 PASS"
- "R 330 C_d 3.5 pF: min ratio 0.868 FAIL"

## Numerical findings
See the study. Key figures:
- Max C_d for ratio ≥ 0.90: 0 pF at 3k3 and 2 pF at 330 Ω (SIMULATION).
- Max leakage: about 100 nA, which gives a 2.3-count offset against the 12-count threshold (CALCULATION on the model).
- V_R with a clamp: about 50-100 V instead of 3.6-7.3 kV (CALCULATION, ASSUMPTION overshoot).
- Cost: +1.86 / +1.96 / +6.18 EUR, giving 15.70 / 15.80 / 20.02 EUR per board (CALCULATION).

## Assumptions
- 2 nH of clamp-path inductance, PESD5V0S1BA r_dyn extrapolation, leakage modelled as a constant current.
- SOD323 hand-solder lands 0.8 x 1.0 mm. Fine-pitch package land gaps were not opened.

## Errors
- nexperia.com returned 403, so old NXP revisions from distributor copies were used.
- A duplicate PESD5V0U1BA copy (chipdip) was discarded.

## Open decisions for manager
1. Accept a sensing deviation for a clamp, or keep the board without clamps (recommended for now).
2. Order an ESD-gun test of the present board (outside my scope).

## Next actions
If a clamp is chosen:
- Confirm the Bourns maximum C_d and its leakage at 3.3 V.
- Add the SOD323 footprint and its placement in gen_pcb.py, and choose R1-R12 = 1 kΩ.
- Re-run DRC, check_gap and sim_electrode.
