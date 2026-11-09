#!/bin/sh
# Re-runs every T-050 / T-060 calculation and stores the raw output next to each script.
cd "$(dirname "$0")"
KICAD_PY="${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"
for s in sim_electrode calc_esd_variants calc_power calc_i2c calc_flashover calc_pulse_rated calc_pot_rc; do python3 -I $s.py > $s.out 2>&1 || exit 1; done
"$KICAD_PY" calc_mechanical.py > calc_mechanical.out 2>/dev/null || exit 1
"$KICAD_PY" check_gap.py > check_gap.out 2>/dev/null || exit 1          # T-091: SMD gaps, terminations, mounting metal, spark gap
"$KICAD_PY" calc_gnd_bounce.py > calc_gnd_bounce.out 2>/dev/null || exit 1   # T-073 / C2-005: arc to GND, bounce
"$KICAD_PY" check_smd.py > check_smd.out 2>/dev/null || exit 1          # T-091: single-layer SMD rules, keep-outs, footprint fit (no silkscreen on the board, check_silk.py retired)
echo "outputs: $(ls *.out | tr '\n' ' ')"
