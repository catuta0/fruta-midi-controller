---
name: firmware-workflow
description: Firmware route for FrutaMIDI: compile with project-local arduino-cli cores and run host unit tests. Use for any firmware/ task.
---

# Firmware workflow

- Config: `arduino-cli --config-file tools/arduino/cli.yaml` (cores rp2040:rp2040, arduino:avr; libs Adafruit MPR121, MIDI Library, MIDIUSB — all inside `tools/arduino`).
- FQBNs: `rp2040:rp2040:<rpipico|rpipicow|rpipico2|rpipico2w>:usbstack=tinyusb`, `arduino:avr:leonardo`. PCB variant: `--build-property "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB"`.
- MCP: `eng-tools` → `firmware_compile {sketch_dir, board, pcb_variant}`.
- UF2 output: `--output-dir <dir>` → `FrutaMIDI.ino.uf2`.
- Host tests: `.venv/bin/python -m pytest -q tests/firmware` (MCP `run_pytest`). Pure logic should live in a header that compiles on host (e.g. with `c++` from Xcode CLT) or be mirrored in Python only if the mirror is generated from or checked against the C++ source.
- zsh: never store a command in `$A` and run `$A args` (no word splitting).
