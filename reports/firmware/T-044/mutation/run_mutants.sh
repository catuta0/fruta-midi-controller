#!/bin/zsh
# T-044 mutants for fm_notes.h / fm_sensor_health.h / fm_mpr121.h touch bits.
R=/Users/rod/fruta-midi-controller; O=$R/reports/firmware/T-044/mutation; F=$R/firmware/FrutaMIDI
: > $O/summary.txt
mutate() {
  local f=$F/$1 before after
  before=$(shasum -a 256 $f | cut -d' ' -f1); cp $f $O/.backup
  python3 -c "import sys,pathlib; p=pathlib.Path(sys.argv[1]); s=p.read_text(); assert s.count(sys.argv[2])==1; p.write_text(s.replace(sys.argv[2], sys.argv[3]))" $f "$2" "$3" || { echo "$4: NOT APPLIED" >> $O/summary.txt; rm $O/.backup; return; }
  $R/.venv/bin/python -m pytest -q -x -p no:cacheprovider $R/tests/firmware > $O/$4.log 2>&1; local rc=$?
  cp $O/.backup $f; rm $O/.backup; after=$(shasum -a 256 $f | cut -d' ' -f1)
  echo "$4: pytest_exit=$rc result='$(tail -1 $O/$4.log)' restored=$([[ $before == $after ]] && echo yes || echo NO)" >> $O/summary.txt
}
mutate fm_notes.h "    bool first = holders(n) == 0;" "    bool first = holders(n) < 2;" N1_note_on_second_holder
mutate fm_notes.h "    if (holders(n) == 0) {" "    if (true) {" N2_note_off_every_release
mutate fm_notes.h "if (note[p] == n && pressure[p] > m) m = pressure[p];" "if (note[p] == n) m = pressure[p];" N3_last_not_max
mutate fm_notes.h "      if (pressure_reset_on_release(s0)) out.pressure(n, 0);" "" N4_no_final_zero
mutate fm_notes.h "if (note[q] == n) { s0 = sent[q]; break; }" "if (false) { s0 = sent[q]; break; }" N5_no_sent_inherit
mutate fm_sensor_health.h "const uint8_t  SENSOR_FAIL_LIMIT = 3;" "const uint8_t  SENSOR_FAIL_LIMIT = 1;" H1_fail_limit_1
mutate fm_sensor_health.h "    if (success) { fails = 0; return false; }" "    if (success) { return false; }" H2_no_fail_reset
mutate fm_sensor_health.h "    if (success && ecr != expectedEcr) {" "    if (success && ecr == 0x55 && ecr != expectedEcr) {" H3_no_ecr_check
mutate fm_sensor_health.h "    if (ok || !elapsed_more_than(now, lastRetry, SENSOR_RETRY_MS)) return false;" "    if (!elapsed_more_than(now, lastRetry, SENSOR_RETRY_MS)) return false;" H4_retry_when_ok
mutate fm_mpr121.h "& 0x0FFFu);" "& 0xFFFFu);" H5_touch_mask
