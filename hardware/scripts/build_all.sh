#!/bin/sh
# Regenera esquemático + PCB, verifica (ERC/DRC/paridade) e exporta os ficheiros de fabrico.
# Uso:  sh hardware/scripts/build_all.sh      (macOS; noutros sistemas ajusta KICAD_BIN / KICAD_PY)
set -e
cd "$(dirname "$0")/.."
KICAD_BIN="${KICAD_BIN:-/Applications/KiCad/KiCad.app/Contents/MacOS}"
KICAD_PY="${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}"
K="$KICAD_BIN/kicad-cli"
F=fabrico

python3 scripts/gen_schematic.py
"$KICAD_PY" scripts/gen_pcb.py 2>/dev/null

mkdir -p build
"$K" sch erc --severity-all --exit-code-violations -o build/erc.rpt frutamidi.kicad_sch
"$K" pcb drc --severity-all --schematic-parity --exit-code-violations -o build/drc.rpt frutamidi.kicad_pcb

rm -rf "$F" && mkdir -p "$F/gerbers" "$F/imagens"
"$K" sch export pdf --black-and-white -o "$F/frutamidi-esquematico.pdf" frutamidi.kicad_sch
PDF="$K pcb export pdf --mode-single --black-and-white --scale 1"
$PDF --layers B.Cu,Edge.Cuts --drill-shape-opt 1            -o "$F/1-cobre-para-transferir.pdf" frutamidi.kicad_pcb
$PDF --layers B.Cu,Edge.Cuts --drill-shape-opt 1 --negative -o "$F/1b-cobre-negativo.pdf" frutamidi.kicad_pcb
$PDF --layers F.SilkS,F.Fab,Edge.Cuts --drill-shape-opt 2 --sp -o "$F/2-mapa-de-montagem.pdf" frutamidi.kicad_pcb
$PDF --layers F.SilkS,Edge.Cuts --drill-shape-opt 0 --mirror -o "$F/3-serigrafia-opcional-espelhada.pdf" frutamidi.kicad_pcb
"$K" pcb export gerbers --layers B.Cu,F.SilkS,Edge.Cuts,B.Mask --use-drill-file-origin -o "$F/gerbers/" frutamidi.kicad_pcb
"$K" pcb export drill --format excellon --drill-origin plot --excellon-units mm --generate-map --map-format pdf -o "$F/gerbers/" frutamidi.kicad_pcb
"$K" sch export bom --fields 'Reference,Value,Footprint,${QUANTITY}' --labels 'Ref,Valor,Footprint,Qtd' \
     --group-by Value,Footprint -o "$F/bom-kicad.csv" frutamidi.kicad_sch
"$K" pcb render --side top --width 1600 --height 1120 --background opaque -o "$F/imagens/placa-topo.png" frutamidi.kicad_pcb
"$K" pcb render --rotate "-50,0,20" --perspective --zoom 0.9 --width 1600 --height 1100 --background opaque -o "$F/imagens/placa-3d.png" frutamidi.kicad_pcb
"$K" pcb render --side bottom --width 1600 --height 1120 --background opaque -o "$F/imagens/placa-cobre.png" frutamidi.kicad_pcb
(cd "$F" && zip -qr ../build/frutamidi-fabrico.zip .)
echo "OK: ERC e DRC sem violações; ficheiros em hardware/$F"
