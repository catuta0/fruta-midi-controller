#!/bin/sh
# Regenerates schematic + PCB, checks them (ERC / DRC / schematic parity) and exports the fabrication files.
# Usage:  sh hardware/scripts/build_all.sh      (macOS; on other systems set KICAD_BIN / KICAD_PY)
# Fails on any ERC or DRC violation (kicad-cli --exit-code-violations).
#
# CR-003 / ADR-023: copper on the component side (F.Cu). F.Cu is mirrored for toner transfer: the paper is turned face
# down on the copper, so what is printed is the mirror image of the top view. Mirroring is verified in the exported PDF
# (sim/electronics/calc/check_smd.py and reports/electronics/evidence/T-091/), not assumed.
set -e
cd "$(dirname "$0")/.."
KICAD_BIN="${KICAD_BIN:-/Applications/KiCad/KiCad.app/Contents/MacOS}"
KICAD_PY="${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"
K="$KICAD_BIN/kicad-cli"
F=fabrication

python3 scripts/gen_schematic.py
"$KICAD_PY" scripts/gen_pcb.py 2>/dev/null

mkdir -p build
"$K" sch erc --severity-all --exit-code-violations -o build/erc.rpt frutamidi.kicad_sch
"$K" pcb drc --severity-all --schematic-parity --exit-code-violations -o build/drc.rpt frutamidi.kicad_pcb

rm -rf "$F" && mkdir -p "$F/gerbers" "$F/images"
"$K" sch export pdf --black-and-white -o "$F/frutamidi-schematic.pdf" frutamidi.kicad_sch
PDF="$K pcb export pdf --mode-single --black-and-white --scale 1"
$PDF --layers F.Cu,Edge.Cuts --drill-shape-opt 1 --mirror            -o "$F/1-copper-for-transfer.pdf" frutamidi.kicad_pcb
$PDF --layers F.Cu,Edge.Cuts --drill-shape-opt 1 --mirror --negative -o "$F/1b-copper-negative.pdf" frutamidi.kicad_pcb
$PDF --layers F.Fab,Edge.Cuts --drill-shape-opt 2 -o "$F/2-assembly-map.pdf" frutamidi.kicad_pcb
"$K" pcb export gerbers --layers F.Cu,F.Mask,Edge.Cuts --use-drill-file-origin -o "$F/gerbers/" frutamidi.kicad_pcb
"$K" pcb export drill --format excellon --drill-origin plot --excellon-units mm --generate-map --map-format pdf -o "$F/gerbers/" frutamidi.kicad_pcb
"$K" sch export bom --fields 'Reference,Value,Footprint,Manufacturer,MPN,${QUANTITY}' \
     --labels 'Ref,Value,Footprint,Manufacturer,MPN,Qty' \
     --group-by Value,Footprint -o "$F/bom-kicad.csv" frutamidi.kicad_sch
"$K" pcb render --side top --width 1600 --height 1120 --background opaque -o "$F/images/board-top.png" frutamidi.kicad_pcb
"$K" pcb render --rotate "-50,0,20" --perspective --zoom 0.9 --width 1600 --height 1100 --background opaque -o "$F/images/board-3d.png" frutamidi.kicad_pcb
rm -f build/frutamidi-fabrication.zip
(cd "$F" && zip -qr ../build/frutamidi-fabrication.zip .)
echo "OK: ERC and DRC without violations; files in hardware/$F"
