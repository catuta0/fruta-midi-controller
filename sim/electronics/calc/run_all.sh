#!/bin/sh
# Re-runs every T-050 / T-060 calculation and stores the raw output next to each script.
cd "$(dirname "$0")"
KICAD_PY="${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"
for s in sim_electrode calc_esd_variants calc_power calc_i2c calc_flashover calc_pulse_rated; do python3 -I $s.py > $s.out 2>&1 || exit 1; done
"$KICAD_PY" calc_mechanical.py > calc_mechanical.out 2>/dev/null || exit 1
"$KICAD_PY" check_gap.py > check_gap.out 2>/dev/null || exit 1          # T-060: measured ELE/E gaps vs flashover rule
echo "outputs: $(ls *.out | tr '\n' ' ')"
