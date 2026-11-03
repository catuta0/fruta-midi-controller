#!/bin/zsh
S=${0:a:h}
CFG=/Users/rod/fruta-midi-controller/tools/arduino/cli.yaml
for b in rpipico rpipicow rpipico2 rpipico2w; do
  for v in std pcb; do
    if [[ $v == pcb ]]; then
      arduino-cli --config-file $CFG compile -b rp2040:rp2040:${b}:usbstack=tinyusb --build-property "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB" $S/FrutaMIDI > $S/$b-$v.log 2>&1
    else
      arduino-cli --config-file $CFG compile -b rp2040:rp2040:${b}:usbstack=tinyusb $S/FrutaMIDI > $S/$b-$v.log 2>&1
    fi
    echo "$b-$v exit=$?" >> $S/summary.txt
  done
done
arduino-cli --config-file $CFG compile -b arduino:avr:leonardo $S/FrutaMIDI > $S/leonardo-std.log 2>&1
echo "leonardo-std exit=$?" >> $S/summary.txt
