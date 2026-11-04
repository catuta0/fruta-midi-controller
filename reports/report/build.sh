#!/bin/sh
# Build the FrutaMIDI report: regenerate the requirements table from the CSV,
# then run three pdflatex passes (longtable widths settle on the third) with the project-local TinyTeX.
# Usage: sh reports/report/build.sh
# The MCP eng-tools latex_build also works (it uses the last generated table).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PDFLATEX="$ROOT/tools/TinyTeX/bin/universal-darwin/pdflatex"

python3 -I "$HERE/scripts/csv_to_table.py"
cd "$HERE"
"$PDFLATEX" -interaction=nonstopmode -halt-on-error frutamidi_report.tex > /dev/null
"$PDFLATEX" -interaction=nonstopmode -halt-on-error frutamidi_report.tex > /dev/null
"$PDFLATEX" -interaction=nonstopmode -halt-on-error frutamidi_report.tex > /dev/null

# Proof lines (exit code 0 alone is not a pass).
grep "Output written on" frutamidi_report.log
ERRORS=$(grep -c '^! ' frutamidi_report.log || true)
echo "LaTeX error lines: $ERRORS"
[ "$ERRORS" -eq 0 ]
