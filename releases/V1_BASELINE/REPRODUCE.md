# Reproduce V1_BASELINE

Measured on macOS 26.5.2 (arm64, Apple M4). Tool versions: management/TOOLCHAIN.md.

1. Clone at the release tag `v1.1.0-baseline` and install the project-local toolchain:
   - Arduino: `arduino-cli --config-file tools/arduino/cli.yaml core install rp2040:rp2040 arduino:avr` (arduino-pico 6.3.1, avr 1.8.8) and `lib install "Adafruit MPR121" "MIDI Library" MIDIUSB` (cli.yaml as in management/RESUME.md history / logs/setup-install.log).
   - Python: `python3 -m venv .venv && .venv/bin/pip install pytest pypdf`.
   - TinyTeX v2026.10 in tools/TinyTeX (+ siunitx, enumitem, caption).
   - KiCad 10.0.4 installed in /Applications.
2. Hardware: `sh hardware/scripts/build_all.sh` → regenerates schematic/PCB, fails on any ERC/DRC/parity violation, exports hardware/fabrication/.
3. Checks: `.venv/bin/python sim/systems/interface_check.py` (expect `78 PASS, 0 FAIL`), `sim/systems/pcb_rules_check.py`, `sim/systems/budgets.py`, `sh sim/electronics/calc/run_all.sh`.
4. Firmware tests: `.venv/bin/python -m pytest -q tests/firmware` (expect 295 passed). Host/sampler tests: `cd tests/host/browser && npm ci` then `.venv/bin/python -m pytest -q tests/host` (needs Google Chrome).
5. Firmware binaries: for B in rpipico rpipicow rpipico2 rpipico2w: `arduino-cli --config-file tools/arduino/cli.yaml compile -b rp2040:rp2040:$B:usbstack=tinyusb [--build-property "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB"] --output-dir <dir> firmware/FrutaMIDI`; Leonardo: `-b arduino:avr:leonardo`. Expected sizes: firmware/build.log in this folder. UF2 bytes may differ between toolchain builds; compare sizes, not hashes.
6. Report: `sh reports/report/build.sh`.
7. Verify this folder: `shasum -a 256 -c SHA256SUMS`.

Nothing in this baseline has been tested on real hardware. See the physical validation plan in the report.
