#!/bin/zsh
# Targeted mutants for the F-1/F-2 code (the full set is in run_mutants.sh).
R=/Users/rod/fruta-midi-controller; O=$R/reports/firmware/T-041/mutation; F=$R/firmware/FrutaMIDI
: > $O/summary_f1f2.txt
mutate() {
  local f=$F/$1 before after
  before=$(shasum -a 256 $f | cut -d' ' -f1); cp $f $O/.backup
  python3 -c "import sys,pathlib; p=pathlib.Path(sys.argv[1]); s=p.read_text(); assert s.count(sys.argv[2])==1; p.write_text(s.replace(sys.argv[2], sys.argv[3]))" $f "$2" "$3" || { echo "$4: NOT APPLIED" >> $O/summary_f1f2.txt; rm $O/.backup; return; }
  $R/.venv/bin/python -m pytest -q -x $R/tests/firmware > $O/$4.log 2>&1; local rc=$?
  cp $O/.backup $f; rm $O/.backup; after=$(shasum -a 256 $f | cut -d' ' -f1)
  echo "$4: pytest_exit=$rc result='$(tail -1 $O/$4.log)' restored=$([[ $before == $after ]] && echo yes || echo NO)" >> $O/summary_f1f2.txt
}
mutate fm_mpr121.h "const uint8_t MPR121_AUTOCONFIG1_VALUE = 0x00;" "const uint8_t MPR121_AUTOCONFIG1_VALUE = 0x80;" M24_scts_set
mutate fm_mpr121.h "(vddMv - 700u)" "(vddMv - 600u)" M25_usl_formula
mutate fm_mpr121.h "usl * 65u / 100u" "usl * 60u / 100u" M26_lsl_factor
mutate fm_mpr121.h "const uint8_t MPR121_REG_AUTOCONFIG1 = 0x7C;" "const uint8_t MPR121_REG_AUTOCONFIG1 = 0x7B;" M27_wrong_register
