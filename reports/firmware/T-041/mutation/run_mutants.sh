#!/bin/zsh
# Mutation check for T-041: apply one mutant at a time to a production header,
# run the host tests, restore the header and verify its checksum.
R=/Users/rod/fruta-midi-controller
O=$R/reports/firmware/T-041/mutation
F=$R/firmware/FrutaMIDI
: > $O/summary.txt
mutate() {   # file  old  new  label
  local f=$F/$1 before after
  before=$(shasum -a 256 $f | cut -d' ' -f1)
  cp $f $O/.backup
  python3 -c "import sys,pathlib; p=pathlib.Path(sys.argv[1]); s=p.read_text(); assert s.count(sys.argv[2])==1, 'pattern'; p.write_text(s.replace(sys.argv[2], sys.argv[3]))" $f "$2" "$3" || { echo "$4: MUTANT NOT APPLIED" >> $O/summary.txt; return; }
  $R/.venv/bin/python -m pytest -q $R/tests/firmware > $O/$4.log 2>&1
  local rc=$?
  cp $O/.backup $f; rm $O/.backup
  after=$(shasum -a 256 $f | cut -d' ' -f1)
  echo "$4: pytest_exit=$rc result='$(tail -1 $O/$4.log)' restored=$([[ $before == $after ]] && echo yes || echo NO)" >> $O/summary.txt
}
mutate fm_debounce.h  "elapsed_at_least(now, lastChangeMs, debounceMs)" "elapsed_more_than(now, lastChangeMs, debounceMs)" M1_debounce_ge_to_gt
mutate fm_scales.h    "12 * (pad / sc.len)" "12 * (pad / (sc.len + 1))" M2_scale_wrap
mutate fm_scales.h    "int oct  = sc.fixed ? 0 : octaveShift;" "int oct  = octaveShift;" M3_fixed_ignored
mutate fm_scales.h    "return (uint8_t)clamp_int(note, MIDI_NOTE_MIN, MIDI_NOTE_MAX);" "return (uint8_t)note;" M4_no_clamp
mutate fm_aftertouch.h "(127L - 0L)" "(126L - 0L)" M5_at_scale
mutate fm_aftertouch.h "return d >= AT_MIN_CHANGE;" "return d > AT_MIN_CHANGE;" M6_at_filter
mutate fm_pot.h       "const float    POT_HYSTERESIS = 0.7f;" "const float    POT_HYSTERESIS = 0.5f;" M7_pot_no_hysteresis
mutate fm_button.h    "const uint16_t BUTTON_SAMPLE_MS = 10;" "const uint16_t BUTTON_SAMPLE_MS = 1;" M8_button_no_sampling
mutate fm_time.h      "return (uint32_t)(now - since) >= interval;" "return now >= since + interval;" M9_time_not_wrap_safe
mutate fm_midi.h      "(channel - 1)" "(channel)" M10_channel_off_by_one
mutate fm_blink.h     "(phasesLeft % 2u) == 0" "(phasesLeft % 2u) == 1" M11_blink_inverted
mutate fm_blink.h     "elapsed_at_least(now, phaseStart, halfMs)" "elapsed_more_than(now, phaseStart, halfMs)" M12_blink_half_period
mutate fm_debounce.h  "  lastChangeMs = now;" "  (void)now;" M13_padstep_no_timestamp
mutate fm_blink.h     "phasesLeft = (uint16_t)(2u * times);" "phasesLeft = (uint16_t)(2u * times - 1u);" M14_blink_count
mutate fm_aftertouch.h "  if (p == 0) return lastSent > 0;" "" M15_no_floor_rule
mutate fm_aftertouch.h "  return lastSent > 0;
}" "  return lastSent > 200;
}" M16_no_reset_on_release
mutate fm_scales.h    '"Chromatic"' '"Cromatica"' M17_portuguese_name
mutate fm_mpr121.h    "(filt[2 * e + 1] & 0x03u)" "(filt[2 * e + 1] & 0xFFu)" M18_no_10bit_mask
mutate fm_mpr121.h    "(uint16_t)base[e] << 2" "(uint16_t)base[e] << 1" M19_baseline_shift
mutate fm_mpr121.h    "filt[2 * e] | ((uint16_t)(filt[2 * e + 1] & 0x03u) << 8)" "filt[2 * e + 1] | ((uint16_t)(filt[2 * e] & 0x03u) << 8)" M20_lsb_msb_swapped
mutate fm_mpr121.h    "const uint8_t MPR121_MERGE_GAP = 1;" "const uint8_t MPR121_MERGE_GAP = 0;" M21_merge_gap_0
mutate fm_mpr121.h    "const uint8_t MPR121_MERGE_GAP = 1;" "const uint8_t MPR121_MERGE_GAP = 3;" M22_merge_gap_3
mutate fm_mpr121.h    "  n = (uint8_t)(hi - lo + 1);" "  n = (uint8_t)(hi - lo);" M23_run_length
